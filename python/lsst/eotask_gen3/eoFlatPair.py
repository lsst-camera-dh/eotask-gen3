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

    photodiodeData = cT.Input(
        name="photodiode",
        doc="Input photodiode data",
        storageClass="Dataframe",
        dimensions=("instrument", "exposure"),
        multiple=True,
    )
    

class EoFlatPairTaskConfig(EoAmpPairCalibTaskConfig,
                           pipelineConnections=EoAmpPairCalibTaskConnections):

    def setDefaults(self):
        # pylint: disable=no-member        
        self.connections.output = "FlatPair"


class EoFlatPairTask(EoAmpPairCalibTask):

    ConfigClass = EoFlatPairTaskConfig
    _DefaultName = "flatPair"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.statCtrl = afwMath.StatisticsControl()
    
    def run(self, inputPairs, photodiodeDataPairs, **kwargs):  # pylint: disable=arguments-differ
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
        outputData = self.makeOutputData(amps=amps, nAmps=len(amps), nPair=len(inputPairs))
        self.analyzePdData(photodiodeDataPairs, outputData)
        for amp in amps:
            ampCalibs = extractAmpCalibs(amp, **kwargs)                        
            for iPair, inputPair in enumerate(inputPairs):
                calibExp1 = runIsrOnAmp(self, inputPair[0].get(parameters={amp: amp}), amp, **ampCalibs)
                calibExp2 = runIsrOnAmp(self, inputPair[1].get(parameters={amp: amp}), amp, **ampCalibs)
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
    
    def analyzeAmpExpData(self, calibExp1, calibExp2, outputData, amp, iExp):  # pylint: disable=too-many-arguments
        outTable = outputData.ampExposure[amp]
        signal, sig1, sig2 = self.pairMean(calibExp1, calibExp2, amp, self.statCtrl)
        outTable.signal[iExp] = signal
        outTable.flat1Signal[iExp] = sig1        
        outTable.flat1Signal[iExp] = sig2
        outTable.rowMeanVar[iExp] = self.rowMeanVariance(calibExp1, calibExp2, amp, self.statCtrl)
        
    def analyzeAmpRunData(self, outputData, amp):
        inTableAmp = outputData.ampExposure[amp.index]
        outTable = outputData.amps
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

        
