""" Class to make plots from EoCalibData objects
"""

import copy

import lsst.pex.config as pexConfig
import lsst.pipe.base as pipeBase
import lsst.pipe.base.connectionTypes as cT

__all__ = ['EoStaticPlotTaskConfig', 'EoStaticPlotTask']


class EoStaticPlotTaskConnections(pipeBase.PipelineTaskConnections,
                                  dimensions=("instrument",),
                                  defaultTemplates={"eoCalibType": "calib"}):
    inputData = cT.Input(
        name="{eoCalibType}",
        doc="Figure with E.O. calibration data",
        storageClass="Plot",
        dimensions=("instrument", "detector"),
        multiple=True,
    )


class EoStaticPlotTaskConfig(pipeBase.PipelineTaskConfig,
                             pipelineConnections=EoStaticPlotTaskConnections):

    dirName = pexConfig.Field("Directory to store plots", str, ".")
    baseName = pexConfig.Field("Basename for plots", str, ".")


class EoStaticPlotTask(pipeBase.PipelineTask):

    ConfigClass = EoStaticPlotTaskConfig
    _DefaultName = "eoStaticPlot"

    def runQuantum(self, butlerQC, inputRefs, outputRefs):
        cameraDict = OrderedDict()
        inputs = butlerQC.get(inputRefs)
        refObj = None
        for inputData, inputRef in zip(inputs['inputData'], inputRefs.inputData):
            if refObj is None:
                refObj = inputData
            det = inputRef.dataId.records["detector"]
            raftName = det['raftName']
            slotName = det['slotName']
            if raftName in cameraDict:
                raftDict = cameraDict['raftName']
            else:
                raftDict = cameraDict.setdefault(raftName, OrderedDict())
            raftDict[slotName] = inputData
            
        outputs = self.run(refObj=refObj, cameraDict=cameraDict)
        butlerQC.put(outputs, outputRefs)


    def run(self, refObj, cameraDict)
        cameraFigs = refObj.makeCameraFigures("%s_camera" % self.config.baseName, cameraDict)
        refObj.writeFigures(self.config.dirName, cameraFigs)

        for raftName, raftData in cameraDict.items():
            raftFigs = refObj.makeRaftFigures("%s_%s" % (self.config.baseName, raftName), raftData)
            refObj.writeFigures(self.config.dirName, raftFigs)

            for slotName, slotData in raftData.items():
                slotFigs = slotData.makeDetFigures("%s_%s_%s" % (self.config.baseName, raftName, slotName))
                refObj.writeFigures(self.config.dirName, slotFigs)      
         return pipeBase.Struct()


