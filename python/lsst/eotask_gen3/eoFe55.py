import numpy as np

import lsst.afw.math as afwMath
import lsst.pipe.base as pipeBase
import lsst.pipe.base.connectionTypes as cT

from .eoCalibBase import (EoAmpExpCalibTaskConfig, EoAmpExpCalibTaskConnections, EoAmpExpCalibTask,
                          runIsrOnAmp, extractAmpCalibs)
from .eoFe55Data import EoFe55Data

__all__ = ["EoFe55Task", "EoFe55TaskConfig"]


class EoFe55TaskConnections(EoAmpExpCalibTaskConnections):

    outputData = cT.Output(
        name="eoFe55",
        doc="Electrial Optical Calibration Output",
        storageClass="IsrCalib",
        dimensions=("instrument", "detector"),
    )


class EoFe55TaskConfig(EoAmpExpCalibTaskConfig,
                       pipelineConnections=EoFe55TaskConnections):

    def setDefaults(self):
        # pylint: disable=no-member
        self.connections.outputData = "eoFe55"
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
        self.dataSelection = "fe55Flat"


class EoFe55Task(EoAmpExpCalibTask):

    ConfigClass = EoFe55TaskConfig
    _DefaultName = "eoFe55"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.statCtrl = afwMath.StatisticsControl()

    def run(self, inputExps, **kwargs):  # pylint: disable=arguments-differ
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

        ampNames = [amp.getName() for amp in amps]
        outputData = self.makeOutputData(amps=ampNames, nAmps=len(amps), nExposure=len(inputExps),
                                         camera=camera, detector=det)

        for iamp, amp in enumerate(amps):
            ampCalibs = extractAmpCalibs(amp, **kwargs)
            for iExp, inputExp in enumerate(inputExps):
                calibExp = runIsrOnAmp(self, inputExp.get(parameters={'amp': iamp}), **ampCalibs)
                self.analyzeAmpExpData(calibExp, outputData, amp, iExp)
        return pipeBase.Struct(outputData=outputData)

    def makeOutputData(self, amps, nAmps, nExposure, **kwargs):  # pylint: disable=arguments-differ
        return EoFe55Data(amps=amps, nAmps=nAmps, nExposure=nExposure, **kwargs)

    def analyzeAmpExpData(self, calibExp, outputData, amp, iExp):
        outTable = outputData.ampExp["ampExp_%s" % amp.getName()]
        stats = afwMath.makeStatistics(calibExp.image, afwMath.MEDIAN, self.statCtrl)
        outTable.signal[iExp] = stats.getValue(afwMath.MEDIAN)

    @staticmethod
    def getFlux(pdData, factor=5):
        x = pdData['Time']
        y = pdData['Current']
        ythresh = (max(y) - min(y))/factor + min(y)
        index = np.where(y < ythresh)
        y0 = np.median(y[index])
        y -= y0
        return sum((y[1:] + y[:-1])/2.*(x[1:] - x[:-1]))
