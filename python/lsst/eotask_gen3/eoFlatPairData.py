# from lsst.ip.isr import IsrCalib

from .eoCalibTable import EoCalibField, EoCalibTableSchema, EoCalibTable, EoCalibTableHandle
from .eoCalib import EoCalibSchema, EoCalib, RegisterEoCalibSchema

__all__ = ["EoFlatPairAmpExpData",
           "EoFlatPairAmpRunData",
           "EoFlatPairDetExpData",
           "EoFlatPairData"]


class EoFlatPairAmpExpDataSchemaV0(EoCalibTableSchema):

    NAME, VERSION = "EoFlatPairAmpExpData", 0
    TABLELENGTH = "nPair"

    signal = EoCalibField(name='SIGNAL', unit='electron')
    flat1Signal = EoCalibField(name='FLAT1_SIGNAL', unit='electron')
    flat2Signal = EoCalibField(name='FLAT2_SIGNAL', unit='electron')
    rowMeanVar = EoCalibField(name='ROW_MEAN_VAR', unit='electron**2')


class EoFlatPairAmpExpData(EoCalibTable):

    SCHEMA_CLASS = EoFlatPairAmpExpDataSchemaV0

    def __init__(self, data=None, **kwargs):
        super(EoFlatPairAmpExpData, self).__init__(data=None, **kwargs)
        self.signal = self.table[self.SCHEMA_CLASS.signal.name]
        self.flat1Signal = self.table[self.SCHEMA_CLASS.flat1Signal.name]
        self.flat2Signal = self.table[self.SCHEMA_CLASS.flat2Signal.name]
        self.rowMeanVar = self.table[self.SCHEMA_CLASS.rowMeanVar.name]


class EoFlatPairAmpRunDataSchemaV0(EoCalibTableSchema):

    NAME, VERSION = "EoFlatPairAmpRunData", 0
    TABLELENGTH = 'nAmp'

    fullWell = EoCalibField(name="FULL_WELL", dtype=float, unit='adu')
    maxFracDev = EoCalibField(name="MAX_FRAC_DEV", dtype=float)
    rowMeanVarSlope = EoCalibField(name="ROW_MEAN_VAR_SLOPE", dtype=float)
    maxObservedSignal = EoCalibField(name="MAX_OBSERVED_SIGNAL", dtype=float, unit='adu')
    linearityTurnoff = EoCalibField(name="LINEARITY_TURNOFF", dtype=float, unit='adu')


class EoFlatPairAmpRunData(EoCalibTable):

    SCHEMA_CLASS = EoFlatPairAmpRunDataSchemaV0

    def __init__(self, data=None, **kwargs):
        super(EoFlatPairAmpRunData, self).__init__(data=None, **kwargs)
        self.fullWell = self.table[self.SCHEMA_CLASS.fullWell.name]
        self.maxFracDev = self.table[self.SCHEMA_CLASS.maxFracDev.name]
        self.rowMeanVarSlope = self.table[self.SCHEMA_CLASS.rowMeanVarSlope.name]
        self.maxObservedSignal = self.table[self.SCHEMA_CLASS.maxObservedSignal.name]
        self.linearityTurnoff = self.table[self.SCHEMA_CLASS.linearityTurnoff.name]


class EoFlatPairDetExpDataSchemaV0(EoCalibTableSchema):

    NAME, VERSION = "EoFlatPairDetExpData", 0
    TABLELENGTH = "nPair"

    flux = EoCalibField(name="FLUX", dtype=float)
    seqnum = EoCalibField(name="SEQNUM", dtype=int)
    dayobs = EoCalibField(name="DAYOBS", dtype=int)


class EoFlatPairDetExpData(EoCalibTable):

    SCHEMA_CLASS = EoFlatPairDetExpDataSchemaV0

    def __init__(self, data=None, **kwargs):
        super(EoFlatPairDetExpData, self).__init__(data=data, **kwargs)
        self.flux = self.table[self.SCHEMA_CLASS.flux.name]
        self.seqnum = self.table[self.SCHEMA_CLASS.seqnum.name]
        self.dayobs = self.table[self.SCHEMA_CLASS.dayobs.name]


class EoFlatPairDataSchemaV0(EoCalibSchema):

    NAME, VERSION = "EoFlatPairData", 0

    ampExposure = EoCalibTableHandle(tableName="ampExp_{key}",
                                     tableClass=EoFlatPairAmpExpData,
                                     multiKey="amps")

    amps = EoCalibTableHandle(tableName="amps",
                              tableClass=EoFlatPairAmpRunData)

    detExposure = EoCalibTableHandle(tableName="detExp",
                                     tableClass=EoFlatPairDetExpData)


class EoFlatPairData(EoCalib):

    SCHEMA_CLASS = EoFlatPairDataSchemaV0

    _OBSTYPE = 'flat'
    _SCHEMA = SCHEMA_CLASS.fullName()
    _VERSION = SCHEMA_CLASS.version()

    def __init__(self, **kwargs):
        super(EoFlatPairData, self).__init__(**kwargs)
        self.ampExposure = self['ampExposure']
        self.amps = self['amps']
        self.detExposure = self['detExposure']


RegisterEoCalibSchema(EoFlatPairData)


AMPS = ["%02i" % i for i in range(16)]
NEXPOSURE = 10
EoFlatPairData.testData = dict(testCtor=dict(amps=AMPS, nAmp=len(AMPS), nExposure=NEXPOSURE))
