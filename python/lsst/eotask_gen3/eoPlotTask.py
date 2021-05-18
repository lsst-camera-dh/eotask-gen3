""" Class to make plots from EoCalibData objects
"""

import copy

import lsst.pex.config as pexConfig
import lsst.pipe.base as pipeBase
import lsst.pipe.base.connectionTypes as cT

__all__ = ['EoCalibFigureTaskConfig', 'EoCalibFigureTask',
           'EoStaticPlotTaskConfig', 'EoStaticPlotTask']


class EoCalibFigureTaskConnections(pipeBase.PipelineTaskConnections,
                                   dimensions=("instrument", "exposure"),
                                   defaultTemplates={"eoCalibType": "calib", "plotName": "plot"}):
    inputCalib = cT.Input(
        name="{eoCalibType}",
        doc="Electrial Optical Calibration Output",
        storageClass="EoCalib",
        dimensions=("instrument", "detector"),
    )

    output = cT.Output(
        name="{eoCalibType}_{plotName}"
        doc="Figure with E.O. calibration data"
        storageClass="Plot",
        dimensions=("instrument", "detector"),
    )


class EoCalibFigureTaskConfig(pipeBase.PipelineTaskConfig,
                              pipelineConnections=EoCalibFigureTaskConnections):

    plotName = pexConfig.Field("Name of plot for this task", str, "None")


class EoCalibFigureTask(pipeBase.PipelineTask):

    ConfigClass = EoCalibFigureTaskConfig
    _DefaultName = "calibFigure"

    def run(self, inputCalib, **kwargs):
        output = inputCalib.makePlot(self.config.plotName, **kwargs)
        return pipeBase.Struct(output=output)

    

class EoStaticPlotTaskConnections(pipeBase.PipelineTaskConnections,
                                  dimensions=("instrument", "exposure"),
                                  defaultTemplates={"eoCalibType": "calib", "plotName": "plot"}):
    inputFigure = cT.Input(
        name="{eoCalibType}_{plotName}",
        doc="Figure with E.O. calibration data",
        storageClass="Plot",
        dimensions=("instrument", "detector"),
    )


class EoStaticPlotTaskConfig(pipeBase.PipelineTaskConfig,
                             pipelineConnections=EoStaticPlotTaskConnections):

    dirName = pexConfig.Field("Directory to store plots", str, ".")
    pathTemplate = pexConfig.Field("Name of plot for this task", str, "{eoCalibType}_{plotName}_{detector}")


class EoStaticPlotTask(pipeBase.PipelineTask):

    ConfigClass = EoStaticPlotTaskConfig
    _DefaultName = "staticPlot"

    def runQuantum(self, butlerQC, inputRefs, outputRefs):
        savePath = self.formatPath(inputRefs)
        inputs = butlerQC.get(inputRefs)
        inputs['savePath'] = savePath
        outputs = self.run(**inputs)
        butlerQC.put(outputs, outputRefs)

    def run(self, inputFigure, savePath):
        inputFigure.savefig(savePath)
    
    def formatPath(self, inputRefs):        
        fDict = dict(eoCalibType=self.config.eoCalibType,
                     plotName=self.config.plotName,
                     detector="%03i" % inputRefs['inputFigure'].dataId['detector'])
        basename = self.config.pathTemplate.format(**fDict)
        return os.path.join(self.config.dirName, basename)
