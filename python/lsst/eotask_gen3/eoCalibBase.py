""" Base classes for Electrical Optical (EO) calibration tasks.

Provides six bases classes for different iteration scenarios:

    1. EoAmpExpCalibTask : loops over amps, then over exposures
    2. EoAmpPairCalibTask : loops over amps, then over exposure pairs
    3. EoDetExpCalibTask : loops over exposures (analyzes entire detector)
    4. EoDetRunCalibTask : analyzes run-level data (stacked image or table)
                           for 1 detector
    5. EoRunCalibTask : analyzes instrument-wide run-level data

"""

import copy

import lsst.pex.config as pexConfig
import lsst.pipe.base as pipeBase
import lsst.pipe.base.connectionTypes as cT
from lsst.ip.isr import IsrTask, AssembleCcdTask, Defects
from lsst.afw.cameraGeom import AmplifierIsolator

from .eoDataSelection import EoDataSelection

__all__ = ['EoAmpExpCalibTaskConnections', 'EoAmpExpCalibTaskConfig', 'EoAmpExpCalibTask',
           'EoAmpPairCalibTaskConnections', 'EoAmpPairCalibTaskConfig', 'EoAmpPairCalibTask',
           'EoDetExpCalibTaskConnections', 'EoDetExpCalibTaskConfig', 'EoDetExpCalibTask',
           'EoDetRunCalibTaskConnections', 'EoDetRunCalibTaskConfig', 'EoDetRunCalibTask',
           'EoRunCalibTaskConnections', 'EoRunCalibTaskConfig', 'EoRunCalibTask',
           'CAMERA_CONNECT', 'BIAS_CONNECT', 'DARK_CONNECT', 'DEFECTS_CONNECT', 'GAINS_CONNECT',
           'INPUT_RAW_AMPS_CONNECT', 'OUTPUT_IMAGE_CONNECT', 'ISR_CONFIG', 'ASSEMBLE_CCD_CONFIG',
           'OUTPUT_DEFECTS_CONNECT', 'runIsrOnAmp', 'runIsrOnExp']


CAMERA_CONNECT = cT.PrerequisiteInput(
    name="camera",
    storageClass="Camera",
    doc="Access to camera geometry.",
    dimensions=["instrument"],
    isCalibration=True,
)

PHOTODIODE_CONNECT = cT.Input(
    name="photodiode",
    doc="Input photodiode data",
    storageClass="AstropyTable",
    dimensions=("instrument", "exposure"),
    multiple=True,
    deferLoad=True
)

BIAS_CONNECT = cT.Input(
    name="eo_bias",
    doc="Input bias calibration.",
    storageClass="ExposureF",
    dimensions=("instrument", "detector"),
    isCalibration=True,
)

DARK_CONNECT = cT.Input(
    name="eo_dark",
    doc="Input dark calibration.",
    storageClass="ExposureF",
    dimensions=("instrument", "detector"),
    isCalibration=True,
)

DEFECTS_CONNECT = cT.Input(
    name='defects',
    doc="Input defect tables.",
    storageClass="Defects",
    dimensions=("instrument", "detector"),
    isCalibration=True,
)

DEFECTS_PREREQ_CONNECT = cT.PrerequisiteInput(
    name='prereq_defects',
    doc="Input defect tables.",
    storageClass="Defects",
    dimensions=("instrument", "detector"),
    minimum=0,
    isCalibration=True,
)

GAINS_CONNECT = cT.PrerequisiteInput(
    name='gains',
    doc="Input per-amp gain calibrations.",
    storageClass="AmpGains",
    dimensions=("instrument", "detector"),
    minimum=0,
    isCalibration=True,
)

INPUT_RAW_AMPS_CONNECT = cT.Input(
    name="raw",
    doc="Input Frames.",
    storageClass="Exposure",
    dimensions=("instrument", "exposure", "detector"),
    multiple=True,
    deferLoad=True,
)

INPUT_STACK_EXP_CONNECT = cT.Input(
    name="calib",
    doc="Stacked Calibrated Input Frame",
    storageClass="ExposureF",
    dimensions=("instrument", "detector"),
    isCalibration=True,
)

