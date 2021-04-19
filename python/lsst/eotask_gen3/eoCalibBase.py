""" Base classes for Electrical Optical (EO) calibration tasks.

Provides five bases classes for different iteration scenarios:

    1. EoAmpExpCalibTask : loops over amps, then over exposures
    2. EoAmpPairCalibTask : loops over amps, then over exposure pairs
    3. EoAmpRunCalibTask : loops over amps for a single stacked image 
        (e.g., a stacked bias frame or stacked dark frame)
    4. EoDetExpCalibTask : loops over exposures (analyzes entire detector)
    5. EoDetRunCalibTask : analyzes a single stacked image

"""

import lsst.pex.config as pexConfig
import lsst.pipe.base as pipeBase
import lsst.pipe.base.connectionTypes as cT
from lsst.pipe.ip.isr import IsrTask

__all__ = []


CAMERA_CONNECT = cT.PrerequisiteInput(
    name="camera",
    storageClass="Camera",
    doc="Access to camera geometry.",
    dimensions=["instrument"],
    isCalibration=True,
)

BIAS_CONNECT = cT.PrerequisiteInput(
    name="bias",
    doc="Input bias calibration.",
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
    name="raw.amp",
    doc="Input Frames.",
    storageClass="Exposure",
    dimensions=("instrument", "exposure", "detector"),
    multiple=True,
    deferred=True,
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

ISR_CONFIG = pexConfig.ConfigurableField(
    target=IsrTask,
    doc="Used to run a reduced version of ISR approrpiate for EO analyses",
)


__all__ = []


def runIsrOnAmp(isrTask, ampExposure, amp, **kwargs)
    return isrTask.runIsrOnAmp(ampExposure, amp, **kwargs)

def runIsrOnExp(isrTask, rawExposure, **kwargs)
    return isrTask.runIsr(rawExposure, **kwargs)

    
class EoAmpExpCalibTaskConnections(pipeBase.PipelineTaskConnections,
                                   dimensions=("instrument", "exposure", "detector")):
    """ Class snippet with connections needed to read raw amplifier data and
    perform minimal Isr on each amplifier """
    camera = copy_connect(CAMERA_CONNECT)
    bias = copy_connect(BIAS_CONNECT)
    defects = copy_connect(DEFECTS_CONNECT)
    gains = copy_connect(GAINS_CONNECT)
    inputExps = copy_connect(INPUT_RAW_AMPS_CONNECT)


class EoAmpExpCalibTaskConfig(pipeBase.PipelineTaskConfig,
                              pipelineConnections=EoAmpExpCalibTaskConnections):
    """ Class snippet to define IsrTask as a sub-task and attach the 
    correct connections """
    isr = copy_config(ISR_CONFIG)
    

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

    def run(self, inputExps, **kwargs):
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
            for iExp, inputExp in enumerate(inputExps):
                calibExp = runIsrOnAmp(inputExp.get(parameters={amp:amp}), **kwargs)
                self.analyzeAmpExp(calibExp, outputData, amp, iExp)
            self.analyzeAmpRunData(outputData, amp)
        self.analyzeDetRunData(outputData)
        return pipeBase.Struct(outputData=outputData)

    def makeOutputData(self, **kwargs):
        raise NotImplementedError

    def analyzeAmpExpData(self, calibExp, outputData, amp, iExp):
        """ Analyze calibrated exposure for one amp """

    def analyzeAmpRunData(self, outputData, amp):
        """ Aggregate data from all exposures for one amp """

    def analyzeDetRunData(self, outputData, amp):
        """ Aggregate data from amps for detector """


class EoAmpPairCalibTaskConnections(pipeBase.PipelineTaskConnections,
                                    dimensions=("instrument", "exposure", "detector")):
    """ Class snippet with connections needed to read raw amplifier data and
    perform minimal Isr on each amplifier """
    camera = copy_connect(CAMERA_CONNECT)
    bias = copy_connect(BIAS_CONNECT)
    defects = copy_connect(DEFECTS_CONNECT)
    gains = copy_connect(GAINS_CONNECT)
    inputExps = copy_connect(INPUT_RAW_AMPS_CONNECT)
    

class EoAmpPairCalibTaskConfig(pipeBase.PipelineTaskConfig,
                               pipelineConnections=EoAmpPairCalibTaskConnections):
    """ Class snippet to define IsrTask as a sub-task and attach the 
    correct connections """
    isr = copy_config(ISR_CONFIG)


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

    def run(self, inputPairs, **kwargs):
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
        det = camera.get(inputExps[0].dataId['detector'])
        nAmps = len(det.getAmplifiers())
        outputData = self.makeOutputData(amps=det.getAmplifiers(), nAmps=nAmps, nPair=len(inputPairs))
        for amp in amps:
            for iPair, inputPair in enumerate(inputExps):
                calibExp1 = self.runIsrOnAmp(inputPair[0].get(parameters={amp:amp}), **kwargs)
                calibExp2 = self.runIsrOnAmp(inputPair[1].get(parameters={amp:amp}), **kwargs)
                self.analyzeAmpExposureData(calibExp1, calibExp2, outputData, amp, iPair)
            self.analyzeAmpRunData(outputData, amp)
        self.analyzeDetectorRunData(outputData)
        return pipeBase.Struct(outputData=outputData)

    def makeOutputData(self, **kwargs):
        raise NotImplementedError

    def analyzeAmpPairData(self, calibExp1, calibExp2, outputData, amp, iExp):
        """ Analyze calibrated exposure pair for one amp """

    def analyzeAmpRunData(self, outputData, amp):
        """ Aggregate data from all exposures pairs for one amp """

    def analyzeDetRunData(self, outputData, amp):
        """ Aggregate data from amps for detector """


class EoAmpRunCalibTaskConnections(pipeBase.PipelineTaskConnections,
                                   dimensions=("instrument", "detector")):
    """ Class snippet with connections needed to read calibrated data """    
    stackedCalExp = copy_connect(INPUT_STACK_EXP_CONNECT)


class EoAmpRunCalibTaskConfig(pipeBase.PipelineTaskConfig,
                              pipelineConnections=EoAmpRunCalibTaskConnections):
    """ Class snippet to use connections for stacked-calibrated exposure """
    

class EoAmpRunCalibTask(pipeBase.pipeTask):
    """ Class snippet for tasks that loop over amps on stacked image
    
    Implements three methods that can be overridden in sub-classes:

        1. makeOutputData (required, called once)
        2. analyzeAmpRunData (optional, called for each amp)
        3. analyzeDetRunData (optional, called once after all amps)

    """

    ConfigClass = EoAmpRunCalibTaskConfig
    _DefaultName = "DoNotUse"

    def __init__(self, **kwargs):
        """ C'tor """        
        super().__init__(**kwargs)

    def run(self, stackedCalExp, **kwargs):
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
        det = camera.get(stackedCalExp.dataId['detector'])
        nAmps = len(det.getAmplifiers())        
        outputData = self.makeOutputData(amps=det.getAmplifiers(), nAmps=nAmps)
        for amp in amps:
            ampExposure = stackedCalExp[amp]
            self.analyzeAmpRunData(ampExposure, outputData, amp)
        self.analyzeDetectorRunData(outputData)
        return pipeBase.Struct(outputData=outputData)

    def makeOutputData(self, **kwargs):
        raise NotImplementedError

    def analyzeAmpRunData(self, ampExposure, outputData, amp):
        """ Analyze data from on amp """

    def analyzeDetRunData(self, outputData, amp):
        """ Aggregate data from amps for detector """

        
class EoDetExpCalibTaskConnections(pipeBase.PipelineTaskConnections):
    """ Class snippet with connections needed to read raw data 
    and perform mininal Isr """    
    camera = copy_connect(CAMERA_CONNECT)
    bias = copy_connect(BIAS_CONNECT)
    defects = copy_connect(DEFECTS_CONNECT)
    gains = copy_connect(GAINS_CONNECT)
    inputExps = copy_connect(INPUT_RAW_AMPS_CONNECT)


class EoDetExpCalibTaskConfig(pipeBase.PipelineTaskConfig,
                              pipelineConnections=EoDetExpCalibTaskConnections):
    """ Class snippet to use connections for stacked-calibrated exposure """
    isr = copy_config(ISR_CONFIG)


class EoDetExpCalibTask(pipeBase.pipeTask):
    """ Class snippet for tasks that loop over amps on stacked image
    
    Implements three methods that can be overridden in sub-classes:

        1. makeOutputData (required, called once)
        2. analyzeAmpRunData (optional, called for each amp)
        3. analyzeDetRunData (optional, called once after all amps)

    """

    ConfigClass = EoDetRunCalibTaskConfig
    _DefaultName = "DoNotUse"

    def __init__(self, **kwargs):
        """ C'tor """        
        super().__init__(**kwargs)

    def run(self, stackedCalExp, **kwargs):
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
        det = camera.get(stackedCalExp.dataId['detector'])
        nAmps = len(det.getAmplifiers())        
        outputData = self.makeOutputData(amps=det.getAmplifiers(), nAmps=nAmps)
        for amp in amps:
            ampExposure = stackedCalExp[amp]
            self.analyzeAmpRunData(ampExposure, outputData, amp)
        self.analyzeDetectorRunData(outputData)
        return pipeBase.Struct(outputData=outputData)

    def makeOutputData(self, **kwargs):
        raise NotImplementedError

    def analyzeAmpRunData(self, ampExposure, outputData, amp):
        """ Analyze data from on amp """

    def analyzeDetRunData(self, outputData, amp):
        """ Aggregate data from amps for detector """

        
class EoDetRunCalibTaskConnections(pipeBase.PipelineTaskConnections,
                                   dimensions=("instrument", "detector")):
    """ Class snippet with connections needed to read calibrated data """    
    stackedCalExp = copy_connect(INPUT_STACK_EXP_CONNECT)


class EoDetRunCalibTaskConfig(pipeBase.PipelineTaskConfig,
                              pipelineConnections=EoDetRunCalibTaskConnections):
    """ Class snippet to use connections for stacked-calibrated exposure """


class EoDetRunCalibTask(pipeBase.pipeTask):
    """ Class snippet for tasks that analyze a stacked image
    
    Implements three methods that can be overridden in sub-classes:

        1. makeOutputData (required, called once)
        3. analyzeDetRunData (required, called once)

    """

    ConfigClass = EoDetRunCalibTaskConfig
    _DefaultName = "DoNotUse"

    def __init__(self, **kwargs):
        """ C'tor """        
        super().__init__(**kwargs)

    def run(self, stackedCalExp, **kwargs):
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
        self.analyzeDetRunData(outputData)
        return pipeBase.Struct(outputData=outputData)

    def makeOutputData(self, **kwargs):
        raise NotImplementedError

    def analyzeDetRunData(self, outputData):
        """ Analyze data """

        
