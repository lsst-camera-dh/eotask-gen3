# from lsst.ip.isr import IsrCalib

from .eoCalibTable import EoCalibField, EoCalibTableSchema, EoCalibTable, EoCalibTableHandle
from .eoCalib import EoCalibSchema, EoCalib, RegisterEoCalibSchema
from .eoPlotUtils import EoPlotMethod, nullFigure

__all__ = ["EoCtiAmpRunData",
           "EoCtiData"]


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


class EoCtiDataSchemaV0(EoCalibSchema):

    amps = EoCalibTableHandle(tableName="amps",
                              tableClass=EoCtiAmpRunData)


class EoCtiData(EoCalib):

    SCHEMA_CLASS = EoCtiDataSchemaV0

    _OBSTYPE = 'bias'
    _SCHEMA = SCHEMA_CLASS.fullName()
    _VERSION = SCHEMA_CLASS.version()

    def __init__(self, **kwargs):
        super(EoCtiData, self).__init__(**kwargs)
        self.amps = self['amps']


@EoPlotMethod(EoCtiData, "serial_oscan_high", "slot", "cti", "Serial overscan: high flux")
def plotCTISerialHigh(obj):
    return nullFigure()

@EoPlotMethod(EoCtiData, "serial_oscan_low", "slot", "cti", "Serial overscan: low flux")
def plotCTISerialLow(obj):
    return nullFigure()

@EoPlotMethod(EoCtiData, "parallel_oscan_high", "slot", "cti", "Parallel overscan: high flux")
def plotCTIParallelHigh(obj):
    return nullFigure()

@EoPlotMethod(EoCtiData, "parallel_oscan_low", "slot", "cti", "Parallel overscan: low flux")
def plotCTIParallelLow(obj):
    return nullFigure()

@EoPlotMethod(EoCtiData, "serial_cti", "raft", "cti", "Serial CTI")
def plotCTISerialRaft(obj):
    return nullFigure()

@EoPlotMethod(EoCtiData, "parallel_cti", "raft", "cti", "Parallel CTI")
def plotCTIParallelRaft(obj):
    return nullFigure()

@EoPlotMethod(EoCtiData, "high_parallel_mosaic", "camera", "mosaic", "CTI high, parallel")
def plotCTIParallelHighMosaic(cameraDataDict):
    return nullFigure()

@EoPlotMethod(EoCtiData, "high_serial_mosaic", "camera", "mosaic", "CTI high, serial")
def plotCTISerialHighMosaic(cameraDataDict):
    return nullFigure()

@EoPlotMethod(EoCtiData, "low_parallel_mosaic", "camera", "mosaic", "CTI low, parallel")
def plotCTIParallelLowMosaic(cameraDataDict):
    return nullFigure()

@EoPlotMethod(EoCtiData, "low_serial_mosaic", "camera", "mosaic", "CTI low, serial")
def plotCTISerialLowMosaic(cameraDataDict):
    return nullFigure()

@EoPlotMethod(EoCtiData, "high_parallel_hist", "camera", "hist", "CTI high, parallel")
def plotCTIParallelHighHist(cameraDataDict):
    return nullFigure()

@EoPlotMethod(EoCtiData, "high_serial_hist", "camera", "hist", "CTI high, serial")
def plotCTISerialHighHist(cameraDataDict):
    return nullFigure()

@EoPlotMethod(EoCtiData, "low_parallel_hist", "camera", "hist", "CTI low, parallel")
def plotCTIParallelLowHist(cameraDataDict):
    return nullFigure()

@EoPlotMethod(EoCtiData, "low_serial_hist", "camera", "hist", "CTI low, serial")
def plotCTISerialLowHist(cameraDataDict):
    return nullFigure()


RegisterEoCalibSchema(EoCtiData)


AMPS = ["%02i" % i for i in range(16)]

EoCtiData.testData = dict(testCtor=dict(amps=AMPS, nAmp=len(AMPS)))
