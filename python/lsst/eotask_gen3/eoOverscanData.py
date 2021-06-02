# from lsst.ip.isr import IsrCalib

from .eoCalibTable import EoCalibField, EoCalibTableSchema, EoCalibTable, EoCalibTableHandle
from .eoCalib import EoCalibSchema, EoCalib, RegisterEoCalibSchema

__all__ = ["EoOverscanAmpExpData",
           "EoOverscanData"]


class EoOverscanAmpExpDataSchemaV0(EoCalibTableSchema):

    TABLELENGTH = "nExposure"

    columnMean = EoCalibField(name='COLUMN_MEAN', dtype=float, unit='electron', shape=['nCol'])
    columnVariance = EoCalibField(name='COLUMN_VARIANCE', dtype=float, unit='electron', shape=['nCol'])
    rowMean = EoCalibField(name='ROW_MEAN', dtype=float, unit='electron', shape=['nRow'])
    rowVariance = EoCalibField(name='ROW_VARIANCE', dtype=float, unit='electron', shape=['nRow'])
    flatFieldSignal = EoCalibField(name='FLATFIELD_SIGNAL', dtype=float, unit='electron')
    serialOverscanNoise = EoCalibField(name='SERIAL_OVERSCAN_NOISE', dtype=float, unit='electron')
    parallenOverscanNoise = EoCalibField(name='PARALLEL_OVERSCAN_NOISE', dtype=float, unit='electron')


class EoOverscanAmpExpData(EoCalibTable):

    SCHEMA_CLASS = EoOverscanAmpExpDataSchemaV0

    def __init__(self, data=None, **kwargs):
        super(EoOverscanAmpExpData, self).__init__(data=data, **kwargs)
        self.columnMean = self.table[self.SCHEMA_CLASS.columnMean.name]
        self.columnVariance = self.table[self.SCHEMA_CLASS.columnVariance.name]
        self.rowMean = self.table[self.SCHEMA_CLASS.rowMean.name]
        self.rowVariance = self.table[self.SCHEMA_CLASS.rowVariance.name]
        self.serialOverscanNoise = self.table[self.SCHEMA_CLASS.serialOverscanNoise.name]
        self.parallenOverscanNoise = self.table[self.SCHEMA_CLASS.parallenOverscanNoise.name]
        self.flatFieldSignal = self.table[self.SCHEMA_CLASS.flatFieldSignal.name]


class EoOverscanDataSchemaV0(EoCalibSchema):

    ampExp = EoCalibTableHandle(tableName="ampExp_{key}",
                                tableClass=EoOverscanAmpExpData,
                                multiKey="amps")


class EoOverscanData(EoCalib):

    SCHEMA_CLASS = EoOverscanDataSchemaV0

    _OBSTYPE = 'bias'
    _SCHEMA = SCHEMA_CLASS.fullName()
    _VERSION = SCHEMA_CLASS.version()

    def __init__(self, **kwargs):
        super(EoOverscanData, self).__init__(**kwargs)
        self.ampExp = self['ampExp']


RegisterEoCalibSchema(EoOverscanData)

AMPS = ["%02i" % i for i in range(16)]
NEXPOSURE = 10
NCOL = 55
NROW = 47
EoOverscanData.testData = dict(testCtor=dict(amps=AMPS, nExposure=NEXPOSURE, nCol=NCOL, nRow=NROW))
