# from lsst.ip.isr import IsrCalib

from .eoCalibTable import EoCalibField, EoCalibTableSchema, EoCalibTable, EoCalibTableHandle
from .eoCalib import EoCalibSchema, EoCalib, RegisterEoCalibSchema

__all__ = ["EoDefectAmpRunData",
           "EoDefectData"]


class EoDefectAmpRunDataSchemaV0(EoCalibTableSchema):

    TABLELENGTH = "nAmp"

    nBrightPixel = EoCalibField(name="NUM_BRIGHT_PIXELS", dtype=int)
    nBrightColumn = EoCalibField(name="NUM_BRIGHT_COLUMNS", dtype=int)
    nDarkPixel = EoCalibField(name="NUM_DARK_PIXELS", dtype=int)
    nDarkColumn = EoCalibField(name="NUM_DARK_COLUMNS", dtype=int)
    nTraps = EoCalibField(name="NUM_TRAPS", dtype=int)


class EoDefectAmpRunData(EoCalibTable):

    SCHEMA_CLASS = EoDefectAmpRunDataSchemaV0

    def __init__(self, data=None, **kwargs):
        super(EoDefectAmpRunData, self).__init__(data=data, **kwargs)
        self.nBrightPixel = self.table[self.SCHEMA_CLASS.nBrightPixel.name]
        self.nBrightColumn = self.table[self.SCHEMA_CLASS.nBrightColumn.name]
        self.nDarkPixel = self.table[self.SCHEMA_CLASS.nDarkPixel.name]
        self.nDarkColumn = self.table[self.SCHEMA_CLASS.nDarkColumn.name]
        self.nTraps = self.table[self.SCHEMA_CLASS.nTraps.name]


class EoDefectDataSchemaV0(EoCalibSchema):

    amps = EoCalibTableHandle(tableName="amps",
                              tableClass=EoDefectAmpRunData)


class EoDefectData(EoCalib):

    SCHEMA_CLASS = EoDefectDataSchemaV0

    _OBSTYPE = 'bias'
    _SCHEMA = SCHEMA_CLASS.fullName()
    _VERSION = SCHEMA_CLASS.version()

    def __init__(self, **kwargs):
        super(EoDefectData, self).__init__(**kwargs)
        self.amps = self['amps']


RegisterEoCalibSchema(EoDefectData)

AMPS = ["%02i" % i for i in range(16)]
EoDefectData.testData = dict(testCtor=dict(nAmp=len(AMPS)))
