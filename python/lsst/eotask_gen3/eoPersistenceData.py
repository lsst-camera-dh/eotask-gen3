# from lsst.ip.isr import IsrCalib

from eoCalibTable import EoCalibField, EoCalibTableSchema, EoCalibTable, RegisterEoCalibTableSchema
from eoCalib import EoCalibTableHandle, EoCalibSchema, EoCalib, RegisterEoCalibSchema

__all__ = ["EoPersistenceAmpExpDataSchemaV0", "EoPersistenceAmpExpData",
           "EoPersistenceDataSchemaV0", "EoPersistenceData"]


class EoPersistenceAmpExpDataSchemaV0(EoCalibTableSchema):

    VERSION = 0
    TABLELENGTH = "nExposure"

    mean = EoCalibField(name="MEAN", dtype=float, unit='ADU')
    stdev = EoCalibField(name="STDEV", dtype=float, unit='ADU')


class EoPersistenceAmpExpData(EoCalibTable):

    SCHEMA_CLASS = EoPersistenceAmpExpDataSchemaV0

    def __init__(self, data=None, **kwargs):
        super(EoPersistenceAmpExpData, self).__init__(data=data, **kwargs)
        self.mean = self.table[self.SCHEMA_CLASS.mean.name]
        self.stdev = self.table[self.SCHEMA_CLASS.stdev.name]


class EoPersistenceDataSchemaV0(EoCalibSchema):

    ampExposure = EoCalibTableHandle(tableName="ampExp_{key}",
                                     tableClass=EoPersistenceAmpExpData,
                                     multiKey="amps")


class EoPersistenceData(EoCalib):

    SCHEMA_CLASS = EoPersistenceDataSchemaV0

    _OBSTYPE = 'bias'
    _SCHEMA = SCHEMA_CLASS.fullName()
    _VERSION = SCHEMA_CLASS.VERSION

    def __init__(self, **kwargs):
        super(EoPersistenceData, self).__init__(**kwargs)
        self.ampExposure = self._tables['ampExposure']


RegisterEoCalibTableSchema(EoPersistenceAmpExpData)
RegisterEoCalibSchema(EoPersistenceData)


AMPS = ["%02i" % i for i in range(16)]
NEXPOSURE = 10

testData = EoPersistenceData(amps=AMPS, nExposure=NEXPOSURE)
