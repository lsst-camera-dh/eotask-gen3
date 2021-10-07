import lsst.pipe.base as pipeBase
import lsst.pipe.base.connectionTypes as cT

from lsst.ip.isr import Defects

from .eoCalibBase import EoDetRunCalibTaskConfig, EoDetRunCalibTaskConnections, EoDetRunCalibTask


__all__ = ["EoDefectsTaskConfig", "EoDefectsTask"]


class EoDefectsTaskConnections(EoDetRunCalibTaskConnections):

    brightPixels = cT.Input(
        name="eoBrightPixels",
        doc="Electrial Optical Calibration Output",
        storageClass="Defects",
        dimensions=("instrument", "detector"),
        isCalibration=True,
    )

    darkPixels = cT.Input(
        name="eoDarkPixels",
        doc="Electrial Optical Calibration Output",
        storageClass="Defects",
        dimensions=("instrument", "detector"),
        isCalibration=True,
    )

    defects = cT.Output(
        name='defects',
        doc="Output defect tables.",
        storageClass="Defects",
        dimensions=("instrument", "detector"),
        isCalibration=True,
    )


class EoDefectsTaskConfig(EoDetRunCalibTaskConfig,
                          pipelineConnections=EoDefectsTaskConnections):

    def setDefaults(self):
        self.connections.brightPixels = "eoBrightPixels"
        self.connections.darkPixels = "eoDarkPixels"
        self.connections.defects = "defects"


class EoDefectsTask(EoDetRunCalibTask):
    """Combines Defect sets from other tasks

    Summary output is stored as `lsst.eotask_gen3.EoDefectsData`

    Defect sets are stored as `lsst.ip.isr.Defects`

    Currently combined defects from EoBrightPixelsTask and EoDarkPixelsTask.

    To Do: add edge rolloff masking
    """

    ConfigClass = EoDefectsTaskConfig
    _DefaultName = "eoDefects"

    def run(self, brightPixels, darkPixels, **kwargs):
        """ Run method

        Parameters
        ----------
        brightPixels : `lsst.ip.isr.Defects`
            Bright Pixel defect set

        darkPixels : `lsst.ip.isr.Defects`
            Dark Pixel defect set

        Returns
        -------
        defects : `lsst.ip.isr.Defects`
            Output defect list
        """
        outDefects = Defects()
        with outDefects.bulk_update():
            for inputDefects in [brightPixels, darkPixels]:
                for d in inputDefects:
                    outDefects.append(d)
        return pipeBase.Struct(defects=outDefects)
