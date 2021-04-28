# from lsst.ip.isr import IsrCalib

from .eoCalibTable import EoCalibField, EoCalibTableSchema, EoCalibTable, EoCalibTableHandle
from .eoCalib import EoCalibSchema, EoCalib, RegisterEoCalibSchema

__all__ = ["EoBiasStabilityAmpExpData",
           "EoBiasStabilityDetExpData",
           "EoBiasStabilityData"]


class EoBiasStabilityAmpExpDataSchemaV0(EoCalibTableSchema):

    TABLELENGTH = "nExposure"

    mean = EoCalibField(name="MEAN", dtype=float, unit='adu')
    stdev = EoCalibField(name="STDEV", dtype=float, unit='adu')
    rowMedian = EoCalibField(name="ROW_MEDIAN", dtype=float, unit='adu', shape=['nRow'])
    

class EoBiasStabilityAmpExpData(EoCalibTable):

    SCHEMA_CLASS = EoBiasStabilityAmpExpDataSchemaV0

    def __init__(self, data=None, **kwargs):
        super(EoBiasStabilityAmpExpData, self).__init__(data=None, **kwargs)
        self.mean = self.table[self.SCHEMA_CLASS.mean.name]
        self.stdev = self.table[self.SCHEMA_CLASS.stdev.name]
        self.rowMedian = self.table[self.SCHEMA_CLASS.rowMedian.name]


class EoBiasStabilityDetExpDataSchemaV0(EoCalibTableSchema):

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

    ampExposure = EoCalibTableHandle(tableName="ampExp_{key}",
                                     tableClass=EoBiasStabilityAmpExpData,
                                     multiKey="amps")

    detExposure = EoCalibTableHandle(tableName="detExp",
                                     tableClass=EoBiasStabilityDetExpData)


class EoBiasStabilityData(EoCalib):

    SCHEMA_CLASS = EoBiasStabilityDataSchemaV0

    _OBSTYPE = 'bias'
    _SCHEMA = SCHEMA_CLASS.fullName()
    _VERSION = SCHEMA_CLASS.version()

    def __init__(self, **kwargs):
        super(EoBiasStabilityData, self).__init__(**kwargs)
        self.ampExposure = self['ampExposure']
        self.detExposure = self['detExposure']


RegisterEoCalibSchema(EoBiasStabilityData)


AMPS = ["%02i" % i for i in range(16)]
NEXPOSURE = 10
NTEMP = 10
EoBiasStabilityData.testData = dict(testCtor=dict(amps=AMPS, nExposure=NEXPOSURE, nTemp=NTEMP))
