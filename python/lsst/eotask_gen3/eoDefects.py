
import numpy as np

import lsst.pex.config as pexConfig
import lsst.pipe.base as pipeBase
import lsst.pipe.base.connectionTypes as cT
import lsst.afw.detection as afwDetect

from lsst.ip.isr import Defects

from .eoCalibBase import (EoDetRunCalibTaskConfig, EoDetRunCalibTaskConnections, EoDetRunCalibTask,\
                          extractAmpImage, OUTPUT_DEFECTS_CONNECT, copyConnect)


__all__ = ["EoBrightPixelTask", "EoBrightPixelTaskConfig"]


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

    ConfigClass = EoDefectsTaskConfig
    _DefaultName = "eoDefects"
    
    def run(self, brightPixels, darkPixels, **kwargs): 
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
        defects : `ip.isr.Defects`
            Output defect list
        """
        outDefects = Defects()
        with outDefects.bulk_update():
            for inputDefects in [brightPixels, darkPixels]:
                for d in inputDefects:
                    outDefects.append(d)
        return pipeBase.Struct(defects=outDefects)


        
