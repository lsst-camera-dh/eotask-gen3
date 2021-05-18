
import numpy as np

import lsst.pipe.base as pipeBase
from lsst.ip.isr import Defects

from .eoCalibBase import (EoAmpRunCalibTaskConfig, EoAmpRunCalibTaskConnections, EoAmpRunCalibTask,\
                          extractAmpImage, OUTPUT_DEFECTS_CONNECT, copyConnect)
from .eoBrightPixelsData import EoBrightPixelsData

__all__ = ["EoBrightPixelTask", "EoBrightPixelTaskConfig"]


class EoBrightPixelsTaskConnections(EoAmpRunCalibTaskConnections):

    defectsOut = copyConnect(OUTPUT_DEFECTS_CONNECT)


class EoBrightPixelTaskConfig(EoAmpRunCalibTaskConfig,
                              pipelineConnections=EoAmpRunCalibTaskConnections):
   
    def setDefaults(self):
        self.connections.output = "BrightPixel"


class EoBrightPixelTask(EoAmpRunCalibTask):

    ConfigClass = EoBrightPixelTaskConfig
    _DefaultName = "brightPixel"
    
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
        camera = kwargs['camera']
        det = camera.get(stackedCalExp.dataId['detector'])
        amps = det.getAmplifiers(nAmps=len(amps))        
        outputData = self.makeOutputData()
        nBrightPixel, nBrightColumn, fpSet = self.findBrightPixels(stackedCalExp, amp)
        defects = Defects.fromFootprintList(fpSet.getFootprints())
        return pipeBase.Struct(outputData=outputData, defects=defects)        

    def makeOutputData(self, nAmps, **kwargs):
        return EoBrightPixelsData(nAmps=nAmps)

    def findBrightPixels(self, stackedCalExp, amp, gain):
        exptime = stackedCalExp.meta['EXPTIME']
        threshold = afwDetect.Threshold(self.config.ethresh * exptime)
        fpSet = afwDetect.FootprintSet(stackedCalExp, threshold)
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
            if badColumn(columns[x], self.config.colthresh):
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
