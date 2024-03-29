import numpy as np

import lsst.pex.config as pexConfig
import lsst.afw.image as afwImage
import lsst.afw.math as afwMath

import lsst.pipe.base as pipeBase
import lsst.pipe.base.connectionTypes as cT

from .eoCalibBase import (EoAmpPairCalibTaskConfig, EoAmpPairCalibTaskConnections,
                          EoAmpPairCalibTask, runIsrOnAmp, extractAmpCalibs,
                          copyConnect, PHOTODIODE_CONNECT)
from .eoFlatPairData import EoFlatPairData
from .eoFlatPairUtils import DetectorResponse

__all__ = ["EoFlatPairTask", "EoFlatPairTaskConfig"]


class EoFlatPairTaskConnections(EoAmpPairCalibTaskConnections):

    photodiodeData = copyConnect(PHOTODIODE_CONNECT)

    outputData = cT.Output(
        name="eoFlatPair",
        doc="Electrial Optical Calibration Output",
        storageClass="IsrCalib",
        dimensions=("instrument", "detector"),
    )


class EoFlatPairTaskConfig(EoAmpPairCalibTaskConfig,
                           pipelineConnections=EoFlatPairTaskConnections):

    maxPDFracDev = pexConfig.Field("Maximum photodiode fractional deviation", float, default=0.05)

    def setDefaults(self):
        # pylint: disable=no-member
        self.connections.outputData = "eoFlatPair"
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
        self.dataSelection = "flatFlat"


