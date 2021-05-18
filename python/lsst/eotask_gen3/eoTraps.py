
import numpy as np

import lsst.pipe.base as pipeBase
from lsst.ip.isr import Defects

from .eoCalibBase import (EoAmpRunCalibTaskConfig, EoAmpRunCalibTaskConnections, EoAmpRunCalibTask,\
                          extractAmpImage, OUTPUT_DEFECTS_CONNECT, copyConnect)
from .eoTrapsData import EoTrapsData

__all__ = ["EoTrapsTask", "EoTrapsTaskConfig"]


class EoTrapsTaskConnections(EoAmpRunCalibTaskConnections):

    defectsOut = copyConnect(OUTPUT_DEFECTS_CONNECT)


class EoTrapsTaskConfig(EoAmpRunCalibTaskConfig,
                        pipelineConnections=EoTrapsTaskConnections):
   
    def setDefaults(self):
        # pylint: disable=no-member        
        self.connections.output = "Traps"


class EoTrapsTask(EoAmpRunCalibTask):

    ConfigClass = EoTrapsTaskConfig
    _DefaultName = "traps"
    
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
        amps = det.getAmplifiers()        
        outputData = self.makeOutputData(nAmps=len(amps))
        for amp in amps:
            ampExp = extractAmpImage(stackedCalExp, amp)
            nTraps, fpSet = self.findTraps(ampExp, amp)
            outputData.amps.nTraps[amp.index] = nTraps
        defectsOut = Defects.fromFootprintList(fpSet.getFootprints())
        return pipeBase.Struct(outputData=outputData, defectsOut=defectsOut)        

    def makeOutputData(self, nAmps):  # pylint: disable=arguments-differ,no-self-use
        return EoTrapsData(nAmps=nAmps)

    def findTraps(self, ampExp, amp):
        myTraps = []
        nx = amp.imaging.getWidth()
        myArrays = []
        for i in range(6):
            myArrays.append([])
        for icol in range(nx):
            results = self.processColumn(ampExp, icol)
            for i, item in enumerate(myArrays):
                item.extend(results[i])
        for item in myArrays:
            item = np.array(item)
        return tuple(myArrays)

    def processColumn(self, ampExp, icol):
        """
        Process a single column and return a tuple of
        ix = x-pixel in image coordinates
        iy = y-pixel in image coordinates
        C2 = Correlator value = A0*A1
        C3 = abs((A0 + A1)/sqrt(abs(C2)))
        A0 = Background-subtracted pixel value of first pixel of dipole
        A1 = Background-subtracted pixel value of second pixel of dipole
        """
        col0 = ampExp[icol][self.config.edge_rolloff:self.row_max]
        sigma = np.std(col0)
        col = col0/sigma
        C2 = col[1:]*col[:-1]
        C3 = np.abs((col[1:] + col[:-1])/np.sqrt(np.abs(C2)))
        index = np.where((C2 < -self.config.C2_thresh) & (C3 < self.config.C3_thresh))
        iy, a1 = [], []
        for irow in index[0]:
            iy.append(irow + self.config.edge_rolloff + 1)
            a1.append(col0[irow + 1])
            if col0[irow] < a1[-1]:
                # We have a forward trap so increment y-coordinate by 1
                iy[-1] += 1
        ix = np.ones(len(index[0]), dtype=int)*(icol + self.prescan + 1)
        iy = np.array(iy)
        c2 = C2[index]
        c3 = C3[index]
        a0 = col0[index]
        a1 = np.array(a1)
        return ix, iy, c2, c3, a0, a1
