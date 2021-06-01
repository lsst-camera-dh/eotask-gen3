
import lsst.afw.math as afwMath

import lsst.pex.config as pexConfig
import lsst.pipe.base.connectionTypes as cT

from .eoCalibBase import EoAmpRunCalibTaskConfig, EoAmpRunCalibTaskConnections, EoAmpRunCalibTask
from .eoCtiData import EoCtiData
from .eoCtiUtils import estimateCti

__all__ = ["EoCtiTask", "EoCtiTaskConfig"]



class EoCtiTaskConnections(EoAmpRunCalibTaskConnections):

    outputData = cT.Output(
        name="eoCti",
        doc="Electrial Optical Calibration Output",
        storageClass="EoCalib",
        dimensions=("instrument", "detector"),
    )

class EoCtiTaskConfig(EoAmpRunCalibTaskConfig,
                      pipelineConnections=EoCtiTaskConnections):

    overscans = pexConfig.Field("Number of overscan rows/columns to use", int, default=2)
    cti = pexConfig.Field('Return CTI instead of CTE', bool, default=False)
    
    def setDefaults(self):
        # pylint: disable=no-member
        self.connections.stackedCalExp = "eo_flat"
        self.connections.outputData = "eoCti"



class EoCtiTask(EoAmpRunCalibTask):

    ConfigClass = EoCtiTaskConfig
    _DefaultName = "cti"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.statCtrl = afwMath.StatisticsControl()
    
    def makeOutputData(self, amps, nAmps):
        return EoCtiData(amps=amps, nAmp=nAmps)

    def analyzeAmpRunData(self, ampExposure, outputData, iamp, amp, **kwargs):
        ctiSerialEstim = estimateCti(ampExposure, amp, 's', self.statCtrl, self.config.overscans)
        ctiParallelEstim = estimateCti(ampExposure, amp, 'p', self.statCtrl, self.config.overscans)

        outputTable = outputData.amps['amps']

        if self.config.cti:
            outputTable.ctiSerial[iamp] = ctiSerialEstim.value
            outputTable.ctiParallel[iamp] = ctiParallelEstim.value
        else:
            outputTable.ctiSerial[iamp] = 1 - ctiSerialEstim.value
            outputTable.ctiParallel[iamp] = 1 - ctiParallelEstim.value

        outputTable.ctiSerialError[iamp] = ctiSerialEstim.error
        outputTable.ctiParalleError[iamp] = ctiParallelEstim.error
