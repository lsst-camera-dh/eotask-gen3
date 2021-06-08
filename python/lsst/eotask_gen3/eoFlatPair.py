import numpy as np

import lsst.afw.image as afwImage
import lsst.afw.math as afwMath

import lsst.pipe.base as pipeBase
import lsst.pipe.base.connectionTypes as cT

from .eoCalibBase import (EoAmpPairCalibTaskConfig, EoAmpPairCalibTaskConnections,
                          EoAmpPairCalibTask, runIsrOnAmp, extractAmpCalibs)
from .eoFlatPairData import EoFlatPairData
from .eoFlatPairUtils import DetectorResponse

__all__ = ["EoFlatPairTask", "EoFlatPairTaskConfig"]


class EoFlatPairTaskConnections(EoAmpPairCalibTaskConnections):

    photodiodeData = cT.PrerequisiteInput(
        name="photodiode",
        doc="Input photodiode data",
        storageClass="Dataframe",
        dimensions=("instrument", "exposure"),
        multiple=True,
    )
    
    outputData = cT.Output(
        name="eoFlatPair",
        doc="Electrial Optical Calibration Output",
        storageClass="EoCalib",
        dimensions=("instrument", "detector"),
    )



class EoFlatPairTaskConfig(EoAmpPairCalibTaskConfig,
                           pipelineConnections=EoAmpPairCalibTaskConnections):

    def setDefaults(self):
        # pylint: disable=no-member        
        self.connections.output = "eoFlatPair"
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


class EoFlatPairTask(EoAmpPairCalibTask):

    ConfigClass = EoFlatPairTaskConfig
    _DefaultName = "flatPair"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.statCtrl = afwMath.StatisticsControl()
    
    def run(self, inputPairs, **kwargs):  # pylint: disable=arguments-differ
        """ Run method

        Parameters
        ----------
        inputPairs :
            Used to retrieve the exposures

        Keywords
        --------
        camera : `lsst.obs.lsst.camera`
        bias : `ExposureF`
        defects : `Defects`
        gains : `Gains`

        Returns
        -------
        outputData : `EoCalib`
            Output data in formatted tables
        """
        camera = kwargs['camera']
        det = camera.get(inputPairs[0].dataId['detector'])
        amps = det.getAmplifiers()
        ampNames = [amp.getName() for amp in amps]
        outputData = self.makeOutputData(amps=ampNames, nAmps=len(amps), nPair=len(inputPairs))
        if kwargs.get('photodiodeDataPairs', None):
            self.analyzePdData(photodiodeDataPairs, outputData)
        for iamp, amp in enumerate(amps):
            ampCalibs = extractAmpCalibs(amp, **kwargs)                        
            for iPair, inputPair in enumerate(inputPairs):
                calibExp1 = runIsrOnAmp(self, inputPair[0].get(parameters={"amp": iamp}), amp, **ampCalibs)
                calibExp2 = runIsrOnAmp(self, inputPair[1].get(parameters={"amp": iamp}), amp, **ampCalibs)
                self.analyzeAmpPairData(calibExp1, calibExp2, outputData, amp, iPair)
            self.analyzeAmpRunData(outputData, amp)
        return pipeBase.Struct(outputData=outputData)
    
    def makeOutputData(self, amps, nAmps, nPair, **kwargs):  # pylint: disable=arguments-differ,no-self-use
        return EoFlatPairData(amps=amps, nAmps=nAmps, nPair=nPair, **kwargs)

    def analyzePdData(self, photodiodeDataPairs, outputData):
        outTable = outputData.detExposure
        for iPair, pdData in enumerate(photodiodeDataPairs):
            pd1 = self.getFlux(pdData[0].get())
            pd2 = self.getFlux(pdData[1].get())
            if np.abs((pd1 - pd2)/((pd1 + pd2)/2.)) > self.config.max_pd_frac_dev:
                flux = np.nan
            else:
                flux = 0.5*(pd1 * pd2)
            outTable.flux[iPair] = flux
            outTable.seqnum[iPair] = pdData[0].seqnum
            outTable.dayobs[iPair] = pdData[0].dayobs
    
    def analyzeAmpPairData(self, calibExp1, calibExp2, outputData, amp, iPair):  # pylint: disable=too-many-arguments
        outTable = outputData.ampExposure[amp]
        signal, sig1, sig2 = self.pairMean(calibExp1, calibExp2, amp, self.statCtrl)
        outTable.signal[iPair] = signal
        outTable.flat1Signal[iPair] = sig1        
        outTable.flat1Signal[iPair] = sig2
        outTable.rowMeanVar[iPair] = self.rowMeanVariance(calibExp1, calibExp2, amp, self.statCtrl)
        
    def analyzeAmpRunData(self, outputData, iamp, amp):
        inTableAmp = outputData.ampExp["ampExp_%s" % amp.getName()]
        outTable = outputData.amps['amps']
        detResp = DetectorResponse(inTableAmp.flux)
        results = detResp.linearity(inTableAmp.signal, specRange=(1e3, 9e4))
        outTable.fullWell[amp.index] = detResp.fullWell(inTableAmp.signal)
        outTable.maxFracDev[amp.index] = results[0]
        #outTable.maxObservedSignal[amp.index] = np.max(inTableAmp.signal) / gains[amp.index]
        outTable.maxObservedSignal[amp.index] = np.max(inTableAmp.signal)
        #outTable.linearityTurnoff[amp.index] = results[-1]/gains[amp.index]
        outTable.linearityTurnoff[amp.index] = results[-1]
        outTable.rowMeanVarSlope[amp.index] = detResp.rowMeanVarSlope(inTableAmp.rowMeanVar, nCols=amp.getWidth())

    @staticmethod
    def getFlux(pdData, factor=5):
        x = pdData.x
        y = pdData.y
        ythresh = (max(y) - min(y))/factor + min(y)
        index = np.where(y < ythresh)
        y0 = np.median(y[index])
        y -= y0
        return sum((y[1:] + y[:-1])/2.*(x[1:] - x[:-1]))

    @staticmethod
    def pairMean(calibExp1, calibExp2, amp, statCtrl):
        flat1Value = afwMath.makeStatistics(calibExp1[amp.imaging], afwMath.MEAN, statCtrl).getValue()
        flat2Value = afwMath.makeStatistics(calibExp2[amp.imaging], afwMath.MEAN, statCtrl).getValue()
        avgMeanValue = (flat1Value + flat2Value)/2.
        return np.array([avgMeanValue, flat1Value, flat2Value], dtype=float)

    @staticmethod
    def rowMeanVariance(calibExp1, calibExp2, amp, statCtrl):
        miDiff = afwImage.MaskedImageF(calibExp1[amp.imaging], deep=True)
        miDiff -= calibExp2[amp.imaging]
        rowMeans = np.mean(miDiff.getImage().array, axis=1)
        return afwMath.makeStatistics(rowMeans, afwMath.VARIANCECLIP, statCtrl).getValue()

        
