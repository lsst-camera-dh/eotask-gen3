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
    """Analysis of bias frames to measure the stability of the gain

    Output is stored as `lsst.eotask_gen3.EoGainStabilityData` objects
    """

    ConfigClass = EoGainStabilityTaskConfig
    _DefaultName = "eoGainStability"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.statCtrl = afwMath.StatisticsControl()

    def run(self, inputExps, photodiodeData, **kwargs):  # pylint: disable=arguments-differ
        """ Run method

        Parameters
        ----------
        inputExps : `list` [`lsst.daf.Butler.DeferedDatasetRef`]
            Used to retrieve the exposures

        photodiodeData : `list` [`astropy.Table`]
            The photodiode data

        Returns
        -------
        outputData : `lsst.eotask_gen3.EoGainStabilityData`
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
        """Construct the output data object

        Parameters
        ----------
        amps : `Iterable` [`str`]
            The amplifier names
        nAmps : `int`
            Number of amplifiers
        nExposure : `int`
            Number of exposure pairs

        kwargs are passed to `lsst.eotask_gen3.EoCalib` base class constructor

        Returns
        -------
        outputData : `lsst.eotask_gen3.EoGainStabilityData`
            Container for output data
        """
        return EoGainStabilityData(amps=amps, nAmps=nAmps, nExposure=nExposure, **kwargs)

    def analyzeAmpExpData(self, calibExp, outputData, amp, iExp):
        """Analyze data from a single amp for a single exposure

        See base class for argument description

        This method just extracts summary statistics from the
        amplifier imaging region.
        """
        outTable = outputData.ampExp["ampExp_%s" % amp.getName()]
        stats = afwMath.makeStatistics(calibExp.image, afwMath.MEDIAN, self.statCtrl)
        outTable.signal[iExp] = stats.getValue(afwMath.MEDIAN)

    def analyzePdData(self, photodiodeData, outputData):
        """ Analyze the photodidode data and fill the output table

        Parameters
        ----------
        photodiodeData : `list` [`astropy.Table`]
            The photodiode data, sorted into a list of tables
            Each table is one set of reading from one exposure

        outputData : `lsst.eotask_gen3.EoGainStabilityData`
            Container for output data
        """
        outTable = outputData.detExp['detExp']
        for iExp, pdData in enumerate(photodiodeData):
            # FIXME, kludge for testing under we sort out
            # the photodiode selection stuff
            if iExp >= len(outTable.flux):
                continue
            flux = self.getFlux(pdData.get())
            outTable.flux[iExp] = flux
            outTable.seqnum[iExp] = 0  # pdData.seqnum
            outTable.mjd[iExp] = 0  # pdData.dayobs

    @staticmethod
    def getFlux(pdData, factor=5):
        """Method to intergrate the flux

        This does top-hat integration after removing an offset level.

        This removes the baseline computed by taking the median of all
        readings less than 1/'factor' times maximum reading.
        """
        x = pdData['Time']
        y = pdData['Current']
        ythresh = (max(y) - min(y))/factor + min(y)
        index = np.where(y < ythresh)
        y0 = np.median(y[index])
        y -= y0
        return sum((y[1:] + y[:-1])/2.*(x[1:] - x[:-1]))