OUTPUT_CONNECT = cT.Output(
    name="calibOutput",
    doc="Electrial Optical Calibration Output",
    storageClass="IsrCalib",
    dimensions=("instrument", "detector"),
)

OUTPUT_IMAGE_CONNECT = cT.Output(
    name="calibOutput",
    doc="Combined Image",
    storageClass="ExposureF",
    dimensions=("instrument", "detector"),
    isCalibration=True,
)

OUTPUT_DEFECTS_CONNECT = cT.Output(
    name='defects',
    doc="Output defect tables.",
    storageClass="Defects",
    dimensions=("instrument", "detector"),
    isCalibration=True,
)

ISR_CONFIG = pexConfig.ConfigurableField(
    target=IsrTask,
    doc="Used to run a reduced version of ISR approrpiate for EO analyses",
)

ASSEMBLE_CCD_CONFIG = pexConfig.ConfigurableField(
    target=AssembleCcdTask,
    doc="Used to run a reduced version of ISR approrpiate for EO analyses",
)


def runIsrOnAmp(task, ampExposure, **kwargs):
    return task.isr.run(ampExposure, **kwargs).exposure


def runIsrOnExp(task, rawExposure, **kwargs):
    return task.isr.run(rawExposure, **kwargs).exposure


def copyConnect(connection):
    return copy.deepcopy(connection)


def copyConfig(config):
    return copy.deepcopy(config)


def extractAmpImage(detImage, amp):
    return AmplifierIsolator.apply(detImage, amp)


def extractAmpDefects(detDefects, amp):
    return Defects()
    # return detDefects.getAmpDefects(amp)


def extractAmpNonlinearity(detNlc, amp):
    return detNlc[amp]


def extractAmpGain(detGain, amp):
    return detGain[amp]


def extractAmpCalibs(amp, **kwargs):
    detBias = kwargs.get('bias', None)
    detDark = kwargs.get('dark', None)
    detDefects = kwargs.get('defects', None)
    detNlc = kwargs.get('linearity', None)
    detGain = kwargs.get('gain', None)
    ampCalibDict = {}
    if detBias is not None:
        ampCalibDict['bias'] = extractAmpImage(detBias, amp)
    if detDark is not None:
        ampCalibDict['dark'] = extractAmpImage(detDark, amp)
    if detDefects is not None:
        ampCalibDict['defects'] = extractAmpDefects(detDefects, amp)
    if detNlc is not None:
        ampCalibDict['linearity'] = extractAmpNonlinearity(detNlc, amp)
    if detGain is not None:
        ampCalibDict['gain'] = extractAmpGain(detGain, amp)
    return ampCalibDict


def arrangeFlatsByExpId(exposureList, exposureIdList):
    """Arrange exposures by exposure ID.
    There is no guarantee that this will properly group exposures, but
    allows a sequence of flats that have different illumination
    (despite having the same exposure time) to be processed.
    Parameters
    ----------
    exposureList : `list`[`lsst.afw.image.exposure.exposure.ExposureF`]
        Input list of exposures.
    exposureIdList : `list`[`int`]
        List of exposure ids as obtained by dataId[`exposure`].
    Returns
    ------
    flatsAtExpId : `dict` [`float`,
                   `list`[(`lsst.afw.image.ExposureF`, `int`)]]
        Dictionary that groups flat-field exposures (and their IDs)
        sequentially by their exposure id.
    Notes
    -----
    This algorithm sorts the input exposures by their exposure id, and
    then assigns each pair of exposures (exp_j, exp_{j+1}) to pair k,
    such that 2*k = j, where j is the python index of one of the
    exposures (starting from zero).  By checking for the IndexError
    while appending, we can ensure that there will only ever be fully
    populated pairs.
    """
    flatsAtExpId = {}
    # sortedExposures = sorted(exposureList,
    #    key=lambda exp: exp.getInfo().getVisitInfo().getExposureId())
    assert len(exposureList) == len(exposureIdList), "Different lengths for exp. list and exp. ID lists"
    # Sort exposures by expIds, which are in the second list `exposureIdList`.
    sortedExposures = sorted(zip(exposureList, exposureIdList), key=lambda pair: pair[1])

    for jPair, expTuple in enumerate(sortedExposures):
        if (jPair + 1) % 2:
            kPair = jPair // 2
            listAtExpId = flatsAtExpId.setdefault(kPair, [])
            try:
                listAtExpId.append(expTuple)
                listAtExpId.append(sortedExposures[jPair + 1])
            except IndexError:
                pass

    return flatsAtExpId


