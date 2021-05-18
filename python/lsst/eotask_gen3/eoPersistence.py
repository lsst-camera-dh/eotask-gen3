
import lsst.afw.math as afwMath

from .eoCalibBase import EoAmpExpCalibTaskConfig, EoAmpExpCalibTaskConnections, EoAmpExpCalibTask
from .eoPersistenceData import EoPersistenceData

__all__ = ["EoPersistenceTask", "EoPersistenceTaskConfig"]


class EoPersistenceTaskConfig(EoAmpExpCalibTaskConfig,
                              pipelineConnections=EoAmpExpCalibTaskConnections):

    def setDefaults(self):
        # pylint: disable=no-member
        self.connections.output = "Persistence"


class EoPersistenceTask(EoAmpExpCalibTask):

    ConfigClass = EoPersistenceTaskConfig
    _DefaultName = "persistence"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.statCtrl = afwMath.StatisticsControl()

    def makeOutputObject(self, amps, nExposure):  # pylint: disable=arguments-differ,no-self-use
        return EoPersistenceData(amps=amps, nExposure=nExposure)

    def analyzeAmpExpData(self, calibExp, outputData, amp, iExp):
        stats = afwMath.makeStatistics(calibExp, afwMath.MEANCLIP | afwMath.STDEVCLIP, self.statCtrl)
        outputData.ampExposure[amp.index].mean[iExp] = stats.getValue(afwMath.MEANCLIP)
        outputData.ampExposure[amp.index].stdev[iExp] = stats.getValue(afwMath.STDEVCLIP)
