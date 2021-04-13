# from lsst.ip.isr import IsrCalib

from .eoCalibTable import EoCalibField, EoCalibTableSchema, EoCalibTable, RegisterEoCalibTableSchema
from .eoCalib import EoCalibTableHandle, EoCalibSchema, EoCalib, RegisterEoCalibSchema

from .eoReadNoiseData import EoReadNoiseAmpRunData
from .eoDarkCurrentData import EoDarkCurrentAmpRunData
from .eoCtiData import EoCtiAmpRunData
from .eoDefectData import EoDefectAmpRunData
from .eoPtcData import EoPtcAmpRunData
from .eoBrighterFatterData import EoBrighterFatterAmpRunData
from .eoFlatPairData import EoFlatPairAmpRunData
from .eoFe55Data import EoFe55AmpRunData

__all__ = ["EoSummaryAmpTableData",
           "EoSummaryDetTableData",
           "EOSummaryData"]


def copyEoCalibField(eoCalibField, nameSuffix=""):

    return eoCalibField.copy(name=eoCalibField.name + nameSuffix)


class EoSummaryAmpTableSchemaV0(EoCalibTableSchema):

    VERSION = 0
    TABLELENGTH = 'nAmp'

    READNOISESCHEMA = EoReadNoiseAmpRunData.SCHEMA_CLASS
    DARKCURRENTSCHEMA = EoDarkCurrentAmpRunData.SCHEMA_CLASS
    DEFECTSSCHEMA = EoDefectAmpRunData.SCHEMA_CLASS
    CTISCHEMA = EoCtiAmpRunData.SCHEMA_CLASS
    PTCSCHEMA = EoPtcAmpRunData.SCHEMA_CLASS
    BFSCHEMA = EoBrighterFatterAmpRunData.SCHEMA_CLASS
    FLATPAIRSCHEMA = EoFlatPairAmpRunData.SCHEMA_CLASS
    FE55SCHEMA = EoFe55AmpRunData.SCHEMA_CLASS

    amp = EoCalibField(name='AMP', dtype=int)
    detector = EoCalibField(name='DETECTOR', dtype=int)
    dc95ShotNoise = EoCalibField(name='DC95_SHOT_NOISE', dtype=float)

    readNoise = copyEoCalibField(READNOISESCHEMA.readNoise)
    totalNoise = copyEoCalibField(READNOISESCHEMA.totalNoise)
    systemNoise = copyEoCalibField(READNOISESCHEMA.systemNoise)

    darkCurrent95 = copyEoCalibField(DARKCURRENTSCHEMA.darkCurrent95)
    darkCurrentMedian = copyEoCalibField(DARKCURRENTSCHEMA.darkCurrentMedian)

    ctiLowSerial = copyEoCalibField(CTISCHEMA.ctiSerial, "_LOW")
    ctiLowSerialError = copyEoCalibField(CTISCHEMA.ctiSerialError, "_LOW")
    ctiLowParallel = copyEoCalibField(CTISCHEMA.ctiParallel, "_LOW")
    ctiLowParallelError = copyEoCalibField(CTISCHEMA.ctiParallelError, "_LOW")
    ctiHighSerial = copyEoCalibField(CTISCHEMA.ctiSerial, "_HIGH")
    ctiHighSerialError = copyEoCalibField(CTISCHEMA.ctiSerialError, "_HIGH")
    ctiHighParallel = copyEoCalibField(CTISCHEMA.ctiParallel, "_HIGH")
    ctiHighParallelError = copyEoCalibField(CTISCHEMA.ctiParallelError, "_HIGH")
    ptcGain = copyEoCalibField(PTCSCHEMA.ptcGain)
    ptcGainError = copyEoCalibField(PTCSCHEMA.ptcGainError)
    ptcA00 = copyEoCalibField(PTCSCHEMA.ptcA00)
    ptcA00Error = copyEoCalibField(PTCSCHEMA.ptcA00Error)
    ptcNoise = copyEoCalibField(PTCSCHEMA.ptcNoise)
    ptcNoiseError = copyEoCalibField(PTCSCHEMA.ptcNoiseError)
    ptcTurnoff = copyEoCalibField(PTCSCHEMA.ptcTurnoff)

    bfMean = copyEoCalibField(BFSCHEMA.bfMean)
    bfXCorr = copyEoCalibField(BFSCHEMA.bfXCorr)
    bfXCorrErr = copyEoCalibField(BFSCHEMA.bfXCorrErr)
    bfXSlope = copyEoCalibField(BFSCHEMA.bfXSlope)
    bfXSlopeErr = copyEoCalibField(BFSCHEMA.bfXSlopeErr)
    bfYCorr = copyEoCalibField(BFSCHEMA.bfYCorr)
    bfYCorrErr = copyEoCalibField(BFSCHEMA.bfYCorrErr)
    bfYSlope = copyEoCalibField(BFSCHEMA.bfYSlope)
    bfYSlopeErr = copyEoCalibField(BFSCHEMA.bfYSlopeErr)

    fullWell = copyEoCalibField(FLATPAIRSCHEMA.fullWell)
    maxFracDev = copyEoCalibField(FLATPAIRSCHEMA.maxFracDev)
    rowMeanVarSlope = copyEoCalibField(FLATPAIRSCHEMA.rowMeanVarSlope)
    maxObservedSignal = copyEoCalibField(FLATPAIRSCHEMA.maxObservedSignal)
    linearityTurnoff = copyEoCalibField(FLATPAIRSCHEMA.linearityTurnoff)

    gain = copyEoCalibField(FE55SCHEMA.gain)
    gainError = copyEoCalibField(FE55SCHEMA.gainError)
    psfSigma = copyEoCalibField(FE55SCHEMA.psfSigma)

    nBrightPixel = copyEoCalibField(DEFECTSSCHEMA.nBrightPixel)
    nBrightColumn = copyEoCalibField(DEFECTSSCHEMA.nBrightColumn)
    nDarkPixel = copyEoCalibField(DEFECTSSCHEMA.nDarkPixel)
    nDarkColumn = copyEoCalibField(DEFECTSSCHEMA.nDarkColumn)
    nTraps = copyEoCalibField(DEFECTSSCHEMA.nTraps)


