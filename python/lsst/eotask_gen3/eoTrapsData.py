# from lsst.ip.isr import IsrCalib

from .eoCalibTable import EoCalibField, EoCalibTableSchema, EoCalibTable, EoCalibTableHandle
from .eoCalib import EoCalibSchema, EoCalib, RegisterEoCalibSchema

__all__ = ["EoTrapsAmpRunData",
           "EoTrapsData"]


class EoTrapsAmpRunDataSchemaV0(EoCalibTableSchema):

    TABLELENGTH = "nAmp"

    nTraps = EoCalibField(name="NUM_TRAPS", dtype=int)


class EoTrapsAmpRunData(EoCalibTable):

    SCHEMA_CLASS = EoTrapsAmpRunDataSchemaV0

    def __init__(self, data=None, **kwargs):
        super(EoTrapsAmpRunData, self).__init__(data=data, **kwargs)
        self.nTraps = self.table[self.SCHEMA_CLASS.nTraps.name]


class EoTrapsDataSchemaV0(EoCalibSchema):

    amps = EoCalibTableHandle(tableName="amps",
                              tableClass=EoTrapsAmpRunData)


class EoTrapsData(EoCalib):

    SCHEMA_CLASS = EoTrapsDataSchemaV0

    _OBSTYPE = 'bias'
    _SCHEMA = SCHEMA_CLASS.fullName()
    _VERSION = SCHEMA_CLASS.version()

    def __init__(self, **kwargs):
        super(EoTrapsData, self).__init__(**kwargs)
        self.amps = self['amps']


RegisterEoCalibSchema(EoTrapsData)

AMPS = ["%02i" % i for i in range(16)]
EoTrapsData.testData = dict(testCtor=dict(nAmp=len(AMPS)))
