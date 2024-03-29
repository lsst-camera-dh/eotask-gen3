import copy
import numpy as np

from scipy.optimize import leastsq
import astropy.stats as astats

import lsst.pex.config as pexConfig
import lsst.afw.math as afwMath

import lsst.pipe.base as pipeBase
import lsst.pipe.base.connectionTypes as cT

from .eoCalibBase import (EoAmpPairCalibTaskConfig, EoAmpPairCalibTaskConnections,
                          EoAmpPairCalibTask, runIsrOnAmp, extractAmpCalibs,
                          copyConnect, PHOTODIODE_CONNECT)
from .eoPtcData import EoPtcData

__all__ = ["EoPtcTask", "EoPtcTaskConfig"]


def ptcFunc(pars, mean):
    """
    Model for variance vs mean.  See Astier et al. (arXiv:1905.08677)
    https://confluence.slac.stanford.edu/pages/viewpage.action?pageId=242286867
    """
    a00, gain, intcpt = pars
    return 0.5/(a00*gain*gain)*(1 - np.exp(-2*a00*mean*gain)) + intcpt/(gain*gain)


def residuals(pars, mean, var):
    """
    Residuals function for least-squares fit of PTC curve.
    """
    return (var - ptcFunc(pars, mean))/np.sqrt(var)


class EoPtcTaskConnections(EoAmpPairCalibTaskConnections):

    photodiodeData = copyConnect(PHOTODIODE_CONNECT)

    outputData = cT.Output(
        name="eoPtc",
        doc="Electrial Optical Calibration Output",
        storageClass="IsrCalib",
        dimensions=("instrument", "detector"),
    )


class EoPtcTaskConfig(EoAmpPairCalibTaskConfig,
                      pipelineConnections=EoPtcTaskConnections):

    maxPDFracDev = pexConfig.Field("Maximum photodiode fractional deviation", float, default=0.05)
    maxFracOffset = pexConfig.Field("maximum fraction offset from median gain curve to omit points from PTC fit.",  # noqa
                                    float, default=0.2)
    sigCut = pexConfig.Field("Cut on outliers in sigma", float, default=5.0)

    def setDefaults(self):
        # pylint: disable=no-member
        self.connections.outputData = "eoPtc"
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


