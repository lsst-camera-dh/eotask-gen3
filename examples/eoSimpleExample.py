import lsst.afw.math as afwMath

import lsst.pex.config as pexConfig
import lsst.pipe.base as pipeBase
import lsst.pipe.base.connectionTypes as cT

__all__ = ['EoExampleTaskConfig', 'EoExampleTask']

class EoExampleTaskConnections(pipeBase.PipelineTaskConnections,
                               dimensions=("instrument", "exposure", "detector")):

    inputCalExp = cT.Input(
        name="calExpBias",
        doc="Input Frames.",
        storageClass="Exposure",
        dimensions=("instrument", "exposure", "detector"),
    )

    output = cT.Output(
        name="calibOutput",
        doc="Example Output",
        storageClass="StructuredDataDict",
        dimensions=("instrument", "exposure", "detector"),
    )


class EoExampleTaskConfig(pipeBase.PipelineTaskConfig, pipelineConnections=EoExampleTaskConnections):

    stat = pexConfig.Field(
        dtype=str,
        default='MEAN',
        doc="Statistic name to extract (from lsst.afw.math)",
    )


class EoExampleTask(pipeBase.PipelineTask):

    ConfigClass = EoExampleTaskConfig
    _DefaultName = "eoExample"

    def run(self, inputCalExp):

        stats = afwMath.StatisticsControl()
        statType = afwMath.stringToStatisticsProperty(self.config.stat)
        output = {self.config.stat: afwMath.makeStatistics(inputCalExp.image, statType, stats).getValue()}
        return pipeBase.Struct(output=output)
