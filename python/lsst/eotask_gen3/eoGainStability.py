import numpy as np

import lsst.afw.math as afwMath
import lsst.pipe.base as pipeBase
import lsst.pipe.base.connectionTypes as cT

from .eoCalibBase import (EoAmpExpCalibTaskConfig, EoAmpExpCalibTaskConnections, EoAmpExpCalibTask,
                          runIsrOnAmp, extractAmpCalibs, copyConnect, PHOTODIODE_CONNECT)
from .eoGainStabilityData import EoGainStabilityData

__all__ = ["EoGainStabilityTask", "EoGainStabilityTaskConfig"]


class EoGainStabilityTaskConnections(EoAmpExpCalibTaskConnections):

    photodiodeData = copyConnect(PHOTODIODE_CONNECT)

    outputData = cT.Output(
        name="eoGainStability",
        doc="Electrial Optical Calibration Output",
        storageClass="IsrCalib",
        dimensions=("instrument", "detector"),
    )


class EoGainStabilityTaskConfig(EoAmpExpCalibTaskConfig,
                                pipelineConnections=EoGainStabilityTaskConnections):

    def setDefaults(self):
        # pylint: disable=no-member                
        self.connections.outputData = "eoGainStability"
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
        

class EoGainStabilityTask(EoAmpExpCalibTask):

    ConfigClass = EoGainStabilityTaskConfig
    _DefaultName = "eoGainStability"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.statCtrl = afwMath.StatisticsControl()

    def run(self, inputExps, photodiodeData, **kwargs):  # pylint: disable=arguments-differ
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
        numExps = len(inputExps)
        if numExps < 1:
            raise RuntimeError("No valid input data")
        
        det = inputExps[0].get().getDetector()
        amps = det.getAmplifiers()

        ampNames = [amp.getName() for amp in amps]
        outputData = self.makeOutputData(amps=ampNames, nAmps=len(amps), nExposure=len(inputExps),
                                         camera=camera, detector=det)

        self.analyzePdData(photodiodeData, outputData)
        for iamp, amp in enumerate(amps):
            ampCalibs = extractAmpCalibs(amp, **kwargs)                                    
            for iExp, inputExp in enumerate(inputExps):
                calibExp = runIsrOnAmp(self, inputExp.get(parameters={'amp': iamp}), **ampCalibs)
                self.analyzeAmpExpData(calibExp, outputData, amp, iExp)
        return pipeBase.Struct(outputData=outputData)
            
    def makeOutputData(self, amps, nAmps, nExposure, **kwargs):  # pylint: disable=arguments-differ
        return EoGainStabilityData(amps=amps, nAmps=nAmps, nExposure=nExposure, **kwargs)

    def analyzeAmpExpData(self, calibExp, outputData, amp, iExp):
        outTable = outputData.ampExp["ampExp_%s" % amp.getName()]
        stats = afwMath.makeStatistics(calibExp.image, afwMath.MEDIAN, self.statCtrl)
        outTable.signal[iExp] = stats.getValue(afwMath.MEDIAN)

    def analyzePdData(self, photodiodeData, outputData):
        outTable = outputData.detExp['detExp']
        for iExp, pdData in enumerate(photodiodeData):
            flux = self.getFlux(pdData)
            outTable.flux[iExp] = flux
            outTable.seqnum[iExp] = 0 #pdData.seqnum
            outTable.mjd[iExp] = 0 #pdData.dayobs

    @staticmethod
    def getFlux(pdData, factor=5):
        x = pdData['Time']
        y = pdData['Current']
        ythresh = (max(y) - min(y))/factor + min(y)
        index = np.where(y < ythresh)
        y0 = np.median(y[index])
        y -= y0
        return sum((y[1:] + y[:-1])/2.*(x[1:] - x[:-1]))
