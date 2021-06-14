
import numpy as np

import lsst.pex.config as pexConfig
import lsst.pipe.base as pipeBase
import lsst.pipe.base.connectionTypes as cT
import lsst.afw.detection as afwDetect

from lsst.ip.isr import Defects

from .eoCalibBase import (EoDetRunCalibTaskConfig, EoDetRunCalibTaskConnections, EoDetRunCalibTask,\
                          extractAmpImage, OUTPUT_DEFECTS_CONNECT, copyConnect)
from .eoBrightPixelsData import EoBrightPixelsData

__all__ = ["EoBrightPixelTask", "EoBrightPixelTaskConfig"]


class EoBrightPixelsTaskConnections(EoDetRunCalibTaskConnections):

    stackedCalExp = cT.Input(
        name="eoDark",
        doc="Stacked Calibrated Input Frame",
        storageClass="ExposureF",
        dimensions=("instrument", "detector"),
        isCalibration=True,
    )

    outputData = cT.Output(
        name="eoBrightPixelsStats",
        doc="Electrial Optical Calibration Output",
        storageClass="EoCalib",
        dimensions=("instrument", "detector"),
    )

    defects = cT.Output(
        name='eoBrightPixel',
        doc="Output defect tables.",
        storageClass="Defects",
        dimensions=("instrument", "detector"),
        isCalibration=True,
    )
    

class EoBrightPixelTaskConfig(EoDetRunCalibTaskConfig,
                              pipelineConnections=EoBrightPixelsTaskConnections):
   
    ethresh = pexConfig.Field("Bright pixel threshold in e- per pixel per second", int, default=5)
    colthresh = pexConfig.Field("Bright column threshold in # bright pixels", int, default=20)
    
    def setDefaults(self):
        self.connections.stackedCalExp = "eoDark"
        self.connections.outputData = "eoBrightPixelStats"
        self.connections.defects = "eoBrightPixel"
        

class EoBrightPixelTask(EoDetRunCalibTask):

    ConfigClass = EoBrightPixelTaskConfig
    _DefaultName = "eoBrightPixel"
    
    def run(self, stackedCalExp, **kwargs):
        """ Run method

        Parameters
        ----------
        stackedCalExp :
            Input data

        Keywords
        --------
        camera : `lsst.obs.lsst.camera`

        Returns
        -------
        outputData : `EoCalib`
            Output data in formatted tables
        """
        det = stackedCalExp.getDetector()
        amps = det.getAmplifiers()
        nAmp = len(amps)
        outputData = self.makeOutputData(nAmp=nAmp)
        outputTable = outputData.amps['amps']
        fpMap = {}
        for iamp, amp in enumerate(amps):
            nBrightPixel, nBrightColumn, fpSet = self.findBrightPixels(stackedCalExp, amp, 1.)
            fpMap[amp] = fpSet
            outputTable.nBrightPixel[iamp] = nBrightPixel
            outputTable.nBrightColumn[iamp] = nBrightColumn
        fpCcd = self.mergeFootprints(fpMap)
        defects = Defects(defectList=fpCcd)
        return pipeBase.Struct(outputData=outputData, defects=defects)        

    def makeOutputData(self, nAmp, **kwargs):
        return EoBrightPixelsData(nAmp=nAmp)

    def findBrightPixels(self, stackedCalExp, amp, gain):
        try:
            exptime = stackedCalExp.getMetadata().toDict()['EXPTIME']
        except KeyError:
            print("Warning no EXPTIME: using 1.")
            exptime = 1.
        threshold = afwDetect.Threshold(self.config.ethresh * exptime)
        fpSet = afwDetect.FootprintSet(stackedCalExp[amp.getBBox()].image, threshold)
        # 
        # Organize bright pixels by column.
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
        # Divide into bright columns (with # bright pixels > self.colthresh)
        # and remaining bright pixels.
        #
        brightPixs = []
        brightCols = []
        x0 = stackedCalExp.getX0()
        y0 = stackedCalExp.getY0()
        for x in columns:
            if self.badColumn(columns[x], self.config.colthresh):
                brightCols.append(x - x0)
            else:
                brightPixs.extend([(x - x0, y - y0) for y in columns[x]])

        return len(brightPixs), len(brightCols), fpSet
                
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
                #if amp.getFlipX():
                #    minX = amp.getRawBBox().getX1() - bbox.getMaxX()
                #    maxX = amp.getRawBBox().getX1() - bbox.getMinX()
                #else:
                #    minX = bbox.getMinX() + amp.getRawBBox().getX0()
                #    maxX = bbox.getMaxX() + amp.getRawBBox().getX0()
                #if amp.getFlipY():
                #    minY = amp.getRawBBox().getY1() - bbox.getMaxY()
                #    maxY = amp.getRawBBox().getY1() - bbox.getMinY()
                #else:
                #    minY = bbox.getMinY() + amp.getRawBBox().getY0()
                #    maxY = bbox.getMaxY() + amp.getRawBBox().getY0()
                #    detBBox = lsst.geom.Box2I(lsst.geom.Point2I(minX, minY),
                #                              lsst.geom.Point2I(maxX, maxY))
                outList.append(detBBox)
        return outList
