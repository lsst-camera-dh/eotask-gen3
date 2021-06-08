""" Utility functions for EO charge transfer inefficiency tests
"""

import numpy as np
from collections import namedtuple

__all__ = ["AmpTearingStats"]



class AmpTearingStats:
    """
    Class to compute Pierre Antilogus' tearing statistics based on
    the size of the transitions in the ratio of the two outermost
    columns of pixels on both sides of an amplifier.
    """
    def __init__(self, calibExp, ampGeom):
        """
        Parameters
        ----------
        calibExp: lsst.afw.image.Image
            Image object of the full segment of an amplifier.
        ampGeom: lsst.eotest.sensor.AmplifierGeometry
            Object containing the amplifier pixel geometry.
        buf: int [10]
            Number of pixels to avoid on leading and trailing edge of
            serial overscan to compute the bias level for each row.
        """
        self.imarr = calibExp[ampGeom.getRawDataBBox()].image.array
        self._ratioProfiles = None
        self._ratios = None
        self._stdevs = None
        self._rstats = None
        self.ylocs = 150, 1000, 1950
        self.dy = 50

    @property
    def rstats(self):
        """Full range of mean edge ratio values with errors."""
        RatioStats = namedtuple('RatioStats', ('diff', 'error'))
        if self._rstats is None:
            self._rstats = []
            for i in range(2):
                r = self.ratios[i]
                dr = self.stdevs[i]
                jmin = np.argmin(r)
                jmax = np.argmax(r)
                self._rstats.append(
                    RatioStats(r[jmax] - r[jmin],
                               np.sqrt(dr[jmax]**2 + dr[jmin]**2)/10.))
        return self._rstats

    @property
    def ratioProfiles(self):
        """Profiles of the edge pixel ratios."""
        if self._ratioProfiles is None:
            self._ratioProfiles = (self.imarr[:, 1]/self.imarr[:, 0], self.imarr[:, -2]/self.imarr[:, -1])
        return self._ratioProfiles

    @property
    def ratios(self):
        """Mean values of ratio profiles evaluated at self.yloc locations."""
        if self._ratios is None:
            self._computeRatios()
        return self._ratios

    @property
    def stdevs(self):
        """Standard deviations of ratio profiles evaluated at self.yloc
        locations."""
        if self._stdevs is None:
            self._computeRatios()
        return self._stdevs

    def _computeRatios(self):
        self._ratios = []
        self._stdevs = []
        for profile in self.ratioProfiles:
            myRatios = []
            myStdevs = []
            for yloc in self.ylocs:
                ymin, ymax = yloc - self.dy, yloc + self.dy
                myRatios.append(profile[ymin:ymax].mean())
                myStdevs.append(profile[ymin:ymax].std())
            self._ratios.append(myRatios)
            self._stdevs.append(myStdevs)
