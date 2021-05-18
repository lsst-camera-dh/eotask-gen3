import numpy as np
from scipy import stats

import lsst.pex.config as pexConfig
import lsst.afw.math as afwMath
import lsst.geom as lsstGeom

from .eoCalibBase import EoAmpPairCalibTaskConfig, EoAmpPairCalibTaskConnections, EoAmpPairCalibTask
from .eoBrighterFatterData import EoBrighterFatterData

__all__ = ["EoBrighterFatterTask", "EoBrighterFatterTaskConfig"]


class EoBrighterFatterTaskConfig(EoAmpPairCalibTaskConfig,
                                 pipelineConnections=EoAmpPairCalibTaskConnections):

    maxLag = pexConfig.Field("Maximum lag", int, default=2)
    nPixBorder = pexConfig.Field("Number of pixels to clip on the border",
                                 int, default=10)
    nSigmaClip = pexConfig.Field("Number of sigma to clip for corr calc", int,
                                 default=3)
    backgroundBinSize = pexConfig.Field("Background bin size", int, default=128)

    def setDefaults(self):
        # pylint: disable=no-member        
        self.connections.output = "BrighterFatter"


class EoBrighterFatterTask(EoAmpPairCalibTask):

    ConfigClass = EoBrighterFatterTaskConfig
    _DefaultName = "brighterFatter"

    def makeOutputObject(self, amps, nAmps, nPair):   # pylint: disable=arguments-differ,no-self-use
        return EoBrighterFatterData(amps=amps, nAmps=nAmps, nPair=nPair)

    def analyzeAmpExpData(self, calibExp1, calibExp2, outputData, amp, iExp):  # pylint: disable=too-many-arguments
        outTable = outputData.ampExposure[amp]

        preppedImage1, median1 = self.prepImage(calibExp1, self.config)
        preppedImage2, median2 = self.prepImage(calibExp2, self.config)

        outTable.mean[iExp] = (median1 + median2)/2.
        outTable.covarience[iExp], outTable.covarienceError[iExp] =\
            self.crossCorrelate(preppedImage1, preppedImage2, self.config)

    def analyzeAmpRunData(self, outputData, amp):

        inTable = outputData.ampExposure[amp.index]
        outTable = outputData.amps

        meanidx = self.config.meanindex

        outTable.bfMean = inTable.mean[meanidx]
        outTable.bfXCorr[amp.index] = inTable.covarience[meanidx, 0, 1]
        outTable.bfXCorrErr[amp.index] = inTable.covarienceError[meanidx, 0, 1]
        outTable.bfYCorr[amp.index] = inTable.covarience[meanidx, 1, 0]
        outTable.bfYCorrErr[amp.index] = inTable.covarienceError[meanidx, 1, 0]

        outTable.bfXSlope[amp.index], outTable.bfXSlopeErr[amp.index] =\
            self.fitSlopes(inTable.mean, inTable.covarience[:, 0, 1])
        outTable.bfYSlope[amp.index], outTable.bfYSlopeErr[amp.index] =\
            self.fitSlopes(inTable.mean, inTable.covarience[:, 1, 0])

    @staticmethod
    def prepImage(calibExp, config):
        """
        Crop the image to avoid edge effects based on the Config border
        parameter. Additionally, if there is a dark image, subtract.
        """

        # Clone so that we don't modify the input image.
        localExp = calibExp.clone()

        # The border that we wish to crop.
        border = config.nPixBorder

        sctrl = afwMath.StatisticsControl()

        # Crop the image within a border region.
        bbox = localExp.getBBox()
        bbox.grow(-border)
        localExp = localExp[bbox]

        # Calculate the median of the image.
        median = afwMath.makeStatistics(localExp, afwMath.MEDIAN, sctrl).getValue()
        return localExp, median

    @staticmethod
    def crossCorrelate(maskedimage1, maskedimage2, config):
        """
        Calculate the correlation coefficients.
        """
        sctrl = afwMath.StatisticsControl()
        sctrl.setNumSigmaClip(config.sigma)
        mask = maskedimage1.getMask()
        INTRP = mask.getPlaneBitMask("INTRP")
        sctrl.setAndMask(INTRP)

        # Diff the images.
        diff = maskedimage1.clone()
        diff -= maskedimage2.getImage()

        # Subtract background.
        nx = diff.getWidth()//config.binsize
        ny = diff.getHeight()//config.binsize
        bctrl = afwMath.BackgroundControl(nx, ny, sctrl, afwMath.MEDIAN)  # pylint: disable=no-member
        bkgd = afwMath.makeBackground(diff, bctrl)  # pylint: disable=no-member
        bgImg = bkgd.getImageF(afwMath.Interpolate.CUBIC_SPLINE,
                               afwMath.REDUCE_INTERP_ORDER)  # pylint: disable=no-member

        diff -= bgImg

        # Measure the correlations
        x0, y0 = diff.getXY0()
        width, height = diff.getDimensions()
        bbox_extent = lsstGeom.Extent2I(width - config.maxLag, height - config.maxLag)

        bbox = lsstGeom.Box2I(lsstGeom.Point2I(x0, y0), bbox_extent)
        dim0 = diff[bbox].clone()
        dim0 -= afwMath.makeStatistics(dim0, afwMath.MEDIAN, sctrl).getValue()

        xcorr = np.zeros((config.maxLag + 1, config.maxLag + 1), dtype=np.float64)
        xcorr_err = np.zeros((config.maxLag + 1, config.maxLag + 1), dtype=np.float64)

        for xlag in range(config.maxLag + 1):
            for ylag in range(config.maxLag + 1):
                bbox_lag = lsstGeom.Box2I(lsstGeom.Point2I(x0 + xlag, y0 + ylag),
                                          bbox_extent)
                dim_xy = diff[bbox_lag].clone()
                dim_xy -= afwMath.makeStatistics(dim_xy, afwMath.MEDIAN,
                                                 sctrl).getValue()
                dim_xy *= dim0
                xcorr[xlag, ylag] = afwMath.makeStatistics(
                    dim_xy, afwMath.MEDIAN, sctrl).getValue()
                dim_xy_array = dim_xy.getImage().getArray().flatten()/xcorr[0][0]
                N = len(dim_xy_array.flatten())
                if xlag != 0 and ylag != 0:
                    f = (1+xcorr[xlag, ylag]/xcorr[0][0]) / \
                        (1-xcorr[xlag, ylag]/xcorr[0][0])
                    xcorr_err[xlag, ylag] = (
                        np.std(dim_xy_array)/np.sqrt(N))*np.sqrt(f)
                else:
                    xcorr_err[xlag, ylag] = 0
        return xcorr, xcorr_err

    @staticmethod
    def fitSlopes(xcorr, mean, adu_max=1e5):
        xcorr = np.array(xcorr)
        mean = np.array(mean)
        xcorr = xcorr[mean < adu_max]
        mean = mean[mean < adu_max]
        slopex, _, _, _, errx = stats.linregress(mean, xcorr)
        return slopex, errx
