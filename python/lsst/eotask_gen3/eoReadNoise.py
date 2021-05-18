import numpy as np

import lsst.afw.math as afwMath
import lsst.geom as lsstGeom

from .eoCalibBase import EoAmpExpCalibTaskConfig, EoAmpExpCalibTaskConnections, EoAmpExpCalibTask
from .eoReadNoiseData import EoReadNoiseData

__all__ = ["EoReadNoiseTask", "EoReadNoiseTaskConfig"]


class SubRegionSampler:
    """ Generate sub-regions at random locations on the segment
    imaging region.
    """
    def __init__(self, dx, dy, nsamp, imaging):
        self.dx = dx
        self.dy = dy
        self.xarr = np.random.randint(imaging.getWidth() - dx - 1, size=nsamp)
        self.yarr = np.random.randint(imaging.getHeight() - dy - 1, size=nsamp)
        self.imaging = imaging

    def bbox(self, x, y):
        return lsstGeom.Box2I(lsstGeom.Point2I(int(x), int(y)),
                              lsstGeom.Extent2I(self.dx, self.dy))

    def subim(self, im, x, y):
        return im.Factory(im, self.bbox(x, y))

    def noiseSamples(self, calibExp, statCtrl=afwMath.StatisticsControl()):
        image = calibExp.Factory(calibExp, self.imaging)
        bbox = image.getBBox()
        samples = []
        for x, y in zip(self.xarr, self.yarr):
            subim = self.subim(image, x + bbox.getMinX(), y + bbox.getMinY())
            stdev = afwMath.makeStatistics(subim, afwMath.STDEV, statCtrl).getValue()  # pylint: disable=no-member
        samples.append(stdev)
        return np.array(samples)


class EoReadNoiseTaskConfig(EoAmpExpCalibTaskConfig,
                            pipelineConnections=EoAmpExpCalibTaskConnections):

    def setDefaults(self):
        # pylint: disable=no-member
        self.connections.output = "ReadNoise"


class EoReadNoiseTask(EoAmpExpCalibTask):

    ConfigClass = EoReadNoiseTaskConfig
    _DefaultName = "readNoise"

    def makeOutputData(self, amps, nExposure):  # pylint: disable=arguments-differ

        return EoReadNoiseData(amps=amps, nAmp=len(amps), nExposure=nExposure, nSamples=self.config.nsamp)

    def analyzeAmpExpData(self, calibExp, outputData, amp, iExp):

        imaging = calibExp.imaging  # FIXME
        dx = self.config.dx
        dy = self.config.dy
        nsamp = self.config.nsamp

        sampler = SubRegionSampler(dx, dy, nsamp, imaging=imaging)
        outputData.ampExp[amp.index].totalNoise[iExp] = sampler.noiseSamples(calibExp)

    def analyzeAmpRunData(self, outputData, amp):

        totalNoise = afwMath.makeStatistics(outputData.ampExp[amp.index].totalNoise,
                                            afwMath.MEDIAN).getValue()
        systemNoise = 0.  # FIXME
        if totalNoise >= systemNoise:
            readNoise = np.sqrt(totalNoise**2 - systemNoise**2)
        else:
            readNoise = -1
        outputData.amps.totalNoise[amp.index] = totalNoise
        outputData.amps.systemNoise[amp.index] = systemNoise
        outputData.amps.readNoiseNoise[amp.index] = readNoise
