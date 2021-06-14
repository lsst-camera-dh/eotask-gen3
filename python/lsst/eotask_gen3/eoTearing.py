
import lsst.afw.math as afwMath

import lsst.pipe.base.connectionTypes as cT

from .eoCalibBase import (EoAmpExpCalibTaskConfig, EoAmpExpCalibTaskConnections, EoAmpExpCalibTask,
                          extractAmpImage)
from .eoTearingData import EoTearingData
from .eoTearingUtils import AmpTearingStats

__all__ = ["EoTearingTask", "EoTearingTaskConfig"]


class EoTearingTaskConnections(EoAmpExpCalibTaskConnections):

    outputData = cT.Output(
        name="eoTearing",
        doc="Electrial Optical Calibration Output",
        storageClass="EoCalib",
        dimensions=("instrument", "detector"),
    )

    
class EoTearingTaskConfig(EoAmpExpCalibTaskConfig,
                          pipelineConnections=EoTearingTaskConnections):

    def setDefaults(self):
        # pylint: disable=no-member        
        self.connections.outputData = "Tearing"
        self.isr.expectWcs = False
        self.isr.doSaturation = False
        self.isr.doSetBadRegions = False
        self.isr.doAssembleCcd = False
        self.isr.doBias = True
        self.isr.doLinearize = False
        self.isr.doDefect = False
        self.isr.doNanMasking = False
        self.isr.doWidenSaturationTrails = False
        self.isr.doDark = True
        self.isr.doFlat = False
        self.isr.doFringe = False
        self.isr.doInterpolate = False
        self.isr.doWrite = False
        self.dataSelection = "anySuperFlat"


class EoTearingTask(EoAmpExpCalibTask):

    ConfigClass = EoTearingTaskConfig
    _DefaultName = "tearing"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.statCtrl = afwMath.StatisticsControl()
            
    def makeOutputData(self, amps, nExposure, **kwargs):  # pylint: disable=arguments-differ,no-self-use
        ampNames = [amp.getName() for amp in amps]
        return EoTearingData(amps=ampNames, nAmp=len(amps), nExposure=nExposure)

    def analyzeAmpExpData(self, calibExp, outputData, iamp, amp, iExp):
        outTable = outputData.ampExp["ampExp_%s" % amp.getName()]
        outTable.nDetection[iExp] = self.ampTearingCount(calibExp, amp)

    @staticmethod
    def ampTearingCount(calibExp, amp, cut1=0.05, cut2=-0.01, nsig=1):
        ampTearing = AmpTearingStats(calibExp, amp)
        ntear = 0
        rstats1, rstats2 = ampTearing.rstats
        if (rstats1.diff - cut1 > nsig*rstats1.error and
            rstats2.diff - cut2 > nsig*rstats2.error):
            ntear += 1
        if (rstats1.diff - cut2 > nsig*rstats1.error and
            rstats2.diff - cut1 > nsig*rstats2.error):
            ntear += 1
        return ntear
