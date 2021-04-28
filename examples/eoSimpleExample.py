""" An example task to perform a trivial analysis """

import lsst.afw.math as afwMath

import lsst.pex.config as pexConfig
import lsst.pipe.base as pipeBase
import lsst.pipe.base.connectionTypes as cT

__all__ = ['EoSimpleExampleTaskConfig', 'EoSimpleExampleTask']


class EoSimpleExampleTaskConnections(pipeBase.PipelineTaskConnections,
                                     dimensions=("instrument", "exposure", "detector")):
    """ This class defines the Task connections, i.e.,
    the input and output to the task, as well as 
    how to find them and how to iterate.

    The dimensions=("instrument", "exposure", "detector") line above
    means that the task will run once per exposure, per ccd (aka detector)
    
    The inputCalExp connection defines the input data.  In this
    case calibrated exposures, i.e., overscan and bias-subtracted images 
    written by a particular version of IsrTask.
    (using examples/config/isrBias.yaml to configure the IsrTask)
    
    The output connection defines the output data.  In this case a yaml
    file with a dictionary.

    See daf_butler/python/lsst/daf/butler/configs/storageClasses.yaml for 
    available storage types and the corresponding python data types.

    In this example both the input and output have the same dimensions
    as the task itself, so the task will be called with one input,
    and provide one output.
    """
    
    inputCalExp = cT.Input(
        name="calExpBias",
        doc="Input Frames.",
        storageClass="Exposure",
        dimensions=("instrument", "exposure", "detector"),
    )

    output = cT.Output(
        name="eoSimpleExampleOutput",
        doc="Example Output",
        storageClass="StructuredDataDict",
        dimensions=("instrument", "exposure", "detector"),
    )


class EoSimpleExampleTaskConfig(pipeBase.PipelineTaskConfig,
                                pipelineConnections=EoSimpleExampleTaskConnections):
    """ This class defines the Task configuration.

    In this case we have a single parameter, a string which 
    tells us which statistic to extract from the image.
    """
    
    stat = pexConfig.Field(
        dtype=str,
        default='MEAN',
        doc="Statistic name to extract (from lsst.afw.math)",
    )


class EoSimpleExampleTask(pipeBase.PipelineTask):
    """ This is the task itself.

    In this case the task run() method takes a calibrated image
    and computes a statistic using all the pixel in the image
    
    Which statistic is set by the self.config.stat parameter defined 
    in the config class above

    The next two variables are important.
    
    ConfigClass sets the name of the configuration class.

    _DefaultName sets the 'label' for this task, which will
    be used for a few things, in particular associating
    configuration metadata with a specific version of this
    task.  

    If you change the configuration paramters you will have
    to provide a new label. 

    Specifically, the butler will prevent you from writing data 
    using two different configurations of a task with the 
    same label into a single repository.
    """
    
    ConfigClass = EoSimpleExampleTaskConfig
    _DefaultName = "eoSimpleExample"

    def run(self, inputCalExp):
        """ This is the run method.  It does the work.
        
        For now the arguments should _exactly_ match the Input type
        connections defined in the connection class.
        
        This method should return a `pipeBase.Struct` object
        that is construct to _exactly_ match the Output type
        connections defined in the connection class.

        There are way to get fancy with both the input and output
        data, but this is a simple example.
        """        
        # This lets use control things like clipping & masking 
        stats = afwMath.StatisticsControl()
        # This interpets the configuration parameter & raises an error
        # if it was set to an invalid value
        statType = afwMath.stringToStatisticsProperty(self.config.stat)
        # The python type for StructuredDataDict is just a dict,
        # so we fill a dict
        output = {self.config.stat: afwMath.makeStatistics(inputCalExp.image, statType, stats).getValue()}
        # The output should _exactly_ match the connections
        return pipeBase.Struct(output=output)
