# from lsst.ip.isr import IsrCalib

import numpy as np

from .eoCalibTable import EoCalibField, EoCalibTableSchema, EoCalibTable, EoCalibTableHandle
from .eoCalib import EoCalibSchema, EoCalib, RegisterEoCalibSchema

__all__ = ["EoTestAmpExpData",
           "EoTestAmpRunData",
           "EoTestData"]


class EoTestAmpExpDataSchemaV0(EoCalibTableSchema):
    """ Schema for a test class for per-amp, per-exposure tables"""

    TABLELENGTH = "nExposure"

    varExp1 = EoCalibField(name="VAR1", dtype=float, description="A variables", unit="s")


class EoTestAmpExpDataSchemaV1(EoTestAmpExpDataSchemaV0):
    """ Schema for a test class for per-amp, per-exposure tables"""
    TABLELENGTH = "nExposure"

    varExp2 = EoCalibField(name="VAR2", dtype=float, shape=["nSample"])


class EoTestAmpExpData(EoCalibTable):
    """Container class and interface for per-amp, per-exposure-pair table
    for a test class."""

    SCHEMA_CLASS = EoTestAmpExpDataSchemaV1
    PREVIOUS_SCHEMAS = [EoTestAmpExpDataSchemaV0]

    def __init__(self, data=None, **kwargs):
        """C'tor, arguments are passed to base class.

        Class specialization just associates class properties with columns

        This is also where we deal with schema evolution to provide
        a single unified interface
        """
        super(EoTestAmpExpData, self).__init__(data=data, **kwargs)
        self.varExp1 = self.table[self.SCHEMA_CLASS.varExp1.name]
        try:
            self.varExp2 = self.table[self.SCHEMA_CLASS.varExp2.name]
        except KeyError:
            self.varExp2 = np.nan


class EoTestAmpRunDataSchemaV0(EoCalibTableSchema):
    """ Schema for a test class for per-amp, per-exposure tables"""

    TABLELENGTH = "nAmp"

    varAmp1 = EoCalibField(name="VARAMP1", dtype=float)


class EoTestAmpRunData(EoCalibTable):
    """Container class and interface for per-amp, per-run table
    for a test class."""

    SCHEMA_CLASS = EoTestAmpRunDataSchemaV0

    def __init__(self, data=None, **kwargs):
        """C'tor, arguments are passed to base class.

        Class specialization just associates class properties with columns
        """
        super(EoTestAmpRunData, self).__init__(data=data, **kwargs)
        self.varAmp1 = self.table[self.SCHEMA_CLASS.varAmp1.name]


class EoTestDataSchemaV0(EoCalibSchema):
    """Schema definitions for output data for a test class

    This defines correct versions of the sub-tables"""

    amps = EoCalibTableHandle(tableName="amps",
                              tableClass=EoTestAmpRunData)


class EoTestDataSchemaV1(EoTestDataSchemaV0):
    """Schema definitions for output data for a test class

    This defines correct versions of the sub-tables"""

    ampExp = EoCalibTableHandle(tableName="ampExp_{key}",
                                tableClass=EoTestAmpExpData,
                                multiKey="amps")


class EoTestData(EoCalib):
    """Container class and interface for test class outputs."""

    SCHEMA_CLASS = EoTestDataSchemaV1
    PREVIOUS_SCHEMAS = [EoTestDataSchemaV0]

    _OBSTYPE = 'bias'
    _SCHEMA = SCHEMA_CLASS.fullName()
    _VERSION = SCHEMA_CLASS.version()

    def __init__(self, **kwargs):
        """C'tor, arguments are passed to base class.

        Class specialization just associates instance properties with
        sub-tables
        """
        super(EoTestData, self).__init__(**kwargs)
        try:
            self.ampExp = self['ampExp']
        except KeyError:
            self.ampExp = None
        self.amps = self['amps']


RegisterEoCalibSchema(EoTestData)

AMPS = ["%02i" % i for i in range(16)]
NEXPOSURE = 10
NSAMPLE = 10
EoTestData.testData = dict(testCtor=dict(amps=AMPS, nAmp=len(AMPS), nExposure=NEXPOSURE, nSample=NSAMPLE))
