# from lsst.ip.isr import IsrCalib

from eoCalibTable import EoCalibField, EoCalibTableSchema, EoCalibTable, RegisterEoCalibTableSchema
from eoCalib import EoCalibTableHandle, EoCalibSchema, EoCalib, RegisterEoCalibSchema

__all__ = ["EoBrighterFatterAmpExpDataSchemaV0", "EoBrighterFatterAmpExpData",
           "EoBrighterFatterAmpRunDataSchemaV0", "EoBrighterFatterAmpRunData",
           "EoBrighterFatterDataSchemaV0", "EoBrighterFatterData"]


class EoBrighterFatterAmpExpDataSchemaV0(EoCalibTableSchema):

    NAME, VERSION = "EoBrighterFatterAmpExpData", 0
    TABLELENGTH = "nExposure"

    mean = EoCalibField(name="MEAN", dtype=float, unit='e-')
    covarience = EoCalibField(name="COV", dtype=float, unit='e-**2', shape=['nCov', 'nCov'])
    covarienceError = EoCalibField(name="COV_ERROR", dtype=float, unit='e-**2', shape=['nCov', 'nCov'])


class EoBrighterFatterAmpExpData(EoCalibTable):

    SCHEMA_CLASS = EoBrighterFatterAmpExpDataSchemaV0

    def __init__(self, data=None, **kwargs):
        super(EoBrighterFatterAmpExpData, self).__init__(data=None, **kwargs)
        self.mean = self.table[self.SCHEMA_CLASS.mean.name]
        self.covarience = self.table[self.SCHEMA_CLASS.covarience.name]
        self.covarienceError = self.table[self.SCHEMA_CLASS.covarienceError.name]


class EoBrighterFatterAmpRunDataSchemaV0(EoCalibTableSchema):

    NAME, VERSION = "EoBrighterFatterAmpRunData", 0
    TABLELENGTH = "nAmp"

    bfMean = EoCalibField(name='BF_MEAN', dtype=float)
    bfXCorr = EoCalibField(name='BF_XCORR', dtype=float)
    bfXCorrErr = EoCalibField(name='BF_XCORR_ERR', dtype=float)
    bfXSlope = EoCalibField(name='BF_SLOPEX', dtype=float)
    bfXSlopeErr = EoCalibField(name='BF_SLOPEX_ERR', dtype=float)
    bfYCorr = EoCalibField(name='BF_YCORR', dtype=float)
    bfYCorrErr = EoCalibField(name='BF_YCORR_ERR', dtype=float)
    bfYSlope = EoCalibField(name='BF_SLOPEY', dtype=float)
    bfYSlopeErr = EoCalibField(name='BF_SLOPEY_ERR', dtype=float)


class EoBrighterFatterAmpRunData(EoCalibTable):

    SCHEMA_CLASS = EoBrighterFatterAmpRunDataSchemaV0

    def __init__(self, data=None, **kwargs):
        super(EoBrighterFatterAmpRunData, self).__init__(data=data, **kwargs)
        self.bfMean = self.table[self.SCHEMA_CLASS.bfMean.name]
        self.bfXCorr = self.table[self.SCHEMA_CLASS.bfXCorr.name]
        self.bfXCorrErr = self.table[self.SCHEMA_CLASS.bfXCorrErr.name]
        self.bfXSlope = self.table[self.SCHEMA_CLASS.bfXSlope.name]
        self.bfXSlopeErr = self.table[self.SCHEMA_CLASS.bfXSlopeErr.name]
        self.bfYCorr = self.table[self.SCHEMA_CLASS.bfYCorr.name]
        self.bfYCorrErr = self.table[self.SCHEMA_CLASS.bfYCorrErr.name]
        self.bfYSlope = self.table[self.SCHEMA_CLASS.bfYSlope.name]
        self.bfYSlopeErr = self.table[self.SCHEMA_CLASS.bfYSlopeErr.name]


class EoBrighterFatterDataSchemaV0(EoCalibSchema):

    NAME, VERSION = "EoBrighterFatterData", 0
    
    ampExposure = EoCalibTableHandle(tableName="ampExp_{key}",
                                     tableClass=EoBrighterFatterAmpExpData,
                                     multiKey="amps")

    amps = EoCalibTableHandle(tableName="amps",
                              tableClass=EoBrighterFatterAmpRunData)


class EoBrighterFatterData(EoCalib):

    SCHEMA_CLASS = EoBrighterFatterDataSchemaV0

    _OBSTYPE = 'bias'
    _SCHEMA = SCHEMA_CLASS.fullName()
    _VERSION = SCHEMA_CLASS.VERSION

    def __init__(self, **kwargs):
        super(EoBrighterFatterData, self).__init__(**kwargs)
        self.ampExposure = self._tables['ampExposure']
        self.amps = self._tables['amps']


RegisterEoCalibTableSchema(EoBrighterFatterAmpExpDataSchemaV0)
RegisterEoCalibTableSchema(EoBrighterFatterAmpRunDataSchemaV0)
RegisterEoCalibSchema(EoBrighterFatterDataSchemaV0)


AMPS = ["%02i" % i for i in range(16)]
NEXPOSURE = 10
NCOV = 100

testData = EoBrighterFatterData(amps=AMPS, nAmp=len(AMPS), nExposure=NEXPOSURE, nCov=NCOV)