class EoAmpExpCalibTaskConnections(pipeBase.PipelineTaskConnections,
                                   dimensions=("instrument", "detector")):
    """ Class snippet with connections needed to read raw amplifier data and
    perform minimal Isr on each amplifier """
    camera = copyConnect(CAMERA_CONNECT)
    bias = copyConnect(BIAS_CONNECT)
    defects = copyConnect(DEFECTS_CONNECT)
    dark = copyConnect(DARK_CONNECT)
    gains = copyConnect(GAINS_CONNECT)
    inputExps = copyConnect(INPUT_RAW_AMPS_CONNECT)


class EoAmpExpCalibTaskConfig(pipeBase.PipelineTaskConfig,
                              pipelineConnections=EoAmpExpCalibTaskConnections):
    """ Class snippet to define IsrTask as a sub-task and attach the
    correct connections """
    isr = copyConfig(ISR_CONFIG)
    dataSelection = pexConfig.ChoiceField("Data sub-selection rules", str,
                                          EoDataSelection.choiceDict(), default="any")


class EoAmpExpCalibTask(pipeBase.PipelineTask):
    """ Class snippet for tasks that loop over amps, then over exposures

    Implements four methods that can be overridden in sub-classes:

        1. makeOutputData (required, called once)
        2. analyzeAmpExpData (optional, called for each amp, exposure)
        3. analyzeAmpRunData (optional, called for each amp after exposures)
        4. analyzeDetRunData (optional, called once after all amps)

    """
    ConfigClass = EoAmpExpCalibTaskConfig
    _DefaultName = "DoNotUse"

    def __init__(self, **kwargs):
        """ C'tor """
        super().__init__(**kwargs)
        self.makeSubtask("isr")
        self._dataSelection = EoDataSelection.getSelection(self.config.dataSelection)

    @property
    def dataSelection(self):
        return self._dataSelection

    @property
    def getDataQuery(self):
        return self._dataSelection.queryString

    def runQuantum(self, butlerQC, inputRefs, outputRefs):
        """ Here we filter the input data selection

        This will filter the input data using the `dataSelection`

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
        if hasattr(inputRefs, 'photodiodeData'):
            inputRefs.photodiodeData = self.dataSelection.selectData(inputRefs.photodiodeData)
            if len(inputRefs.inputExps) != len(inputRefs.photodiodeData):
                raise ValueError("Number of exposures (%i) != number of photodiode data (%i)"
                                 % (len(inputRefs.inputExps), len(inputRefs.photodiodeData)))
        inputs = butlerQC.get(inputRefs)
        outputs = self.run(**inputs)
        butlerQC.put(outputs, outputRefs)

    def run(self, inputExps, **kwargs):  # pylint: disable=arguments-differ
        """ Run method

        Parameters
        ----------
        inputExps :
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
        outputData : `lsst.eotask_gen3.EoCalib`
            Output data in formatted tables
        """
        camera = kwargs['camera']
        numExps = len(inputExps)
        if numExps < 1:
            raise RuntimeError("No valid input data")

        det = inputExps[0].get().getDetector()
        nAmps = len(det.getAmplifiers())
        outputData = self.makeOutputData(amps=det.getAmplifiers(), nAmps=nAmps, nExposure=len(inputExps),
                                         camera=camera, detector=det)

        for iamp, amp in enumerate(det.getAmplifiers()):
            ampCalibs = extractAmpCalibs(amp, **kwargs)
            for iExp, inputExp in enumerate(inputExps):
                calibExp = runIsrOnAmp(self, inputExp.get(parameters={"amp": iamp}), **ampCalibs)
                amp2 = calibExp.getDetector().getAmplifiers()[0]
                self.analyzeAmpExpData(calibExp, outputData, iamp, amp2, iExp)
            self.analyzeAmpRunData(outputData, iamp, amp2)
        self.analyzeDetRunData(outputData)
        return pipeBase.Struct(outputData=outputData)

    def makeOutputData(self, **kwargs):
        raise NotImplementedError

    def analyzeAmpExpData(self, calibExp, outputData, iamp, amp, iExp):
        """ Analyze calibrated exposure for one amp

        Parameter
        ---------
        calibExp : `lsst.afw.image.ExposureF`
            The calibrated exposure
        outputData : `lsst.eotask_gen3.EoCalib`
            The output data container
        iamp : `int`
            Index for the amplifier
        amp : `lsst.afw.geom.AmplifierGeometry`
            The amplifier
        iExp : `int`
            Index for the exposure
        """

    def analyzeAmpRunData(self, outputData, iamp, amp):
        """ Aggregate data from all exposures for one amp

        Parameter
        ---------
        outputData : `lsst.eotask_gen3.EoCalib`
            The output data container
        iamp : `int`
            Index for the amplifier
        iExp : `int`
            Index for the exposure
        """

    def analyzeDetRunData(self, outputData):
        """ Aggregate data from amps for detector

        Parameter
        ---------
        outputData : `lsst.eotask_gen3.EoCalib`
            The output data container
        """


class EoAmpPairCalibTaskConnections(pipeBase.PipelineTaskConnections,
                                    dimensions=("instrument", "detector")):
    """ Class snippet with connections needed to read raw amplifier data and
    perform minimal Isr on each amplifier """
    camera = copyConnect(CAMERA_CONNECT)
    bias = copyConnect(BIAS_CONNECT)
    defects = copyConnect(DEFECTS_CONNECT)
    gains = copyConnect(GAINS_CONNECT)
    dark = copyConnect(DARK_CONNECT)
    inputExps = copyConnect(INPUT_RAW_AMPS_CONNECT)


class EoAmpPairCalibTaskConfig(pipeBase.PipelineTaskConfig,
                               pipelineConnections=EoAmpPairCalibTaskConnections):
    """ Class snippet to define IsrTask as a sub-task and attach the
    correct connections """
    isr = copyConfig(ISR_CONFIG)
    dataSelection = pexConfig.ChoiceField("Data sub-selection rules", str,
                                          EoDataSelection.choiceDict(), default="any")


class EoAmpPairCalibTask(pipeBase.PipelineTask):
    """ Class snippet for tasks that loop over amps, then over exposure pairs

    Implements four methods that can be overridden in sub-classes:

        1. makeOutputData (required, called once)
        2. analyzeAmpPairData (optional, called for each amp, pair)
        3. analyzeAmpRunData (optional, called for each amp after pair)
        4. analyzeDetRunData (optional, called once after all amps)

    """
    ConfigClass = EoAmpPairCalibTaskConfig
    _DefaultName = "DoNotUse"

    def __init__(self, **kwargs):
        """ C'tor """
        super().__init__(**kwargs)
        self.makeSubtask("isr")
        self._dataSelection = EoDataSelection.getSelection(self.config.dataSelection)

    @property
    def dataSelection(self):
        return self._dataSelection

    @property
    def getDataQuery(self):
        return self._dataSelection.queryString

    def runQuantum(self, butlerQC, inputRefs, outputRefs):
        """Ensure that the input and output dimensions are passed along.

        This will filter the input data using the dataSelection and sort
        the input exposures into pairs

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
        if hasattr(inputRefs, 'photodiodeData'):
            inputRefs.photodiodeData = self.dataSelection.selectData(inputRefs.photodiodeData)

        inputs = butlerQC.get(inputRefs)

        inputExps = inputs.pop('inputExps')
        expIds = [expId.dataId['exposure'] for expId in inputExps]
        inputPairs = [v for v in arrangeFlatsByExpId(inputExps, expIds).values()]

        try:
            pdData = inputs['photodiodeData']
            pdDict = {pdRef.dataId['exposure']: pdRef for pdRef in pdData}
            pdPairs = [[pdDict[expId[0][1]], pdDict[expId[1][1]]] for expId in inputPairs]
        except Exception:
            pdPairs = None

        inputs['inputPairs'] = inputPairs
        if pdPairs is not None:
            inputs['photodiodePairs'] = pdPairs

        outputs = self.run(**inputs)
        butlerQC.put(outputs, outputRefs)

    def run(self, inputPairs, **kwargs):  # pylint: disable=arguments-differ
        """ Run method

        Parameters
        ----------
        inputPairs :
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
        outputData : `lsst.eotask_gen3.EoCalib`
            Output data in formatted tables
        """
        camera = kwargs['camera']
        nPair = len(inputPairs)
        if nPair < 1:
            raise RuntimeError("No valid input data")

        det = inputPairs[0][0][0].get().getDetector()

        amps = det.getAmplifiers()
        outputData = self.makeOutputData(amps=amps, nAmps=len(amps), nPair=len(inputPairs),
                                         camera=camera, detector=det)
        for iamp, amp in enumerate(amps):

            ampCalibs = extractAmpCalibs(amp, **kwargs)
            for iPair, inputPair in enumerate(inputPairs):
                if len(inputPair) != 2:
                    self.log.warn("Length of pair %i = %i" % (iPair, len(inputPair)))
                    continue
                calibExp1 = runIsrOnAmp(self, inputPair[0][0].get(parameters={"amp": iamp}), **ampCalibs)
                calibExp2 = runIsrOnAmp(self, inputPair[1][0].get(parameters={"amp": iamp}), **ampCalibs)
                amp2 = calibExp1.getDetector().getAmplifiers()[0]

                self.analyzeAmpPairData(calibExp1, calibExp2, outputData, amp2, iPair)
            self.analyzeAmpRunData(outputData, iamp, amp2)
        self.analyzeDetRunData(outputData)
        return pipeBase.Struct(outputData=outputData)

    def makeOutputData(self, **kwargs):
        raise NotImplementedError

    def analyzeAmpPairData(self, calibExp1, calibExp2, outputData, amp, iPair):
        """ Analyze calibrated exposure pair for one amp

        Parameter
        ---------
        calibExp1 : `lsst.afw.image.ExposureF`
            The first calibrated exposure
        calibExp2 : `lsst.afw.image.ExposureF`
            The second calibrated exposure
        outputData : `lsst.eotask_gen3.EoCalib`
            The output data container
        amp : `lsst.afw.geom.AmplifierGeometry`
            The amplifier
        iPair : `int`
            Index for the exposure
        """

    def analyzeAmpRunData(self, outputData, amp):
        """ Aggregate data from all exposures pairs for one amp

        Parameter
        ---------
        outputData : `lsst.eotask_gen3.EoCalib`
            The output data container
        amp : `lsst.afw.geom.AmplifierGeometry`
            The amplifier
        """

    def analyzeDetRunData(self, outputData):
        """ Aggregate data from amps for detector

        Parameter
        ---------
        outputData : `lsst.eotask_gen3.EoCalib`
            The output data container
        """


class EoDetExpCalibTaskConnections(pipeBase.PipelineTaskConnections,
                                   dimensions=("instrument", "detector", "exposure")):
    """ Class snippet with connections needed to read raw data
    and perform mininal Isr """
    camera = copyConnect(CAMERA_CONNECT)
    bias = copyConnect(BIAS_CONNECT)
    defects = copyConnect(DEFECTS_CONNECT)
    gains = copyConnect(GAINS_CONNECT)
    inputExps = copyConnect(INPUT_RAW_AMPS_CONNECT)
    output = copyConnect(OUTPUT_CONNECT)


class EoDetExpCalibTaskConfig(pipeBase.PipelineTaskConfig,
                              pipelineConnections=EoDetExpCalibTaskConnections):
    """ Class snippet to use connections for stacked-calibrated exposure """
    isr = copyConfig(ISR_CONFIG)


class EoDetExpCalibTask(pipeBase.PipelineTask):
    """ Class snippet for tasks that loop over amps on stacked image

    Implements three methods that can be overridden in sub-classes:

        1. makeOutputData (required, called once)
        2. analyzeAmpRunData (optional, called for each amp)
        3. analyzeDetRunData (optional, called once after all amps)

    """

    ConfigClass = EoDetExpCalibTaskConfig
    _DefaultName = "DoNotUse"

    def __init__(self, **kwargs):
        """ C'tor """
        super().__init__(**kwargs)
        self.makeSubtask("isr")

    def run(self, inputExps, **kwargs):  # pylint: disable=arguments-differ
        """ Run method

        Parameters
        ----------
        stackedCalExp :
            Input data

        Keywords
        --------
        camera : `lsst.obs.lsst.camera`, optional
            The camera object, used to look up detector geometry

        Returns
        -------
        outputData : `EoCalib`
            Output data in formatted tables
        """
        camera = kwargs['camera']
        # det = camera.get(inputExps[0].dataId['detector'])
        det = inputExps[0].get().getDetector()
        outputData = self.makeOutputData(nExposure=len(inputExps), detector=det, camera=camera)
        for iExp, inputExp in enumerate(inputExps):
            calibExp = runIsrOnExp(self, inputExp.get(), **kwargs)
            self.analyzeDetExpData(calibExp, outputData, iExp)
        self.analyzeDetRunData(outputData)
        return pipeBase.Struct(outputData=outputData)

    def makeOutputData(self, **kwargs):
        raise NotImplementedError

    def analyzeDetExpData(self, calibExp, outputData, iExp):
        """ Analyze data from one ccd

        Parameter
        ---------
        calibExp : `lsst.afw.image.ExposureF`
            The calibrated exposure
        outputData : `lsst.eotask_gen3.EoCalib`
            The output data container
        iExp : `int`
            Index for the exposure
        """

    def analyzeDetRunData(self, outputData):
        """ Aggregate data from for detector

        Parameter
        ---------
        outputData : `lsst.eotask_gen3.EoCalib`
            The output data container
        """


