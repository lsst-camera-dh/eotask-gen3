import lsst.afw.math as afwMath

import lsst.pipe.base.connectionTypes as cT

from .eoCalibBase import EoAmpExpCalibTaskConfig, EoAmpExpCalibTaskConnections, EoAmpExpCalibTask
from .eoTearingData import EoTearingData
from .eoTearingUtils import AmpTearingStats

__all__ = ["EoTearingTask", "EoTearingTaskConfig"]


class EoTearingTaskConnections(EoAmpExpCalibTaskConnections):

    outputData = cT.Output(
        name="eoTearing",
        doc="Electrial Optical Calibration Output",
        storageClass="IsrCalib",
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
        """Construct the output data object

        Parameters
        ----------
        amps : `Iterable` [`lsst.afw.geom.AmplifierGeometry`]
            The amplifier names
        nExposure : `int`
            Number of exposures

        kwargs are passed to `lsst.eotask_gen3.EoCalib` base class constructor

        Returns
        -------
        outputData : `lsst.eotask_gen3.EoTearingData`
            Container for output data
        """
        ampNames = [amp.getName() for amp in amps]
        return EoTearingData(amps=ampNames, nAmp=len(amps), nExposure=nExposure, **kwargs)

    def analyzeAmpExpData(self, calibExp, outputData, iamp, amp, iExp):
        """Analyze data from a single amp for a single exposure

        See base class for argument description

        This method runs the tearing detection and counts the
        number of detections.
        """
        outTable = outputData.ampExp["ampExp_%s" % amp.getName()]
        outTable.nDetection[iExp] = self.ampTearingCount(calibExp, amp)
        
    def analyzeAmpRunData(self, outputData, iamp, amp):
        """Analyze data from a single amp for all exposures in run
        
        This method sums the tearing detections across the run for
        each amp.
        """
        inTable = outputData.ampExp["ampExp_%s" % amp.getName()]
        outTable = outputData.amps['amps']
        
        runDetect = sum(inTable.nDetection.data.flatten())
        outTable.nDetection[iamp] = runDetect

    @staticmethod
    def ampTearingCount(calibExp, amp, cut1=0.05, cut2=-0.01, nsig=1):
        """ Search for tearing

        Parameters
        ----------
        calibExp : `lsst.afw.image.Exposure`
            The image being analyzed
        amp : `lsst.afw.geom.AmplifierGeometry`
            The amp being analyzed
        cut1 : `float`
            ??
        cut2 : `float`
            ??
        nsig : `float`
            Number of standard deviations to apply the cut at

        Returns
        -------
        ntear = `int`
            Number of tearing detections
        """
        ampTearing = AmpTearingStats(calibExp, amp)
        ntear = 0
        rstats1, rstats2 = ampTearing.rstats
        if rstats1.diff - cut1 > nsig*rstats1.error\
           and rstats2.diff - cut2 > nsig*rstats2.error:
            ntear += 1
        if rstats1.diff - cut2 > nsig*rstats1.error\
           and rstats2.diff - cut1 > nsig*rstats2.error:
            ntear += 1
        return ntear
