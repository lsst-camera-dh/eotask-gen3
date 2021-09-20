""" Class to make plots from EoCalibData objects
"""

import os
from collections import OrderedDict
import copy

import lsst.pex.config as pexConfig
import lsst.pipe.base as pipeBase
import lsst.pipe.base.connectionTypes as cT

__all__ = ['EoStaticPlotTaskConfig', 'EoStaticPlotTask']


class EoStaticPlotTaskConnections(pipeBase.PipelineTaskConnections,
                                  dimensions=("instrument",)):
    inputData = cT.Input(
        name="calib",
        doc="Object with E.O. calibration data",
        storageClass="IsrCalib",
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
            det = inputRef.dataId.records["detector"].toDict()
            raftName = det['raft']
            slotName = det['name_in_raft']
            if raftName in cameraDict:
                raftDict = cameraDict['raftName']
            else:
                raftDict = cameraDict.setdefault(raftName, OrderedDict())
            raftDict[slotName] = inputData
            
        outputs = self.run(refObj=refObj, cameraDict=cameraDict)
        butlerQC.put(outputs, outputRefs)


    def run(self, refObj, cameraDict):
        cameraFigs = refObj.makeCameraFigures("%s_camera" % self.config.baseName, cameraDict)
        cameraDir = os.path.join(self.config.dirName, 'camera')
        try:
            os.makedirs(cameraDir)
        except:
            pass
        refObj.writeFigures(cameraDir, cameraFigs)

        for raftName, raftData in cameraDict.items():
            raftDir = os.path.join(self.config.dirName, 'camera', raftName)
            try:
                os.makedirs(raftDir)
            except:
                pass
            raftFigs = refObj.makeRaftFigures("%s_%s" % (self.config.baseName, raftName), raftData)
            refObj.writeFigures(raftDir, raftFigs)

            for slotName, slotData in raftData.items():
                slotDir = os.path.join(self.config.dirName, 'camera', raftName, slotName)
                try:
                    os.makedirs(slotDir)
                except:
                    pass
                slotFigs = slotData.makeFigures("%s_%s_%s" % (self.config.baseName, raftName, slotName))
                refObj.writeFigures(slotDir, slotFigs)      
        return pipeBase.Struct()


