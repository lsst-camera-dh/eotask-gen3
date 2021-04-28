import lsst.afw.math as afwMath

import lsst.pex.config as pexConfig
import lsst.pipe.base as pipeBase
import lsst.pipe.base.connectionTypes as cT
from lsst.ip.isr import IsrTask


class EoFullExampleTaskConnections(pipeBase.PipelineTaskConnections,
                                   dimensions=("instrument", "detector")):

#    camera = cT.PrerequisiteInput(
#        name="camera",
#        storageClass="Camera",
#        doc="Access to camera geometry.",
#        dimensions=["instrument"],
#        isCalibration=True,
#    )

    bias = cT.PrerequisiteInput(
        name="bias",
        doc="Input bias calibration.",
        storageClass="ExposureF",
        dimensions=("instrument", "detector"),
        isCalibration=True,
    )

    defects = cT.PrerequisiteInput(
        name='defects',
        doc="Input defect tables.",
        storageClass="Defects",
        dimensions=("instrument", "detector"),
        isCalibration=True,
    )

    inputExps = cT.Input(
        name="raw",
        doc="Input Frames.",
        storageClass="Exposure",
        dimensions=("instrument", "exposure", "detector"),
        multiple=True,
        deferLoad=True,
    )

    output = cT.Output(
        name="exampleRunOutput",
        doc="Example Output",
        storageClass="StructuredDataDict",
        dimensions=("instrument", "detector"),
    )


class EoFullExampleTaskConfig(pipeBase.PipelineTaskConfig,
                              pipelineConnections=EoFullExampleTaskConnections):

    isr = pexConfig.ConfigurableField(
        target=IsrTask,
        doc="Used to run a reduced version of ISR approrpiate for EO analyses",
    )

    stat = pexConfig.Field(
        dtype=str,
        default='MEAN',
        doc="Statistic name to extract (from lsst.afw.math)",
    )

    def setDefaults(self):
        # pylint: disable=no-member
        self.isr.doBias = True
        self.isr.doVariance = True
        self.isr.doLinearize = False
        self.isr.doCrosstalk = False
        self.isr.doDefect = False
        self.isr.doNanMasking = True
        self.isr.doInterpolate = True
        self.isr.doBrighterFatter = False
        self.isr.doDark = False
        self.isr.doFlat = False
        self.isr.doApplyGains = False
        self.isr.doFringe = False


class EoFullExampleTask(pipeBase.PipelineTask):

    ConfigClass = EoFullExampleTaskConfig
    _DefaultName = "eoFullExample"

    def __init__(self, **kwargs):
        """ C'tor """
        super().__init__(**kwargs)
        self.makeSubtask("isr")


    def run(self, inputExps, bias, defects, **kwargs):
        
        output = {self.config.stat:[]}
        stats = afwMath.StatisticsControl()
        statType = afwMath.stringToStatisticsProperty(self.config.stat)
        for iExp, inputExp in enumerate(inputExps):
            calibExp = self.isr.run(inputExp.get(), bias=bias, defects=defects).exposure
            output[self.config.stat].append(afwMath.makeStatistics(calibExp.image, statType, stats).getValue())

        return pipeBase.Struct(output=output)
