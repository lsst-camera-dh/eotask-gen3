# from lsst.ip.isr import IsrCalib

import numpy as np

from .eoCalibTable import EoCalibField, EoCalibTableSchema, EoCalibTable, EoCalibTableHandle
from .eoCalib import EoCalibSchema, EoCalib, RegisterEoCalibSchema
from .eoPlotUtils import *

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
    fig, ax = plot4x4('(Sensor, Run)', 'column', 'median signal (ADU)')
    ampExpData = obj.ampExp
    for iamp, ampData in enumerate(ampExpData.values()):
        imarr = ampData.rowMedian
        ax[iamp+1].plot(np.array([range(imarr.shape[1])]*imarr.shape[0]).T, imarr.T)
    return fig


@EoPlotMethod(EoBiasStabilityData, "mean", "raft", "BiasStability", "Bias frame amp-wise mean vs time")
def plotDetBiasStabilityMean(raftDataDict):
    """Make and return a figure with the bias mean
    curves over time for all the amps on each CCD

    Parameters
    ----------
    raftDataDict : `OrderedDict`
        Dictionary of the data being plotted,
        one entry for each CCD, each pointing to
        a `BiasStabilityData` object

    Returns
    -------
    fig : `matplotlib.Figure`
        The generated figure
    """
    fig, ax = plot3x3('(Raft_Run), bias stability, mean signal', f'MJD - ', 'Mean signal (ADU)')
    
    for ccd in raftDataDict:
        obj = raftDataDict[ccd]
        ampExpData = obj.ampExp
        detExpData = obj.detExp
        date = int(detExpData.mjd[0]) #date in MJD
        times = detExpData.mjd - date
        
        moreColors(ax[ccd])
        for amp, ampData in ampExpData.items():
            means = ampData.mean
            ax[ccd].scatter(times, means, label=amp[-3:])
        ax[ccd].legend()
    tempAx = fig.axes[-1]
    tempAx.set_xlabel(tempAx.get_xlabel() + str(date))
    return fig


@EoPlotMethod(EoBiasStabilityData, "stdev", "raft", "BiasStability", "Bias frame amp-wise stdev vs time")
def plotDetBiasStabilityStdev(raftDataDict):
    """Make and return a figure with the bias stdev
    curves over time for all the amps on each CCD

    Parameters
    ----------
    raftDataDict : `OrderedDict`
        Dictionary of the data being plotted,
        one entry for each CCD, each pointing to
        a `BiasStabilityData` object

    Returns
    -------
    fig : `matplotlib.Figure`
        The generated figure
    """
    fig, ax = plot3x3('(Raft_Run), bias stability, signal standard deviation', f'MJD - ', 'Signal stdev (ADU)')
    
    for ccd in raftDataDict:
        obj = raftDataDict[ccd]
        ampExpData = obj.ampExp
        detExpData = obj.detExp
        date = int(detExpData.mjd[0]) #date in MJD
        times = detExpData.mjd - date
        
        moreColors(ax[ccd])
        
        for amp, ampData in ampExpData.items():
            stdevs = ampData.stdev
            ax[ccd].scatter(times, stdevs, label=amp[-3:])
        ax[ccd].legend()
    tempAx = fig.axes[-1]
    tempAx.set_xlabel(tempAx.get_xlabel() + str(date))
    return fig


RegisterEoCalibSchema(EoBiasStabilityData)


AMPS = ["%02i" % i for i in range(16)]
NEXPOSURE = 10
NTEMP = 10
NROW = 4000
EoBiasStabilityData.testData = dict(testCtor=dict(amps=AMPS, nRow=NROW, nExposure=NEXPOSURE, nTemp=NTEMP))
