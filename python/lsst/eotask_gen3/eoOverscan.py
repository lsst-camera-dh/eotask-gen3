import numpy as np

import lsst.afw.math as afwMath

import lsst.pipe.base.connectionTypes as cT

from .eoCalibBase import EoAmpExpCalibTaskConfig, EoAmpExpCalibTaskConnections, EoAmpExpCalibTask
from .eoOverscanData import EoOverscanData

__all__ = ["EoOverscanTask", "EoOverscanTaskConfig"]


class EoOverscanTaskConnections(EoAmpExpCalibTaskConnections):

    outputData = cT.Output(
        name="eoOverscan",
        doc="Electrial Optical Calibration Output",
        storageClass="IsrCalib",
        dimensions=("instrument", "detector"),
    )


class EoOverscanTaskConfig(EoAmpExpCalibTaskConfig,
                           pipelineConnections=EoOverscanTaskConnections):

    def setDefaults(self):
        # pylint: disable=no-member
        self.connections.outputData = "eoOverscan"
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
        self.dataSelection = "flatFlat"


class EoOverscanTask(EoAmpExpCalibTask):
    """Analysis of overscan region in flat exposures

    Primarily this just makes summary statisitcs of the overscan regions

    Output is stored as `lsst.eotask_gen3.EoOverscanData` objects
    """

    ConfigClass = EoOverscanTaskConfig
    _DefaultName = "eoOverscan"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.statCtrl = afwMath.StatisticsControl()

    def makeOutputData(self, amps, nAmps,
                       nExposure, **kwargs):  # pylint: disable=arguments-differ,no-self-use
        """Construct the output data object

        Parameters
        ----------
        amps : `Iterable` [`lsst.afw.geom.AmplifierGeometry`]
            The amplifiers
        nAmps : `int`
            Number of amplifiers
        nExposure : `int`
            Number of exposure pairs

        kwargs are passed to `lsst.eotask_gen3.EoCalib` base class constructor

        Returns
        -------
        outputData : `lsst.eotask_gen3.EoOverscanData`
            Container for output data
        """
        ampNames = [amp.getName() for amp in amps]
        amp = amps[0]
        nCol = amp.getRawSerialOverscanBBox().getWidth() + 2
        nRow = amp.getRawParallelOverscanBBox().getHeight() + 2
        return EoOverscanData(amps=ampNames, nAmp=nAmps,
                              nExposure=nExposure, nRow=nRow, nCol=nCol, **kwargs)

    def analyzeAmpExpData(self, calibExp, outputData, iamp, amp, iExp):
        """Analyze data from a single amp for a single exposure

        See base class for argument description

        This method just extracts summary statistics from the
        amplifier overscan regions.
        """
        outTable = outputData.ampExp["ampExp_%s" % amp.getName()]

        xmin = amp.getRawDataBBox().getMinX()
        xmax = amp.getRawDataBBox().getMaxX()
        ymin = amp.getRawDataBBox().getMinY()
        ymax = amp.getRawDataBBox().getMaxY()

        imarr = calibExp.image.array
        outTable.columnMean[iExp] = np.mean(imarr[max(ymin-1, 0):ymax, xmax-1:], axis=0)
        outTable.columnVariance[iExp] = np.var(imarr[max(ymin-1, 0):ymax, xmax-1:], axis=0)
        outTable.rowMean[iExp] = np.mean(imarr[ymax-1:, max(xmin-1, 0):xmax], axis=1)
        outTable.rowVariance[iExp] = np.var(imarr[ymax-1:, max(xmin-1, 0):xmax], axis=1)
        outTable.serialOverscanNoise[iExp] = np.mean(np.std(imarr[max(ymin-1, 0):ymax, xmax+2:], axis=1))
        outTable.parallenOverscanNoise[iExp] = np.mean(np.std(imarr[ymax+2:, max(xmin-1, 0):xmax], axis=1))
        outTable.flatFieldSignal[iExp] = np.mean(imarr[max(ymin-1, 0):ymax, max(xmin-1, 0):xmax])
