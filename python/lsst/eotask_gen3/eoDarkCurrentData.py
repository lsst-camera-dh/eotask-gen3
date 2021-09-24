# from lsst.ip.isr import IsrCalib

from .eoCalibTable import EoCalibField, EoCalibTableSchema, EoCalibTable, EoCalibTableHandle
from .eoCalib import EoCalibSchema, EoCalib, RegisterEoCalibSchema
from .eoPlotUtils import EoSlotPlotMethod, EoRaftPlotMethod, EoCameraPlotMethod, nullFigure

__all__ = ["EoDarkCurrentAmpRunData",
           "EoDarkCurrentData"]


class EoDarkCurrentAmpRunDataSchemaV0(EoCalibTableSchema):

    TABLELENGTH = "nAmp"

    darkCurrent95 = EoCalibField(name="DARK_CURRENT_95", dtype=float, unit='electron/s')
    darkCurrentMedian = EoCalibField(name="DARK_CURRENT_MEDIAN", dtype=float, unit='electron/s')


class EoDarkCurrentAmpRunData(EoCalibTable):

    SCHEMA_CLASS = EoDarkCurrentAmpRunDataSchemaV0

    def __init__(self, data=None, **kwargs):
        super(EoDarkCurrentAmpRunData, self).__init__(data=None, **kwargs)
        self.darkCurrent95 = self.table[self.SCHEMA_CLASS.darkCurrent95.name]
        self.darkCurrentMedian = self.table[self.SCHEMA_CLASS.darkCurrentMedian.name]


class EoDarkCurrentDataSchemaV0(EoCalibSchema):

    amps = EoCalibTableHandle(tableName="amps",
                              tableClass=EoDarkCurrentAmpRunData)


class EoDarkCurrentData(EoCalib):

    SCHEMA_CLASS = EoDarkCurrentDataSchemaV0

    _OBSTYPE = 'dark'
    _SCHEMA = SCHEMA_CLASS.fullName()
    _VERSION = SCHEMA_CLASS.version()

    def __init__(self, **kwargs):
        super(EoDarkCurrentData, self).__init__(**kwargs)
        self.amps = self['amps']


@EoSlotPlotMethod(EoDarkCurrentData, "noise", "Dark Current")
def plotSlotNoise(obj):
    return nullFigure()

@EoRaftPlotMethod(EoDarkCurrentData, "noise", "Dark Current")
def plotRaftNoise(raftDataDict):
    return nullFigure()

@EoCameraPlotMethod(EoDarkCurrentData, "95CL", "Dark Current")
def plotCamera95CL(cameraDataDict):
    return nullFigure()

RegisterEoCalibSchema(EoDarkCurrentData)


AMPS = ["%02i" % i for i in range(16)]
EoDarkCurrentData.testData = dict(testCtor=dict(amps=AMPS, nAmp=len(AMPS)))
