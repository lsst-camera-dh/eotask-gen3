import numpy as np

import lsst.afw.math as afwMath
import lsst.pipe.base.connectionTypes as cT

from .eoCalibBase import EoAmpExpCalibTaskConfig, EoAmpExpCalibTaskConnections, EoAmpExpCalibTask
from .eoBiasStabilityData import EoBiasStabilityData

__all__ = ["EoBiasStabilityTask", "EoBiasStabilityTaskConfig"]


class EoBiasStabilityTaskConnections(EoAmpExpCalibTaskConnections):

    outputData = cT.Output(
        name="eoBiasStability",
        doc="Electrial Optical Calibration Output",
        storageClass="IsrCalib",
        dimensions=("instrument", "detector"),
    )


class EoBiasStabilityTaskConfig(EoAmpExpCalibTaskConfig,
                                pipelineConnections=EoBiasStabilityTaskConnections):

    def setDefaults(self):
        # pylint: disable=no-member
        self.connections.outputData = "eoBiasStability"
        self.isr.expectWcs = False
        self.isr.doSaturation = False
        self.isr.doSetBadRegions = False
        self.isr.doAssembleCcd = False
        self.isr.doBias = True
        self.isr.doLinearize = False
        self.isr.doDefect = False
        self.isr.doNanMasking = False
        self.isr.doWidenSaturationTrails = False
        self.isr.doDark = False
        self.isr.doFlat = False
        self.isr.doFringe = False
        self.isr.doInterpolate = False
        self.isr.doWrite = False
        self.dataSelection = "anyBias"


class EoBiasStabilityTask(EoAmpExpCalibTask):
    """Analysis of bias frames to measure the stability of the bias levels.

    Output is stored as `lsst.eotask_gen3.EoBiasStabilityData` objects
    """

    ConfigClass = EoBiasStabilityTaskConfig
    _DefaultName = "biasStability"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.statCtrl = afwMath.StatisticsControl()

    def makeOutputData(self, amps, nExposure, **kwargs):  # pylint: disable=arguments-differ
        """Construct the output data object

        Parameters
        ----------
        amps : `Iterable` [`lsst.afw.geom.AmplifierGeometry']
            The amplifiers
        nExposure : `int`
            Number of exposures

        kwargs are passed to `lsst.eotask_gen3.EoCalib` base class constructor

        Returns
        -------
        outputData : `lsst.eotask_gen3.EoBiasStabilityData`
            Container for output data
        """
        ampNames = [amp.getName() for amp in amps]

        return EoBiasStabilityData(amps=ampNames, nAmp=len(amps), nExposure=nExposure,
                                   nRow=amps[0].getRawBBox().getWidth(), nTemp=10, **kwargs)

    def analyzeAmpExpData(self, calibExp, outputData, iamp, amp, iExp):
        """Analyze data from a single amp for a single exposure

        See base class for argument description

        This method just extracts summary statistics from the amplifier
        imaging region.
        """
        outTable = outputData.ampExp["ampExp_%s" % amp.getName()]
        stats = afwMath.makeStatistics(calibExp.image, afwMath.MEANCLIP | afwMath.STDEVCLIP, self.statCtrl)
        outTable.mean[iExp] = stats.getValue(afwMath.MEANCLIP)
        outTable.stdev[iExp] = stats.getValue(afwMath.STDEVCLIP)
        outTable.rowMedian[iExp] = np.median(calibExp.image.array, axis=0)

    def analyzeDetExpData(self, calibExp, outputData, iExp):
        """Analyze data from the CCD for a single exposure

        See base class for argument description

        The method is mainly here to match data produced by EO-analysis-jobs

        Note that we are not actually accessing the temperatures, and that
        the other data actually discernable from the dataId, but having
        them here makes it easier to make plots.
        """
        outTable = outputData.detExp
        outTable.seqnum[iExp] = calibExp.meta['SEQNUM']
        outTable.mjd[iExp] = calibExp.meta['MJD']
        for iTemp in range(self.config.nTemp):
            outTable.temp[iExp][iTemp] = -100.  # calibExp.meta['Temp%s'] % iTemp