class EoDetRunCalibTaskConnections(pipeBase.PipelineTaskConnections,
                                   dimensions=("instrument", "detector")):
    """ Class snippet with connections needed to read calibrated data """


class EoDetRunCalibTaskConfig(pipeBase.PipelineTaskConfig,
                              pipelineConnections=EoDetRunCalibTaskConnections):
    """ Class snippet to use connections for stacked-calibrated exposure """


class EoDetRunCalibTask(pipeBase.PipelineTask):
    """ Class snippet for tasks that analyze a stacked image

    Implements three methods that can be overridden in sub-classes:

        1. makeOutputData (required, called once)
        2. analyzeDetRunData (required, called once)

    """

    ConfigClass = EoDetRunCalibTaskConfig
    _DefaultName = "DoNotUse"

    def makeOutputData(self, **kwargs):
        raise NotImplementedError

    def analyzeDetRunData(self, outputData, **kwargs):
        """ Analyze data

        Parameter
        ---------
        outputData : `lsst.eotask_gen3.EoCalib`
            The output data container
        """


class EoRunCalibTaskConnections(pipeBase.PipelineTaskConnections,
                                dimensions=("instrument",)):
    """ Class snippet with connections needed to read calibrated data """
    output = copyConnect(OUTPUT_CONNECT)


