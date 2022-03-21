# from lsst.ip.isr import IsrCalib

from .eoCalibTable import EoCalibField, EoCalibTableSchema, EoCalibTable, EoCalibTableHandle
from .eoCalib import EoCalibSchema, EoCalib, RegisterEoCalibSchema
from .eoPlotUtils import *

# TEMPORARY, UNTIL THE FUNCTION IS MERGED TO THE MAIN BRANCH
from .TEMPafwutils import plotAmpFocalPlane

__all__ = ["EoTearingAmpExpData",
           "EoTearingData"]


class EoTearingAmpExpDataSchemaV0(EoCalibTableSchema):
    """Schema definitions for output data for per-amp, per-exposure tables
    for EoTearingTask.

    This is just the number of tearing detections
    """

    TABLELENGTH = 'nExposure'

    nDetection = EoCalibField(name="NDETECT", dtype=int)


class EoTearingAmpExpData(EoCalibTable):
    """Container class and interface for per-amp, per-exposure-pair tables
    for EoTearingTask."""

    SCHEMA_CLASS = EoTearingAmpExpDataSchemaV0

    def __init__(self, data=None, **kwargs):
        """C'tor, arguments are passed to base class.

        Class specialization just associates class properties with columns
        """
        super(EoTearingAmpExpData, self).__init__(data=data, **kwargs)
        self.nDetection = self.table[self.SCHEMA_CLASS.nDetection.name]
        
        
class EoTearingAmpRunDataSchemaV0(EoCalibTableSchema):
    """Schema definitions for output data for per-amp, per-run tables
    for EoTearingTask.
    This is counts of the number of tearing detections in the run
    """
    TABLELENGTH = "nAmp"
    
    nDetection = EoCalibField(name="NDETECT", dtype=int)
    
    
class EoTearingAmpRunData(EoCalibTable):
    """Container class and interface for per-amp, per-run tables
    for EoTearingTask."""

    SCHEMA_CLASS = EoTearingAmpRunDataSchemaV0

    def __init__(self, data=None, **kwargs):
        super(EoTearingAmpRunData, self).__init__(data=data, **kwargs)
        self.nDetection = self.table[self.SCHEMA_CLASS.nDetection.name]


class EoTearingDataSchemaV0(EoCalibSchema):
    """Schema definitions for output data for EoTearingTask

    This defines correct versions of the sub-tables"""

    ampExp = EoCalibTableHandle(tableName="ampExp_{key}",
                                tableClass=EoTearingAmpExpData,
                                multiKey="amps")
    
    amps = EoCalibTableHandle(tableName="amps",
                              tableClass=EoTearingAmpRunData)


class EoTearingData(EoCalib):
    """Container class and interface for EoTearingTask outputs."""

    SCHEMA_CLASS = EoTearingDataSchemaV0

    _OBSTYPE = 'flat'
    _SCHEMA = SCHEMA_CLASS.fullName()
    _VERSION = SCHEMA_CLASS.version()

    def __init__(self, **kwargs):
        """C'tor, arguments are passed to base class.

        Class specialization just associates instance properties with
        sub-tables
        """
        super(EoTearingData, self).__init__(**kwargs)
        self.ampExp = self['ampExp']
        self.amps = self['amps']


@EoPlotMethod(EoTearingData, "mosaic", "camera", "mosaic", "Tearing detections")
def plotTearingMosaic(cameraDataDict, cameraObj):
    dataValues = extractVals(cameraDataDict, 'nDetection')
    plotAmpFocalPlane(cameraObj, level='AMPLIFIER', dataValues=dataValues, showFig=False,
                      figsize=(16,16), colorMapName='hot', colorScale='linear')
    fig = plt.gcf()
    ax = plt.gca()
    ax.set_aspect('equal')
    ax.set_title('(Run) tearing_detections')
    return fig


@EoPlotMethod(EoTearingData, "hist", "camera", "hist", "Tearing detections")
def plotTearingHist(cameraDataDict, cameraObj):
    dataValues = extractVals(cameraDataDict, 'nDetection')
    fig, ax = plotHist(dataValues, logx=False, title='(Run), tearing_detections', xlabel='tearing_detections')
    return fig


@EoPlotMethod(EoTearingData, "divisadero_mosaic", "camera", "mosaic", "Divisadero max")
def plotDivisaderoMosaic(obj, cameraObj):
    return nullFigure()


@EoPlotMethod(EoTearingData, "divisadero_hist", "camera", "hist", "Divisadero max")
def plotDivisaderoHist(obj, cameraObj):
    return nullFigure()


@EoPlotMethod(EoTearingData, "divisadero", "raft", "divisadero", "Divisadero Tearing")
def plotDivisadero(obj):
    return nullFigure()


RegisterEoCalibSchema(EoTearingData)

AMPS = ["%02i" % i for i in range(16)]
NEXPOSURE = 10
EoTearingData.testData = dict(testCtor=dict(amps=AMPS, nAmp=len(AMPS), nExposure=NEXPOSURE))
