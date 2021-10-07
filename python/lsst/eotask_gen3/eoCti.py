import lsst.afw.math as afwMath

import lsst.pex.config as pexConfig
import lsst.pipe.base.connectionTypes as cT
import lsst.pipe.base as pipeBase

from .eoCalibBase import EoDetRunCalibTaskConfig, EoDetRunCalibTaskConnections, EoDetRunCalibTask
from .eoCtiData import EoCtiData
from .eoCtiUtils import estimateCti

__all__ = ["EoCtiTask", "EoCtiTaskConfig"]


class EoCtiTaskConnections(EoDetRunCalibTaskConnections):

    stackedCalExp = cT.Input(
        name="eoFlatHigh",
        doc="Stacked Calibrated Input Frame",
        storageClass="ExposureF",
        dimensions=("instrument", "detector"),
        isCalibration=True,
    )

    outputData = cT.Output(
        name="eoCti",
        doc="Electrial Optical Calibration Output",
        storageClass="IsrCalib",
        dimensions=("instrument", "detector"),
    )


class EoCtiTaskConfig(EoDetRunCalibTaskConfig,
                      pipelineConnections=EoCtiTaskConnections):

    overscans = pexConfig.Field("Number of overscan rows/columns to use", int, default=2)
    cti = pexConfig.Field('Return CTI instead of CTE', bool, default=False)

    def setDefaults(self):
        # pylint: disable=no-member
        self.connections.stackedCalExp = "eoFlatHigh"
        self.connections.outputData = "eoCti"


class EoCtiTask(EoDetRunCalibTask):

    ConfigClass = EoCtiTaskConfig
    _DefaultName = "eoCti"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.statCtrl = afwMath.StatisticsControl()

    def run(self, stackedCalExp, **kwargs):  # pylint: disable=arguments-differ
        """ Run method.  Generates summary data.

        Parameters
        ----------
        stackedCalExp : `lsst.afw.Exposure`
            Input data, i.e., a stacked exposure of dark frames

        Returns
        -------
        outputData : `lsst.eotask_gen3.EoCtiData`
            Output data in formatted tables
        """
        camera = kwargs.get('camera', None)
        det = stackedCalExp.getDetector()
        amps = det.getAmplifiers()
        nAmp = len(amps)
        ampNames = [amp.getName() for amp in amps]
        outputData = self.makeOutputData(amps=ampNames, nAmp=nAmp, detector=det, camera=camera)
        for iamp, amp in enumerate(amps):
            self.analyzeAmpRunData(stackedCalExp, outputData, iamp, amp, **kwargs)
        return pipeBase.Struct(outputData=outputData)

    def makeOutputData(self, amps, nAmp, **kwargs):
        """Construct the output data object

        Parameters
        ----------
        amps : `list` [`str`]
            Names of the amplifiers

        nAmp : `int`
            Number of amplifiers

        kwargs are passed to `lsst.eotask_gen3.EoCalib` base class
        constructor

        Returns
        -------
        outputData : `lsst.eotask_gen3.EoCtiData`
            Container for output data
        """
        return EoCtiData(amps=amps, nAmp=nAmp, **kwargs)

    def analyzeAmpRunData(self, detExposure, outputData, iamp, amp, **kwargs):
        """Analyze data from a single amplifier for the run.

        See base class for argument description

        This esimates the charge transfer inefficiency for the amplifier
        by looking at the overscan regions from the stacked flat exposures
        """
        ctiSerialEstim = estimateCti(detExposure, amp, 's', self.config.overscans, self.statCtrl)
        ctiParallelEstim = estimateCti(detExposure, amp, 'p', self.config.overscans, self.statCtrl)

        outputTable = outputData.amps['amps']

        if self.config.cti:
            outputTable.ctiSerial[iamp] = ctiSerialEstim.value
            outputTable.ctiParallel[iamp] = ctiParallelEstim.value
        else:
            outputTable.ctiSerial[iamp] = 1 - ctiSerialEstim.value
            outputTable.ctiParallel[iamp] = 1 - ctiParallelEstim.value

        outputTable.ctiSerialError[iamp] = ctiSerialEstim.error
        outputTable.ctiParalleError[iamp] = ctiParallelEstim.error
