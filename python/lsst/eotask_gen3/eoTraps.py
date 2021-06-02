
import numpy as np

import lsst.afw.math as afwMath
import lsst.pex.exceptions as pexExcept
import lsst.pex.config as pexConfig
import lsst.pipe.base as pipeBase
import lsst.pipe.base.connectionTypes as cT
from lsst.ip.isr import Defects



from .eoCalibBase import (EoAmpExpCalibTaskConfig, EoAmpExpCalibTaskConnections, EoAmpExpCalibTask,\
                          extractAmpImage, OUTPUT_DEFECTS_CONNECT, copyConnect, extractAmpCalibs, 
                          runIsrOnAmp)
from .eoTrapsData import EoTrapsData

__all__ = ["EoTrapsTask", "EoTrapsTaskConfig"]


class EoTrapsTaskConnections(EoAmpExpCalibTaskConnections):

    outputData = cT.Output(
        name="eoTrapsStats",
        doc="Electrial Optical Calibration Output",
        storageClass="EoCalib",
        dimensions=("instrument", "detector"),
    )

    defectsOut = cT.Output(
        name='Traps',
        doc="Output defect tables.",
        storageClass="Defects",
        dimensions=("instrument", "detector"),
        isCalibration=True,
    )


class EoTrapsTaskConfig(EoAmpExpCalibTaskConfig,
                        pipelineConnections=EoTrapsTaskConnections):

    C2_thresh = pexConfig.Field("C2 threshold", float, default=10.)
    C3_thresh = pexConfig.Field("C3 threshold", float, default=1.)
    nx = pexConfig.Field("Local background width (pixels)", int, default=10)
    ny = pexConfig.Field("Local background height (pixels)", int, default=10)
    edge_rolloff = pexConfig.Field("Edge rolloff width (pixels)", int, default=10)
   
    def setDefaults(self):
        # pylint: disable=no-member        
        self.connections.outputData = "eoTrapsStats"
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


class EoTrapsTask(EoAmpExpCalibTask):

    ConfigClass = EoTrapsTaskConfig
    _DefaultName = "eoTraps"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.statCtrl = afwMath.StatisticsControl()
    
    def run(self, inputExps, **kwargs):
        """ Run method

        Parameters
        ----------
        inputExps :
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
        det = camera.get(inputExps[0].dataId['detector'])
        amps = det.getAmplifiers()
        outputData = self.makeOutputData(nAmps=len(amps))
        fpMap = {}
        for iamp, amp in enumerate(amps):
            ampCalibs = extractAmpCalibs(amp, **kwargs)
            inputExp = inputExps[0]
            calibExp = runIsrOnAmp(self, inputExp.get(parameters={"amp": iamp}), **ampCalibs)
            nTraps, fpSet = self.findTraps(calibExp, amp)
            outputData.amps["amps"].nTraps[iamp] = nTraps
            fpMap[amp] = fpSet

        fpCcd = self.mergeFootprints(fpMap)
        defectsOut = Defects(defectList=fpCcd)
        return pipeBase.Struct(outputData=outputData, defectsOut=defectsOut)        

    def makeOutputData(self, nAmps):  # pylint: disable=arguments-differ,no-self-use
        return EoTrapsData(nAmps=nAmps)

    def findTraps(self, ampExp, amp):

        bgCtrl = afwMath.BackgroundControl(self.config.nx, self.config.ny, self.statCtrl)
        image = ampExp.clone()

        self.prescan = amp.getRawPrescanBBox().getWidth()
        self.row_max = amp.getBBox().getHeight()+1

        try:
            bg = afwMath.makeBackground(image.image, bgCtrl)
            image.image.array -= bg.getImageF().array
        except pexExcept.OutOfRangeError as eObj:
            # Stack fails to derive a local background image so rely on
            # bias subtraction. This produces less reliable results on
            # real and simulated data.
            print("TrapFinder.getProcessedImageArray:", eObj)
            print("Skipping local background subtraction for amp", amp)
            
        imArray = image.image.array

        myTraps = []
        nx = amp.getBBox().getWidth()
        myArrays = []
        for i in range(6):
            myArrays.append([])
        for icol in range(nx):
            results = self.processColumn(imArray, icol)
            for i, item in enumerate(myArrays):
                item.extend(results[i])
        for item in myArrays:
            item = np.array(item)
        return tuple(myArrays)

    def processColumn(self, imArray, icol):
        """
        Process a single column and return a tuple of
        ix = x-pixel in image coordinates
        iy = y-pixel in image coordinates
        C2 = Correlator value = A0*A1
        C3 = abs((A0 + A1)/sqrt(abs(C2)))
        A0 = Background-subtracted pixel value of first pixel of dipole
        A1 = Background-subtracted pixel value of second pixel of dipole
        """
        col0 = imArray[icol][self.config.edge_rolloff:self.row_max]
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
