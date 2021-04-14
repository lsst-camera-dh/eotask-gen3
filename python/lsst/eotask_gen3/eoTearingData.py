# from lsst.ip.isr import IsrCalib

from .eoCalibTable import EoCalibField, EoCalibTableSchema, EoCalibTable, EoCalibTableHandle
from .eoCalib import EoCalibSchema, EoCalib, RegisterEoCalibSchema

__all__ = ["EoTearingAmpRunData",
           "EoTearingData"]


class EoTearingAmpRunDataSchemaV0(EoCalibTableSchema):

    TABLELENGTH = 'nAmp'

    nDetection = EoCalibField(name="NDETECT", dtype=int)


class EoTearingAmpRunData(EoCalibTable):

    SCHEMA_CLASS = EoTearingAmpRunDataSchemaV0

    def __init__(self, data=None, **kwargs):
        super(EoTearingAmpRunData, self).__init__(data=data, **kwargs)
        self.ndetection = self.table[self.SCHEMA_CLASS.nDetection.name]


class EoTearingDataSchemaV0(EoCalibSchema):

    amps = EoCalibTableHandle(tableName="amps",
                              tableClass=EoTearingAmpRunData)


class EoTearingData(EoCalib):

    SCHEMA_CLASS = EoTearingDataSchemaV0

    _OBSTYPE = 'flat'
    _SCHEMA = SCHEMA_CLASS.fullName()
    _VERSION = SCHEMA_CLASS.VERSION

    def __init__(self, **kwargs):
        super(EoTearingData, self).__init__(**kwargs)
        self.amps = self['amps']


RegisterEoCalibSchema(EoTearingData)

AMPS = ["%02i" % i for i in range(16)]
EoTearingData.testData = dict(testCtor=dict(nAmp=len(AMPS)))
