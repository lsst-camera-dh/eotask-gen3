# from lsst.ip.isr import IsrCalib

from .eoCalibTable import EoCalibField, EoCalibTableSchema, EoCalibTable, EoCalibTableHandle
from .eoCalib import EoCalibSchema, EoCalib, RegisterEoCalibSchema
from .eoPlotUtils import EoPlotMethod, nullFigure

__all__ = ["EoDarkCurrentAmpRunData",
           "EoDarkCurrentData"]


class EoDarkCurrentAmpRunDataSchemaV0(EoCalibTableSchema):
    """Schema definitions for output data for per-amp, per-run tables
    for EoDarkCurrentTask.

    These are just the median and 95% quantile for the dark current
    """

    TABLELENGTH = "nAmp"

    darkCurrent95 = EoCalibField(name="DARK_CURRENT_95", dtype=float, unit='electron/s')
    darkCurrentMedian = EoCalibField(name="DARK_CURRENT_MEDIAN", dtype=float, unit='electron/s')


class EoDarkCurrentAmpRunData(EoCalibTable):
    """Container class and interface for per-amp, per-run tables
    for EoBrightPixelsTask."""

    SCHEMA_CLASS = EoDarkCurrentAmpRunDataSchemaV0

    def __init__(self, data=None, **kwargs):
        """C'tor, arguments are passed to base class.

        This just associates class properties with columns
        """
        super(EoDarkCurrentAmpRunData, self).__init__(data=data, **kwargs)
        self.darkCurrent95 = self.table[self.SCHEMA_CLASS.darkCurrent95.name]
        self.darkCurrentMedian = self.table[self.SCHEMA_CLASS.darkCurrentMedian.name]


class EoDarkCurrentDataSchemaV0(EoCalibSchema):
    """Schema definitions for output data for EoDarkCurrentTask

    This defines correct versions of the sub-tables"""

    amps = EoCalibTableHandle(tableName="amps",
                              tableClass=EoDarkCurrentAmpRunData)


class EoDarkCurrentData(EoCalib):
    """Container class and interface for EoDarkCurrentTask outputs."""

    SCHEMA_CLASS = EoDarkCurrentDataSchemaV0

    _OBSTYPE = 'dark'
    _SCHEMA = SCHEMA_CLASS.fullName()
    _VERSION = SCHEMA_CLASS.version()

    def __init__(self, **kwargs):
        """C'tor, arguments are passed to base class.

        Class specialization just associates instance properties with
        sub-tables
        """
        super(EoDarkCurrentData, self).__init__(**kwargs)
        self.amps = self['amps']


@EoPlotMethod(EoDarkCurrentData, "noise", "slot", "Dark Current", "Dark Current")
def plotSlotNoise(obj):
    return nullFigure()


@EoPlotMethod(EoDarkCurrentData, "noise", "slot", "Dark Current", "Dark Current")
def plotRaftNoise(raftDataDict):
    return nullFigure()


@EoPlotMethod(EoDarkCurrentData, "95CL", "slot", "Dark Current", "Dark Current 95% Containment")
def plotCamera95CL(cameraDataDict):
    return nullFigure()


RegisterEoCalibSchema(EoDarkCurrentData)


AMPS = ["%02i" % i for i in range(16)]
EoDarkCurrentData.testData = dict(testCtor=dict(amps=AMPS, nAmp=len(AMPS)))
