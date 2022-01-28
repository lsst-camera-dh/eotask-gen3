# from lsst.ip.isr import IsrCalib

from .eoCalibTable import EoCalibField, EoCalibTableSchema, EoCalibTable, EoCalibTableHandle
from .eoCalib import EoCalibSchema, EoCalib, RegisterEoCalibSchema
from .eoPlotUtils import EoPlotMethod, nullFigure

__all__ = ["EoCtiAmpRunData",
           "EoCtiData"]


class EoCtiAmpRunDataSchemaV0(EoCalibTableSchema):
    """Schema definitions for output data for per-amp, per-run tables
    for EoBrightPixelsTask.

    These are just the serial and parallel charge transfer inefficiency
    estimates and their errros
    """

    TABLELENGTH = "nAmp"

    ctiSerial = EoCalibField(name="CTI_SERIAL", dtype=float)
    ctiSerialError = EoCalibField(name="CTI_SERIAL_ERR", dtype=float)
    ctiParallel = EoCalibField(name="CTI_PARALLEL", dtype=float)
    ctiParallelError = EoCalibField(name="CTI_PARALLEL_ERR", dtype=float)


class EoCtiAmpRunData(EoCalibTable):
    """Container class and interface for EoCtiTask outputs."""

    SCHEMA_CLASS = EoCtiAmpRunDataSchemaV0

    def __init__(self, data=None, **kwargs):
        """C'tor, arguments are passed to base class.

        This just associates class properties with columns
        """
        super(EoCtiAmpRunData, self).__init__(data=None, **kwargs)
        self.ctiSerial = self.table[self.SCHEMA_CLASS.ctiSerial.name]
        self.ctiSerialError = self.table[self.SCHEMA_CLASS.ctiSerialError.name]
        self.ctiParallel = self.table[self.SCHEMA_CLASS.ctiParallel.name]
        self.ctiParallelError = self.table[self.SCHEMA_CLASS.ctiParallelError.name]


class EoCtiDataSchemaV0(EoCalibSchema):
    """Schema definitions for output data for for EoCtiTask

    This defines correct versions of the sub-tables"""

    amps = EoCalibTableHandle(tableName="amps",
                              tableClass=EoCtiAmpRunData)


class EoCtiData(EoCalib):
    """Container class and interface for EoCtiTask outputs."""

    SCHEMA_CLASS = EoCtiDataSchemaV0

    _OBSTYPE = 'bias'
    _SCHEMA = SCHEMA_CLASS.fullName()
    _VERSION = SCHEMA_CLASS.version()

    def __init__(self, **kwargs):
        """C'tor, arguments are passed to base class.

        Class specialization just associates instance properties with
        sub-tables
        """
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
def plotCTIParallelHighMosaic(cameraDataDict, cameraObj):
    return nullFigure()


@EoPlotMethod(EoCtiData, "high_serial_mosaic", "camera", "mosaic", "CTI high, serial")
def plotCTISerialHighMosaic(cameraDataDict, cameraObj):
    return nullFigure()


@EoPlotMethod(EoCtiData, "low_parallel_mosaic", "camera", "mosaic", "CTI low, parallel")
def plotCTIParallelLowMosaic(cameraDataDict, cameraObj):
    return nullFigure()


@EoPlotMethod(EoCtiData, "low_serial_mosaic", "camera", "mosaic", "CTI low, serial")
def plotCTISerialLowMosaic(cameraDataDict, cameraObj):
    return nullFigure()


@EoPlotMethod(EoCtiData, "high_parallel_hist", "camera", "hist", "CTI high, parallel")
def plotCTIParallelHighHist(cameraDataDict, cameraObj):
    return nullFigure()


@EoPlotMethod(EoCtiData, "high_serial_hist", "camera", "hist", "CTI high, serial")
def plotCTISerialHighHist(cameraDataDict, cameraObj):
    return nullFigure()


@EoPlotMethod(EoCtiData, "low_parallel_hist", "camera", "hist", "CTI low, parallel")
def plotCTIParallelLowHist(cameraDataDict, cameraObj):
    return nullFigure()


@EoPlotMethod(EoCtiData, "low_serial_hist", "camera", "hist", "CTI low, serial")
def plotCTISerialLowHist(cameraDataDict, cameraObj):
    return nullFigure()


RegisterEoCalibSchema(EoCtiData)


AMPS = ["%02i" % i for i in range(16)]

EoCtiData.testData = dict(testCtor=dict(amps=AMPS, nAmp=len(AMPS)))
