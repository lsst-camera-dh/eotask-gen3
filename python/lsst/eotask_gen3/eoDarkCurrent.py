
import numpy as np

import lsst.pex.config as pexConfig
import lsst.pipe.base as pipeBase
import lsst.pipe.base.connectionTypes as cT
import lsst.afw.detection as afwDetect

from lsst.ip.isr import Defects

from .eoCalibBase import (EoAmpRunCalibTaskConfig, EoAmpRunCalibTaskConnections, EoAmpRunCalibTask,
                          extractAmpImage, copyConnect)
from .eoDarkCurrentData import EoDarkCurrentData

__all__ = ["EoDarkCurrentTask", "EoDarkCurrentTaskConfig"]


class EoDarkCurrentTaskConnections(EoAmpRunCalibTaskConnections):

    outputData = cT.Output(
        name="eoDarkCurrent",
        doc="Electrial Optical Calibration Output",
        storageClass="EoCalib",
        dimensions=("instrument", "detector"),
    )

class EoDarkCurrentTaskConfig(EoAmpRunCalibTaskConfig,
                              pipelineConnections=EoDarkCurrentTaskConnections):
   
    def setDefaults(self):
        # pylint: disable=no-member        
        self.connections.stackedCalExp = "eo_dark"
        self.connections.outputData = "eoDarkCurrent"


class EoDarkCurrentTask(EoAmpRunCalibTask):

    ConfigClass = EoDarkCurrentTaskConfig
    _DefaultName = "darkCurrent"
    
    def makeOutputData(self, amps, nAmps):  # pylint: disable=arguments-differ,no-self-use
        return EoDarkCurrentData(nAmp=nAmps)

    def analyzeAmpRunData(self, ampExposure, outputData, iAmp, amp, **kwargs):

        try:
            exptime = ampExposure.getMetadata().toDict()['DARKTIME']
        except KeyError:
            try:
                exptime = ampExposure.getMetadata().toDict()['EXPTIME']
            except KeyError:
                exptime = 1.

        q50, q95 = np.quantile(ampExposure.image.array, [0.50, 0.95])
        outputData.amps['amps'].darkCurrentMedian[iAmp] = q50/exptime
        outputData.amps['amps'].darkCurrent95[iAmp] = q95/exptime
