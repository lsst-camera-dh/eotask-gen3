import numpy as np

import lsst.pex.config as pexConfig
import lsst.pipe.base as pipeBase
import lsst.pipe.base.connectionTypes as cT
import lsst.afw.detection as afwDetect
import lsst.afw.math as afwMath

from lsst.ip.isr import Defects

from .eoCalibBase import EoDetRunCalibTaskConfig, EoDetRunCalibTaskConnections, EoDetRunCalibTask
from .eoDarkPixelsData import EoDarkPixelsData

__all__ = ["EoDarkPixelTask", "EoDarkPixelTaskConfig"]


class EoDarkPixelsTaskConnections(EoDetRunCalibTaskConnections):

    stackedCalExp = cT.Input(
        name="eoFlatHigh",
        doc="Stacked Calibrated Input Frame",
        storageClass="ExposureF",
        dimensions=("instrument", "detector"),
        isCalibration=True,
    )

    outputData = cT.Output(
        name="eoDarkPixelsStats",
        doc="Electrial Optical Calibration Output",
        storageClass="IsrCalib",
        dimensions=("instrument", "detector"),
    )

    defects = cT.Output(
        name='DarkPixel',
        doc="Output defect tables.",
        storageClass="Defects",
        dimensions=("instrument", "detector"),
        isCalibration=True,
    )


class EoDarkPixelTaskConfig(EoDetRunCalibTaskConfig,
                            pipelineConnections=EoDarkPixelsTaskConnections):

    thresh = pexConfig.Field("Fractions threshold w.r.t. amp median", float, default=0.8)
    colthresh = pexConfig.Field("Dark column threshold in # bright pixels", int, default=20)

    def setDefaults(self):
        self.connections.stackedCalExp = "eoFlatHigh"
        self.connections.outputData = "eoDarkPixelStats"
        self.connections.defects = "eoDarkPixel"


