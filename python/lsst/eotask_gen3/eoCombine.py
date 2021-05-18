import time
from collections import OrderedDict

import lsst.pex.config as pexConfig
import lsst.pipe.base as pipeBase
import lsst.afw.math as afwMath
import lsst.afw.image as afwImage

from lsst.ip.isr import IsrTask, AssembleCcdTask
from astro_metadata_translator import merge_headers, ObservationGroup
from astro_metadata_translator.serialize import dates_to_fits

from .eoCalibBase import CAMERA_CONNECT, BIAS_CONNECT, DARK_CONNECT, DEFECTS_CONNECT,\
                          GAINS_CONNECT, INPUT_RAW_AMPS_CONNECT, OUTPUT_IMAGE_CONNECT,\
                          copyConnect, runIsrOnAmp, extractAmpCalibs


class EoCombineCalibTaskConnections(pipeBase.PipelineTaskConnections,
                                    dimensions=("instrument", "exposure", "detector")):
    """ Class snippet with connections needed to read raw amplifier data and
    perform minimal Isr on each amplifier """
    camera = copyConnect(CAMERA_CONNECT)
    inputExps = copyConnect(INPUT_RAW_AMPS_CONNECT)
    outputImage = copyConnect(OUTPUT_IMAGE_CONNECT)


class EoCombineCalibTaskConfig(pipeBase.PipelineTaskConfig,
                               pipelineConnections=EoCombineCalibTaskConnections):
    """ Class snippet to define IsrTask and AssembleCCD as sub-tasks and
    attach the correct connections """

    calibrationType = pexConfig.Field(
        dtype=str,
        default="calibration",
        doc="Name of calibration to be generated.",
    )

    maxVisitsToCalcErrorFromInputVariance = pexConfig.Field(
        dtype=int,
        default=5,
        doc="Maximum number of visits to estimate variance from input variance, not per-pixel spread",
    )

    mask = pexConfig.ListField(
        dtype=str,
        default=["SAT", "DETECTED", "INTRP"],
        doc="Mask planes to respect",
    )

    combine = pexConfig.Field(
        dtype=str,
        default='MEDIAN',
        doc="Statistic name to use for combination (from lsst.afw.math)",
    )

    clip = pexConfig.Field(
        dtype=float,
        default=3.0,
        doc="Clipping threshold for combination",
    )

    nIter = pexConfig.Field(
        dtype=int,
        default=3,
        doc="Clipping iterations for combination",
    )

    isr = pexConfig.ConfigurableField(
        target=IsrTask,
        doc="Used to run a reduced version of ISR approrpiate for EO analyses",
    )

    assembleCcd = pexConfig.ConfigurableField(
        target=AssembleCcdTask,
        doc="Used to run a reduced version of ISR approrpiate for EO analyses",
    )


