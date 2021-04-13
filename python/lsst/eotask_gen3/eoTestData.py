# from lsst.ip.isr import IsrCalib

import numpy as np

from .eoCalibTable import EoCalibField, EoCalibTableSchema, EoCalibTable, RegisterEoCalibTableSchema
from .eoCalib import EoCalibTableHandle, EoCalibSchema, EoCalib, RegisterEoCalibSchema

__all__ = ["EoTestAmpExpData",
           "EoTestAmpRunData",
           "EoTestData"]


class EoTestAmpExpDataSchemaV0(EoCalibTableSchema):

    NAME, VERSION = "EoTestAmpExpData", 0
    TABLELENGTH = "nExposure"

    varExp1 = EoCalibField(name="VAR1", dtype=float)


class EoTestAmpExpDataSchemaV1(EoTestAmpExpDataSchemaV0):

    NAME, VERSION = "EoTestAmpExpData", 1
    TABLELENGTH = "nExposure"

    varExp2 = EoCalibField(name="VAR2", dtype=float, shape=["nSample"])


class EoTestAmpExpData(EoCalibTable):

    SCHEMA_CLASS = EoTestAmpExpDataSchemaV1
    PREVIOUS_SCHEMAS = [EoTestAmpExpDataSchemaV0]

    def __init__(self, data=None, **kwargs):
        super(EoTestAmpExpData, self).__init__(data=data, **kwargs)
        self.varExp1 = self.table[self.SCHEMA_CLASS.varExp1.name]
        try:
            self.varExp2 = self.table[self.SCHEMA_CLASS.varExp2.name]
        except KeyError:
            self.varExp2 = np.nan


class EoTestAmpRunDataSchemaV0(EoCalibTableSchema):

    VERSION = 0
    TABLELENGTH = "nAmp"

    varAmp1 = EoCalibField(name="VARAMP1", dtype=float)


class EoTestAmpRunData(EoCalibTable):

    SCHEMA_CLASS = EoTestAmpRunDataSchemaV0

    def __init__(self, data=None, **kwargs):
        super(EoTestAmpRunData, self).__init__(data=data, **kwargs)
        self.varAmp1 = self.table[self.SCHEMA_CLASS.varAmp1.name]


class EoTestDataSchemaV0(EoCalibSchema):

    NAME, VERSION = "EoTestData", 0

    amps = EoCalibTableHandle(tableName="amps",
                              tableClass=EoTestAmpRunData)


class EoTestDataSchemaV1(EoTestDataSchemaV0):

    NAME, VERSION = "EoTestData", 1

    ampExposure = EoCalibTableHandle(tableName="ampExp_{key}",
                                     tableClass=EoTestAmpExpData,
                                     multiKey="amps")


class EoTestData(EoCalib):

    SCHEMA_CLASS = EoTestDataSchemaV1
    PREVIOUS_SCHEMAS = [EoTestDataSchemaV0]

    _OBSTYPE = 'bias'
    _SCHEMA = SCHEMA_CLASS.fullName()
    _VERSION = SCHEMA_CLASS.VERSION

    def __init__(self, **kwargs):
        super(EoTestData, self).__init__(**kwargs)
        try:
            self.ampExposure = self._tables['ampExposure']
        except KeyError:
            self.ampExposure = None
        self.amps = self._tables['amps']


RegisterEoCalibTableSchema(EoTestAmpExpData)
RegisterEoCalibTableSchema(EoTestAmpRunData)
RegisterEoCalibSchema(EoTestData)

AMPS = ["%02i" % i for i in range(16)]
NEXPOSURE = 10
NSAMPLE = 10

testData = EoTestData(amps=AMPS, nAmp=len(AMPS), nExposure=NEXPOSURE, nSample=NSAMPLE)