class EoDarkPixelTask(EoDetRunCalibTask):
    """Analysis of stacked flat frames to find dark pixels

    Summary output is stored as `lsst.eotask_gen3.EoDarkPixelsData`

    Defect sets are stored as `lsst.ip.isr.Defects`

    Identifies dark pixels as any that are below
    the `self.config.thresh` of the median in the median stacked flat frames

    Identifies bad columns as any columns that have more than
    `self.config.colthresh` bad pixels
    """

    ConfigClass = EoDarkPixelTaskConfig
    _DefaultName = "eoDarkPixel"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.statCtrl = afwMath.StatisticsControl()

    def run(self, stackedCalExp, **kwargs):
        """ Run method

        Parameters
        ----------
        stackedCalExp : `lsst.afw.Exposure`
            Input data, i.e., a stacked exposure of dark frames

        Returns
        -------
        outputData : `lsst.eotask_gen3.EoDarkPixelsData`
            Summary data
        defects : `lsst.ip.isr.Defects`
            Defect set
        """
        camera = kwargs.get('camera', None)
        det = stackedCalExp.getDetector()
        amps = det.getAmplifiers()
        nAmp = len(amps)
        outputData = self.makeOutputData(nAmp=nAmp, detector=det, camera=camera)
        outputTable = outputData.amps['amps']
        fpMap = {}
        for iamp, amp in enumerate(amps):
            nDarkPixel, nDarkColumn, fpSet = self.findDarkPixels(stackedCalExp, amp, 1.)
            fpMap[amp] = fpSet
            outputTable.nDarkPixel[iamp] = nDarkPixel
            outputTable.nDarkColumn[iamp] = nDarkColumn
        fpCcd = self.mergeFootprints(fpMap)
        defects = Defects(defectList=fpCcd)
        return pipeBase.Struct(outputData=outputData, defects=defects)

    def makeOutputData(self, nAmp, **kwargs):
        """Construct the output data object

        Parameters
        ----------
        nAmp : `int`
            Number of amplifiers

        kwargs are passed to `lsst.eotask_gen3.EoCalib` base class constructor

        Returns
        -------
        outputData : `lsst.eotask_gen3.EoDarkPixelsData`
            Container for output data
        """
        return EoDarkPixelsData(nAmp=nAmp, **kwargs)

    def findDarkPixels(self, stackedCalExp, amp, gain):
        """Identify bad pixels and bad columns for a single amp

        Parameters
        ----------
        stackedCalExp : `lsst.afw.Exposure`
            Input data, i.e., a stacked exposure of dark frames
        amp : `lsst.afw.geom.AmplifierGeometry`
            The amp to analyze
        gain : `float`
            The amplifier gain, used to convery from ADU to e-

        Returns
        -------
        nDarkPixs : `int`
            The number of dark pixels
        nDarkCols : `int`
            The number of dark columns
        fpSet : `lsst.afw.detection.FootprintSet`
            The footprints of the bad pixels
        """
        try:
            exptime = stackedCalExp.getMetadata().toDict()['EXPTIME']
        except KeyError:
            self.log.warn("Warning no EXPTIME: using 1.")
            exptime = 1.

        ampImage = stackedCalExp[amp.getBBox()].image
        median = afwMath.makeStatistics(ampImage, afwMath.MEDIAN, self.statCtrl).getValue()
        threshold = afwDetect.Threshold((1. - self.config.thresh)*median*exptime)
        invImage = ampImage.clone()
        invImage *= -1.
        invImage += median
        fpSet = afwDetect.FootprintSet(invImage, threshold)
        #
        # Organize dark pixels by column.
        #
        # FIXME, vectorize this
        columns = dict()
        for footprint in fpSet.getFootprints():
            for span in footprint.getSpans():
                y = span.getY()
                for x in range(span.getX0(), span.getX1()+1):
                    if x not in columns:
                        columns[x] = []
                    columns[x].append(y)
        #
        # Divide into dark columns (with # dark pixels > self.colthresh)
        # and remaining dark pixels.
        #
        darkPixs = []
        darkCols = []
        x0 = stackedCalExp.getX0()
        y0 = stackedCalExp.getY0()
        for x in columns:
            if self.badColumn(columns[x], self.config.colthresh):
                darkCols.append(x - x0)
            else:
                darkPixs.extend([(x - x0, y - y0) for y in columns[x]])

        return len(darkPixs), len(darkCols), fpSet

    @staticmethod
    def badColumn(columnIndices, threshold):
        """
        Count the sizes of contiguous sequences of masked pixels and
        return True if the length of any sequence exceeds the threshold
        number.
        """
        if len(columnIndices) < threshold:
            # There are not enough masked pixels to mark this as a bad
            # column.
            return False
        # Fill an array with zeros, then fill with ones at mask locations.
        column = np.zeros(max(columnIndices) + 1)
        column[(columnIndices,)] = 1
        # Count pixels in contiguous masked sequences.
        maskedPixelCount = []
        last = 0
        for value in column:
            if value != 0 and last == 0:
                maskedPixelCount.append(1)
            elif value != 0 and last != 0:
                maskedPixelCount[-1] += 1
            last = value
        if len(maskedPixelCount) > 0 and max(maskedPixelCount) >= threshold:
            return True
        return False

    @staticmethod
    def mergeFootprints(fpMap):
        outList = []
        for amp, fpSet in fpMap.items():
            for fp in fpSet.getFootprints():
                detBBox = fp.getBBox()
                # if amp.getFlipX():
                #    minX = amp.getRawBBox().getX1() - bbox.getMaxX()
                #    maxX = amp.getRawBBox().getX1() - bbox.getMinX()
                # else:
                #    minX = bbox.getMinX() + amp.getRawBBox().getX0()
                #    maxX = bbox.getMaxX() + amp.getRawBBox().getX0()
                # if amp.getFlipY():
                #    minY = amp.getRawBBox().getY1() - bbox.getMaxY()
                #    maxY = amp.getRawBBox().getY1() - bbox.getMinY()
                # else:
                #    minY = bbox.getMinY() + amp.getRawBBox().getY0()
                #    maxY = bbox.getMaxY() + amp.getRawBBox().getY0()
                #    detBBox = lsst.geom.Box2I(lsst.geom.Point2I(minX, minY),
                #                              lsst.geom.Point2I(maxX, maxY))
                outList.append(detBBox)
        return outList
