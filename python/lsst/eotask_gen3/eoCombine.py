from collections import OrderedDict

import lsst.pex.config as pexConfig
import lsst.pipe.base as pipeBase
import lsst.afw.math as afwMath
import lsst.afw.image as afwImage

from lsst.ip.isr import IsrTask, AssembleCcdTask

from .eoCalibBase import CAMERA_CONNECT, BIAS_CONNECT, DARK_CONNECT, DEFECTS_PREREQ_CONNECT,\
    INPUT_RAW_AMPS_CONNECT, OUTPUT_IMAGE_CONNECT,\
    copyConnect, runIsrOnAmp, extractAmpCalibs

from .eoDataSelection import EoDataSelection


class EoCombineCalibTaskConnections(pipeBase.PipelineTaskConnections,
                                    dimensions=("instrument", "detector")):
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

    dataSelection = pexConfig.ChoiceField(
        dtype=str,
        allowed=EoDataSelection.choiceDict(),
        doc="Data sub-selection rules",
        default="any"
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
        self._dataSelection = EoDataSelection.getSelection(self.config.dataSelection)

    @property
    def dataSelection(self):
        return self._dataSelection

    @property
    def getDataQuery(self):
        return self._dataSelection.queryString

    def runQuantum(self, butlerQC, inputRefs, outputRefs):
        """ Here we filter the input data selection

        Parameters
        ----------
        butlerQC : `~lsst.daf.butler.butlerQuantumContext.ButlerQuantumContext`
            Butler to operate on.
        inputRefs : `~lsst.pipe.base.connections.InputQuantizedConnection`
            Input data refs to load.
        ouptutRefs : `~lsst.pipe.base.connections.OutputQuantizedConnection`
            Output data refs to persist.
        """
        inputRefs.inputExps = self.dataSelection.selectData(inputRefs.inputExps)
        inputs = butlerQC.get(inputRefs)
        outputs = self.run(**inputs)
        butlerQC.put(outputs, outputRefs)

    def run(self, inputExps, **kwargs):  # pylint: disable=arguments-differ
        """ Run method

        Parameters
        ----------
        inputExps : `list` ['lsst.daf.butler.DeferredDatasetRef']
            Used to retrieve the exposures

        Keywords
        --------
        camera : `lsst.obs.lsst.camera`, optional
            The camera object, used to look up detector geometry
        bias : `lsst.afw.image.ExposureF`, optional
            The bias frame to subtrace
        defects : `lsst.ip.isr.Defects`
            The defect set
        gains : ??

        Returns
        -------
        combined : `ExpsoureF`
            Stacked and assembled output
        """
        # camera = kwargs['camera']
        # det = camera.get(inputExps[0].dataId['detector'])
        ampDict = OrderedDict()

        stats = afwMath.StatisticsControl(self.config.clip, self.config.nIter,
                                          afwImage.Mask.getPlaneBitMask(self.config.mask))
        numExps = len(inputExps)
        if numExps < 1:
            raise RuntimeError("No valid input data")
        if numExps < self.config.maxVisitsToCalcErrorFromInputVariance:
            stats.setCalcErrorFromInputVariance(True)
        det = inputExps[0].get().getDetector()

        # for iamp, (amp, amp2) in enumerate(zip(det.getAmplifiers(),
        #     det2.getAmplifiers())):
        for iamp, amp in enumerate(det.getAmplifiers()):
            toStack = []
            ampCalibs = extractAmpCalibs(amp, **kwargs)
            for inputExp in inputExps:
                calibExp = runIsrOnAmp(self, inputExp.get(parameters={"amp": iamp}), **ampCalibs)
                toStack.append(calibExp.getMaskedImage())
            combined = afwImage.MaskedImageF(amp.getRawBBox())
            combinedExp = afwImage.makeExposure(combined)  # pylint: disable=no-member
            combineType = afwMath.stringToStatisticsProperty(self.config.combine)  # pylint: disable=no-member
            afwMath.statisticsStack(combined, toStack, combineType, stats)  # pylint: disable=no-member
            combinedExp.setDetector(det)
            ampDict[amp.getName()] = combinedExp
        outputImage = self.assembleCcd.assembleCcd(ampDict)  # pylint: disable=no-member
        # FIXME, this should be a method provided by ip_isr or cp_pipe
        # self.combineHeaders(inputExps, outputImage,
        #     calibType=self.config.calibrationType)
        return pipeBase.Struct(outputImage=outputImage)


class EoCombineBiasTaskConnections(EoCombineCalibTaskConnections):
    """ Specialization for combining bias frames """


class EoCombineBiasTaskConfig(EoCombineCalibTaskConfig,
                              pipelineConnections=EoCombineBiasTaskConnections):

    def setDefaults(self):
        # pylint: disable=no-member
        self.connections.outputImage = "eoBias"
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
        self.isr.doFringe = False
        self.isr.doInterpolate = False
        self.isr.doWrite = False
        self.assembleCcd.doTrim = False
        self.dataSelection = 'anyBias'


class EoCombineBiasTask(EoCombineCalibTask):
    """ Specific class to combine bias frames """

    ConfigClass = EoCombineBiasTaskConfig
    _DefaultName = "combineBias"


class EoCombineDarkTaskConnections(EoCombineCalibTaskConnections):
    """ Specialization dark frames """

    bias = copyConnect(BIAS_CONNECT)


class EoCombineDarkTaskConfig(EoCombineCalibTaskConfig,
                              pipelineConnections=EoCombineDarkTaskConnections):

    def setDefaults(self):
        # pylint: disable=no-member
        self.connections.outputImage = "eoDark"
        self.isr.expectWcs = False
        self.isr.doSaturation = True
        self.isr.doSetBadRegions = False
        self.isr.doAssembleCcd = False
        self.isr.doBias = True
        self.isr.doLinearize = False
        self.isr.doDefect = False
        self.isr.doNanMasking = False
        self.isr.doWidenSaturationTrails = False
        self.isr.doDark = False
        self.isr.doFlat = False
        self.isr.doFringe = False
        self.isr.doInterpolate = False
        self.isr.doWrite = False
        self.assembleCcd.doTrim = False
        self.dataSelection = 'darkDark'


class EoCombineDarkTask(EoCombineCalibTask):
    """ Specific class to combine dark exposures """
    ConfigClass = EoCombineDarkTaskConfig
    _DefaultName = "combineDark"


class EoCombineFlatTaskConnections(EoCombineCalibTaskConnections):
    """ Specialization for flat frames """

    bias = copyConnect(BIAS_CONNECT)
    defects = copyConnect(DEFECTS_PREREQ_CONNECT)
    dark = copyConnect(DARK_CONNECT)
    # gains = copyConnect(GAINS_CONNECT)


class EoCombineFlatTaskConfig(EoCombineCalibTaskConfig,
                              pipelineConnections=EoCombineFlatTaskConnections):

    def setDefaults(self):
        # pylint: disable=no-member
        self.connections.outputImage = "eoFlatLow"
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
        self.isr.doFringe = False
        self.isr.doInterpolate = False
        self.isr.doWrite = False
        self.assembleCcd.doTrim = False
        self.dataSelection = 'superFlatLow'


class EoCombineFlatTask(EoCombineCalibTask):
    """ Specific class to combine flat exposures """
    ConfigClass = EoCombineFlatTaskConfig
    _DefaultName = "combineFlat"
