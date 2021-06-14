import numpy as np

import lsst.pex.config as pexConfig
import lsst.afw.math as afwMath
import lsst.geom as lsstGeom
import lsst.pipe.base.connectionTypes as cT

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


class EoReadNoiseTaskConnections(EoAmpExpCalibTaskConnections):
    
    outputData = cT.Output(
        name="eoReadNoise",
        doc="Electrial Optical Calibration Output",
        storageClass="EoCalib",
        dimensions=("instrument", "detector"),
    )

class EoReadNoiseTaskConfig(EoAmpExpCalibTaskConfig,
                            pipelineConnections=EoReadNoiseTaskConnections):
    
    dx = pexConfig.Field("Size of region to sample", int, default=100)
    dy = pexConfig.Field("Size of region to sample", int, default=100)
    nsamp = pexConfig.Field("Number of samples", int, default=100)

    def setDefaults(self):
        # pylint: disable=no-member
        self.connections.outputData = "eoReadNoise"
        self.isr.expectWcs = False
        self.isr.doSaturation = False
        self.isr.doSetBadRegions = False
        self.isr.doAssembleCcd = False
        self.isr.doBias = True
        self.isr.doLinearize = False
        self.isr.doDefect = False
        self.isr.doNanMasking = False
        self.isr.doWidenSaturationTrails = False
        self.isr.doDark = False
        self.isr.doFlat = False
        self.isr.doFringe = False
        self.isr.doInterpolate = False
        self.isr.doWrite = False
        self.dataSelection = "biasBias"


class EoReadNoiseTask(EoAmpExpCalibTask):

    ConfigClass = EoReadNoiseTaskConfig
    _DefaultName = "readNoise"

    def makeOutputData(self, amps, nAmps, nExposure):  # pylint: disable=arguments-differ

        return EoReadNoiseData(amps=amps, nAmp=nAmps, nExposure=nExposure, nSample=self.config.nsamp)

    def analyzeAmpExpData(self, calibExp, outputData, iamp, amp, iExp):

        imaging = calibExp.getDetector().getAmplifiers()[0].getBBox() # FIXME
        dx = self.config.dx
        dy = self.config.dy
        nsamp = self.config.nsamp

        sampler = SubRegionSampler(dx, dy, nsamp, imaging=imaging)
        outputData.ampExp["ampExp_%s" % amp.getName()].totalNoise[iExp] = sampler.noiseSamples(calibExp)

    def analyzeAmpRunData(self, outputData, iamp, amp):

        totalNoise = afwMath.makeStatistics(outputData.ampExp["ampExp_%s" % amp.getName()].totalNoise,
                                            afwMath.MEDIAN).getValue()
        systemNoise = 0.  # FIXME
        if totalNoise >= systemNoise:
            readNoise = np.sqrt(totalNoise**2 - systemNoise**2)
        else:
            readNoise = -1
        outputData.amps["amps"].totalNoise[iamp] = totalNoise
        outputData.amps["amps"].systemNoise[iamp] = systemNoise
        outputData.amps["amps"].readNoiseNoise[iamp] = readNoise