class EoRunCalibTaskConfig(pipeBase.PipelineTaskConfig,
                           pipelineConnections=EoRunCalibTaskConnections):
    """ Class snippet to use connections for stacked-calibrated exposure """


class EoRunCalibTask(pipeBase.PipelineTask):
    """ Class snippet for tasks that analyze a stacked image

    Implements three methods that can be overridden in sub-classes:

        1. makeOutputData (required, called once)
        3. analyzeRunData (required, called once)

    """

    ConfigClass = EoRunCalibTaskConfig
    _DefaultName = "DoNotUse"

    def run(self, **kwargs):  # pylint: disable=arguments-differ
        """ Run method

        Keywords
        --------
        camera : `lsst.obs.lsst.camera`, optional
            The camera object, used to look up detector geometry

        Returns
        -------
        outputData : `lsst.eotask_gen3.EoCalib`
            Output data in formatted tables
        """
        outputData = self.makeOutputData(**kwargs)
        self.analyzeRunData(outputData, **kwargs)
        return pipeBase.Struct(outputData=outputData)

    def makeOutputData(self, **kwargs):
        raise NotImplementedError

    def analyzeRunData(self, outputData, **kwargs):
        """ Analyze data

        Parameter
        ---------
        outputData : `lsst.eotask_gen3.EoCalib`
            The output data container
        """
