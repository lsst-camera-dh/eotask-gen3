
import copy
import numpy as np

from scipy.optimize import leastsq
import astropy.stats as astats

import lsst.pex.config as pexConfig
import lsst.afw.math as afwMath

import lsst.pipe.base as pipeBase
import lsst.pipe.base.connectionTypes as cT

from .eoCalibBase import (EoAmpPairCalibTaskConfig, EoAmpPairCalibTaskConnections,
                          EoAmpPairCalibTask, runIsrOnAmp, extractAmpCalibs)
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

    photodiodeData = cT.Input(
        name="photodiode",
        doc="Input photodiode data",
        storageClass="Dataframe",
        dimensions=("instrument", "exposure"),
        multiple=True,
    )
    

class EoPtcTaskConfig(EoAmpPairCalibTaskConfig,
                      pipelineConnections=EoAmpPairCalibTaskConnections):

    max_frac_offset = pexConfig.Field(
        "maximum fraction offset from median gain curve to omit points from PTC fit.", float, default=0.2)
    
    def setDefaults(self):
        # pylint: disable=no-member
        self.connections.output = "Ptc"


class EoPtcTask(EoAmpPairCalibTask):

    ConfigClass = EoPtcTaskConfig
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
                calibExp1 = runIsrOnAmp(self, inputPair[0].get(parameters={amp: amp}), **ampCalibs)
                calibExp2 = runIsrOnAmp(self, inputPair[1].get(parameters={amp: amp}), **ampCalibs)
                self.analyzeAmpPairData(calibExp1, calibExp2, outputData, amp, iPair)
            self.analyzeAmpRunData(outputData, amp)
        return pipeBase.Struct(outputData=outputData)
    
    def makeOutputData(self, amps, nAmps, nPair):  # pylint: disable=arguments-differ,no-self-use
        return EoPtcData(amps=amps, nAmps=nAmps, nPair=nPair)

    def analyzePdData(self, photodiodeDataPairs, outputData):
        outTable = outputData.detExposure
        for iPair, pdData in enumerate(photodiodeDataPairs):
            pd1 = self.getFlux(pdData[0])
            pd2 = self.getFlux(pdData[1])
            if np.abs((pd1 - pd2)/((pd1 + pd2)/2.)) > self.config.max_pd_frac_dev:
                flux = np.nan
            else:
                flux = 0.5*(pd1 * pd2)
            outTable.flux[iPair] = flux
            outTable.seqnum[iPair] = pdData[0].seqnum
            outTable.dayobs[iPair] = pdData[0].dayobs

    def analyzeAmpPairData(self, calibExp1, calibExp2, outputData, amp, iPair):  # pylint: disable=too-many-arguments
        outTable = outputData.ampExposure[amp]
        results = self.pairMean(calibExp1, calibExp2, self.statCtrl)
        outTable.mean[iPair] = results[0]
        outTable.var[iPair] = results[1]
        outTable.discard[iPair] = results[2]
        
    def analyzeAmpRunData(self, outputData, amp):
        inTableAmp = outputData.ampExposure[amp.index]
        outTable = outputData.amps
        results = self.fitPtcCurve(inTableAmp.mean, inTableAmp.var, self.config.sigCut)
        outTable.ptcGain[amp.index] = results[0]
        outTable.ptcGainError[amp.index] = results[1]
        outTable.ptcA00[amp.index] = results[2]
        outTable.ptcA00Error[amp.index] = results[3]
        outTable.ptcNoise[amp.index] = results[4]
        outTable.ptcNoiseError[amp.index] = results[5]
        outTable.ptcTurnoff[amp.index] = results[6]
        
    @staticmethod
    def pairMean(calibExp1, calibExp2, statCtrl):

        mean1 = afwMath.makeStatistics(calibExp1, afwMath.MEAN, statCtrl).getValue()
        mean2 = afwMath.makeStatistics(calibExp2, afwMath.MEAN, statCtrl).getValue()
        fmean = (mean1 + mean2)/2.
        # Pierre Astier's symmetric weights to make the difference
        # image have zero mean
        weight1 = mean2/fmean
        weight2 = mean1/fmean
        calibExp1 *= weight1
        calibExp2 *= weight2

        # Make a robust estimate of variance by filtering outliers
        image1 = np.ravel(calibExp1.getArrays()[0])
        image2 = np.ravel(calibExp2.getArrays()[0])
        fdiff = image1 - image2
        mad = astats.mad_std(fdiff)  #/2.
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
                                      args=(mean[index], var[index]))
                except TypeError as err:
                    if self.logger is not None:
                        self.logger.info(err)
                        self.logger.info('Too few remaining mean-variance points:  %s' % len(index))

                pars, cov = results[:2]
                sigResids = residuals(pars, mean, var)
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
    def getFlux(pdData):
        return np.trazp(pdData[0], pdData[1])
