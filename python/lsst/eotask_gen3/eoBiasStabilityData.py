# from lsst.ip.isr import IsrCalib

from .eoCalibTable import EoCalibField, EoCalibTableSchema, EoCalibTable, RegisterEoCalibTableSchema
from .eoCalib import EoCalibTableHandle, EoCalibSchema, EoCalib, RegisterEoCalibSchema

__all__ = ["EoBiasStabilityAmpExpData",
           "EoBiasStabilityDetExpData",
           "EoBiasStabilityData"]


class EoBiasStabilityAmpExpDataSchemaV0(EoCalibTableSchema):

    NAME, VERSION = "EoBiasStabilityAmpExpData", 0
    TABLELENGTH = "nExposure"

    mean = EoCalibField(name="MEAN", dtype=float, unit='ADU')
    stdev = EoCalibField(name="STDEV", dtype=float, unit='ADU')


class EoBiasStabilityAmpExpData(EoCalibTable):

    SCHEMA_CLASS = EoBiasStabilityAmpExpDataSchemaV0

    def __init__(self, data=None, **kwargs):
        super(EoBiasStabilityAmpExpData, self).__init__(data=None, **kwargs)
        self.mean = self.table[self.SCHEMA_CLASS.mean.name]
        self.stdev = self.table[self.SCHEMA_CLASS.stdev.name]


class EoBiasStabilityDetExpDataSchemaV0(EoCalibTableSchema):

    NAME, VERSION = "EoBiasStabilityDetExpData", 0
    TABLELENGTH = "nExposure"

    seqnum = EoCalibField(name="SEQNUM", dtype=int)
    mjd = EoCalibField(name="MJD", dtype=float)
    temp = EoCalibField(name="TEMP", dtype=float, shape=["nTemp"])


class EoBiasStabilityDetExpData(EoCalibTable):

    SCHEMA_CLASS = EoBiasStabilityDetExpDataSchemaV0

    def __init__(self, data=None, **kwargs):
        super(EoBiasStabilityDetExpData, self).__init__(data=data, **kwargs)
        self.seqnum = self.table[self.SCHEMA_CLASS.seqnum.name]
        self.mjd = self.table[self.SCHEMA_CLASS.mjd.name]
        self.temp = self.table[self.SCHEMA_CLASS.temp.name]


class EoBiasStabilityDataSchemaV0(EoCalibSchema):

    NAME, VERSION = "EoBiasStabilityData", 0

    ampExposure = EoCalibTableHandle(tableName="ampExp_{key}",
                                     tableClass=EoBiasStabilityAmpExpData,
                                     multiKey="amps")

    detExposure = EoCalibTableHandle(tableName="detExp",
                                     tableClass=EoBiasStabilityDetExpData)


class EoBiasStabilityData(EoCalib):

    SCHEMA_CLASS = EoBiasStabilityDataSchemaV0

    _OBSTYPE = 'bias'
    _SCHEMA = SCHEMA_CLASS.fullName()
    _VERSION = SCHEMA_CLASS.VERSION

    def __init__(self, **kwargs):
        super(EoBiasStabilityData, self).__init__(**kwargs)
        self.ampExposure = self._tables['ampExposure']
        self.detExposure = self._tables['detExposure']


RegisterEoCalibTableSchema(EoBiasStabilityAmpExpData)
RegisterEoCalibTableSchema(EoBiasStabilityDetExpData)
RegisterEoCalibSchema(EoBiasStabilityData)


AMPS = ["%02i" % i for i in range(16)]
NEXPOSURE = 10
NTEMP = 10

testData = EoBiasStabilityData(amps=AMPS, nExposure=NEXPOSURE, nTemp=NTEMP)
