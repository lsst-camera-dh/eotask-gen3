# from lsst.ip.isr import IsrCalib

from .eoCalibTable import EoCalibField, EoCalibTableSchema, EoCalibTable, EoCalibTableHandle
from .eoCalib import EoCalibSchema, EoCalib, RegisterEoCalibSchema
from .eoPlotUtils import EoCameraPlotMethod, nullFigure

__all__ = ["EoDarkPixelsAmpRunData",
           "EoDarkPixelsData"]


class EoDarkPixelsAmpRunDataSchemaV0(EoCalibTableSchema):

    TABLELENGTH = "nAmp"

    nDarkPixel = EoCalibField(name="NUM_DARK_PIXELS", dtype=int)
    nDarkColumn = EoCalibField(name="NUM_DARK_COLUMNS", dtype=int)


class EoDarkPixelsAmpRunData(EoCalibTable):

    SCHEMA_CLASS = EoDarkPixelsAmpRunDataSchemaV0

    def __init__(self, data=None, **kwargs):
        super(EoDarkPixelsAmpRunData, self).__init__(data=data, **kwargs)
        self.nDarkPixel = self.table[self.SCHEMA_CLASS.nDarkPixel.name]
        self.nDarkColumn = self.table[self.SCHEMA_CLASS.nDarkColumn.name]


class EoDarkPixelsDataSchemaV0(EoCalibSchema):

    amps = EoCalibTableHandle(tableName="amps",
                              tableClass=EoDarkPixelsAmpRunData)


class EoDarkPixelsData(EoCalib):

    SCHEMA_CLASS = EoDarkPixelsDataSchemaV0

    _OBSTYPE = 'bias'
    _SCHEMA = SCHEMA_CLASS.fullName()
    _VERSION = SCHEMA_CLASS.version()

    def __init__(self, **kwargs):
        super(EoDarkPixelsData, self).__init__(**kwargs)
        self.amps = self['amps']


@EoCameraPlotMethod(EoDarkPixelsData, "pixels_mosaic", "Dark pixels per AMP")
def plotDarkPixelMosaic(cameraDataDict):
    return nullFigure()

@EoCameraPlotMethod(EoDarkPixelsData, "column_mosaic", "Dark columns per AMP")
def plotDarkColumnMosaic(cameraDataDict):
    return nullFigure()

@EoCameraPlotMethod(EoDarkPixelsData, "pixels_hist", "Dark pixels per AMP")
def plotDarkPixelHist(cameraDataDict):
    return nullFigure()

@EoCameraPlotMethod(EoDarkPixelsData, "column_hist", "Dark columns per AMP")
def plotDarkColumnHist(cameraDataDict):
    return nullFigure()


RegisterEoCalibSchema(EoDarkPixelsData)

AMPS = ["%02i" % i for i in range(16)]
EoDarkPixelsData.testData = dict(testCtor=dict(nAmp=len(AMPS)))
