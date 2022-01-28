""" Class to make plots from EoCalibData objects
"""

import os
from collections import OrderedDict

import lsst.pex.config as pexConfig
import lsst.pipe.base as pipeBase
import lsst.pipe.base.connectionTypes as cT
from lsst.eotask_gen3.eoCalibBase import CAMERA_CONNECT, copyConnect

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
    
    camera = copyConnect(CAMERA_CONNECT)


class EoStaticPlotTaskConfig(pipeBase.PipelineTaskConfig,
                             pipelineConnections=EoStaticPlotTaskConnections):

    dirName = pexConfig.Field("Directory to store plots", str, ".")
    baseName = pexConfig.Field("Basename for plots", str, ".")


class EoStaticPlotTask(pipeBase.PipelineTask):
    """Generic task to generate static plots from `lsst.eotask_gen3.EoCalib`
    data structures.

    The various data structures each know their associated plotting functions

    This Task just invokes all of those plotting function.

    Note that the plotting functions can be invoked at three different
    granulaties

    1. per-CCD
    2. per-RAFT
    3. for the entire cameram

    The `EoPlotMethod` decorator provides a way to associate plotting
    functions to each level.

    This task will then look over the plotting functions at the correct level
    and provide them with the relevant data
    """

    ConfigClass = EoStaticPlotTaskConfig
    _DefaultName = "eoStaticPlot"

    @staticmethod
    def buildCameraDict(inputData, inputRefs, butler=None):
        """ Construct and return a nested dictionary of dataRefs keyed by
        raft and slot

        Parameters
        ----------
        inputData : `list` [`lsst.eotask_gen3.EoCalib`]
            The input data objects
        inputRefs : `list` [`lsst.daf.butler.DatasetRef`]
            References to the input data objects
        butler : `lsst.daf.butler.Butler` or `None`
            Butler used to look up detector dimension records, if needed

        Returns
        -------
        refObj : `lsst.eotask_gen3.EoCalib`
            The first data object found, used to access the correct
            class interface
        cameraDict : `OrderdedDict` [`str`,
                     `OrderdedDict` [`str`, `lsst.eotask_gen3.EoCalib`] ]
            The sorted data
        """
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
        """ Run Quantum method

        This sorts the inputRefs into a nested dictionary and
        passed that to the run method
        """
        inputs = butlerQC.get(inputRefs)
        refObj, cameraDict = self.buildCameraDict(inputs['inputData'], inputRefs.inputData)
        outputs = self.run(refObj=refObj, cameraDict=cameraDict, cameraObj=inputs['camera'],
                           baseName=self.config.baseName, dirName=self.config.dirName)
        butlerQC.put(outputs, outputRefs)

    def run(self, refObj, cameraDict, cameraObj, baseName, dirName):
        """ Run method

        This invokes
        1. `makeCameraFigures` with all the camera data
        2. `makeRaftFigures` for each raft with all the raft's data
        3. `makeFigures` for each CCD with the CCD's data

        And then calls `writeFigures` in each case to write the output figures

        Parameters
        ----------
        refObj : `lsst.eotask_gen3.EoCalib`
            Reference object, used to get the correct class to
            invoke plotting methods
        cameraDict : `OrderdedDict` [`str`,
                     `OrderdedDict` [`str`, `lsst.eotask_gen3.EoCalib`] ]
            Sorted data
        cameraObj : `lsst.afw.cameraGeom.Camera`
            Camera object, used for making per-amplifier plots
            of the full focal plane
        baseName : `str`
            Base name used to construct output file names
        dirName : `str`
            Path to top-level directory to write figures to
        """
        cameraFigs = refObj.makeCameraFigures("%s_camera" % baseName, cameraDict, cameraObj)
        cameraDir = os.path.join(dirName, 'camera')
        try:
            os.makedirs(cameraDir)
        except Exception:
            pass
        refObj.writeFigures(cameraDir, cameraFigs)

        for raftName, raftData in cameraDict.items():
            raftDir = os.path.join(dirName, 'camera', raftName)
            try:
                os.makedirs(raftDir)
            except Exception:
                pass
            raftFigs = refObj.makeRaftFigures("%s_%s" % (baseName, raftName), raftData)
            refObj.writeFigures(raftDir, raftFigs)

            for slotName, slotData in raftData.items():
                slotDir = os.path.join(dirName, 'camera', raftName, slotName)
                try:
                    os.makedirs(slotDir)
                except Exception:
                    pass
                slotFigs = refObj.makeFigures("%s_%s_%s" % (baseName, raftName, slotName), slotData)
                refObj.writeFigures(slotDir, slotFigs)
        return pipeBase.Struct()
