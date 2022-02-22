# from lsst.ip.isr import IsrCalib

from .eoCalibTable import EoCalibField, EoCalibTableSchema, EoCalibTable, EoCalibTableHandle
from .eoCalib import EoCalibSchema, EoCalib, RegisterEoCalibSchema
from .eoPlotUtils import *

# TEMPORARY, UNTIL THE FUNCTION IS MERGED TO THE MAIN BRANCH
from .TEMPafwutils import plotAmpFocalPlane

__all__ = ["EoDarkPixelsAmpRunData",
           "EoDarkPixelsData"]


class EoDarkPixelsAmpRunDataSchemaV0(EoCalibTableSchema):
    """Schema definitions for output data for per-amp, per-run tables
    for EoDarkPixelsTask.

    These are just counts of the number of bad pixels and channels
    """

    TABLELENGTH = "nAmp"

    nDarkPixel = EoCalibField(name="NUM_DARK_PIXELS", dtype=int)
    nDarkColumn = EoCalibField(name="NUM_DARK_COLUMNS", dtype=int)


class EoDarkPixelsAmpRunData(EoCalibTable):
    """Container class and interface for per-amp, per-run tables
    for EoDarkPixelsTask."""

    SCHEMA_CLASS = EoDarkPixelsAmpRunDataSchemaV0

    def __init__(self, data=None, **kwargs):
        """C'tor, arguments are passed to base class.

        This just associates class properties with columns
        """
        super(EoDarkPixelsAmpRunData, self).__init__(data=data, **kwargs)
        self.nDarkPixel = self.table[self.SCHEMA_CLASS.nDarkPixel.name]
        self.nDarkColumn = self.table[self.SCHEMA_CLASS.nDarkColumn.name]


class EoDarkPixelsDataSchemaV0(EoCalibSchema):
    """Schema definitions for output data for for EoDarkPixelsTask

    This defines correct versions of the sub-tables"""

    amps = EoCalibTableHandle(tableName="amps",
                              tableClass=EoDarkPixelsAmpRunData)


class EoDarkPixelsData(EoCalib):
    """Container class and interface for EoDarkPixelsTask outputs."""

    SCHEMA_CLASS = EoDarkPixelsDataSchemaV0

    _OBSTYPE = 'bias'
    _SCHEMA = SCHEMA_CLASS.fullName()
    _VERSION = SCHEMA_CLASS.version()

    def __init__(self, **kwargs):
        """C'tor, arguments are passed to base class.

        Class specialization just associates instance properties with
        sub-tables
        """
        super(EoDarkPixelsData, self).__init__(**kwargs)
        self.amps = self['amps']


@EoPlotMethod(EoDarkPixelsData, "pixels_mosaic", "camera", "mosaic", "Dark pixels per AMP")
def plotDarkPixelMosaic(cameraDataDict, cameraObj):
    dataValues = extractVals(cameraDataDict, 'nDarkPixel')
    plotAmpFocalPlane(cameraObj, level='AMPLIFIER', dataValues=dataValues, showFig=False,
                      figsize=(16,16), colorMapName='hot', colorScale='linear') # log colorScale?
    fig = plt.gcf()
    ax = plt.gca()
    ax.set_aspect('equal')
    ax.set_title('(Run) dark_pixels')
    return fig


@EoPlotMethod(EoDarkPixelsData, "column_mosaic", "camera", "mosaic", "Dark columns per AMP")
def plotDarkColumnMosaic(cameraDataDict, cameraObj):
    dataValues = extractVals(cameraDataDict, 'nDarkColumn')
    plotAmpFocalPlane(cameraObj, level='AMPLIFIER', dataValues=dataValues, showFig=False,
                      figsize=(16,16), colorMapName='hot', colorScale='linear') # log colorScale?
    fig = plt.gcf()
    ax = plt.gca()
    ax.set_aspect('equal')
    ax.set_title('(Run) dark_pixels')
    return fig


@EoPlotMethod(EoDarkPixelsData, "pixels_hist", "camera", "hist", "Dark pixels per AMP")
def plotDarkPixelHist(cameraDataDict, cameraObj):
    values = extractVals(cameraDataDict, 'nDarkPixel')
    fig, ax = plotHist(values, logx=True, title='(Run), dark_pixels', xlabel='dark_pixels')
    return fig


@EoPlotMethod(EoDarkPixelsData, "column_hist", "camera", "hist", "Dark columns per AMP")
def plotDarkColumnHist(cameraDataDict, cameraObj):
    values = extractVals(cameraDataDict, 'nDarkColumn')
    fig, ax = plotHist(values, logx=True, title='(Run), dark_columns', xlabel='dark_columns')
    return fig


RegisterEoCalibSchema(EoDarkPixelsData)

AMPS = ["%02i" % i for i in range(16)]
EoDarkPixelsData.testData = dict(testCtor=dict(nAmp=len(AMPS)))
