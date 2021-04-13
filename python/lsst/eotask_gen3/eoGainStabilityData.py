# from lsst.ip.isr import IsrCalib

from eoCalibTable import EoCalibField, EoCalibTableSchema, EoCalibTable, RegisterEoCalibTableSchema
from eoCalib import EoCalibTableHandle, EoCalibSchema, EoCalib, RegisterEoCalibSchema

__all__ = ["EoGainStabilityAmpExpDataSchemaV0", "EoGainStabilityAmpExpData",
           "EoGainStabilityDetExpDataSchemaV0", "EoGainStabilityDetExpData",
           "EoGainStabilityDataSchemaV0", "EoGainStabilityData"]


class EoGainStabilityAmpExpDataSchemaV0(EoCalibTableSchema):

    VERSION = 0
    TABLELENGTH = "nExposure"

    signal = EoCalibField(name="SIGNAL", dtype=float, unit='e-')


class EoGainStabilityAmpExpData(EoCalibTable):

    SCHEMA_CLASS = EoGainStabilityAmpExpDataSchemaV0

    def __init__(self, data=None, **kwargs):
        super(EoGainStabilityAmpExpData, self).__init__(data=data, **kwargs)
        self.signal = self.table[self.SCHEMA_CLASS.signal.name]


class EoGainStabilityDetExpDataSchemaV0(EoCalibTableSchema):

    VERSION = 0
    TABLELENGTH = "nExposure"

    mjd = EoCalibField(name="MJD", dtype=float, unit='e-')
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

    ampExposure = EoCalibTableHandle(tableName="ampExp_{key}",
                                     tableClass=EoGainStabilityAmpExpData,
                                     multiKey="amps")

    detExposure = EoCalibTableHandle(tableName="detExp",
                                     tableClass=EoGainStabilityDetExpData)


class EoGainStabilityData(EoCalib):

    SCHEMA_CLASS = EoGainStabilityDataSchemaV0

    _OBSTYPE = 'flat'
    _SCHEMA = SCHEMA_CLASS.fullName()
    _VERSION = SCHEMA_CLASS.VERSION

    def __init__(self, **kwargs):
        super(EoGainStabilityData, self).__init__(**kwargs)
        self.ampExposure = self._tables['ampExposure']
        self.detExposure = self._tables['detExposure']


RegisterEoCalibTableSchema(EoGainStabilityAmpExpData)
RegisterEoCalibTableSchema(EoGainStabilityDetExpData)
RegisterEoCalibSchema(EoGainStabilityData)

AMPS = ["%02i" % i for i in range(16)]
NEXPOSURE = 10

testData = EoGainStabilityData(amps=AMPS, nExposure=NEXPOSURE)
