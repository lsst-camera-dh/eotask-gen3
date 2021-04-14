# from lsst.ip.isr import IsrCalib

from .eoCalibTable import EoCalibField, EoCalibTableSchema, EoCalibTable, EoCalibTableHandle
from .eoCalib import EoCalibSchema, EoCalib, RegisterEoCalibSchema

__all__ = ["EoPtcAmpExpData",
           "EoPtcAmpRunData",
           "EoPtcDetExpData",
           "EoPtcData"]


class EoPtcAmpExpDataSchemaV0(EoCalibTableSchema):

    NAME, VERSION = "EoPtcAmpExpData", 0
    TABLELENGTH = "nExposure"

    mean = EoCalibField(name="MEAN", dtype=float, unit='adu')
    var = EoCalibField(name="VAR", dtype=float, unit='adu**2')
    discard = EoCalibField(name="DISCARD", dtype=int, unit='pixel')


class EoPtcAmpExpData(EoCalibTable):

    SCHEMA_CLASS = EoPtcAmpExpDataSchemaV0

    def __init__(self, data=None, **kwargs):
        super(EoPtcAmpExpData, self).__init__(data=data, **kwargs)
        self.mean = self.table[self.SCHEMA_CLASS.mean.name]
        self.var = self.table[self.SCHEMA_CLASS.var.name]
        self.discard = self.table[self.SCHEMA_CLASS.discard.name]


class EoPtcAmpRunDataSchemaV0(EoCalibTableSchema):

    NAME, VERSION = "EoPtcAmpRunData", 0
    TABLELENGTH = 'nAmp'

    ptcGain = EoCalibField(name="PTC_GAIN", dtype=float, unit='adu/electron')
    ptcGainError = EoCalibField(name="PTC_GAIN_ERROR", dtype=float, unit='adu/electron')
    ptcA00 = EoCalibField(name="PTC_A00", dtype=float)
    ptcA00Error = EoCalibField(name="PTC_A00_ERROR", dtype=float)
    ptcNoise = EoCalibField(name="PTC_NOISE", dtype=float, unit='adu')
    ptcNoiseError = EoCalibField(name="PTC_NOISE_ERROR", dtype=float, unit='adu')
    ptcTurnoff = EoCalibField(name="PTC_TURNOFF", dtype=float, unit='adu')


class EoPtcAmpRunData(EoCalibTable):

    SCHEMA_CLASS = EoPtcAmpRunDataSchemaV0

    def __init__(self, data=None, **kwargs):
        super(EoPtcAmpRunData, self).__init__(data=data, **kwargs)
        self.ptcGain = self.table[self.SCHEMA_CLASS.ptcGain.name]
        self.ptcGainError = self.table[self.SCHEMA_CLASS.ptcGainError.name]
        self.ptcA00 = self.table[self.SCHEMA_CLASS.ptcA00.name]
        self.ptcA00Error = self.table[self.SCHEMA_CLASS.ptcA00Error.name]
        self.ptcNoise = self.table[self.SCHEMA_CLASS.ptcNoise.name]
        self.ptcNoiseError = self.table[self.SCHEMA_CLASS.ptcNoiseError.name]
        self.ptcTurnoff = self.table[self.SCHEMA_CLASS.ptcTurnoff.name]


class EoPtcDetExpDataSchemaV0(EoCalibTableSchema):

    NAME, VERSION = "EoPtcDetExpData", 0
    TABLELENGTH = 'nExposure'

    exposure = EoCalibField(name="EXPOSURE", dtype=float)
    seqnum = EoCalibField(name="SEQNUM", dtype=int)
    dayobs = EoCalibField(name="DAYOBS", dtype=int)


class EoPtcDetExpData(EoCalibTable):

    SCHEMA_CLASS = EoPtcDetExpDataSchemaV0

    def __init__(self, data=None, **kwargs):
        super(EoPtcDetExpData, self).__init__(data=None, **kwargs)
        self.exposure = self.table[self.SCHEMA_CLASS.exposure.name]
        self.seqnum = self.table[self.SCHEMA_CLASS.seqnum.name]
        self.dayobs = self.table[self.SCHEMA_CLASS.dayobs.name]


class EoPtcDataSchemaV0(EoCalibSchema):

    ampExposure = EoCalibTableHandle(tableName="ampExp_{key}",
                                     tableClass=EoPtcAmpExpData,
                                     multiKey="amps")

    amps = EoCalibTableHandle(tableName="amps",
                              tableClass=EoPtcAmpRunData)

    detExposure = EoCalibTableHandle(tableName="detExp",
                                     tableClass=EoPtcDetExpData)


class EoPtcData(EoCalib):

    SCHEMA_CLASS = EoPtcDataSchemaV0

    _OBSTYPE = 'flat'
    _SCHEMA = SCHEMA_CLASS.fullName()
    _VERSION = SCHEMA_CLASS.version()

    def __init__(self, **kwargs):
        super(EoPtcData, self).__init__(**kwargs)
        self.ampExposure = self['ampExposure']
        self.amps = self['amps']
        self.detExposure = self['detExposure']


RegisterEoCalibSchema(EoPtcData)

AMPS = ["%02i" % i for i in range(16)]
NEXPOSURE = 10
EoPtcData.testData = dict(testCtor=dict(amps=AMPS, nAmp=len(AMPS), nExposure=NEXPOSURE))
