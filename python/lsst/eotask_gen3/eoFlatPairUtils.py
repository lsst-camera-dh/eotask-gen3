""" Utility functions for EO charge transfer inefficiency tests
"""

import numpy as np

__all__ = ["DetectorResponse"]


def _fwcSolve(f1Pars, f2Pars, g=0.1):
    """
    The solution (provided by e2v) for the flux corresponding to the
    full-well capacity described in LCA-10103-A.  This is simply the
    flux at which the quadratic fit to the data in the vicinity of
    full well lies below the linear extrapolation of the detector
    response from lower flux levels by a fraction g.
    """
    a, b, c = f2Pars
    d, f = f1Pars
    x = (-np.sqrt((b + d*g - d)**2 - 4.*a*(c + f*g - f)) - b - d*g + d)/2./a
    return x


class DetectorResponse:

    def __init__(self, flux):
        self._flux = flux
        self._index = np.argsort(self._flux)

    def fullWell(self, Ne, maxNonLinearity=0.02, fracOffset=0.1, fitRange=(1e2, 5e4)):
        results = self.linearity(Ne, fitRange=fitRange)
        _, f1Pars, Ne, flux = results[:4]
        f1 = np.poly1d(f1Pars)
        dNfrac = 1 - Ne/f1(flux)
        indexes = np.arange(len(dNfrac))
        goodVals = np.where(np.abs(dNfrac) <= maxNonLinearity)[0]
        if goodVals.sum() < 2:
            return (0., f1)

        imin = goodVals[-1]
        try:
            imax = np.where((np.abs(dNfrac) >= fracOffset) &
                            (indexes > imin))[0][0] + 1
        except IndexError:
            imax = len(dNfrac)
        #imin = imax - 3  # this is the proposed change from e2v on 2015-06-04
        x, y = flux[imin:imax], Ne[imin:imax]
        f2Pars = np.polyfit(x, y, 2)
        f2 = np.poly1d(f2Pars)
        fwc = _fwcSolve(f1Pars, f2Pars)
        fullWellEst = f2(fwc)
        return fullWellEst, f1


    def linearity(self, Ne, fitRange=None, specRange=(1e3, 9e4), maxFracDev=0.05):
        flux = self._flux[self._index]
        Ne = Ne[self._index]
        if fitRange is None:
            fitRange = specRange
        maxNeIndex = np.where(Ne == max(Ne))[0][0]
        index = np.where((Ne > fitRange[0]) & (Ne < fitRange[1])
                         & (flux <= flux[maxNeIndex]))

        defaultResults = 0, (1, 0), Ne, flux, [], [], max(Ne)
        if sum(index[0]) < 1:
            return defaultResults
        # Fit a linear slope to these data, using the variance for the
        # signal levels assuming Poisson statistics in the chi-square
        # and fixing the y-intercept to zero.  Package the slope as
        # part of a tuple to be passed to np.poly1d.
        slope = len(Ne[index])/np.sum(flux[index]/Ne[index])
        f1Pars = slope, 0
        f1 = np.poly1d(f1Pars)
        # Further select points that are within the specification range
        # for computing the maximum fractional deviation.
        specIndex = np.where((Ne > specRange[0]) & (Ne < specRange[1])
                                & (flux <= flux[maxNeIndex]))

        fluxSpec = flux[specIndex]
        NeSpec = Ne[specIndex]
        if len(NeSpec) < 1:
            return defaultResults

        dNfrac = 1 - NeSpec/f1(fluxSpec)
        return (max(abs(dNfrac)), f1Pars, Ne, flux, Ne[index], flux[index],
                self.linearityTurnoff(f1, flux, Ne, maxFracDev=maxFracDev))

    @staticmethod
    def linearityTurnoff(f1, flux, Ne, maxFracDev=0.05):
        """
        Find the maximum signal consistent with the linear fit within
        the specified maximum fractional deviation.
        """
        fracDev = f1(flux)/Ne - 1
        index = np.where(fracDev < maxFracDev)
        return np.max(Ne[index])

    def rowMeanVarSlope(self, rowMeanVar, nCols, minFlux=3000, maxFlux=1e5):
        # Restrict to higher flux values below full well and
        # avoid nans in row_mean_var.
        index = np.where((minFlux < self._flux) & (self._flux < maxFlux) & (np.isfinite(rowMeanVar)))
        if len(index[0]) == 0:
            return 0
        return sum(rowMeanVar[index])/sum(2.*self._flux[index]/nCols)
