# from lsst.ip.isr import IsrCalib

from .eoCalibTable import EoCalibField, EoCalibTableSchema, EoCalibTable, EoCalibTableHandle
from .eoCalib import EoCalibSchema, EoCalib, RegisterEoCalibSchema

__all__ = ["EoNonlinearityAmpRunData",
           "EoNonlinearityData"]


class EoNonlinearityAmpRunDataSchemaV0(EoCalibTableSchema):

    TABLELENGTH = 'nAmp'

    profX = EoCalibField(name="PROF_X", dtype=float, unit='adu', shape=['nProf'])
    profYCorr = EoCalibField(name="PROF_YCORR", dtype=float, unit='adu', shape=['nProf'])
    profYErr = EoCalibField(name="PROF_YERR", dtype=float, unit='adu', shape=['nProf'])


class EoNonlinearityAmpRunData(EoCalibTable):

    SCHEMA_CLASS = EoNonlinearityAmpRunDataSchemaV0

    def __init__(self, data=None, **kwargs):
        super(EoNonlinearityAmpRunData, self).__init__(data=data, **kwargs)
        self.profX = self.table[self.SCHEMA_CLASS.profX.name]
        self.profYCorr = self.table[self.SCHEMA_CLASS.profYCorr.name]
        self.profYErr = self.table[self.SCHEMA_CLASS.profYErr.name]


class EoNonlinearityDataSchemaV0(EoCalibSchema):

    amps = EoCalibTableHandle(tableName="amps",
                              tableClass=EoNonlinearityAmpRunData)
    

class EoNonlinearityData(EoCalib):

    SCHEMA_CLASS = EoNonlinearityDataSchemaV0

    _OBSTYPE = 'flat'
    _SCHEMA = SCHEMA_CLASS.fullName()
    _VERSION = SCHEMA_CLASS.version()

    def __init__(self, **kwargs):
        super(EoNonlinearityData, self).__init__(**kwargs)
        self.amps = self['amps']


RegisterEoCalibSchema(EoNonlinearityData)


AMPS = ["%02i" % i for i in range(16)]
NPROFILE = 20
EoNonlinearityData.testData = dict(testCtor=dict(nAmp=len(AMPS), nProf=NPROFILE)
