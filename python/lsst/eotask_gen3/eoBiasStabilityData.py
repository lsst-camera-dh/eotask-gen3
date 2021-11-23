# from lsst.ip.isr import IsrCalib

import numpy as np

from .eoCalibTable import EoCalibField, EoCalibTableSchema, EoCalibTable, EoCalibTableHandle
from .eoCalib import EoCalibSchema, EoCalib, RegisterEoCalibSchema
from .eoPlotUtils import EoPlotMethod, nullFigure

import matplotlib.pyplot as plt

__all__ = ["EoBiasStabilityAmpExpData",
           "EoBiasStabilityDetExpData",
           "EoBiasStabilityData"]


class EoBiasStabilityAmpExpDataSchemaV0(EoCalibTableSchema):
    """Schema definitions for output data for per-amp, per-exposure tables
    for EoBiasStabilityTask.

    These are summary statistics from the amplifier data.
    """

    TABLELENGTH = "nExposure"

    mean = EoCalibField(name="MEAN", dtype=float, unit='adu')
    stdev = EoCalibField(name="STDEV", dtype=float, unit='adu')
    rowMedian = EoCalibField(name="ROW_MEDIAN", dtype=float, unit='adu', shape=['nRow'])


class EoBiasStabilityAmpExpData(EoCalibTable):
    """Container class and interface for per-amp, per-exposure tables
    for EoBiasStabilityTask."""

    SCHEMA_CLASS = EoBiasStabilityAmpExpDataSchemaV0

    def __init__(self, data=None, **kwargs):
        """C'tor, arguments are passed to base class.

        This just associates class properties with columns
        """
        super(EoBiasStabilityAmpExpData, self).__init__(data=data, **kwargs)
        self.mean = self.table[self.SCHEMA_CLASS.mean.name]
        self.stdev = self.table[self.SCHEMA_CLASS.stdev.name]
        self.rowMedian = self.table[self.SCHEMA_CLASS.rowMedian.name]


class EoBiasStabilityDetExpDataSchemaV0(EoCalibTableSchema):
    """Schema definitions for output data for per-detector, per-exposure table
    for EoBiasStabilityTask.

    These are copied from the EO-analysis-jobs code and in part
    are retained to allow for possible conversion of old data.

    Note that we are not actually accessing the temperatures, and that
    the other data actually discernable from the dataId, but having
    them here makes it easier to make plots of trends.
    """

    TABLELENGTH = "nExposure"

    seqnum = EoCalibField(name="SEQNUM", dtype=int)
    mjd = EoCalibField(name="MJD", dtype=float)
    temp = EoCalibField(name="TEMP", dtype=float, shape=["nTemp"])


class EoBiasStabilityDetExpData(EoCalibTable):
    """Container class and interface for per-amp, per-exposure table
    for EoBiasStabilityTask."""

    SCHEMA_CLASS = EoBiasStabilityDetExpDataSchemaV0

    def __init__(self, data=None, **kwargs):
        """C'tor, arguments are passed to base class.

        This just associates class properties with columns
        """
        super(EoBiasStabilityDetExpData, self).__init__(data=data, **kwargs)
        self.seqnum = self.table[self.SCHEMA_CLASS.seqnum.name]
        self.mjd = self.table[self.SCHEMA_CLASS.mjd.name]
        self.temp = self.table[self.SCHEMA_CLASS.temp.name]


class EoBiasStabilityDataSchemaV0(EoCalibSchema):
    """Schema definitions for output data for for EoBiasStabilityTask

    This defines correct versions of the sub-tables"""

    ampExp = EoCalibTableHandle(tableName="ampExp_{key}",
                                tableClass=EoBiasStabilityAmpExpData,
                                multiKey="amps")

    detExp = EoCalibTableHandle(tableName="detExp",
                                tableClass=EoBiasStabilityDetExpData)


class EoBiasStabilityData(EoCalib):
    """Container class and interface for EoBiasStabilityTask outputs."""

    SCHEMA_CLASS = EoBiasStabilityDataSchemaV0

    _OBSTYPE = 'bias'
    _SCHEMA = SCHEMA_CLASS.fullName()
    _VERSION = SCHEMA_CLASS.version()

    def __init__(self, **kwargs):
        """C'tor, arguments are passed to base class.

        Class specialization just associates instance properties with
        sub-tables
        """
        super(EoBiasStabilityData, self).__init__(**kwargs)
        self.ampExp = self['ampExp']
        self.detExp = self['detExp']


@EoPlotMethod(EoBiasStabilityData, "serial_profiles", "slot",
              "BiasStability", "Bias frame amp-wise mean vs time")
def plotDetBiasStability(obj):
    """Make and return a figure with the bias stability
    curves for all the amps on one CCD

    Parameters
    ----------
    obj : `EoBiasStabilityData`
        The data being plotted

    Returns
    -------
    fig : `matplotlib.Figure`
        The generated figure
    """
    fig = plt.figure(figsize=(16, 16))
    ax = {amp: fig.add_subplot(4, 4, amp) for amp in range(1, 17)}
    title = 'median signal (ADU) vs column'
    plt.suptitle(title)
    plt.tight_layout(rect=(0, 0, 1, 0.95))
    ampExpData = obj.ampExp
    for iamp, ampData in enumerate(ampExpData.values()):
        imarr = ampData.rowMedian
        ax[iamp+1].plot(np.array([range(imarr.shape[1])]*imarr.shape[0]).T, imarr.T)
        ax[iamp+1].annotate(f'amp {iamp+1}', (0.5, 0.95), xycoords='axes fraction', ha='center')
    return fig


@EoPlotMethod(EoBiasStabilityData, "mean", "raft", "BiasStability", "Bias frame amp-wise mean vs time")
def plotDetBiasStabilityMean(raftDataDict):
    return nullFigure()


@EoPlotMethod(EoBiasStabilityData, "stdev", "raft", "BiasStability", "Bias frame amp-wise stdev vs time")
def plotDetBiasStabilityStdev(raftDataDict):
    return nullFigure()


RegisterEoCalibSchema(EoBiasStabilityData)


AMPS = ["%02i" % i for i in range(16)]
NEXPOSURE = 10
NTEMP = 10
NROW = 4000
EoBiasStabilityData.testData = dict(testCtor=dict(amps=AMPS, nRow=NROW, nExposure=NEXPOSURE, nTemp=NTEMP))
