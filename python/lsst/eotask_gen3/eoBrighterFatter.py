import numpy as np
from scipy import stats

import lsst.pex.config as pexConfig
import lsst.afw.math as afwMath
import lsst.geom as lsstGeom

import lsst.pipe.base as pipeBase
import lsst.pipe.base.connectionTypes as cT

from .eoCalibBase import EoAmpPairCalibTaskConfig, EoAmpPairCalibTaskConnections, EoAmpPairCalibTask
from .eoBrighterFatterData import EoBrighterFatterData

__all__ = ["EoBrighterFatterTask", "EoBrighterFatterTaskConfig"]


class EoBrighterFatterTaskConnections(EoAmpPairCalibTaskConnections):

    outputData = cT.Output(
        name="eoBrighterFatter",
        doc="Electrial Optical Calibration Output",
        storageClass="EoCalib",
        dimensions=("instrument", "detector"),
    )


class EoBrighterFatterTaskConfig(EoAmpPairCalibTaskConfig,
                                 pipelineConnections=EoBrighterFatterTaskConnections):

    maxLag = pexConfig.Field("Maximum lag", int, default=2)
    nPixBorder = pexConfig.Field("Number of pixels to clip on the border",
                                 int, default=10)
    nSigmaClip = pexConfig.Field("Number of sigma to clip for corr calc", int,
                                 default=3)
    backgroundBinSize = pexConfig.Field("Background bin size", int, default=128)
    meanindex = pexConfig.Field("Index of image to use for mean", int, default=0)

    def setDefaults(self):
        # pylint: disable=no-member        
        self.connections.outputData = "BrighterFatter"
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


class EoBrighterFatterTask(EoAmpPairCalibTask):

    ConfigClass = EoBrighterFatterTaskConfig
    _DefaultName = "brighterFatter"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.statCtrl = afwMath.StatisticsControl()

    def makeOutputData(self, amps, nAmps, nPair, **kwargs):   # pylint: disable=arguments-differ,no-self-use
        ampNames = [amp.getName() for amp in amps]
        nCov = self.config.maxLag + 1
        return EoBrighterFatterData(amps=ampNames, nAmp=nAmps, nPair=nPair, nCov=nCov, **kwargs)

    def analyzeAmpPairData(self, calibExp1, calibExp2, outputData, amp, iPair):  # pylint: disable=too-many-arguments
        outTable = outputData.ampExp["ampExp_%s" % amp.getName()]

        preppedImage1, median1 = self.prepImage(calibExp1, amp)
        preppedImage2, median2 = self.prepImage(calibExp2, amp)

        outTable.mean[iPair] = (median1 + median2)/2.
        outTable.covarience[iPair], outTable.covarienceError[iPair] =\
            self.crossCorrelate(preppedImage1, preppedImage2)

    def analyzeAmpRunData(self, outputData, iamp, amp):

        inTable = outputData.ampExp["ampExp_%s" % amp.getName()]
        outTable = outputData.amps["amps"]

        meanidx = self.config.meanindex

        outTable.bfMean = inTable.mean[meanidx]
        outTable.bfXCorr[iamp] = inTable.covarience[meanidx, 0, 1]
        outTable.bfXCorrErr[iamp] = inTable.covarienceError[meanidx, 0, 1]
        outTable.bfYCorr[iamp] = inTable.covarience[meanidx, 1, 0]
        outTable.bfYCorrErr[iamp] = inTable.covarienceError[meanidx, 1, 0]

        outTable.bfXSlope[iamp], outTable.bfXSlopeErr[iamp] =\
            self.fitSlopes(inTable.mean, inTable.covarience[:, 0, 1])
        outTable.bfYSlope[iamp], outTable.bfYSlopeErr[iamp] =\
            self.fitSlopes(inTable.mean, inTable.covarience[:, 1, 0])

    def prepImage(self, calibExp, amp):
        """
        Crop the image to avoid edge effects based on the Config border
        parameter. Additionally, if there is a dark image, subtract.
        """

        # Clone so that we don't modify the input image.
        localExp = calibExp.clone()

        # The border that we wish to crop.
        border = self.config.nPixBorder

        # Crop the image within a border region.
        bbox = amp.getRawDataBBox()
        bbox.grow(-border)
        localExp = localExp[bbox]

        # Calculate the median of the image.
        median = afwMath.makeStatistics(localExp.image, afwMath.MEDIAN, self.statCtrl).getValue()
        return localExp, median

    def crossCorrelate(self, maskedimage1, maskedimage2):
        """
        Calculate the correlation coefficients.
        """
        sctrl = afwMath.StatisticsControl()
        sctrl.setNumSigmaClip(self.config.nSigmaClip)
        mask = maskedimage1.getMask()
        INTRP = mask.getPlaneBitMask("INTRP")
        sctrl.setAndMask(INTRP)

        # Diff the images.
        diff = maskedimage1.clone()
        diff.image.array -= maskedimage2.image.array

        # Subtract background.
        nx = diff.getWidth()//self.config.backgroundBinSize
        ny = diff.getHeight()//self.config.backgroundBinSize
        bctrl = afwMath.BackgroundControl(nx, ny, self.statCtrl, afwMath.MEDIAN)  # pylint: disable=no-member
        bkgd = afwMath.makeBackground(diff.image, bctrl)  # pylint: disable=no-member
        bgImg = bkgd.getImageF(afwMath.Interpolate.CUBIC_SPLINE,
                               afwMath.REDUCE_INTERP_ORDER)  # pylint: disable=no-member

        diff.image.array -= bgImg.array

        # Measure the correlations
        x0, y0 = diff.getXY0()
        width, height = diff.getDimensions()
        bbox_extent = lsstGeom.Extent2I(width - self.config.maxLag, height - self.config.maxLag)

        bbox = lsstGeom.Box2I(lsstGeom.Point2I(x0, y0), bbox_extent)
        dim0 = diff[bbox].clone()
        dim0.image.array -= afwMath.makeStatistics(dim0.image, afwMath.MEDIAN, sctrl).getValue()

        xcorr = np.zeros((self.config.maxLag + 1, self.config.maxLag + 1), dtype=np.float64)
        xcorr_err = np.zeros((self.config.maxLag + 1, self.config.maxLag + 1), dtype=np.float64)

        for xlag in range(self.config.maxLag + 1):
            for ylag in range(self.config.maxLag + 1):
                bbox_lag = lsstGeom.Box2I(lsstGeom.Point2I(x0 + xlag, y0 + ylag),
                                          bbox_extent)
                dim_xy = diff[bbox_lag].clone()
                dim_xy.image.array -= afwMath.makeStatistics(dim_xy.image, afwMath.MEDIAN, self.statCtrl).getValue()
                dim_xy.image.array *= dim0.image.array
                xcorr[xlag, ylag] = afwMath.makeStatistics(dim_xy.image, afwMath.MEDIAN, self.statCtrl).getValue()
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
        xcorr = np.squeeze(xcorr)
        mean = np.squeeze(mean)
        xcorr = xcorr[mean < adu_max]
        mean = mean[mean < adu_max]
        slopex, _, _, _, errx = stats.linregress(mean, xcorr)
        return slopex, errx
