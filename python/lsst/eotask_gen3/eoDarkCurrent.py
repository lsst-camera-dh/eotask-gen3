import numpy as np

import lsst.pipe.base as pipeBase
import lsst.pipe.base.connectionTypes as cT

from .eoCalibBase import (EoDetRunCalibTaskConfig, EoDetRunCalibTaskConnections, EoDetRunCalibTask,
                          extractAmpImage)
from .eoDarkCurrentData import EoDarkCurrentData

__all__ = ["EoDarkCurrentTask", "EoDarkCurrentTaskConfig"]


class EoDarkCurrentTaskConnections(EoDetRunCalibTaskConnections):

    stackedCalExp = cT.Input(
        name="eoDark",
        doc="Stacked Calibrated Input Frame",
        storageClass="ExposureF",
        dimensions=("instrument", "detector"),
        isCalibration=True,
    )

    outputData = cT.Output(
        name="eoDarkCurrent",
        doc="Electrial Optical Calibration Output",
        storageClass="IsrCalib",
        dimensions=("instrument", "detector"),
    )


class EoDarkCurrentTaskConfig(EoDetRunCalibTaskConfig,
                              pipelineConnections=EoDarkCurrentTaskConnections):

    def setDefaults(self):
        # pylint: disable=no-member
        self.connections.stackedCalExp = "eoDark"
        self.connections.outputData = "eoDarkCurrent"


class EoDarkCurrentTask(EoDetRunCalibTask):

    ConfigClass = EoDarkCurrentTaskConfig
    _DefaultName = "darkCurrent"

    def run(self, stackedCalExp, **kwargs):  # pylint: disable=arguments-differ
        """ Run method

        Parameters
        ----------
        stackedCalExp :: `lsst.afw.Exposure`
            Input data, i.e., a stacked exposure of dark frames

        Returns
        -------
        outputData : `lsst.eotask_gen3.EoDarkCurrentData`
            Output data in formatted tables
        """
        camera = kwargs.get('camera', None)
        det = stackedCalExp.getDetector()
        amps = det.getAmplifiers()
        nAmp = len(amps)
        outputData = self.makeOutputData(nAmp=nAmp, detector=det, camera=camera)
        import pdb
        pdb.set_trace()
        for iAmp, amp in enumerate(amps):
            ampExposure = extractAmpImage(stackedCalExp, amp)
            self.analyzeAmpRunData(ampExposure, outputData, iAmp, amp)
        return pipeBase.Struct(outputData=outputData)

    def makeOutputData(self, nAmp, **kwargs):  # pylint: disable=arguments-differ,no-self-use
        """Construct the output data object

        Parameters
        ----------
        nAmp : `int`
            Number of amplifiers

        kwargs are passed to `lsst.eotask_gen3.EoCalib` base class constructor

        Returns
        -------
        outputData : `lsst.eotask_gen3.EoDarkCurrentData`
            Container for output data
        """
        return EoDarkCurrentData(nAmp=nAmp, **kwargs)

    def analyzeAmpRunData(self, ampExposure, outputData, iAmp, amp, **kwargs):
        """Analyze data from a single amplifier for the run.

        See base class for argument description

        This just extract the median and 95% quantile of the signal per pixel
        from the stacked dark exposure
        """

        try:
            exptime = ampExposure.getMetadata().toDict()['DARKTIME']
        except KeyError:
            try:
                exptime = ampExposure.getMetadata().toDict()['EXPTIME']
            except KeyError:
                exptime = 1.

        import pdb
        pdb.set_trace()
        q50, q95 = np.quantile(ampExposure.image.array, [0.50, 0.95])
        outputData.amps['amps'].darkCurrentMedian[iAmp] = q50/exptime
        outputData.amps['amps'].darkCurrent95[iAmp] = q95/exptime
