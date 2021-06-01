
import lsst.afw.math as afwMath

import lsst.pipe.base.connectionTypes as cT
from .eoCalibBase import EoAmpExpCalibTaskConfig, EoAmpExpCalibTaskConnections, EoAmpExpCalibTask
from .eoPersistenceData import EoPersistenceData

__all__ = ["EoPersistenceTask", "EoPersistenceTaskConfig"]



class EoPersistanceTaskConnections(EoAmpExpCalibTaskConnections):

    outputData = cT.Output(
        name="eoBiasStability",
        doc="Electrial Optical Calibration Output",
        storageClass="EoCalib",
        dimensions=("instrument", "detector"),
    )

class EoPersistenceTaskConfig(EoAmpExpCalibTaskConfig,
                              pipelineConnections=EoPersistanceTaskConnections):

    def setDefaults(self):
        # pylint: disable=no-member
        self.connections.outputData = "eoPersistence"
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


class EoPersistenceTask(EoAmpExpCalibTask):

    ConfigClass = EoPersistenceTaskConfig
    _DefaultName = "persistence"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.statCtrl = afwMath.StatisticsControl()

    def makeOutputData(self, amps, nExposure, **kwargs):  # pylint: disable=arguments-differ,no-self-use
        ampNames = [amp.getName() for amp in amps]
        return EoPersistenceData(amps=ampNames, nExposure=nExposure)

    def analyzeAmpExpData(self, calibExp, outputData, iamp, amp, iExp):
        stats = afwMath.makeStatistics(calibExp.image, afwMath.MEANCLIP | afwMath.STDEVCLIP, self.statCtrl)
        outputData.ampExp["ampExp_%s" % amp.getName()].mean[iExp] = stats.getValue(afwMath.MEANCLIP)
        outputData.ampExp["ampExp_%s" % amp.getName()].stdev[iExp] = stats.getValue(afwMath.STDEVCLIP)

