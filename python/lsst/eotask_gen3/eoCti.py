
import lsst.afw.math as afwMath

import lsst.pex.config as pexConfig

from .eoCalibBase import EoAmpRunCalibTaskConfig, EoAmpRunCalibTaskConnections, EoAmpRunCalibTask
from .eoCtiData import EoCtiData
from .eoCtiUtils import estimateCti

__all__ = ["EoCtiTask", "EoCtiTaskConfig"]


class EoCtiTaskConfig(EoAmpRunCalibTaskConfig,
                      pipelineConnections=EoAmpRunCalibTaskConnections):

    overscans = pexConfig.Field("Number of overscan rows/columns to use", int, default=2)
    cti = pexConfig.Field('Return CTI instead of CTE', bool, default=False)
    
    def setDefaults(self):
        # pylint: disable=no-member
        self.connections.output = "Cti"


class EoCtiTask(EoAmpRunCalibTask):

    ConfigClass = EoCtiTaskConfig
    _DefaultName = "cti"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.statCtrl = afwMath.StatisticsControl()
    
    def makeOutputData(self, amps, nAmps):
        return EoCtiData(amps=amps, nAmp=nAmps)

    def analyzeAmpRunData(self, ampExposure, outputData, amp):
        ctiSerialEstim = estimateCti(ampExposure, amp, 's', self.statCtrl, self.config.overscans)
        ctiParallelEstim = estimateCti(ampExposure, amp, 'p', self.statCtrl, self.config.overscans)

        if self.config.cti:
            outputData.amps.ctiSerial[amp.index] = ctiSerialEstim.value
            outputData.amps.ctiParallel[amp.index] = ctiParallelEstim.value
        else:
            outputData.amps.ctiSerial[amp.index] = 1 - ctiSerialEstim.value
            outputData.amps.ctiParallel[amp.index] = 1 - ctiParallelEstim.value

        outputData.amps.ctiSerialError[amp.index] = ctiSerialEstim.error
        outputData.amps.ctiParalleError[amp.index] = ctiParallelEstim.error