class EoPtcTask(EoAmpPairCalibTask):
    """Analysis of pair of flat-field exposure to extract the
    photon-tranfer-curve (PTC) of the amplifier response.

    Output is stored as `lsst.eotask_gen3.EoPtcData` objects
    """

    ConfigClass = EoPtcTaskConfig
    _DefaultName = "eoPtc"

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
        outputData : `lsst.eotask_gen3.EoPtcData`
            Output data in formatted tables
        """
        camera = kwargs['camera']
        # det = camera.get(inputPairs[0][0][0].dataId['detector'])
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
        outputData : `lsst.eotask_gen3.EoPtcData`
            Container for output data
        """
        return EoPtcData(amps=amps, nAmp=nAmps, nPair=nPair, **kwargs)

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
            pd1 = self.getFlux(pdData[0].get())
            pd2 = self.getFlux(pdData[1].get())
            if np.abs((pd1 - pd2)/((pd1 + pd2)/2.)) > self.config.maxPDFracDev:
                flux = np.nan
            else:
                flux = 0.5*(pd1 * pd2)
            outTable.flux[iPair] = flux
            outTable.seqnum[iPair] = 0  #
            outTable.dayobs[iPair] = 0  #

    def analyzeAmpPairData(self, calibExp1, calibExp2,
                           outputData, amp, iPair):  # pylint: disable=too-many-arguments
        """Analyze data from a single amp for a single exposure-pair

        See base class for argument description

        This method just extracts summary statistics from the
        amplifier imaging region.
        """
        outTable = outputData.ampExp["ampExp_%s" % amp.getName()]
        results = self.pairMean(calibExp1, calibExp2, amp, self.statCtrl)
        outTable.mean[iPair] = results[0]
        outTable.var[iPair] = results[1]
        outTable.discard[iPair] = results[2]

    def analyzeAmpRunData(self, outputData, iamp, amp):
        """Analyze data from a single amp for a run

        See base class for argument description

        This method fits the PTC curve and stores the result in
        the output data container
        """
        inTableAmp = outputData.ampExp["ampExp_%s" % amp.getName()]
        # inTableExp = outputData.detExp['detExp']
        outTable = outputData.amps['amps']
        results = self.fitPtcCurve(inTableAmp.mean, inTableAmp.var, self.config.sigCut)
        outTable.ptcGain[iamp] = results[0]
        outTable.ptcGainError[iamp] = results[1]
        outTable.ptcA00[iamp] = results[2]
        outTable.ptcA00Error[iamp] = results[3]
        outTable.ptcNoise[iamp] = results[4]
        outTable.ptcNoiseError[iamp] = results[5]
        outTable.ptcTurnoff[iamp] = results[6]

    @staticmethod
    def pairMean(calibExp1, calibExp2, amp, statCtrl):
        """Return the mean of the two exposures, and the mean of the means"""
        mean1 = afwMath.makeStatistics(calibExp1[amp.getRawDataBBox()].image,
                                       afwMath.MEAN, statCtrl).getValue()
        mean2 = afwMath.makeStatistics(calibExp2[amp.getRawDataBBox()].image,
                                       afwMath.MEAN, statCtrl).getValue()
        fmean = (mean1 + mean2)/2.
        # Pierre Astier's symmetric weights to make the difference
        # image have zero mean
        weight1 = mean2/fmean
        weight2 = mean1/fmean
        calibExp1.image.array *= weight1
        calibExp2.image.array *= weight2

        # Make a robust estimate of variance by filtering outliers
        image1 = np.ravel(calibExp1.image.array)
        image2 = np.ravel(calibExp2.image.array)
        fdiff = image1 - image2
        mad = astats.mad_std(fdiff)  # /2.
        # The factor 14.826 below makes the filter the equivalent of a 10-sigma
        # cut for a normal distribution
        keep = np.where((np.abs(fdiff) < (mad*14.826)))[0]

        # Re-weight the images
        mean1 = np.mean(image1[keep], dtype=np.float64)
        mean2 = np.mean(image2[keep], dtype=np.float64)
        fmean = (mean1 + mean2)/2.
        weight1 = mean2/fmean
        weight2 = mean1/fmean
        image1 *= weight1
        image2 *= weight2

        fmean = (mean1 + mean2)/2.
        fvar = np.var(image1[keep] - image2[keep])/2.
        discard = len(image1) - len(keep)

        return fmean, fvar, discard

    def fitPtcCurve(self, mean, var, sigCut=5):
        """Fit the PTC curve for a set of mean-variance points."""
        indexOld = []
        index = list(np.where((mean < 4e4)*(var > 0))[0])
        count = 1
        # Initial guess for BF coeff, gain, and square of the read noise
        pars = 2.7e-6, 0.75, 25
        try:
            while index != indexOld and count < 10:
                try:
                    results = leastsq(residuals, pars, full_output=1,
                                      args=(mean[index].data.flatten(), var[index].data.flatten()))
                except TypeError as err:
                    if self.logger is not None:
                        self.logger.info(err)
                        self.logger.info('Too few remaining mean-variance points:  %s' % len(index))

                pars, cov = results[:2]
                sigResids = residuals(pars, mean.data.flatten(), var.data.flatten())
                indexOld = copy.deepcopy(index)
                index = list(np.where(np.abs(sigResids) < sigCut)[0])
                count += 1

            ptcA00 = pars[0]
            ptcA00Error = np.sqrt(cov[0][0])
            ptcGain = pars[1]
            ptcError = np.sqrt(cov[1][1])
            ptcNoise = np.sqrt(pars[2])
            ptcNoiseError = 0.5/ptcNoise*np.sqrt(cov[2][2])
            # Cannot assume that the mean values are sorted
            ptcTurnoff = max(mean[index])
        except Exception:
            ptcGain = 0.
            ptcError = -1.
            ptcA00 = 0.
            ptcA00Error = -1.
            ptcNoise = 0.
            ptcNoiseError = -1.
            ptcTurnoff = 0.
        return (ptcGain, ptcError, ptcA00, ptcA00Error, ptcNoise,
                ptcNoiseError, ptcTurnoff)

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
