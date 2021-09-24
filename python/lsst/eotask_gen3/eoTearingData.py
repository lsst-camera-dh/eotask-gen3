# from lsst.ip.isr import IsrCalib

from .eoCalibTable import EoCalibField, EoCalibTableSchema, EoCalibTable, EoCalibTableHandle
from .eoCalib import EoCalibSchema, EoCalib, RegisterEoCalibSchema
from .eoPlotUtils import EoSlotPlotMethod, EoRaftPlotMethod, EoCameraPlotMethod, nullFigure

__all__ = ["EoTearingAmpExpData",
           "EoTearingData"]


class EoTearingAmpExpDataSchemaV0(EoCalibTableSchema):

    TABLELENGTH = 'nExposure'

    nDetection = EoCalibField(name="NDETECT", dtype=int)


class EoTearingAmpExpData(EoCalibTable):

    SCHEMA_CLASS = EoTearingAmpExpDataSchemaV0

    def __init__(self, data=None, **kwargs):
        super(EoTearingAmpExpData, self).__init__(data=data, **kwargs)
        self.nDetection = self.table[self.SCHEMA_CLASS.nDetection.name]


class EoTearingDataSchemaV0(EoCalibSchema):

    ampExp = EoCalibTableHandle(tableName="ampExp_{key}",
                                tableClass=EoTearingAmpExpData,
                                multiKey="amps")


class EoTearingData(EoCalib):

    SCHEMA_CLASS = EoTearingDataSchemaV0

    _OBSTYPE = 'flat'
    _SCHEMA = SCHEMA_CLASS.fullName()
    _VERSION = SCHEMA_CLASS.version()

    def __init__(self, **kwargs):
        super(EoTearingData, self).__init__(**kwargs)
        self.ampExp = self['ampExp']


@EoCameraPlotMethod(EoTearingData, "mosaic", "Tearing detections")
def plotTearingMosaic(obj):
    return nullFigure()

@EoCameraPlotMethod(EoTearingData, "hist", "Tearing detections")
def plotTearingHist(obj):
    return nullFigure()


RegisterEoCalibSchema(EoTearingData)

AMPS = ["%02i" % i for i in range(16)]
NEXPOSURE = 10
EoTearingData.testData = dict(testCtor=dict(amps=AMPS, nAmp=len(AMPS), nExposure=NEXPOSURE))
