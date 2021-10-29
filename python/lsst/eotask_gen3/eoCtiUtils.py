""" Utility functions for EO charge transfer inefficiency tests
"""

import numpy as np

import lsst.afw.math as afwMath
import lsst.geom as lsstGeom

__all__ = ["Estimator", "SubImage", "estimateCti"]


class Estimator:
    "Abstraction for a point estimator of pixel data and its errors"

    def __init__(self, *args, **kwds):
        self.image = None
        self.statCtrl = None
        self.statistic = None
        self.value = None
        self.error = None
        self._format_str = None
        if args:
            self.set_properties(*args, **kwds)

    def set_properties(self, image, statCtrl, statistic=afwMath.MEAN, varWt=1):
        # Make a deep copy of the input image so that we can convert to
        # e- and have Poisson statistics apply.
        self.image = image.clone()
        self.statCtrl = statCtrl
        self.statistic = statistic
        self.varWt = varWt
        self._compute_stats()

    def _compute_stats(self):
        if self.statCtrl is None:
            makeStatistics = lambda *args: afwMath.makeStatistics(*args[:2])
        else:
            makeStatistics = lambda *args: afwMath.makeStatistics(*args[:3])
        if self.statistic not in (afwMath.MEAN, afwMath.MEDIAN):
            # In case other statistics are given, set error to zero for now.
            self.value = makeStatistics(self.image.image, self.statistic,
                                        self.statCtrl).getValue()
            self.error = 0
            return
        # Compute the error assuming the statistic is afw.MEAN.  For
        # Gaussian stats, the error on the median is sqrt(pi/2.)
        # times the error on the mean, but for Poisson stats, it is
        # actually zero when the number of pixels is much larger than
        # the expected count per pixel, but within factors of order
        # unity to the error on the mean for numpix \la O(100)*count/pixel.
        flags = self.statistic | afwMath.SUM | afwMath.MEAN  # pylint: disable=no-member
        stats = makeStatistics(self.image.image, flags, self.statCtrl)
        pixel_sum = stats.getValue(afwMath.SUM)  # pylint: disable=no-member
        # Infer the number of pixels taking into account masking.
        if pixel_sum == 0:
            # Handle case where pixel_sum is zero (and hence the
            # mean is zero).
            self.value = 0
            self.error = 0
            return
        npix = pixel_sum/stats.getValue(afwMath.MEAN)  # pylint: disable=no-member
        self.value = stats.getValue(self.statistic)
        self.error = np.sqrt(pixel_sum/self.varWt)/npix

    def __add__(self, other):
        result = Estimator()
        if isinstance(other, Estimator):
            result.value = self.value + other.value
            result.error = np.sqrt(self.error**2 + other.error**2)
        else:
            # Assume other is an int or float.
            result.value = self.value + other
            result.error = self.error
        return result

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        result = Estimator()
        if isinstance(other, Estimator):
            result.value = self.value - other.value
            result.error = np.sqrt(self.error**2 + other.error**2)
        else:
            # Assume other is an int or float.
            result.value = self.value - other
            result.error = self.error
        return result

    def __rsub__(self, other):
        result = self.__sub__(other)
        if isinstance(other, Estimator):
            result.value *= -1
        return result

    def __mul__(self, other):
        result = Estimator()
        if isinstance(other, Estimator):
            result.value = self.value*other.value
            result.error = (np.abs(result.value)
                            * np.sqrt((self.error/self.value)**2
                                      + (other.error/other.value)**2))
        else:
            result.value = self.value*other
            result.error = self.error*other
        return result

    def __rmul__(self, other):
        return self.__mul__(other)

    def __div__(self, other):
        return self.__truediv__(other)

    def __truediv__(self, other):
        result = Estimator()
        if isinstance(other, Estimator):
            result.value = self.value/other.value
            result.error = (np.abs(result.value)
                            * np.sqrt((self.error/self.value)**2
                                      + (other.error/other.value)**2))
        else:
            result.value = self.value/other
            result.error = self.error/other
        return result

    def set_format_str(self, format_str):
        self._format_str = format_str

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        if self._format_str is None:
            return "%s +/- %s" % (self.value, self.error)
        return ' +/- '.join((self._format_str.format(self.value),
                             self._format_str.format(self.error)))


