
import numpy as np

import lsst.pex.config as pexConfig
import lsst.pipe.base as pipeBase
import lsst.pipe.base.connectionTypes as cT
import lsst.afw.detection as afwDetect

from lsst.ip.isr import Defects

from .eoCalibBase import (EoDetRunCalibTaskConfig, EoDetRunCalibTaskConnections, EoDetRunCalibTask,
                          extractAmpImage, copyConnect)
from .eoDarkCurrentData import EoDarkCurrentData

__all__ = ["EoDarkCurrentTask", "EoDarkCurrentTaskConfig"]


class EoDarkCurrentTaskConnections(EoDetRunCalibTaskConnections):

    stackedCalExp = cT.Input(
        name="eoDark",
        doc="Stacked Calibrated Input Frame",
        storageClass="ExposureF",
        dimensions=("instrument", "detector"),
        isCalibration=True,
    )
    
    outputData = cT.Output(
        name="eoDarkCurrent",
        doc="Electrial Optical Calibration Output",
        storageClass="EoCalib",
        dimensions=("instrument", "detector"),
    )

class EoDarkCurrentTaskConfig(EoDetRunCalibTaskConfig,
                              pipelineConnections=EoDarkCurrentTaskConnections):
   
    def setDefaults(self):
        # pylint: disable=no-member        
        self.connections.stackedCalExp = "eoDark"
        self.connections.outputData = "eoDarkCurrent"


class EoDarkCurrentTask(EoDetRunCalibTask):

    ConfigClass = EoDarkCurrentTaskConfig
    _DefaultName = "darkCurrent"

    def run(self, stackedCalExp, **kwargs):  # pylint: disable=arguments-differ
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
        ampNames = [amp.getName() for amp in amps]
        outputData = self.makeOutputData(amps=ampNames, nAmp=nAmp)
        for iAmp, amp in enumerate(amps):
            ampExposure = extractAmpImage(stackedCalExp, amp)
            self.analyzeAmpRunData(ampExposure, outputData, iAmp, amp)
        return pipeBase.Struct(outputData=outputData)
            
    def makeOutputData(self, amps, nAmp):  # pylint: disable=arguments-differ,no-self-use
        return EoDarkCurrentData(nAmp=nAmp)

    
    def analyzeAmpRunData(self, ampExposure, outputData, iAmp, amp, **kwargs):

        try:
            exptime = ampExposure.getMetadata().toDict()['DARKTIME']
        except KeyError:
            try:
                exptime = ampExposure.getMetadata().toDict()['EXPTIME']
            except KeyError:
                exptime = 1.

        q50, q95 = np.quantile(ampExposure.image.array, [0.50, 0.95])
        outputData.amps['amps'].darkCurrentMedian[iAmp] = q50/exptime
        outputData.amps['amps'].darkCurrent95[iAmp] = q95/exptime
