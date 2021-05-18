import numpy as np

import lsst.afw.math as afwMath

from .eoCalibBase import EoAmpExpCalibTaskConfig, EoAmpExpCalibTaskConnections, EoAmpExpCalibTask
from .eoOverscanData import EoOverscanData

__all__ = ["EoOverscanTask", "EoOverscanTaskConfig"]


class EoOverscanTaskConfig(EoAmpExpCalibTaskConfig,
                                pipelineConnections=EoAmpExpCalibTaskConnections):

    def setDefaults(self):
        # pylint: disable=no-member
        self.connections.output = "Overscan"


class EoOverscanTask(EoAmpExpCalibTask):

    ConfigClass = EoOverscanTaskConfig
    _DefaultName = "overscan"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.statCtrl = afwMath.StatisticsControl()
    
    def makeOutputData(self, amps, nExposure):  # pylint: disable=arguments-differ,no-self-use
        return EoOverscanData(amps=amps, nAmp=len(amps), nExposure=nExposure)

    def analyzeAmpExpData(self, calibExp, outputData, amp, iExp):
        outTable = outputData.ampExposure[amp.index]

        ampGeom = amp.geom
        xmin = ampGeom['xmin']
        xmax = ampGeom['xmax']
        ymin = ampGeom['ymin']
        ymax = ampGeom['ymax']

        imarr = calibExp.image.array
        outTable.columnMean[iExp] = np.mean(imarr[ymin-1:ymax, xmax-1:], axis=0)
        outTable.columnVariance[iExp] = np.var(imarr[ymin-1:ymax, xmax-1:], axis=0)
        outTable.rowMean[iExp] = np.mean(imarr[ymax-1:, xmin-1:xmax], axis=1)
        outTable.rowVariance[iExp] = np.var(imarr[ymax-1:, xmin-1:xmax], axis=1)
        outTable.serialOverscanNoise[iExp] = np.mean(np.std(imarr[ymin-1:ymax, xmax+2:], axis=1))
        outTable.parallenOverscanNoise[iExp] = np.mean(np.std(imarr[ymax+2:, xmin-1:xmax], axis=1))
        outTable.flatFeildSignal[iExp] = np.mean(imarr[ymin-1:ymax, xmin-1:xmax])
