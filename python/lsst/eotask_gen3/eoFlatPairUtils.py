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
    """Class to extract and cache parameters from linearity analysis
    of flat-pair data"""

    def __init__(self, flux):
        """C'tor from set of flux values

        Parameters
        ----------
        flux : `np.array`
            The flux values from the photodiode (a.u.)
        """
        self._flux = flux
        self._index = np.argsort(self._flux)

    def fullWell(self, Ne, maxNonLinearity=0.02, fracOffset=0.1, fitRange=(1e2, 5e4)):
        """Compute and return estimate of the full well charge in e-

        Parameters
        ----------
        Ne : `numpy.array`
            Mean signals in electrons
        maxNonLinearity : `float`
            Maximum deviation from linearity to use define start of turn off
        fracOffset : `float`
            Fractional deviation for points used to fit turn off curve
        fitRange : `tuple` [`float`]
            Range of values of Ne to use for fitting linearity

        Returns
        -------
        fullWellEst : `float`
            Full well estimate
        f1 : `np.poly1d`
            Fitted linearity curve

        Notes
        -----
        The solution (provided by e2v) for the flux corresponding
        to the full-well capacity described in LCA-10103-A.  This
        is simply the flux at which the quadratic fit to the data
        in the vicinity of full well lies below the linear
        extrapolation of the detector response from lower flux
        levels by a fraction `fracOffset`.
        """
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
            imax = np.where((np.abs(dNfrac) >= fracOffset)
                            & (indexes > imin))[0][0] + 1
        except IndexError:
            imax = len(dNfrac)
        # imin = imax - 3  # this is the proposed change from e2v on 2015-06-04
        x, y = flux[imin:imax], Ne[imin:imax]
        f2Pars = np.polyfit(x, y, 2)
        f2 = np.poly1d(f2Pars)
        fwc = _fwcSolve(f1Pars, f2Pars)
        fullWellEst = f2(fwc)
        return fullWellEst, f1

    def linearity(self, Ne, fitRange=None, specRange=(1e3, 9e4), maxFracDev=0.05):
        """Fit the linearity

        Parameters
        ----------
        Ne : `numpy.array`
            Mean signals in electrons
        fitRange : `tuple` [`float`] or `None`
            Used to select points to fit
        specRange : `tuple` [`float`]
            Range used to define maximum fractional deviation
        maxFracDev : `float`
            Maximum fraction deviation, used to define linearity turnoff point

        Returns
        -------
        maxDnFrac : `float`
            Maximum absolute fraction deviation
        f1Pars : `float`
            Linearity fit parameters
        Ne : `numpy.array`
            Mean signals in electrons
        flux : `numpy.array`
            Fluxes
        Ne_used : `numpy.array`
            Mean signals in electrons used in fit
        flux_used : `numpy.array`
            Flux values used in fit
        linearityTurnoff : `float`
            Maximum signal consistent with the linear fit
        """

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
        slope = len(Ne[index[0]])/np.sum(flux[index[0]]/Ne[index[0]])
        f1Pars = slope, 0
        f1 = np.poly1d(f1Pars)
        # Further select points that are within the specification range
        # for computing the maximum fractional deviation.
        specIndex = np.where((Ne > specRange[0]) & (Ne < specRange[1])
                             & (flux <= flux[maxNeIndex]))

        fluxSpec = flux[specIndex[0]]
        NeSpec = Ne[specIndex[0]]
        if len(NeSpec) < 1:
            return defaultResults

        dNfrac = 1 - NeSpec/f1(fluxSpec)
        return (max(abs(dNfrac)), f1Pars, Ne, flux, Ne[index[0]], flux[index[0]],
                self.linearityTurnoff(f1, flux, Ne, maxFracDev=maxFracDev))

    @staticmethod
    def linearityTurnoff(f1, flux, Ne, maxFracDev=0.05):
        """ Find the maximum signal consistent with the linear fit within
        the specified maximum fractional deviation.

        Parameters
        ----------
        f1 : `np.poly1d`
            Fitted linearity curve
        flux : `numpy.array`
            Flux values
        Ne : `float`
            Flat-pair means
        maxFracDev : `float`
            Maximum fractional deviation

        Returns
        -------
        value : `float`
            Estimated linearity turnoff point
        """
        fracDev = f1(flux)/Ne - 1
        index = np.where(fracDev < maxFracDev)
        return np.max(Ne[index])

    def rowMeanVarSlope(self, rowMeanVar, signal, nCols, minFlux=3000, maxFlux=1e5):
        """ Fit the slope of the variance of the row-wise means v. flux

        Parameters
        ----------
        rowMeanVar : `numpy.array`
            variance of the mean of the rows of the difference image
        signal : `numpy.array`
            mean signal
        nCols : `int`
            Number of columns, used to correctly scale the output
        minFlux : `float`
            Minimum flux to use in computing slope
        maxFlux : `float`
            Maximum flux to use in computing slope

        Returns
        -------
        value : `float`
            Estimate of the slope of the rowMeanVar v. flux

        Notes
        -----
        The returned value is actually computed as the ratio
        of the sum of the row-wise means to the sum of the fluxes,
        scaled by the number of columns
        """
        # Restrict to higher flux values below full well and
        # avoid nans in row_mean_var.
        index = np.where((minFlux < signal) & (signal < maxFlux) & (np.isfinite(rowMeanVar)))
        if len(index[0]) == 0:
            return 0
        return sum(rowMeanVar[index[0]])/sum(2.*signal[index[0]]/nCols)