class SubImage:
    """Functor to produce sub-images depending on scan direction."""

    def __init__(self, calibExp, amp, overscans, direction):
        self.imaging = amp.getBBox()
        self.image = calibExp
        self.amp = amp
        if direction == 'p':
            self._bbox = self._parallelBox
            llc = lsstGeom.Point2I(amp.getRawParallelOverscanBBox().getMinX(),
                                   amp.getRawParallelOverscanBBox().getMinY() + overscans)
            urc = amp.getRawParallelOverscanBBox().getCorners()[2]
            self._biasReg = lsstGeom.Box2I(llc, urc)
            self.lastpix = amp.getRawDataBBox().getMaxY()
            return
        if direction == 's':
            self._bbox = self._serialBox
            llc = lsstGeom.Point2I(amp.getRawSerialOverscanBBox().getMinX() + overscans,
                                   amp.getRawSerialOverscanBBox().getMinY())
            urc = amp.getRawSerialOverscanBBox().getCorners()[2]
            #
            # Omit the last 4 columns to avoid the bright column in the
            # last overscan column in the e2v vendor data.
            #
            urc[0] -= 4
            self._biasReg = lsstGeom.Box2I(llc, urc)
            self.lastpix = amp.getRawDataBBox().getMaxX()
            return
        raise ValueError("Unknown scan direction: " + str(direction))

    def biasEst(self, statistic=afwMath.MEAN):
        subim = self.image.Factory(self.image, self._biasReg)
        biasEstimate = Estimator()
        biasEstimate.value = afwMath.makeStatistics(subim.image, statistic).getValue()
        num_pix = len(subim.getImage().getArray().flatten())
        biasEstimate.error = afwMath.makeStatistics(subim.image, afwMath.STDEV).getValue()\
            / np.sqrt(float(num_pix))  # pylint: disable=no-member
        return biasEstimate

    def __call__(self, start, end=None):

        if end is None:
            end = start
        my_exp = self.image.Factory(self.image, self._bbox(start, end))
        return my_exp

    def _parallelBox(self, start, end):
        llc = lsstGeom.PointI(self.amp.getRawDataBBox().getMinX(), start)
        urc = lsstGeom.PointI(self.amp.getRawDataBBox().getMaxX(), end)
        return lsstGeom.BoxI(llc, urc)

    def _serialBox(self, start, end):
        llc = lsstGeom.PointI(start, self.amp.getRawDataBBox().getMinY())
        urc = lsstGeom.PointI(end, self.amp.getRawDataBBox().getMaxY())
        return lsstGeom.BoxI(llc, urc)


def estimateCti(calibExp, amp, direction, overscans, statCtrl):
    nFrames = 10  # alibExp.meta['nFrames']
    subimage = SubImage(calibExp, amp, overscans, direction)
    lastpix = subimage.lastpix

    # find signal in last image vector (i.e., row or column)
    lastIm = Estimator(subimage(lastpix), statCtrl, varWt=nFrames)

    # find signal in each overscan vector
    overscan_ests = []
    for i in range(1, overscans+1):
        overscan_ests.append(Estimator(subimage(lastpix+i), statCtrl, varWt=nFrames))

    # sum medians of first n overscan rows
    summed = sum(overscan_ests)

    # Find bias level.
    biasEst = subimage.biasEst(statistic=afwMath.MEAN)

    # signal = last - bias
    sig = lastIm - biasEst

    # trailed = sum(last2) - bias
    trailed = summed - overscans*biasEst

    # charge loss per transfer = (trailed/signal)/N
    chargelosspt = (trailed/sig)/(lastpix + 1.)

    return chargelosspt
