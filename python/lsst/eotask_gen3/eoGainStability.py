import numpy as np

import lsst.afw.math as afwMath
import lsst.pipe.base as pipeBase
import lsst.pipe.base.connectionTypes as cT

from .eoCalibBase import (EoAmpExpCalibTaskConfig, EoAmpExpCalibTaskConnections, EoAmpExpCalibTask,
                          runIsrOnAmp, extractAmpCalibs)
from .eoGainStabilityData import EoGainStabilityData

__all__ = ["EoGainStabilityTask", "EoGainStabilityTaskConfig"]


class EoGainStabilityTaskConnections(EoAmpExpCalibTaskConnections):

    photodiodeData = cT.Input(
        name="photodiode",
        doc="Input photodiode data",
        storageClass="Dataframe",
        dimensions=("instrument", "exposure"),
        multiple=True,
    )


class EoGainStabilityTaskConfig(EoAmpExpCalibTaskConfig,
                                pipelineConnections=EoGainStabilityTaskConnections):

    def setDefaults(self):
        # pylint: disable=no-member                
        self.connections.output = "GainStability"


class EoGainStabilityTask(EoAmpExpCalibTask):

    ConfigClass = EoGainStabilityTaskConfig
    _DefaultName = "biasStability"

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
        det = camera.get(inputExps[0].dataId['detector'])
        amps = det.getAmplifiers()
        outputData = self.makeOutputData(amps=amps, nAmps=len(amps), nExposure=len(inputExps))
        self.analyzePdData(photodiodeData, outputData)
        for amp in amps:
            ampCalibs = extractAmpCalibs(amp, **kwargs)                                    
            for iExp, inputExp in enumerate(inputExps):
                calibExp = runIsrOnAmp(self, inputExp.get(parameters={amp: amp}), amp, **ampCalibs)
                self.analyzeAmpExpData(calibExp, outputData, amp, iExp)
        return pipeBase.Struct(outputData=outputData)
            
    def makeOutputData(self, amps, nAmps, nExposure):  # pylint: disable=arguments-differ
        return EoGainStabilityData(amps=amps, nAmps=nAmps, nExposure=nExposure)

    def analyzeAmpExpData(self, calibExp, outputData, amp, iExp):
        outTable = outputData.ampExposure[amp.index]
        stats = afwMath.makeStatistics(calibExp, afwMath.MEDIAN, self.statCtrl)
        outTable.signal[iExp] = stats.getValue(afwMath.MEDIAN)

    def analyzePdData(self, photodiodeData, outputData):
        outTable = outputData.detExposure
        for iExp, pdData in enumerate(photodiodeData):
            flux = self.getFlux(pdData)
            outTable.flux[iExp] = flux
            outTable.seqnum[iExp] = pdData.seqnum
            outTable.dayobs[iExp] = pdData.dayobs

    @staticmethod
    def getFlux(pdData, factor=5):
        x = pdData.x
        y = pdData.y
        ythresh = (max(y) - min(y))/factor + min(y)
        index = np.where(y < ythresh)
        y0 = np.median(y[index])
        y -= y0
        return sum((y[1:] + y[:-1])/2.*(x[1:] - x[:-1]))
