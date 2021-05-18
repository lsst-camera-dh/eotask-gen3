
import lsst.afw.math as afwMath

from .eoCalibBase import EoAmpExpCalibTaskConfig, EoAmpExpCalibTaskConnections, EoAmpExpCalibTask
from .eoTearingData import EoTearingData
from .eoTearingUtils import AmpTearingStats

__all__ = ["EoTearingTask", "EoTearingTaskConfig"]


class EoTearingTaskConfig(EoAmpExpCalibTaskConfig,
                          pipelineConnections=EoAmpExpCalibTaskConnections):

    def setDefaults(self):
        # pylint: disable=no-member        
        self.connections.output = "Tearing"


class EoTearingTask(EoAmpExpCalibTask):

    ConfigClass = EoTearingTaskConfig
    _DefaultName = "tearing"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.statCtrl = afwMath.StatisticsControl()
            
    def makeOutputData(self, amps, nExposure, **kwargs):  # pylint: disable=arguments-differ,no-self-use
        return EoTearingData(amps=amps, nAmp=len(amps), nExposure=nExposure)

    def analyzeAmpExpData(self, calibExp, outputData, amp, iExp):
        outTable = outputData.ampExposure[amp.index]
        outTable.nDetection[iExp] = self.ampTearingCount(calibExp, amp)

    @staticmethod
    def ampTearingCount(calibExp, amp, cut1=0.05, cut2=-0.01, nsig=1):
        ampTearing = AmpTearingStats(calibExp, amp.geom)
        ntear = 0
        rstats1, rstats2 = ampTearing.rstats
        if (rstats1.diff - cut1 > nsig*rstats1.error and
            rstats2.diff - cut2 > nsig*rstats2.error):
            ntear += 1
        if (rstats1.diff - cut2 > nsig*rstats1.error and
            rstats2.diff - cut1 > nsig*rstats2.error):
            ntear += 1
        return ntear
