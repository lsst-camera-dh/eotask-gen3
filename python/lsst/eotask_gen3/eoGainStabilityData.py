# from lsst.ip.isr import IsrCalib

from .eoCalibTable import EoCalibField, EoCalibTableSchema, EoCalibTable, EoCalibTableHandle
from .eoCalib import EoCalibSchema, EoCalib, RegisterEoCalibSchema

__all__ = ["EoGainStabilityAmpExpData",
           "EoGainStabilityDetExpData",
           "EoGainStabilityData"]


class EoGainStabilityAmpExpDataSchemaV0(EoCalibTableSchema):

    TABLELENGTH = "nExposure"

    signal = EoCalibField(name="SIGNAL", dtype=float, unit='electron')


class EoGainStabilityAmpExpData(EoCalibTable):

    SCHEMA_CLASS = EoGainStabilityAmpExpDataSchemaV0

    def __init__(self, data=None, **kwargs):
        super(EoGainStabilityAmpExpData, self).__init__(data=data, **kwargs)
        self.signal = self.table[self.SCHEMA_CLASS.signal.name]


class EoGainStabilityDetExpDataSchemaV0(EoCalibTableSchema):

    TABLELENGTH = "nExposure"

    mjd = EoCalibField(name="MJD", dtype=float, unit='electron')
    seqnum = EoCalibField(name="SEQNUM", dtype=int)
    flux = EoCalibField(name="FLUX", dtype=float)


class EoGainStabilityDetExpData(EoCalibTable):

    SCHEMA_CLASS = EoGainStabilityDetExpDataSchemaV0

    def __init__(self, data=None, **kwargs):
        super(EoGainStabilityDetExpData, self).__init__(data=None, **kwargs)
        self.mjd = self.table[self.SCHEMA_CLASS.mjd.name]
        self.seqnum = self.table[self.SCHEMA_CLASS.seqnum.name]
        self.flux = self.table[self.SCHEMA_CLASS.flux.name]


class EoGainStabilityDataSchemaV0(EoCalibSchema):

    ampExp = EoCalibTableHandle(tableName="ampExp_{key}",
                                tableClass=EoGainStabilityAmpExpData,
                                multiKey="amps")

    detExp = EoCalibTableHandle(tableName="detExp",
                                tableClass=EoGainStabilityDetExpData)


class EoGainStabilityData(EoCalib):

    SCHEMA_CLASS = EoGainStabilityDataSchemaV0

    _OBSTYPE = 'flat'
    _SCHEMA = SCHEMA_CLASS.fullName()
    _VERSION = SCHEMA_CLASS.version()

    def __init__(self, **kwargs):
        super(EoGainStabilityData, self).__init__(**kwargs)
        self.ampExp = self['ampExp']
        self.detExp = self['detExp']


RegisterEoCalibSchema(EoGainStabilityData)


AMPS = ["%02i" % i for i in range(16)]
NEXPOSURE = 10
EoGainStabilityData.testData = dict(testCtor=dict(amps=AMPS, nExposure=NEXPOSURE))
