import numpy as np

import lsst.afw.math as afwMath

from .eoCalibBase import EoAmpExpCalibTaskConfig, EoAmpExpCalibTaskConnections, EoAmpExpCalibTask
from .eoBiasStabilityData import EoBiasStabilityData

__all__ = ["EoBiasStabilityTask", "EoBiasStabilityTaskConfig"]


class EoBiasStabilityTaskConfig(EoAmpExpCalibTaskConfig,
                                pipelineConnections=EoAmpExpCalibTaskConnections):

    def setDefaults(self):
        # pylint: disable=no-member
        self.connections.output = "BiasStability"


class EoBiasStabilityTask(EoAmpExpCalibTask):

    ConfigClass = EoBiasStabilityTaskConfig
    _DefaultName = "biasStability"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.statCtrl = afwMath.StatisticsControl()
    
    def makeOutputData(self, amps, nExposure, **kwargs):  # pylint: disable=arguments-differ
        return EoBiasStabilityData(amps=amps, nAmp=len(amps), nExposure=nExposure,
                                   nRow=amps[0].getWidth(), nTemp=self.config.nTemp)

    def analyzeAmpExpData(self, calibExp, outputData, amp, iExp):
        outTable = outputData.ampExposure[amp.index]
        stats = afwMath.makeStatistics(calibExp, afwMath.MEANCLIP | afwMath.STDEVCLIP, self.statCtrl)
        outTable.mean[iExp] = stats.getValue(afwMath.MEANCLIP)
        outTable.stdev[iExp] = stats.getValue(afwMath.STDEVCLIP)
        outTable.rowMedian[iExp] = np.median(calibExp.image.array, axis=0)
        
    def analyzeDetExpData(self, calibExp, outputData, iExp):
        outTable = outputData.detExposure
        outTable.seqnum[iExp] = calibExp.meta['SEQNUM']
        outTable.mjd[iExp] = calibExp.meta['MJD']
        for iTemp in range(self.config.nTemp):
            outTable.temp[iExp][iTemp] = calibExp.meta['Temp%s'] % iTemp
        
