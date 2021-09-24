# from lsst.ip.isr import IsrCalib

import numpy as np

from .eoCalibTable import EoCalibField, EoCalibTableSchema, EoCalibTable, EoCalibTableHandle
from .eoCalib import EoCalibSchema, EoCalib, RegisterEoCalibSchema
from .eoPlotUtils import EoSlotPlotMethod, EoRaftPlotMethod, nullFigure

import matplotlib.pyplot as plt

__all__ = ["EoBiasStabilityAmpExpData",
           "EoBiasStabilityDetExpData",
           "EoBiasStabilityData"]


class EoBiasStabilityAmpExpDataSchemaV0(EoCalibTableSchema):

    TABLELENGTH = "nExposure"

    mean = EoCalibField(name="MEAN", dtype=float, unit='adu')
    stdev = EoCalibField(name="STDEV", dtype=float, unit='adu')
    rowMedian = EoCalibField(name="ROW_MEDIAN", dtype=float, unit='adu', shape=['nRow'])
    

class EoBiasStabilityAmpExpData(EoCalibTable):

    SCHEMA_CLASS = EoBiasStabilityAmpExpDataSchemaV0

    def __init__(self, data=None, **kwargs):
        super(EoBiasStabilityAmpExpData, self).__init__(data=data, **kwargs)
        self.mean = self.table[self.SCHEMA_CLASS.mean.name]
        self.stdev = self.table[self.SCHEMA_CLASS.stdev.name]
        self.rowMedian = self.table[self.SCHEMA_CLASS.rowMedian.name]


class EoBiasStabilityDetExpDataSchemaV0(EoCalibTableSchema):

    TABLELENGTH = "nExposure"

    seqnum = EoCalibField(name="SEQNUM", dtype=int)
    mjd = EoCalibField(name="MJD", dtype=float)
    temp = EoCalibField(name="TEMP", dtype=float, shape=["nTemp"])


class EoBiasStabilityDetExpData(EoCalibTable):

    SCHEMA_CLASS = EoBiasStabilityDetExpDataSchemaV0

    def __init__(self, data=None, **kwargs):
        super(EoBiasStabilityDetExpData, self).__init__(data=data, **kwargs)
        self.seqnum = self.table[self.SCHEMA_CLASS.seqnum.name]
        self.mjd = self.table[self.SCHEMA_CLASS.mjd.name]
        self.temp = self.table[self.SCHEMA_CLASS.temp.name]


class EoBiasStabilityDataSchemaV0(EoCalibSchema):

    ampExposure = EoCalibTableHandle(tableName="ampExp_{key}",
                                     tableClass=EoBiasStabilityAmpExpData,
                                     multiKey="amps")

    detExposure = EoCalibTableHandle(tableName="detExp",
                                     tableClass=EoBiasStabilityDetExpData)


class EoBiasStabilityData(EoCalib):

    SCHEMA_CLASS = EoBiasStabilityDataSchemaV0

    _OBSTYPE = 'bias'
    _SCHEMA = SCHEMA_CLASS.fullName()
    _VERSION = SCHEMA_CLASS.version()

    def __init__(self, **kwargs):
        super(EoBiasStabilityData, self).__init__(**kwargs)
        self.ampExposure = self['ampExposure']
        self.detExposure = self['detExposure']
        

@EoSlotPlotMethod(EoBiasStabilityData, "serial_profiles", "Bias frame amp-wise mean vs time")
def plotDetBiasStabilty(obj):
    fig = plt.figure(figsize=(10, 10))
    xlabelAmps = (13, 14, 15, 16)
    ylabelAmps = (1, 5, 9, 13)
    ax = {amp: fig.add_subplot(4, 4, amp) for amp in range(1, 17)}
    title = 'median signal (ADU) vs column'
    plt.suptitle(title)
    plt.tight_layout(rect=(0, 0, 1, 0.95))
    ampExpData = obj.ampExposure
    for iamp, ampData in enumerate(ampExpData.values()):
        imarr = ampData.rowMedian
        ax[iamp+1].plot(range(imarr.shape[1]), np.median(imarr, axis=0))            
        ax[iamp+1].annotate(f'amp {iamp}', (0.5, 0.95), xycoords='axes fraction', ha='center')
    return fig

@EoRaftPlotMethod(EoBiasStabilityData, "mean", "Bias frame amp-wise mean vs time")
def plotDetBiasStabiltyMean(raftDataDict):
    return nullFigure()

@EoRaftPlotMethod(EoBiasStabilityData, "stdev", "Bias frame amp-wise stdev vs time")
def plotDetBiasStabiltyStdev(raftDataDict):
    return nullFigure()

            
RegisterEoCalibSchema(EoBiasStabilityData)


AMPS = ["%02i" % i for i in range(16)]
NEXPOSURE = 10
NTEMP = 10
EoBiasStabilityData.testData = dict(testCtor=dict(amps=AMPS, nExposure=NEXPOSURE, nTemp=NTEMP))
