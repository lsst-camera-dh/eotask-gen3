# from lsst.ip.isr import IsrCalib

from .eoCalibTable import EoCalibField, EoCalibTableSchema, EoCalibTable, EoCalibTableHandle
from .eoCalib import EoCalibSchema, EoCalib, RegisterEoCalibSchema
from .eoPlotUtils import EoPlotMethod, nullFigure

__all__ = ["EoReadNoiseAmpExpData",
           "EoReadNoiseAmpRunData",
           "EoReadNoiseData"]


class EoReadNoiseAmpExpDataSchemaV0(EoCalibTableSchema):
    """Schema definitions for output data for per-amp, per-exposure tables
    for EoReadNoiseTask.

    This is just the total noise measured for this amp for this exposure
    """

    TABLELENGTH = "nExposure"

    totalNoise = EoCalibField(name="TOTAL_NOISE", dtype=float, unit='electron', shape=["nSample"])


class EoReadNoiseAmpExpData(EoCalibTable):
    """Container class and interface for per-amp, per-exposure-pair tables
    for EoReadNoiseTask."""

    SCHEMA_CLASS = EoReadNoiseAmpExpDataSchemaV0

    def __init__(self, data=None, **kwargs):
        """C'tor, arguments are passed to base class.

        Class specialization just associates class properties with columns
        """
        super(EoReadNoiseAmpExpData, self).__init__(data=data, **kwargs)
        self.totalNoise = self.table[self.SCHEMA_CLASS.totalNoise.name]


class EoReadNoiseAmpRunDataSchemaV0(EoCalibTableSchema):
    """Schema definitions for output data for per-amp, per-run table
    for EoReadNoiseTask.

    The total noise is just the median noise measured for this amp for
    the exposures in this run.
    """

    TABLELENGTH = "nAmp"

    readNoise = EoCalibField(name="READ_NOISE", dtype=float, unit='electron')
    totalNoise = EoCalibField(name="TOTAL_NOISE", dtype=float, unit='electron')
    systemNoise = EoCalibField(name="SYSTEM_NOISE", dtype=float, unit='electron')


class EoReadNoiseAmpRunData(EoCalibTable):
    """Container class and interface for per-amp, per-run tables
    for EoReadNoiseTask."""

    SCHEMA_CLASS = EoReadNoiseAmpRunDataSchemaV0

    def __init__(self, data=None, **kwargs):
        """C'tor, arguments are passed to base class.

        Class specialization just associates class properties with columns
        """
        super(EoReadNoiseAmpRunData, self).__init__(data=data, **kwargs)
        self.readNoise = self.table[self.SCHEMA_CLASS.readNoise.name]
        self.totalNoise = self.table[self.SCHEMA_CLASS.totalNoise.name]
        self.systemNoise = self.table[self.SCHEMA_CLASS.systemNoise.name]


class EoReadNoiseDataSchemaV0(EoCalibSchema):
    """Schema definitions for output data for EoReadNoiseTask

    This defines correct versions of the sub-tables"""

    ampExp = EoCalibTableHandle(tableName="ampExp_{key}",
                                tableClass=EoReadNoiseAmpExpData,
                                multiKey="amps")

    amps = EoCalibTableHandle(tableName="amps",
                              tableClass=EoReadNoiseAmpRunData)


class EoReadNoiseData(EoCalib):
    """Container class and interface for EoReadNoiseTask outputs."""

    SCHEMA_CLASS = EoReadNoiseDataSchemaV0

    _OBSTYPE = 'bias'
    _SCHEMA = SCHEMA_CLASS.fullName()
    _VERSION = SCHEMA_CLASS.version()

    def __init__(self, **kwargs):
        """C'tor, arguments are passed to base class.

        Class specialization just associates instance properties with
        sub-tables
        """
        super(EoReadNoiseData, self).__init__(**kwargs)
        self.ampExp = self['ampExp']
        self.amps = self['amps']


@EoPlotMethod(EoReadNoiseData, "noise", "slot", "Read Noise", "Read noise")
def plotReadNoise(obj):
    return nullFigure()


@EoPlotMethod(EoReadNoiseData, "noise_mosaic", "camera", "mosaic", "Read noise")
def plotReadNoiseMosaic(obj, cameraObj):
    return nullFigure()


@EoPlotMethod(EoReadNoiseData, "noise_hist", "camera", "hist", "Read noise")
def plotReadNoiseHist(obj, cameraObj):
    return nullFigure()


RegisterEoCalibSchema(EoReadNoiseData)

AMPS = ["%02i" % i for i in range(16)]
NEXPOSURE = 10
NSAMPLES = 100
EoReadNoiseData.testData = dict(testCtor=dict(amps=AMPS, nAmp=len(AMPS),
                                              nExposure=NEXPOSURE, nSample=NSAMPLES))
