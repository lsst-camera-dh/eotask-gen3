# from lsst.ip.isr import IsrCalib

from .eoCalibTable import EoCalibField, EoCalibTableSchema, EoCalibTable, EoCalibTableHandle
from .eoCalib import EoCalibSchema, EoCalib, RegisterEoCalibSchema

__all__ = ["EoCtiAmpRunData",
           "EOCtiData"]


class EoCtiAmpRunDataSchemaV0(EoCalibTableSchema):

    TABLELENGTH = "nAmp"

    ctiSerial = EoCalibField(name="CTI_SERIAL", dtype=float)
    ctiSerialError = EoCalibField(name="CTI_SERIAL_ERR", dtype=float)
    ctiParallel = EoCalibField(name="CTI_PARALLEL", dtype=float)
    ctiParallelError = EoCalibField(name="CTI_PARALLEL_ERR", dtype=float)


class EoCtiAmpRunData(EoCalibTable):

    SCHEMA_CLASS = EoCtiAmpRunDataSchemaV0

    def __init__(self, data=None, **kwargs):
        super(EoCtiAmpRunData, self).__init__(data=None, **kwargs)
        self.ctiSerial = self.table[self.SCHEMA_CLASS.ctiSerial.name]
        self.ctiSerialError = self.table[self.SCHEMA_CLASS.ctiSerialError.name]
        self.ctiParallel = self.table[self.SCHEMA_CLASS.ctiParallel.name]
        self.ctiParallelError = self.table[self.SCHEMA_CLASS.ctiParallelError.name]


class EOCtiDataSchemaV0(EoCalibSchema):

    amps = EoCalibTableHandle(tableName="amps",
                              tableClass=EoCtiAmpRunData)


class EOCtiData(EoCalib):

    SCHEMA_CLASS = EOCtiDataSchemaV0

    _OBSTYPE = 'bias'
    _SCHEMA = SCHEMA_CLASS.fullName()
    _VERSION = SCHEMA_CLASS.version()

    def __init__(self, **kwargs):
        super(EOCtiData, self).__init__(**kwargs)
        self.amps = self['amps']


RegisterEoCalibSchema(EOCtiData)


AMPS = ["%02i" % i for i in range(16)]

EOCtiData.testData = dict(testCtor=dict(amps=AMPS, nAmp=len(AMPS)))