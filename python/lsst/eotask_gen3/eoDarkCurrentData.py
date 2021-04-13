# from lsst.ip.isr import IsrCalib

from .eoCalibTable import EoCalibField, EoCalibTableSchema, EoCalibTable, RegisterEoCalibTableSchema
from .eoCalib import EoCalibTableHandle, EoCalibSchema, EoCalib, RegisterEoCalibSchema

__all__ = ["EoDarkCurrentAmpRunData",
           "EoDarkCurrentData"]


class EoDarkCurrentAmpRunDataSchemaV0(EoCalibTableSchema):

    VERSION = 0
    TABLE_LENGTH = "nAmp"

    darkCurrent95 = EoCalibField(name="DARK_CURRENT_95", dtype=float, unit='e-/s')
    darkCurrentMedian = EoCalibField(name="DARK_CURRENT_MEDIAN", dtype=float, unit='e-/s')


class EoDarkCurrentAmpRunData(EoCalibTable):

    SCHEMA_CLASS = EoDarkCurrentAmpRunDataSchemaV0

    def __init__(self, data=None, **kwargs):
        super(EoDarkCurrentAmpRunData, self).__init__(data=None, **kwargs)
        self.darkCurrent95 = self.table[self.SCHEMA_CLASS.darkCurrent95.name]
        self.darkCurrentMedian = self.table[self.SCHEMA_CLASS.darkCurrentMedian.name]


class EoDarkCurrentDataSchemaV0(EoCalibSchema):

    amps = EoCalibTableHandle(tableName="amps",
                              tableClass=EoDarkCurrentAmpRunData)


class EoDarkCurrentData(EoCalib):

    SCHEMA_CLASS = EoDarkCurrentDataSchemaV0

    _OBSTYPE = 'dark'
    _SCHEMA = SCHEMA_CLASS.fullName()
    _VERSION = SCHEMA_CLASS.VERSION

    def __init__(self, **kwargs):
        super(EoDarkCurrentData, self).__init__(**kwargs)
        self.amps = self._tables['amps']


RegisterEoCalibTableSchema(EoDarkCurrentAmpRunData)
RegisterEoCalibSchema(EoDarkCurrentData)


AMPS = ["%02i" % i for i in range(16)]
testData = EoDarkCurrentData(amps=AMPS, nAmp=len(AMPS))