class EoCombineCalibTask(pipeBase.PipelineTask):
    """ Class snippet for tasks that loop over amps, then over exposures
    and produces stacked and assembled output

    """
    ConfigClass = EoCombineCalibTaskConfig
    _DefaultName = "DoNotUse"

    def __init__(self, **kwargs):
        """ C'tor """
        super().__init__(**kwargs)
        self.makeSubtask("isr")
        self.makeSubtask("assembleCcd")

    def run(self, inputExps, **kwargs):  # pylint: disable=arguments-differ
        """ Run method

        Parameters
        ----------
        inputExps :
            Used to retrieve the exposures

        Keywords
        --------
        camera : `lsst.obs.lsst.camera`
        bias : `ExposureF`
        defects : `Defects`
        gains : `Gains`

        Returns
        -------
        combined : `ExpsoureF`
            Stacked and assembled output
        """
        camera = kwargs['camera']
        det = camera.get(inputExps[0].dataId['detector'])
        ampDict = OrderedDict()

        stats = afwMath.StatisticsControl(self.config.clip, self.config.nIter,
                                          afwImage.Mask.getPlaneBitMask(self.config.mask))
        numExps = len(inputExps)
        if numExps < 1:
            raise RuntimeError("No valid input data")
        if numExps < self.config.maxVisitsToCalcErrorFromInputVariance:
            stats.setCalcErrorFromInputVariance(True)

        for amp in det.getAmplifiers():
            toStack = []
            ampCalibs = extractAmpCalibs(amp, **kwargs)
            for inputExp in inputExps:
                calibExp = runIsrOnAmp(self, inputExp.get(parameters={amp: amp}), amp, **ampCalibs)
                toStack.append(calibExp.getMaskedImage())
            combined = afwImage.MaskedImageF(amp.getWidth(), amp.getHeight())
            combinedExp = afwImage.makeExposure(combined)  # pylint: disable=no-member
            combineType = afwMath.stringToStatisticsProperty(self.config.combine)  # pylint: disable=no-member
            afwMath.statisticsStack(combinedExp, toStack, combineType, stats)  # pylint: disable=no-member
            combinedExp.setDetector(det)
            ampDict[amp.name] = combinedExp
        outputImage = self.assembleCcd.assembleCcd(ampDict)  # pylint: disable=no-member
        self.combineHeaders(inputExps, outputImage, calibType=self.config.calibrationType)
        return pipeBase.Struct(outputImage=outputImage)


    def combineHeaders(self, expList, calib, calibType="CALIB"):
        """Combine input headers to determine the set of common headers,
        supplemented by calibration inputs.

        Parameters
        ----------
        expList : `list` of `lsst.afw.image.Exposure`
            Input list of exposures to combine.
        calib : `lsst.afw.image.Exposure`
            Output calibration to construct headers for.
        calibType: `str`, optional
            OBSTYPE the output should claim.

        Returns
        -------
        header : `lsst.daf.base.PropertyList`
            Constructed header.
        """
        # Header
        header = calib.getMetadata()
        header.set("OBSTYPE", calibType)

        # Keywords we care about
        comments = {"TIMESYS": "Time scale for all dates",
                    "DATE-OBS": "Start date of earliest input observation",
                    "MJD-OBS": "[d] Start MJD of earliest input observation",
                    "DATE-END": "End date of oldest input observation",
                    "MJD-END": "[d] End MJD of oldest input observation",
                    "MJD-AVG": "[d] MJD midpoint of all input observations",
                    "DATE-AVG": "Midpoint date of all input observations"}

        # Creation date
        now = time.localtime()
        calibDate = time.strftime("%Y-%m-%d", now)
        calibTime = time.strftime("%X %Z", now)
        header.set("CALIB_CREATE_DATE", calibDate)
        header.set("CALIB_CREATE_TIME", calibTime)

        # Merge input headers
        inputHeaders = [exp.getMetadata() for exp in expList if exp is not None]
        merged = merge_headers(inputHeaders, mode='drop')
        for k, v in merged.items():
            if k not in header:
                md = expList[0].getMetadata()
                comment = md.getComment(k) if k in md else None
                header.set(k, v, comment=comment)

        # Construct list of visits
        visitInfoList = [exp.getInfo().getVisitInfo() for exp in expList if exp is not None]
        for i, visit in enumerate(visitInfoList):
            if visit is None:
                continue
            header.set("CPP_INPUT_%d" % (i,), visit.getExposureId())
            header.set("CPP_INPUT_DATE_%d" % (i,), str(visit.getDate()))
            header.set("CPP_INPUT_EXPT_%d" % (i,), visit.getExposureTime())

        # Not yet working: DM-22302
        # Create an observation group so we can add some standard headers
        # independent of the form in the input files.
        # Use try block in case we are dealing with unexpected data headers
        try:
            group = ObservationGroup(visitInfoList, pedantic=False)
        except Exception:
            self.log.warn("Exception making an obs group for headers. Continuing.")
            # Fall back to setting a DATE-OBS from the calibDate
            dateCards = {"DATE-OBS": "{}T00:00:00.00".format(calibDate)}
            comments["DATE-OBS"] = "Date of start of day of calibration midpoint"
        else:
            oldest, newest = group.extremes()
            dateCards = dates_to_fits(oldest.datetime_begin, newest.datetime_end)

        for k, v in dateCards.items():
            header.set(k, v, comment=comments.get(k, None))

        return header


