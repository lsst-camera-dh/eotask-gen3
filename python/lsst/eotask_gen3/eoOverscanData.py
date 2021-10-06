# from lsst.ip.isr import IsrCalib

from .eoCalibTable import EoCalibField, EoCalibTableSchema, EoCalibTable, EoCalibTableHandle
from .eoCalib import EoCalibSchema, EoCalib, RegisterEoCalibSchema
from .eoPlotUtils import EoPlotMethod, nullFigure

__all__ = ["EoOverscanAmpExpData",
           "EoOverscanData"]


class EoOverscanAmpExpDataSchemaV0(EoCalibTableSchema):
    """Schema definitions for output data for per-amp, per-exposure tables
    for EoOverscanTask.

    These are summary statistics about the signal in the overscan regions
    """

    TABLELENGTH = "nExposure"

    columnMean = EoCalibField(name='COLUMN_MEAN', dtype=float, unit='electron', shape=['nCol'])
    columnVariance = EoCalibField(name='COLUMN_VARIANCE', dtype=float, unit='electron', shape=['nCol'])
    rowMean = EoCalibField(name='ROW_MEAN', dtype=float, unit='electron', shape=['nRow'])
    rowVariance = EoCalibField(name='ROW_VARIANCE', dtype=float, unit='electron', shape=['nRow'])
    flatFieldSignal = EoCalibField(name='FLATFIELD_SIGNAL', dtype=float, unit='electron')
    serialOverscanNoise = EoCalibField(name='SERIAL_OVERSCAN_NOISE', dtype=float, unit='electron')
    parallenOverscanNoise = EoCalibField(name='PARALLEL_OVERSCAN_NOISE', dtype=float, unit='electron')


class EoOverscanAmpExpData(EoCalibTable):
    """Container class and interface for per-amp, per-exposure tables
    for EoOverscanTask."""

    SCHEMA_CLASS = EoOverscanAmpExpDataSchemaV0

    def __init__(self, data=None, **kwargs):
        """C'tor, arguments are passed to base class.

        Class specialization just associates class properties with columns
        """
        super(EoOverscanAmpExpData, self).__init__(data=data, **kwargs)
        self.columnMean = self.table[self.SCHEMA_CLASS.columnMean.name]
        self.columnVariance = self.table[self.SCHEMA_CLASS.columnVariance.name]
        self.rowMean = self.table[self.SCHEMA_CLASS.rowMean.name]
        self.rowVariance = self.table[self.SCHEMA_CLASS.rowVariance.name]
        self.serialOverscanNoise = self.table[self.SCHEMA_CLASS.serialOverscanNoise.name]
        self.parallenOverscanNoise = self.table[self.SCHEMA_CLASS.parallenOverscanNoise.name]
        self.flatFieldSignal = self.table[self.SCHEMA_CLASS.flatFieldSignal.name]


class EoOverscanDataSchemaV0(EoCalibSchema):
    """Schema definitions for output data for EoOverscanTask

    This defines correct versions of the sub-tables"""

    ampExp = EoCalibTableHandle(tableName="ampExp_{key}",
                                tableClass=EoOverscanAmpExpData,
                                multiKey="amps")


class EoOverscanData(EoCalib):
    """Container class and interface for EoOverscanTask outputs."""

    SCHEMA_CLASS = EoOverscanDataSchemaV0

    _OBSTYPE = 'bias'
    _SCHEMA = SCHEMA_CLASS.fullName()
    _VERSION = SCHEMA_CLASS.version()

    def __init__(self, **kwargs):
        """C'tor, arguments are passed to base class.

        Class specialization just associates instance properties with
        sub-tables
        """
        super(EoOverscanData, self).__init__(**kwargs)
        self.ampExp = self['ampExp']


@EoPlotMethod(EoOverscanData, "serial_eper_low", "slot", "overscan", "Serial overscan EPER low flux")
def plotSerialEperHigh(obj):
    return nullFigure()


@EoPlotMethod(EoOverscanData, "serial_eper_high", "slot", "overscan", "Serial overscan EPER high flux")
def plotSerialEperLow(obj):
    return nullFigure()


@EoPlotMethod(EoOverscanData, "serial_cti", "slot", "overscan", "Serial overscan CTI Estimate")
def plotSerialCTI(obj):
    return nullFigure()


@EoPlotMethod(EoOverscanData, "serial_overscan_signal", "slot", "overscan",
              "Serial overscan EPER v. flux")
def plotSerialOverscanSignal(obj):
    return nullFigure()


@EoPlotMethod(EoOverscanData, "serial_overscan_sum", "slot", "overscan",
              "Serial overscan summed signal (pixels 5-25)")
def plotSerialOverscanSum(obj):
    return nullFigure()


@EoPlotMethod(EoOverscanData, "parallel_eper_low", "slot", "overscan",
              "Parallel overscan EPER low flux")
def plotparallelEperHigh(obj):
    return nullFigure()


@EoPlotMethod(EoOverscanData, "parallel_eper_high", "slot", "overscan",
              "Parallel overscan EPER high flux")
def plotparallelEperLow(obj):
    return nullFigure()


@EoPlotMethod(EoOverscanData, "parallel_cti", "slot", "overscan",
              "Parallel overscan CTI Estimate")
def plotParallelCTI(obj):
    return nullFigure()


@EoPlotMethod(EoOverscanData, "parallel_overscan_signal", "slot", "overscan",
              "Parallel overscan EPER v. flux")
def plotParallelOverscanSignal(obj):
    return nullFigure()


@EoPlotMethod(EoOverscanData, "parallel_overscan_sum", "slot", "overscan",
              "Parallel overscan summed signal (pixels 5-25)")
def plotParallelOverscanSum(obj):
    return nullFigure()


RegisterEoCalibSchema(EoOverscanData)

AMPS = ["%02i" % i for i in range(16)]
NEXPOSURE = 10
NCOL = 55
NROW = 47
EoOverscanData.testData = dict(testCtor=dict(amps=AMPS, nExposure=NEXPOSURE, nCol=NCOL, nRow=NROW))