class EoFlatPairTask(EoAmpPairCalibTask):
    """Analysis of pair of flat-field exposure to measure the linearity
    of the amplifier response.

    Output is stored as `lsst.eotask_gen3.EoFlatPairData` objects
    """

    ConfigClass = EoFlatPairTaskConfig
    _DefaultName = "eoFlatPair"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.statCtrl = afwMath.StatisticsControl()

    def run(self, inputPairs, **kwargs):  # pylint: disable=arguments-differ
        """ Run method

        Parameters
        ----------
        inputPairs : `list` [`tuple` [`lsst.daf.Butler.DeferedDatasetRef`] ]
            Used to retrieve the exposures

        See base class for keywords.

        Returns
        -------
        outputData : `lsst.eotask_gen3.EoFlatPairData`
            Output data in formatted tables
        """
        camera = kwargs['camera']
        nPair = len(inputPairs)
        if nPair < 1:
            raise RuntimeError("No valid input data")

        det = inputPairs[0][0][0].get().getDetector()
        amps = det.getAmplifiers()
        ampNames = [amp.getName() for amp in amps]
        outputData = self.makeOutputData(amps=ampNames, nAmps=len(amps), nPair=len(inputPairs),
                                         camera=camera, detector=det)
        photodiodePairs = kwargs.get('photodiodePairs', None)
        if photodiodePairs is not None:
            self.analyzePdData(photodiodePairs, outputData)
        for iamp, amp in enumerate(amps):
            ampCalibs = extractAmpCalibs(amp, **kwargs)
            for iPair, inputPair in enumerate(inputPairs):
                if len(inputPair) != 2:
                    self.log.warn("exposurePair %i has %i items" % (iPair, len(inputPair)))
                    continue
                calibExp1 = runIsrOnAmp(self, inputPair[0][0].get(parameters={"amp": iamp}), **ampCalibs)
                calibExp2 = runIsrOnAmp(self, inputPair[1][0].get(parameters={"amp": iamp}), **ampCalibs)
                amp2 = calibExp1.getDetector().getAmplifiers()[0]
                self.analyzeAmpPairData(calibExp1, calibExp2, outputData, amp2, iPair)
            self.analyzeAmpRunData(outputData, iamp, amp2)
        return pipeBase.Struct(outputData=outputData)

    def makeOutputData(self, amps, nAmps, nPair, **kwargs):  # pylint: disable=arguments-differ,no-self-use
        """Construct the output data object

        Parameters
        ----------
        amps : `Iterable` [`str`]
            The amplifier names
        nAmp : `int`
            Number of amplifiers
        nPair : `int`
            Number of exposure pairs

        kwargs are passed to `lsst.eotask_gen3.EoCalib` base class constructor

        Returns
        -------
        outputData : `lsst.eotask_gen3.EoFlatPairData`
            Container for output data
        """
        return EoFlatPairData(amps=amps, nAmp=nAmps, nPair=nPair, **kwargs)

    def analyzePdData(self, photodiodeDataPairs, outputData):
        """ Analyze the photodidode data and fill the output table

        Parameters
        ----------
        photodiodeDataPairs : `list` [`tuple` [`astropy.Table`] ]
            The photodiode data, sorted into a list of pairs of tables
            Each table is one set of reading from one exposure

        outputData : `lsst.eotask_gen3.EoFlatPairData`
            Container for output data
        """
        outTable = outputData.detExp['detExp']

        for iPair, pdData in enumerate(photodiodeDataPairs):
            if len(pdData) != 2:
                self.log.warn("photodiodePair %i has %i items" % (iPair, len(pdData)))
                continue
            pd1 = self.getFlux(pdData[0].get())
            pd2 = self.getFlux(pdData[1].get())
            if np.abs((pd1 - pd2)/((pd1 + pd2)/2.)) > self.config.maxPDFracDev:
                flux = np.nan
            else:
                flux = 0.5*(pd1 * pd2)
            outTable.flux[iPair] = flux
            outTable.seqnum[iPair] = 0  #
            outTable.dayobs[iPair] = 0  #

    def analyzeAmpPairData(self, calibExp1, calibExp2, outputData,
                           amp, iPair):  # pylint: disable=too-many-arguments
        """Analyze data from a single amp for a single exposure-pair

        See base class for argument description

        This method just extracts summary statistics from the
        amplifier imaging region.
        """
        outTable = outputData.ampExp["ampExp_%s" % amp.getName()]
        signal, sig1, sig2 = self.pairMean(calibExp1, calibExp2, amp, self.statCtrl)
        outTable.signal[iPair] = signal
        outTable.flat1Signal[iPair] = sig1
        outTable.flat2Signal[iPair] = sig2
        outTable.rowMeanVar[iPair] = self.rowMeanVariance(calibExp1, calibExp2, amp, self.statCtrl)

    def analyzeAmpRunData(self, outputData, iamp, amp):
        """Analyze data from a single amp for a run

        See base class for argument description

        This method creates the linearity curve and associated parameters
        for the amplifier
        """

        inTableAmp = outputData.ampExp["ampExp_%s" % amp.getName()]
        inTableExp = outputData.detExp['detExp']
        outTable = outputData.amps['amps']
        signals = inTableAmp.signal.data.flatten()

        detResp = DetectorResponse(inTableExp.flux.data.flatten())
        results = detResp.linearity(signals, specRange=(1e3, 9e4))
        outTable.fullWell[iamp] = detResp.fullWell(signals)[0]
        outTable.maxFracDev[iamp] = results[0]
        # outTable.maxObservedSignal[iamp] =
        # np.max(inTableAmp.signal) / gains[amp]
        outTable.maxObservedSignal[iamp] = np.max(signals)
        # outTable.linearityTurnoff[iamp] = results[-1]/gains[iamp]
        outTable.linearityTurnoff[iamp] = results[-1]
        outTable.rowMeanVarSlope[iamp] = detResp.rowMeanVarSlope(inTableAmp.rowMeanVar.data.flatten(),
                                                                 signals,
                                                                 nCols=amp.getRawDataBBox().getWidth())

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

    @staticmethod
    def pairMean(calibExp1, calibExp2, amp, statCtrl):
        """Return the mean of the two exposures, and the mean of the means"""
        flat1Value = afwMath.makeStatistics(calibExp1[amp.getRawDataBBox()].image,
                                            afwMath.MEAN, statCtrl).getValue()
        flat2Value = afwMath.makeStatistics(calibExp2[amp.getRawDataBBox()].image,
                                            afwMath.MEAN, statCtrl).getValue()
        avgMeanValue = (flat1Value + flat2Value)/2.
        return np.array([avgMeanValue, flat1Value, flat2Value], dtype=float)

    @staticmethod
    def rowMeanVariance(calibExp1, calibExp2, amp, statCtrl):
        """Return the variance of the mean of the rows of the
        difference image"""
        miDiff = afwImage.MaskedImageF(calibExp1[amp.getRawDataBBox()].getMaskedImage(), deep=True)
        miDiff -= calibExp2[amp.getRawDataBBox()].getMaskedImage()
        rowMeans = np.mean(miDiff.getImage().array, axis=1)
        return afwMath.makeStatistics(rowMeans, afwMath.VARIANCECLIP, statCtrl).getValue()