class EoSummaryAmpTableData(EoCalibTable):

    SCHEMA_CLASS = EoSummaryAmpTableSchemaV0

    def __init__(self, data=None, **kwargs):
        super(EoSummaryAmpTableData, self).__init__(data=data, **kwargs)


class EoSummaryDetTableSchemaV0(EoCalibTableSchema):

    VERSION = 0
    TABLELENGTH = 'nDet'


class EoSummaryDetTableData(EoCalibTable):

    SCHEMA_CLASS = EoSummaryDetTableSchemaV0

    def __init__(self, data=None, **kwargs):
        super(EoSummaryDetTableData, self).__init__(data=data, **kwargs)


class EOSummaryDataSchemaV0(EoCalibSchema):

    amps = EoCalibTableHandle(tableName="amps",
                              tableClass=EoSummaryAmpTableData)

    dets = EoCalibTableHandle(tableName="dets",
                              tableClass=EoSummaryDetTableData)


class EOSummaryData(EoCalib):

    _CURRENT_SCHEMA = EOSummaryDataSchemaV0()
    _SCHEMA = 'Eo Summary'
    _VERSION = _CURRENT_SCHEMA.VERSION

    def __init__(self, **kwargs):
        super(EOSummaryData, self).__init__(**kwargs)
        self.amps = self._tables['amps']
        self.dets = self._tables['dets']


RegisterEoCalibTableSchema(EoSummaryAmpTableData)
RegisterEoCalibTableSchema(EoSummaryDetTableData)
RegisterEoCalibSchema(EOSummaryDataSchemaV0)

AMPS = ["%02i" % i for i in range(16)]

testData = EOSummaryData(nAmp=len(AMPS))
