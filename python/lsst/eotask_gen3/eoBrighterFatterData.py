# from lsst.ip.isr import IsrCalib

from .eoCalibTable import EoCalibField, EoCalibTableSchema, EoCalibTable, EoCalibTableHandle
from .eoCalib import EoCalibSchema, EoCalib, RegisterEoCalibSchema
from .eoPlotUtils import EoSlotPlotMethod, EoRaftPlotMethod, EoCameraPlotMethod, nullFigure

__all__ = ["EoBrighterFatterAmpPairData",
           "EoBrighterFatterAmpRunData",
           "EoBrighterFatterData"]


class EoBrighterFatterAmpPairDataSchemaV0(EoCalibTableSchema):

    TABLELENGTH = "nPair"

    mean = EoCalibField(name="MEAN", dtype=float, unit='electron')
    covarience = EoCalibField(name="COV", dtype=float, unit='electron**2', shape=['nCov', 'nCov'])
    covarienceError = EoCalibField(name="COV_ERROR", dtype=float, unit='electron**2', shape=['nCov', 'nCov'])


class EoBrighterFatterAmpPairData(EoCalibTable):

    SCHEMA_CLASS = EoBrighterFatterAmpPairDataSchemaV0

    def __init__(self, data=None, **kwargs):
        super(EoBrighterFatterAmpPairData, self).__init__(data=data, **kwargs)
        self.mean = self.table[self.SCHEMA_CLASS.mean.name]
        self.covarience = self.table[self.SCHEMA_CLASS.covarience.name]
        self.covarienceError = self.table[self.SCHEMA_CLASS.covarienceError.name]


class EoBrighterFatterAmpRunDataSchemaV0(EoCalibTableSchema):

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

    ampExp = EoCalibTableHandle(tableName="ampExp_{key}",
                                    tableClass=EoBrighterFatterAmpPairData,
                                    multiKey="amps")

    amps = EoCalibTableHandle(tableName="amps",
                              tableClass=EoBrighterFatterAmpRunData)


class EoBrighterFatterData(EoCalib):

    SCHEMA_CLASS = EoBrighterFatterDataSchemaV0

    _OBSTYPE = 'bias'
    _SCHEMA = SCHEMA_CLASS.fullName()
    _VERSION = SCHEMA_CLASS.version()

    def __init__(self, **kwargs):
        super(EoBrighterFatterData, self).__init__(**kwargs)
        self.ampExp = self['ampExp']
        self.amps = self['amps']


@EoSlotPlotMethod(EoBrighterFatterData, "bf", "Brighter Fatter")
def plotSlotBrighterFatter(obj):
    return nullFigure()

@EoCameraPlotMethod(EoBrighterFatterData, "xcorr_mosaic", "Brighter-Fatter cov10 Mosaic")
def plotBrighterFatterCov01Mosaic(cameraDataDict):
    return nullFigure()

@EoCameraPlotMethod(EoBrighterFatterData, "ycorr_mosaic", "Brighter-Fatter cov01 Mosaic")
def plotBrighterFatterCov10Mosaic(cameraDataDict):
    return nullFigure()

@EoCameraPlotMethod(EoBrighterFatterData, "xcorr_hist", "Brighter-Fatter cov10")
def plotBrighterFatterCov01Hist(cameraDataDict):
    return nullFigure()

@EoCameraPlotMethod(EoBrighterFatterData, "ycorr_hist", "Brighter-Fatter cov01")
def plotBrighterFatterCov10Hist(cameraDataDict):
    return nullFigure()



RegisterEoCalibSchema(EoBrighterFatterData)


AMPS = ["%02i" % i for i in range(16)]
NPAIR = 10
NCOV = 3
EoBrighterFatterData.testData = dict(testCtor=dict(amps=AMPS, nAmp=len(AMPS), nPair=NPAIR, nCov=NCOV))
