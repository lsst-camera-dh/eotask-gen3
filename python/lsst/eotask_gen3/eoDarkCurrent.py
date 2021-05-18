
import numpy as np

from .eoCalibBase import EoAmpRunCalibTaskConfig, EoAmpRunCalibTaskConnections, EoAmpRunCalibTask
from .eoDarkCurrentData import EoDarkCurrentData

__all__ = ["EoDarkCurrentTask", "EoDarkCurrentTaskConfig"]


class EoDarkCurrentTaskConfig(EoAmpRunCalibTaskConfig,
                              pipelineConnections=EoAmpRunCalibTaskConnections):
   
    def setDefaults(self):
        # pylint: disable=no-member        
        self.connections.output = "DarkCurrent"


class EoDarkCurrentTask(EoAmpRunCalibTask):

    ConfigClass = EoDarkCurrentTaskConfig
    _DefaultName = "darkCurrent"
    
    def makeOutputData(self, amps):  # pylint: disable=arguments-differ,no-self-use
        return EoDarkCurrentData(nAmp=len(amps))

    def analyzeAmpRunData(self, ampExposure, outputData, amp, **kwargs):

        try:
            exptime = ampExposure.meta['DARKTIME']
        except KeyError:
            exptime = ampExposure.meta['EXPTIME']

        q50, q95 = np.quantiles(ampExposure.image.array, [0.50, 0.95])
        outputData.amp.darkCurrentMedian[amp.index] = q50/exptime
        outputData.amp.darkCurrent95[amp.index] = q95/exptime
