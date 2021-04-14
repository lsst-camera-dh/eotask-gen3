# from lsst.ip.isr import IsrCalib

from .eoCalibTable import EoCalibField, EoCalibTableSchema, EoCalibTable, EoCalibTableHandle
from .eoCalib import EoCalibSchema, EoCalib, RegisterEoCalibSchema

__all__ = ["EoPersistenceAmpExpData",
           "EoPersistenceData"]


class EoPersistenceAmpExpDataSchemaV0(EoCalibTableSchema):

    TABLELENGTH = "nExposure"

    mean = EoCalibField(name="MEAN", dtype=float, unit='adu')
    stdev = EoCalibField(name="STDEV", dtype=float, unit='adu')


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
    _VERSION = SCHEMA_CLASS.version()

    def __init__(self, **kwargs):
        super(EoPersistenceData, self).__init__(**kwargs)
        self.ampExposure = self['ampExposure']


RegisterEoCalibSchema(EoPersistenceData)


AMPS = ["%02i" % i for i in range(16)]
NEXPOSURE = 10
EoPersistenceData.testData = dict(testCtor=dict(amps=AMPS, nExposure=NEXPOSURE))