class EoCombineBiasTaskConnections(EoCombineCalibTaskConnections):
    """ Class snippet with connections needed to read raw amplifier data and
    perform minimal Isr on each amplifier """


class EoCombineBiasTaskConfig(pipeBase.PipelineTaskConfig,
                              pipelineConnections=EoCombineBiasTaskConnections):

    def setDefaults(self):
        # pylint: disable=no-member        
        self.connections.output = "cpBias"
        self.isr.expectWcs = False
        self.isr.doSaturation = False
        self.isr.doSetBadRegions = False
        self.isr.doAssembleCcd = False
        self.isr.doBias = False
        self.isr.doLinearize = False
        self.isr.doDefect = False
        self.isr.doNanMasking = False
        self.isr.doWidenSaturationTrails = False
        self.isr.doDark = False
        self.isr.doFlat = False
        self.isr.doFring = False
        self.isr.doInterpolate = False
        self.isr.doWrite = False
        self.assembleCcd.doTrim = False


class EoCombineBiasTask(EoCombineCalibTask):
    """ Class snippet for tasks that loop over amps, then over exposures
    and produces stacked and assembled output

    """
    ConfigClass = EoCombineBiasTaskConfig
    _DefaultName = "combineBias"



class EoCombineDarkTaskConnections(EoCombineCalibTaskConnections):
    """ Class snippet with connections needed to read raw amplifier data and
    perform minimal Isr on each amplifier """

    bias = copyConnect(BIAS_CONNECT)
    defects = copyConnect(DEFECTS_CONNECT)


class EoCombineDarkTaskConfig(pipeBase.PipelineTaskConfig,
                              pipelineConnections=EoCombineDarkTaskConnections):

    def setDefaults(self):
        # pylint: disable=no-member
        self.connections.output = "cpBias"
        self.isr.expectWcs = False
        self.isr.doSaturation = True
        self.isr.doSetBadRegions = False
        self.isr.doAssembleCcd = False
        self.isr.doBias = True
        self.isr.doLinearize = False
        self.isr.doDefect = True
        self.isr.doNanMasking = False
        self.isr.doWidenSaturationTrails = False
        self.isr.doDark = False
        self.isr.doFlat = False
        self.isr.doFring = False
        self.isr.doInterpolate = True
        self.isr.doWrite = False
        self.assembleCcd.doTrim = False


class EoCombineDarkTask(EoCombineCalibTask):
    """ Class snippet for tasks that loop over amps, then over exposures
    and produces stacked and assembled output

    """
    ConfigClass = EoCombineDarkTaskConfig
    _DefaultName = "combineDark"


class EoCombineFlatTaskConnections(EoCombineCalibTaskConnections):
    """ Class snippet with connections needed to read raw amplifier data and
    perform minimal Isr on each amplifier """

    bias = copyConnect(BIAS_CONNECT)
    defects = copyConnect(DEFECTS_CONNECT)
    dark = copyConnect(DARK_CONNECT)
    gains = copyConnect(GAINS_CONNECT)


class EoCombineFlatTaskConfig(pipeBase.PipelineTaskConfig,
                              pipelineConnections=EoCombineFlatTaskConnections):

    def setDefaults(self):
        # pylint: disable=no-member        
        self.connections.output = "cpBias"
        self.isr.expectWcs = False
        self.isr.doSaturation = True
        self.isr.doSetBadRegions = False
        self.isr.doAssembleCcd = False
        self.isr.doBias = True
        self.isr.doLinearize = False
        self.isr.doDefect = True
        self.isr.doNanMasking = False
        self.isr.doWidenSaturationTrails = False
        self.isr.doDark = True
        self.isr.doFlat = False
        self.isr.doFring = False
        self.isr.doInterpolate = True
        self.isr.doWrite = False
        self.assembleCcd.doTrim = False


class EoCombineFlatTask(EoCombineCalibTask):
    """ Class snippet for tasks that loop over amps, then over exposures
    and produces stacked and assembled output

    """
    ConfigClass = EoCombineFlatTaskConfig
    _DefaultName = "combineFlat"