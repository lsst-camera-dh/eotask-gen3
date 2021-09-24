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

    @staticmethod
    def buildCameraDict(inputData, inputRefs, butler=None):
        cameraDict = OrderedDict()        
        refObj = None            
        for inputData_, inputRef_ in zip(inputData, inputRefs):
            if refObj is None:
                refObj = inputData_
            if not inputRef_.dataId.hasRecords():
                records = list(butler.registry.queryDimensionRecords("detector", dataId=inputRef_.dataId))[0]
            else:
                records = inputRef_.dataId.records["detector"]
            det = records.toDict()
            raftName = det['raft']
            slotName = det['name_in_raft']
            if raftName in cameraDict:
                raftDict = cameraDict['raftName']
            else:
                raftDict = cameraDict.setdefault(raftName, OrderedDict())
            raftDict[slotName] = inputData_
        return refObj, cameraDict


    def runQuantum(self, butlerQC, inputRefs, outputRefs):
        inputs = butlerQC.get(inputRefs)
        refObj, cameraDict = self.buildCameraDict(inputs['inputData'], inputRefs.inputData)
        outputs = self.run(refObj=refObj, cameraDict=cameraDict,
                           baseName=self.config.baseName, dirName=self.config.dirName)
        butlerQC.put(outputs, outputRefs)


    def run(self, refObj, cameraDict, baseName, dirName):
        cameraFigs = refObj.makeCameraFigures("%s_camera" % baseName, cameraDict)
        cameraDir = os.path.join(dirName, 'camera')
        try:
            os.makedirs(cameraDir)
        except:
            pass
        refObj.writeFigures(cameraDir, cameraFigs)

        for raftName, raftData in cameraDict.items():
            raftDir = os.path.join(dirName, 'camera', raftName)
            try:
                os.makedirs(raftDir)
            except:
                pass
            raftFigs = refObj.makeRaftFigures("%s_%s" % (baseName, raftName), raftData)
            refObj.writeFigures(raftDir, raftFigs)

            for slotName, slotData in raftData.items():
                slotDir = os.path.join(dirName, 'camera', raftName, slotName)
                try:
                    os.makedirs(slotDir)
                except:
                    pass
                slotFigs = refObj.makeFigures("%s_%s_%s" % (baseName, raftName, slotName), slotData)
                refObj.writeFigures(slotDir, slotFigs)      
        return pipeBase.Struct()


