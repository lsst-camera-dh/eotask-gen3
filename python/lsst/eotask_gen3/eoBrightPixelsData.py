# from lsst.ip.isr import IsrCalib

from .eoCalibTable import EoCalibField, EoCalibTableSchema, EoCalibTable, EoCalibTableHandle
from .eoCalib import EoCalibSchema, EoCalib, RegisterEoCalibSchema
from .eoPlotUtils import EoPlotMethod, nullFigure

__all__ = ["EoBrightPixelsAmpRunData",
           "EoBrightPixelsData"]


class EoBrightPixelsAmpRunDataSchemaV0(EoCalibTableSchema):
    """Schema definitions for output data for per-amp, per-run tables
    for EoBrightPixelsTask.

    These are just counts of the number of bad pixels and channels
    """
    TABLELENGTH = "nAmp"

    nBrightPixel = EoCalibField(name="NUM_BRIGHT_PIXELS", dtype=int)
    nBrightColumn = EoCalibField(name="NUM_BRIGHT_COLUMNS", dtype=int)


class EoBrightPixelsAmpRunData(EoCalibTable):
    """Container class and interface for per-amp, per-run tables
    for EoBrightPixelsTask."""

    SCHEMA_CLASS = EoBrightPixelsAmpRunDataSchemaV0

    def __init__(self, data=None, **kwargs):
        """C'tor, arguments are passed to base class.

        Class specialization just associates class properties with columns
        """
        super(EoBrightPixelsAmpRunData, self).__init__(data=data, **kwargs)
        self.nBrightPixel = self.table[self.SCHEMA_CLASS.nBrightPixel.name]
        self.nBrightColumn = self.table[self.SCHEMA_CLASS.nBrightColumn.name]


class EoBrightPixelsDataSchemaV0(EoCalibSchema):
    """Schema definitions for output data for for EoBrightPixelsTask

    This defines correct versions of the sub-tables"""

    amps = EoCalibTableHandle(tableName="amps",
                              tableClass=EoBrightPixelsAmpRunData)


class EoBrightPixelsData(EoCalib):
    """Container class and interface for EoBrightPixelsTask outputs."""

    SCHEMA_CLASS = EoBrightPixelsDataSchemaV0

    _OBSTYPE = 'bias'
    _SCHEMA = SCHEMA_CLASS.fullName()
    _VERSION = SCHEMA_CLASS.version()

    def __init__(self, **kwargs):
        """C'tor, arguments are passed to base class.

        Class specialization just associates instance properties with
        sub-tables
        """
        super(EoBrightPixelsData, self).__init__(**kwargs)
        self.amps = self['amps']


@EoPlotMethod(EoBrightPixelsData, "pixels_mosaic", "camera", "mosaic", "Bright pixels per AMP")
def plotBrightPixelMosaic(cameraDataDict, cameraObj):
    return nullFigure()


@EoPlotMethod(EoBrightPixelsData, "columns_mosaic", "camera", "mosaic", "Bright columns per AMP")
def plotBrightColumnMosaic(cameraDataDict, cameraObj):
    return nullFigure()


@EoPlotMethod(EoBrightPixelsData, "pixels_hist", "camera", "hist", "Bright pixels per AMP")
def plotBrightPixelHist(cameraDataDict, cameraObj):
    return nullFigure()


@EoPlotMethod(EoBrightPixelsData, "columns_hist", "camera", "hist", "Bright columns per AMP")
def plotBrightColumnHist(cameraDataDict, cameraObj):
    return nullFigure()


RegisterEoCalibSchema(EoBrightPixelsData)

AMPS = ["%02i" % i for i in range(16)]
EoBrightPixelsData.testData = dict(testCtor=dict(nAmp=len(AMPS)))
