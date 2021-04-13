# from lsst.ip.isr import IsrCalib

from eoCalibTable import EoCalibField, EoCalibTableSchema, EoCalibTable, RegisterEoCalibTableSchema
from eoCalib import EoCalibTableHandle, EoCalibSchema, EoCalib, RegisterEoCalibSchema

__all__ = ["EoReadNoiseAmpExpDataSchemaV0", "EoReadNoiseAmpExpData",
           "EoReadNoiseAmpRunDataSchemaV0", "EoReadNoiseAmpRunData",
           "EoReadNoiseDataSchemaV0", "EoReadNoiseData"]


class EoReadNoiseAmpExpDataSchemaV0(EoCalibTableSchema):

    NAME, VERSION = 'EoReadNoiseAmpExpData', 0
    TABLELENGTH = "nExposure"

    totalNoise = EoCalibField(name="TOTAL_NOISE", dtype=float, unit='e-', shape=["nSample"])


class EoReadNoiseAmpExpData(EoCalibTable):

    SCHEMA_CLASS = EoReadNoiseAmpExpDataSchemaV0

    def __init__(self, data=None, **kwargs):
        super(EoReadNoiseAmpExpData, self).__init__(data=data, **kwargs)
        self.totalNoise = self.table[self.SCHEMA_CLASS.totalNoise.name]


class EoReadNoiseAmpRunDataSchemaV0(EoCalibTableSchema):

    NAME, VERSION = 'EoReadNoiseAmpRunData', 0
    TABLELENGTH = "nAmp"

    readNoise = EoCalibField(name="READ_NOISE", dtype=float, unit='e-')
    totalNoise = EoCalibField(name="TOTAL_NOISE", dtype=float, unit='e-')
    systemNoise = EoCalibField(name="SYSTEM_NOISE", dtype=float, unit='e-')


class EoReadNoiseAmpRunData(EoCalibTable):

    SCHEMA_CLASS = EoReadNoiseAmpRunDataSchemaV0

    def __init__(self, data=None, **kwargs):
        super(EoReadNoiseAmpRunData, self).__init__(data=data, **kwargs)
        self.readNoise = self.table[self.SCHEMA_CLASS.readNoise.name]
        self.totalNoise = self.table[self.SCHEMA_CLASS.totalNoise.name]
        self.systemNoise = self.table[self.SCHEMA_CLASS.systemNoise.name]


class EoReadNoiseDataSchemaV0(EoCalibSchema):

    NAME, VERSION = 'EoReadNoiseData', 0
    
    ampExposure = EoCalibTableHandle(tableName="ampExp_{key}",
                                     tableClass=EoReadNoiseAmpExpData,
                                     multiKey="amps")

    amps = EoCalibTableHandle(tableName="amps",
                              tableClass=EoReadNoiseAmpRunData)


class EoReadNoiseData(EoCalib):

    SCHEMA_CLASS = EoReadNoiseDataSchemaV0

    _OBSTYPE = 'bias'
    _SCHEMA = SCHEMA_CLASS.fullName()
    _VERSION = SCHEMA_CLASS.VERSION

    def __init__(self, **kwargs):
        super(EoReadNoiseData, self).__init__(**kwargs)
        self.ampExposure = self._tables['ampExposure']
        self.amps = self._tables['amps']


RegisterEoCalibTableSchema(EoReadNoiseAmpExpData)
RegisterEoCalibTableSchema(EoReadNoiseAmpRunData)
RegisterEoCalibSchema(EoReadNoiseData)

AMPS = ["%02i" % i for i in range(16)]
NEXPOSURE = 10
NSAMPLES = 100

testData = EoReadNoiseData(amps=AMPS, nAmp=len(AMPS), nExposure=NEXPOSURE, nSample=NSAMPLES)
