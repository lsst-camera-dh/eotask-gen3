""" An example to perform a slightly less trival analysis """

import lsst.afw.math as afwMath

import lsst.pex.config as pexConfig
import lsst.pipe.base as pipeBase
import lsst.pipe.base.connectionTypes as cT
from lsst.ip.isr import IsrTask


class EoIsrExampleTaskConnections(pipeBase.PipelineTaskConnections,
                                   dimensions=("instrument", "detector")):
    """ As with EoSimpleExampleTaskConnections 
    this class defines the Task connections, i.e.,
    the input and output to the task, as well as 
    how to find them and how to iterate.
    
    Note a few changes:

    1.  This class has dimensions=("instrument", "detector") 
    This means the task will run once per CCD for all the exposures we feed it.
    
    2.  This class defines some PrerequisiteInputs to use calibrations.
    These calibrations will be used to do some very minimal Instrument
    Signature Removal (ISR).  Specifically bias subtraction and defect masking.
    
    3.  The input has changes, now it is inputExps, which take raw
    data instead of calibrated images.  That is b/c we will be doing 
    the ISR ourselves.
    The multiple=True field means many exposures will be passed to 
    the run in call to run().  The deferLoad=True field means that rather
    than passing reading in the exposures and passing them to run(), 
    the framework will pass in an object that can read an Exposure when
    it's get() method is called.  

    4.  The output method has dimensions=("instrument", "detector"),
    this means only ony output object will be stored. 
    In this case is is a dictionary containing the name of the statistic
    being computed which point to a list of values.
    """

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
        name="eoIsrExampleOutput",
        doc="Example Output",
        storageClass="StructuredDataDict",
        dimensions=("instrument", "detector"),
    )


class EoIsrExampleTaskConfig(pipeBase.PipelineTaskConfig,
                              pipelineConnections=EoIsrExampleTaskConnections):
    """ This class defines the Task configuration.

    In this case we have a new parameter, `isr`, which
    allows use to create and configure a sub-task of type
    IsrTask.
    """

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
        """ This method lets us set all the default values of the connections
        and the sub-tasks 
        
        In our case we 

        """
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


class EoIsrExampleTask(pipeBase.PipelineTask):
    """ This is the task itself.

    In this case the task run() method takes a series of raw images
    uses the IsrTask sub-task to do minimal Isr, and then computes
    a statistic using all the pixel in the each image

    See `EoSimpleExampleTask` for a description
    of the next two lines
    """ 

    ConfigClass = EoIsrExampleTaskConfig
    _DefaultName = "eoIsrExample"

    def __init__(self, **kwargs):
        """ This is the Task initialization method
        
        In this case we need to do two things.
        
        1.  Make sure that the parent class initialization 
        is invoked by calling `super().__init__`

        2.  Construct the IsrTask subtask
        """
        super().__init__(**kwargs)
        self.makeSubtask("isr")


    def run(self, inputExps, bias, defects):
        """ This is the run method.  It does the work.
        
        Again, the arguments should _exactly_ match the Input type
        connections defined in the connection class.        
        This method should return a `pipeBase.Struct` object
        that is constructed to _exactly_ match the Output type
        connections defined in the connection class.

        In this case we are writing a list of values
        to the output.
        """        

        output = {self.config.stat:[]}
        stats = afwMath.StatisticsControl()
        statType = afwMath.stringToStatisticsProperty(self.config.stat)
        for inputExp in inputExps:
            # Here we read the raw image and pass it to the sub-task
            # which does the ISR
            # We also have to pass in the calibration objects
            calibExp = self.isr.run(inputExp.get(), bias=bias, defects=defects).exposure
            output[self.config.stat].append(afwMath.makeStatistics(calibExp.image, statType, stats).getValue())

        return pipeBase.Struct(output=output)
