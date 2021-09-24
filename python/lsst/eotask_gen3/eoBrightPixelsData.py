# from lsst.ip.isr import IsrCalib

from .eoCalibTable import EoCalibField, EoCalibTableSchema, EoCalibTable, EoCalibTableHandle
from .eoCalib import EoCalibSchema, EoCalib, RegisterEoCalibSchema
from .eoPlotUtils import EoPlotMethod, nullFigure

__all__ = ["EoBrightPixelsAmpRunData",
           "EoBrightPixelsData"]


class EoBrightPixelsAmpRunDataSchemaV0(EoCalibTableSchema):

    TABLELENGTH = "nAmp"

    nBrightPixel = EoCalibField(name="NUM_BRIGHT_PIXELS", dtype=int)
    nBrightColumn = EoCalibField(name="NUM_BRIGHT_COLUMNS", dtype=int)


class EoBrightPixelsAmpRunData(EoCalibTable):

    SCHEMA_CLASS = EoBrightPixelsAmpRunDataSchemaV0

    def __init__(self, data=None, **kwargs):
        super(EoBrightPixelsAmpRunData, self).__init__(data=data, **kwargs)
        self.nBrightPixel = self.table[self.SCHEMA_CLASS.nBrightPixel.name]
        self.nBrightColumn = self.table[self.SCHEMA_CLASS.nBrightColumn.name]


class EoBrightPixelsDataSchemaV0(EoCalibSchema):

    amps = EoCalibTableHandle(tableName="amps",
                              tableClass=EoBrightPixelsAmpRunData)


class EoBrightPixelsData(EoCalib):

    SCHEMA_CLASS = EoBrightPixelsDataSchemaV0

    _OBSTYPE = 'bias'
    _SCHEMA = SCHEMA_CLASS.fullName()
    _VERSION = SCHEMA_CLASS.version()

    def __init__(self, **kwargs):
        super(EoBrightPixelsData, self).__init__(**kwargs)
        self.amps = self['amps']


@EoPlotMethod(EoBrightPixelsData, "pixels_mosaic", "camera", "mosaic", "Bright pixels per AMP")
def plotBrightPixelMosaic(cameraDataDict):
    return nullFigure()

@EoPlotMethod(EoBrightPixelsData, "columns_mosaic", "camera", "mosaic", "Bright columns per AMP")
def plotBrightColumnMosaic(cameraDataDict):
    return nullFigure()

@EoPlotMethod(EoBrightPixelsData, "pixels_hist", "camera", "hist", "Bright pixels per AMP")
def plotBrightPixelHist(cameraDataDict):
    return nullFigure()

@EoPlotMethod(EoBrightPixelsData, "columns_hist", "camera", "hist", "Bright columns per AMP")
def plotBrightColumnHist(cameraDataDict):
    return nullFigure()


RegisterEoCalibSchema(EoBrightPixelsData)

AMPS = ["%02i" % i for i in range(16)]
EoBrightPixelsData.testData = dict(testCtor=dict(nAmp=len(AMPS)))
