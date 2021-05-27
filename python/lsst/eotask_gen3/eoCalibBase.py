""" Base classes for Electrical Optical (EO) calibration tasks.

Provides six bases classes for different iteration scenarios:

    1. EoAmpExpCalibTask : loops over amps, then over exposures
    2. EoAmpPairCalibTask : loops over amps, then over exposure pairs
    3. EoAmpRunCalibTask : loops over amps for a single stacked image
        (e.g., a stacked bias frame or stacked dark frame)
    4. EoDetExpCalibTask : loops over exposures (analyzes entire detector)
    5. EoDetRunCalibTask : analyzes a single stacked image
"""

import copy

import lsst.pex.config as pexConfig
import lsst.pipe.base as pipeBase
import lsst.pipe.base.connectionTypes as cT
from lsst.ip.isr import IsrTask, AssembleCcdTask, Defects
from lsst.afw.cameraGeom import AmplifierIsolator

__all__ = ['EoAmpExpCalibTaskConnections', 'EoAmpExpCalibTaskConfig', 'EoAmpExpCalibTask',
           'EoAmpPairCalibTaskConnections', 'EoAmpPairCalibTaskConfig', 'EoAmpPairCalibTask',
           'EoAmpRunCalibTaskConnections', 'EoAmpRunCalibTaskConfig', 'EoAmpRunCalibTask',
           'EoDetExpCalibTaskConnections', 'EoDetExpCalibTaskConfig', 'EoDetExpCalibTask',
           'EoDetRunCalibTaskConnections', 'EoDetRunCalibTaskConfig', 'EoDetRunCalibTask',
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

BIAS_CONNECT = cT.PrerequisiteInput(
    name="eo_bias",
    doc="Input bias calibration.",
    storageClass="ExposureF",
    dimensions=("instrument", "detector"),
    isCalibration=True,
)

DARK_CONNECT = cT.PrerequisiteInput(
    name="eo_dark",
    doc="Input dark calibration.",
    storageClass="ExposureF",
    dimensions=("instrument", "detector"),
    isCalibration=True,
)

DEFECTS_CONNECT = cT.PrerequisiteInput(
    name='defects',
    doc="Input defect tables.",
    storageClass="Defects",
    dimensions=("instrument", "detector"),
    isCalibration=True,
)

GAINS_CONNECT = cT.PrerequisiteInput(
    name='gains',
    doc="Input per-amp gain calibrations.",
    storageClass="AmpGains",
    dimensions=("instrument", "detector"),
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
)

OUTPUT_CONNECT = cT.Output(
    name="calibOutput",
    doc="Electrial Optical Calibration Output",
    storageClass="EoCalib",
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
    return detDefects.getAmpDefects(amp)

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


class EoAmpExpCalibTaskConnections(pipeBase.PipelineTaskConnections,
                                   dimensions=("instrument", "exposure", "detector")):
    """ Class snippet with connections needed to read raw amplifier data and
    perform minimal Isr on each amplifier """
    camera = copyConnect(CAMERA_CONNECT)
    bias = copyConnect(BIAS_CONNECT)
    defects = copyConnect(DEFECTS_CONNECT)
    gains = copyConnect(GAINS_CONNECT)
    inputExps = copyConnect(INPUT_RAW_AMPS_CONNECT)
    output = copyConnect(OUTPUT_CONNECT)


class EoAmpExpCalibTaskConfig(pipeBase.PipelineTaskConfig,
                              pipelineConnections=EoAmpExpCalibTaskConnections):
    """ Class snippet to define IsrTask as a sub-task and attach the
    correct connections """
    isr = copyConfig(ISR_CONFIG)


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
        outputData : `EoCalib`
            Output data in formatted tables
        """
        camera = kwargs['camera']
        det = camera.get(inputExps[0].dataId['detector'])
        nAmps = len(det.getAmplifiers())
        outputData = self.makeOutputData(amps=det.getAmplifiers(), nAmps=nAmps, nExposure=len(inputExps))
        for amp in det.getAmplifiers():
            ampCalibs = extractAmpCalibs(amp, **kwargs)
            for iExp, inputExp in enumerate(inputExps):
                calibExp = runIsrOnAmp(self, inputExp.get(parameters={amp: amp}), amp, **ampCalibs)
                self.analyzeAmpExpData(calibExp, outputData, amp, iExp)
            self.analyzeAmpRunData(outputData, amp)
        self.analyzeDetRunData(outputData)
        return pipeBase.Struct(outputData=outputData)

    def makeOutputData(self, **kwargs):
        raise NotImplementedError

    def analyzeAmpExpData(self, calibExp, outputData, amp, iExp):
        """ Analyze calibrated exposure for one amp """

    def analyzeAmpRunData(self, outputData, amp):
        """ Aggregate data from all exposures for one amp """

    def analyzeDetRunData(self, outputData):
        """ Aggregate data from amps for detector """


class EoAmpPairCalibTaskConnections(pipeBase.PipelineTaskConnections,
                                    dimensions=("instrument", "exposure", "detector")):
    """ Class snippet with connections needed to read raw amplifier data and
    perform minimal Isr on each amplifier """
    camera = copyConnect(CAMERA_CONNECT)
    bias = copyConnect(BIAS_CONNECT)
    defects = copyConnect(DEFECTS_CONNECT)
    gains = copyConnect(GAINS_CONNECT)
    inputExps = copyConnect(INPUT_RAW_AMPS_CONNECT)
    output = copyConnect(OUTPUT_CONNECT)


class EoAmpPairCalibTaskConfig(pipeBase.PipelineTaskConfig,
                               pipelineConnections=EoAmpPairCalibTaskConnections):
    """ Class snippet to define IsrTask as a sub-task and attach the
    correct connections """
    isr = copyConfig(ISR_CONFIG)


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

    def run(self, inputPairs, **kwargs):  # pylint: disable=arguments-differ
        """ Run method

        Parameters
        ----------
        inputPairs :
            Used to retrieve the exposures

        Keywords
        --------
        camera : `lsst.obs.lsst.camera`
        bias : `ExposureF`
        defects : `Defects`
        gains : `Gains`

        Returns
        -------
        outputData : `EoCalib`
            Output data in formatted tables
        """
        camera = kwargs['camera']
        det = camera.get(inputPairs[0].dataId['detector'])
        amps = det.getAmplifiers()
        outputData = self.makeOutputData(amps=amps, nAmps=len(amps), nPair=len(inputPairs))
        for amp in amps:
            ampCalibs = extractAmpCalibs(amp, **kwargs)
            for iPair, inputPair in enumerate(inputPairs):
                calibExp1 = runIsrOnAmp(self, inputPair[0].get(parameters={amp: amp}), amp, **ampCalibs)
                calibExp2 = runIsrOnAmp(self, inputPair[1].get(parameters={amp: amp}), amp, **ampCalibs)
                self.analyzeAmpPairData(calibExp1, calibExp2, outputData, amp, iPair)
            self.analyzeAmpRunData(outputData, amp)
        self.analyzeDetRunData(outputData)
        return pipeBase.Struct(outputData=outputData)

    def makeOutputData(self, **kwargs):
        raise NotImplementedError

    def analyzeAmpPairData(self, calibExp1, calibExp2, outputData, amp, iPair):
        """ Analyze calibrated exposure pair for one amp """

    def analyzeAmpRunData(self, outputData, amp):
        """ Aggregate data from all exposures pairs for one amp """

    def analyzeDetRunData(self, outputData):
        """ Aggregate data from amps for detector """


class EoAmpRunCalibTaskConnections(pipeBase.PipelineTaskConnections,
                                   dimensions=("instrument", "detector")):
    """ Class snippet with connections needed to read calibrated data """
    stackedCalExp = copyConnect(INPUT_STACK_EXP_CONNECT)
    output = copyConnect(OUTPUT_CONNECT)


class EoAmpRunCalibTaskConfig(pipeBase.PipelineTaskConfig,
                              pipelineConnections=EoAmpRunCalibTaskConnections):
    """ Class snippet to use connections for stacked-calibrated exposure """


class EoAmpRunCalibTask(pipeBase.PipelineTask):
    """ Class snippet for tasks that loop over amps on stacked image

    Implements three methods that can be overridden in sub-classes:

        1. makeOutputData (required, called once)
        2. analyzeAmpRunData (optional, called for each amp)
        3. analyzeDetRunData (optional, called once after all amps)

    """

    ConfigClass = EoAmpRunCalibTaskConfig
    _DefaultName = "DoNotUse"

    def run(self, stackedCalExp, **kwargs):  # pylint: disable=arguments-differ
        """ Run method

        Parameters
        ----------
        stackedCalExp :
            Input data

        Keywords
        --------
        camera : `lsst.obs.lsst.camera`

        Returns
        -------
        outputData : `EoCalib`
            Output data in formatted tables
        """
        camera = kwargs['camera']
        det = camera.get(stackedCalExp.dataId['detector'])
        amps = det.getAmplifiers()
        outputData = self.makeOutputData(amps=amps, nAmps=len(amps))
        for amp in amps:
            ampExposure = extractAmpImage(stackedCalExp, amp)
            self.analyzeAmpRunData(ampExposure, outputData, amp, **kwargs)
        self.analyzeDetRunData(outputData)
        return pipeBase.Struct(outputData=outputData)

    def makeOutputData(self, amps, nAmps):
        raise NotImplementedError

    def analyzeAmpRunData(self, ampExposure, outputData, amp):
        """ Analyze data from on amp """

    def analyzeDetRunData(self, outputData):
        """ Aggregate data from amps for detector """


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
        camera : `lsst.obs.lsst.camera`

        Returns
        -------
        outputData : `EoCalib`
            Output data in formatted tables
        """
        outputData = self.makeOutputData(nExposure=len(inputExps))
        for iExp, inputExp in enumerate(inputExps):
            calibExp = runIsrOnExp(self, inputExp.get(), **kwargs)
            self.analyzeDetExpData(calibExp, outputData, iExp)
        self.analyzeDetRunData(outputData)
        return pipeBase.Struct(outputData=outputData)

    def makeOutputData(self, **kwargs):
        raise NotImplementedError

    def analyzeDetExpData(self, ampExposure, outputData, iExp):
        """ Analyze data from on amp """

    def analyzeDetRunData(self, outputData):
        """ Aggregate data from amps for detector """


class EoDetRunCalibTaskConnections(pipeBase.PipelineTaskConnections,
                                   dimensions=("instrument", "detector")):
    """ Class snippet with connections needed to read calibrated data """
    stackedCalExp = copyConnect(INPUT_STACK_EXP_CONNECT)
    output = copyConnect(OUTPUT_CONNECT)


class EoDetRunCalibTaskConfig(pipeBase.PipelineTaskConfig,
                              pipelineConnections=EoDetRunCalibTaskConnections):
    """ Class snippet to use connections for stacked-calibrated exposure """


class EoDetRunCalibTask(pipeBase.PipelineTask):
    """ Class snippet for tasks that analyze a stacked image

    Implements three methods that can be overridden in sub-classes:

        1. makeOutputData (required, called once)
        3. analyzeDetRunData (required, called once)

    """

    ConfigClass = EoDetRunCalibTaskConfig
    _DefaultName = "DoNotUse"

    def run(self, stackedCalExp, **kwargs):  # pylint: disable=arguments-differ
        """ Run method

        Parameters
        ----------
        stackedCalExp :
            Input data

        Keywords
        --------
        camera : `lsst.obs.lsst.camera`

        Returns
        -------
        outputData : `EoCalib`
            Output data in formatted tables
        """
        outputData = self.makeOutputData()
        self.analyzeDetRunData(stackedCalExp, outputData, **kwargs)
        return pipeBase.Struct(outputData=outputData)

    def makeOutputData(self, **kwargs):
        raise NotImplementedError

    def analyzeDetRunData(self, stackedCalExp, outputData, **kwargs):
        """ Analyze data """
