# from lsst.ip.isr import IsrCalib

from .eoCalibTable import EoCalibField, EoCalibTableSchema, EoCalibTable, EoCalibTableHandle
from .eoCalib import EoCalibSchema, EoCalib, RegisterEoCalibSchema
from .eoPlotUtils import *

__all__ = ["EoPersistenceAmpExpData",
           "EoPersistenceData"]


class EoPersistenceAmpExpDataSchemaV0(EoCalibTableSchema):
    """Schema definitions for output data for per-amp, per-exposure tables
    for EoPersistenceTask.

    These are summary statistics about the signal in the imaging region
    """

    TABLELENGTH = "nExposure"

    mean = EoCalibField(name="MEAN", dtype=float, unit='adu')
    stdev = EoCalibField(name="STDEV", dtype=float, unit='adu')


class EoPersistenceAmpExpData(EoCalibTable):
    """Container class and interface for per-amp, per-exposure tables
    for EoPersistenceTask."""

    SCHEMA_CLASS = EoPersistenceAmpExpDataSchemaV0

    def __init__(self, data=None, **kwargs):
        """C'tor, arguments are passed to base class.

        Class specialization just associates class properties with columns
        """
        super(EoPersistenceAmpExpData, self).__init__(data=data, **kwargs)
        self.mean = self.table[self.SCHEMA_CLASS.mean.name]
        self.stdev = self.table[self.SCHEMA_CLASS.stdev.name]


class EoPersistenceDataSchemaV0(EoCalibSchema):
    """Schema definitions for output data for EoPersistenceTask

    This defines correct versions of the sub-tables"""

    ampExp = EoCalibTableHandle(tableName="ampExp_{key}",
                                tableClass=EoPersistenceAmpExpData,
                                multiKey="amps")


class EoPersistenceData(EoCalib):
    """Container class and interface for EoPersistenceTask outputs."""

    SCHEMA_CLASS = EoPersistenceDataSchemaV0

    _OBSTYPE = 'bias'
    _SCHEMA = SCHEMA_CLASS.fullName()
    _VERSION = SCHEMA_CLASS.version()

    def __init__(self, **kwargs):
        """C'tor, arguments are passed to base class.

        Class specialization just associates instance properties with
        sub-tables
        """
        super(EoPersistenceData, self).__init__(**kwargs)
        self.ampExp = self['ampExp']


@EoPlotMethod(EoPersistenceData, "persistence", "slot", "persistence", "Persistence analysis")
def plotPersistence(obj):
    fig = plt.figure(figsize=(10,8))
    moreColors(plt.gca())
    
    ampExpData = obj.ampExp
    seqnums = range(len(ampExpData['ampExp_C10'].mean)) # temporary, until this is built into the class
    for amp,ampData in ampExpData.items():
        plt.scatter(seqnums, ampData.mean, label=amp[-3:])
    
    plt.legend(ncol=2)
    plt.xticks(seqnums)
    plt.xlabel('Sequence number')
    plt.ylabel('Mean residual signal (ADU)')
    plt.title('(Raft, slot, run) persistence test')
    return fig


RegisterEoCalibSchema(EoPersistenceData)


AMPS = ["%02i" % i for i in range(16)]
NEXPOSURE = 10
EoPersistenceData.testData = dict(testCtor=dict(amps=AMPS, nExposure=NEXPOSURE))
