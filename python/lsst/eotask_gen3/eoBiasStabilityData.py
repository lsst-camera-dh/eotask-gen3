# from lsst.ip.isr import IsrCalib

from .eoCalibTable import EoCalibField, EoCalibTableSchema, EoCalibTable, EoCalibTableHandle
from .eoCalib import EoCalibSchema, EoCalib, RegisterEoCalibSchema

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

    def makeDetFigures(self, baseName):
        """ Make a set of matplotlib figures for this detector """
        oDict = OrderedDict()
        oDict['%s_bias_serial_profiles' % baseName] = self.plotDetBiasStabilty()
        
    def plotDetBiasStabilty(self):
        fig = plt.figure(figsize=(16, 16))
        xlabelAmps = (13, 14, 15, 16)
        ylabelAmps = (1, 5, 9, 13)
        ax = {amp: fig.add_subplot(4, 4, amp) for amp in range(1, 17)}
        title = 'median signal (ADU) vs column'
        plt.suptitle(title)
        plt.tight_layout(rect=(0, 0, 1, 0.95))
        ampExpData = self.ampExpsoure
        for iamp, ampData in enumerate(ampExpData.values()):
            imarr = ampData.rowMedian
            ax[amp].plot(range(imarr.shape[1]), np.median(imarr, axis=0))            
            ax[amp].annotate(f'amp {iamp}', (0.5, 0.95), xycoords='axes fraction', ha='center')
        return fig
            

RegisterEoCalibSchema(EoBiasStabilityData)


AMPS = ["%02i" % i for i in range(16)]
NEXPOSURE = 10
NTEMP = 10
EoBiasStabilityData.testData = dict(testCtor=dict(amps=AMPS, nExposure=NEXPOSURE, nTemp=NTEMP))
