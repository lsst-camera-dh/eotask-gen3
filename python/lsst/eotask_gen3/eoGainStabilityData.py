# from lsst.ip.isr import IsrCalib

from .eoCalibTable import EoCalibField, EoCalibTableSchema, EoCalibTable, EoCalibTableHandle
from .eoCalib import EoCalibSchema, EoCalib, RegisterEoCalibSchema
from .eoPlotUtils import EoPlotMethod, nullFigure

__all__ = ["EoGainStabilityAmpExpData",
           "EoGainStabilityDetExpData",
           "EoGainStabilityData"]


class EoGainStabilityAmpExpDataSchemaV0(EoCalibTableSchema):
    """Schema definitions for output data for per-amp, per-exposure tables
    for EoGainStabilityTask.

    These are summary statistics from the amplifier data.
    """

    TABLELENGTH = "nExposure"

    signal = EoCalibField(name="SIGNAL", dtype=float, unit='electron')


class EoGainStabilityAmpExpData(EoCalibTable):
    """Container class and interface for per-amp, per-exposure tables
    for EoGainStabilityTask."""

    SCHEMA_CLASS = EoGainStabilityAmpExpDataSchemaV0

    def __init__(self, data=None, **kwargs):
        """C'tor, arguments are passed to base class.

        This just associates class properties with columns
        """
        super(EoGainStabilityAmpExpData, self).__init__(data=data, **kwargs)
        self.signal = self.table[self.SCHEMA_CLASS.signal.name]


class EoGainStabilityDetExpDataSchemaV0(EoCalibTableSchema):
    """Schema definitions for output data for per-detector, per-exposure table
    for EoGainStabilityTask.

    These are copied from the EO-analysis-jobs code and in part
    are retained to allow for possible conversion of old data.

    The flux comes from te photodiode reading, and
    the other data are actually discernable from the dataId, but having
    them here makes it easier to make plots of trends.
    """

    TABLELENGTH = "nExposure"

    mjd = EoCalibField(name="MJD", dtype=float, unit='electron')
    seqnum = EoCalibField(name="SEQNUM", dtype=int)
    flux = EoCalibField(name="FLUX", dtype=float)


class EoGainStabilityDetExpData(EoCalibTable):
    """Container class and interface for per-ccd, per-exposure table
    for EoGainStabilityTask."""

    SCHEMA_CLASS = EoGainStabilityDetExpDataSchemaV0

    def __init__(self, data=None, **kwargs):
        """C'tor, arguments are passed to base class.

        This just associates class properties with columns
        """
        super(EoGainStabilityDetExpData, self).__init__(data=data, **kwargs)
        self.mjd = self.table[self.SCHEMA_CLASS.mjd.name]
        self.seqnum = self.table[self.SCHEMA_CLASS.seqnum.name]
        self.flux = self.table[self.SCHEMA_CLASS.flux.name]


class EoGainStabilityDataSchemaV0(EoCalibSchema):
    """Schema definitions for output data for for EoBiasStabilityTask

    This defines correct versions of the sub-tables"""

    ampExp = EoCalibTableHandle(tableName="ampExp_{key}",
                                tableClass=EoGainStabilityAmpExpData,
                                multiKey="amps")

    detExp = EoCalibTableHandle(tableName="detExp",
                                tableClass=EoGainStabilityDetExpData)


class EoGainStabilityData(EoCalib):
    """Container class and interface for EoGainStabilityTask outputs."""

    SCHEMA_CLASS = EoGainStabilityDataSchemaV0

    _OBSTYPE = 'flat'
    _SCHEMA = SCHEMA_CLASS.fullName()
    _VERSION = SCHEMA_CLASS.version()

    def __init__(self, **kwargs):
        """C'tor, arguments are passed to base class.

        Class specialization just associates instance properties with
        sub-tables
        """
        super(EoGainStabilityData, self).__init__(**kwargs)
        self.ampExp = self['ampExp']
        self.detExp = self['detExp']


@EoPlotMethod(EoGainStabilityData, "mosaic", "camera", "mosaic", "Flat Gain Stability")
def plotGainStability(cameraDataDict, cameraObj):
    return nullFigure()


RegisterEoCalibSchema(EoGainStabilityData)


AMPS = ["%02i" % i for i in range(16)]
NEXPOSURE = 10
EoGainStabilityData.testData = dict(testCtor=dict(amps=AMPS, nExposure=NEXPOSURE))
