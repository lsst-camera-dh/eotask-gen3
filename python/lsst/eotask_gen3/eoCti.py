
import lsst.afw.math as afwMath

import lsst.pex.config as pexConfig
import lsst.pipe.base.connectionTypes as cT

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
        """ Run method

        Parameters
        ----------
        stackedCalExp :
            Input data

        Keywords
        --------
        camera : `lsst.obs.lsst.camera`

        Returns
        -------
        outputData : `EoCalib`
            Output data in formatted tables
        """
        camera = kwargs.get('camera')
        det = stackedCalExp.getDetector()
        amps = det.getAmplifiers()
        nAmp = len(amps)
        ampNames = [amp.getName() for amp in amps]
        outputData = self.makeOutputData(amps=ampNames, nAmp=nAmp, camera=camera, detector=det)
        self.analyzeDetRunData(stackedCalExp, outputData, **kwargs)
        return pipeBase.Struct(outputData=outputData)
        
    def makeOutputData(self, amps, nAmp, **kwargs):
        return EoCtiData(amps=amps, nAmp=nAmp, **kwargs)

    def analyzeDetRunData(self, detExposure, outputData, iamp, amp, **kwargs):
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
