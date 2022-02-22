# from lsst.ip.isr import IsrCalib

from .eoCalibTable import EoCalibField, EoCalibTableSchema, EoCalibTable, EoCalibTableHandle
from .eoCalib import EoCalibSchema, EoCalib, RegisterEoCalibSchema
from .eoPlotUtils import *

# TEMPORARY, UNTIL THE FUNCTION IS MERGED TO THE MAIN BRANCH
from .TEMPafwutils import plotAmpFocalPlane

__all__ = ["EoFlatPairAmpExpData",
           "EoFlatPairAmpRunData",
           "EoFlatPairDetExpData",
           "EoFlatPairData"]


class EoFlatPairAmpExpDataSchemaV0(EoCalibTableSchema):
    """Schema definitions for output data for per-amp, per-exposure-pair tables
    for EoFlatPairTask.

    These are the means signals from the two exposure,
    the mean of the two means, and the variance of the
    per-row means
    """

    TABLELENGTH = "nPair"

    signal = EoCalibField(name='SIGNAL', unit='electron')
    flat1Signal = EoCalibField(name='FLAT1_SIGNAL', unit='electron')
    flat2Signal = EoCalibField(name='FLAT2_SIGNAL', unit='electron')
    rowMeanVar = EoCalibField(name='ROW_MEAN_VAR', unit='electron**2')


class EoFlatPairAmpExpData(EoCalibTable):
    """Container class and interface for per-amp, per-exposure-pair tables
    for EoFlatPairTask."""

    SCHEMA_CLASS = EoFlatPairAmpExpDataSchemaV0

    def __init__(self, data=None, **kwargs):
        """C'tor, arguments are passed to base class.

        Class specialization just associates class properties with columns
        """
        super(EoFlatPairAmpExpData, self).__init__(data=data, **kwargs)
        self.signal = self.table[self.SCHEMA_CLASS.signal.name]
        self.flat1Signal = self.table[self.SCHEMA_CLASS.flat1Signal.name]
        self.flat2Signal = self.table[self.SCHEMA_CLASS.flat2Signal.name]
        self.rowMeanVar = self.table[self.SCHEMA_CLASS.rowMeanVar.name]


class EoFlatPairAmpRunDataSchemaV0(EoCalibTableSchema):
    """Schema definitions for output data for per-amp, per-run table
    for EoFlatPairTask.

    These are the quantities derived from fitting the signal v. photodiode
    curves
    """

    TABLELENGTH = 'nAmp'

    fullWell = EoCalibField(name="FULL_WELL", dtype=float, unit='adu')
    maxFracDev = EoCalibField(name="MAX_FRAC_DEV", dtype=float)
    rowMeanVarSlope = EoCalibField(name="ROW_MEAN_VAR_SLOPE", dtype=float)
    maxObservedSignal = EoCalibField(name="MAX_OBSERVED_SIGNAL", dtype=float, unit='adu')
    linearityTurnoff = EoCalibField(name="LINEARITY_TURNOFF", dtype=float, unit='adu')


class EoFlatPairAmpRunData(EoCalibTable):
    """Container class and interface for per-amp, per-run tables
    for EoFlatPairTask."""

    SCHEMA_CLASS = EoFlatPairAmpRunDataSchemaV0

    def __init__(self, data=None, **kwargs):
        super(EoFlatPairAmpRunData, self).__init__(data=data, **kwargs)
        self.fullWell = self.table[self.SCHEMA_CLASS.fullWell.name]
        self.maxFracDev = self.table[self.SCHEMA_CLASS.maxFracDev.name]
        self.rowMeanVarSlope = self.table[self.SCHEMA_CLASS.rowMeanVarSlope.name]
        self.maxObservedSignal = self.table[self.SCHEMA_CLASS.maxObservedSignal.name]
        self.linearityTurnoff = self.table[self.SCHEMA_CLASS.linearityTurnoff.name]


class EoFlatPairDetExpDataSchemaV0(EoCalibTableSchema):
    """Schema definitions for output data for per-ccd, per-exposure-pair table
    for EoFlatPairTask.

    The flux is computed from the photodiode data.

    As for the other quantities, these are copied from the
    EO-analysis-jobs code and in part
    are retained to allow for possible conversion of old data.

    Note that these data actually discernable from the dataId, but having
    them here makes it easier to make plots of trends.
    """

    TABLELENGTH = "nPair"

    flux = EoCalibField(name="FLUX", dtype=float)
    seqnum = EoCalibField(name="SEQNUM", dtype=int)
    dayobs = EoCalibField(name="DAYOBS", dtype=int)


class EoFlatPairDetExpData(EoCalibTable):
    """Container class and interface for per-amp, per-exposure-pair table
    for EoFlatPairTask."""

    SCHEMA_CLASS = EoFlatPairDetExpDataSchemaV0

    def __init__(self, data=None, **kwargs):
        """C'tor, arguments are passed to base class.

        Class specialization just associates class properties with columns
        """
        super(EoFlatPairDetExpData, self).__init__(data=data, **kwargs)
        self.flux = self.table[self.SCHEMA_CLASS.flux.name]
        self.seqnum = self.table[self.SCHEMA_CLASS.seqnum.name]
        self.dayobs = self.table[self.SCHEMA_CLASS.dayobs.name]


class EoFlatPairDataSchemaV0(EoCalibSchema):
    """Schema definitions for output data for EoFlatPairTask

    This defines correct versions of the sub-tables"""

    ampExp = EoCalibTableHandle(tableName="ampExp_{key}",
                                tableClass=EoFlatPairAmpExpData,
                                multiKey="amps")

    amps = EoCalibTableHandle(tableName="amps",
                              tableClass=EoFlatPairAmpRunData)

    detExp = EoCalibTableHandle(tableName="detExp",
                                tableClass=EoFlatPairDetExpData)


class EoFlatPairData(EoCalib):
    """Container class and interface for EoFlatPairTask outputs."""

    SCHEMA_CLASS = EoFlatPairDataSchemaV0

    _OBSTYPE = 'flat'
    _SCHEMA = SCHEMA_CLASS.fullName()
    _VERSION = SCHEMA_CLASS.version()

    def __init__(self, **kwargs):
        """C'tor, arguments are passed to base class.

        Class specialization just associates instance properties with
        sub-tables
        """
        super(EoFlatPairData, self).__init__(**kwargs)
        self.ampExp = self['ampExp']
        self.amps = self['amps']
        self.detExp = self['detExp']


@EoPlotMethod(EoFlatPairData, "row_means_variance", "slot", "Flat Pair", "Row means v. variance")
def plotRowMeanVariance(obj):
    return nullFigure()


@EoPlotMethod(EoFlatPairData, "full_well", "camera", "mosaic", "Full well")
def plotFullWellMosaic(cameraDataDict, cameraObj):
    dataValues = extractVals(cameraDataDict, 'fullWell')
    plotAmpFocalPlane(cameraObj, level='AMPLIFIER', dataValues=dataValues, showFig=False,
                      figsize=(16,16), colorMapName='hot', colorScale='linear')
    fig = plt.gcf()
    ax = plt.gca()
    ax.set_aspect('equal')
    ax.set_title('(Run) full_well (ADU)')
    return fig


@EoPlotMethod(EoFlatPairData, "max_frac_dev", "camera", "mosaic", "Max fractional deviation")
def plotMaxFracDevMosaic(cameraDataDict, cameraObj):
    dataValues = extractVals(cameraDataDict, 'maxFracDev')
    plotAmpFocalPlane(cameraObj, level='AMPLIFIER', dataValues=dataValues, showFig=False,
                      figsize=(16,16), colorMapName='hot', colorScale='linear')
    fig = plt.gcf()
    ax = plt.gca()
    ax.set_aspect('equal')
    ax.set_title('(Run) max_frac_dev')
    return fig


@EoPlotMethod(EoFlatPairData, "row_mean_var_slope", "camera", "mosaic", "Slope of rowwise-mean variance")
def plotRowMeanVarSlopeMosaic(cameraDataDict, cameraObj):
    dataValues = extractVals(cameraDataDict, 'rowMeanVarSlope')
    plotAmpFocalPlane(cameraObj, level='AMPLIFIER', dataValues=dataValues, showFig=False,
                      figsize=(16,16), colorMapName='hot', colorScale='linear')
    fig = plt.gcf()
    ax = plt.gca()
    ax.set_aspect('equal')
    ax.set_title('(Run) row_mean_var_slope')
    return fig


@EoPlotMethod(EoFlatPairData, "max_observed_signal", "camera", "mosaic", "Max observed signal")
def plotMaxObservedSignalMosaic(cameraDataDict, cameraObj):
    dataValues = extractVals(cameraDataDict, 'maxObservedSignal')
    plotAmpFocalPlane(cameraObj, level='AMPLIFIER', dataValues=dataValues, showFig=False,
                      figsize=(16,16), colorMapName='hot', colorScale='linear')
    fig = plt.gcf()
    ax = plt.gca()
    ax.set_aspect('equal')
    ax.set_title('(Run) max_observed_signal (ADU)')
    return fig


@EoPlotMethod(EoFlatPairData, "linearity_turnoff", "camera", "mosaic", "Linearity turnoff")
def plotLinearityTurnoffMosaic(cameraDataDict, cameraObj):
    dataValues = extractVals(cameraDataDict, 'linearityTurnoff')
    plotAmpFocalPlane(cameraObj, level='AMPLIFIER', dataValues=dataValues, showFig=False,
                      figsize=(16,16), colorMapName='hot', colorScale='linear')
    fig = plt.gcf()
    ax = plt.gca()
    ax.set_aspect('equal')
    ax.set_title('(Run) linearity_turnoff (ADU)')
    return fig


@EoPlotMethod(EoFlatPairData, "full_well_hist", "camera", "hist", "Full well")
def plotFullWellHist(cameraDataDict, cameraObj):
    values = extractVals(cameraDataDict, 'fullWell')
    fig, ax = plotHist(values, logx=False, title='(Run), full_well (ADU)', xlabel='full_well')
    return fig


@EoPlotMethod(EoFlatPairData, "max_frac_dev_hist", "camera", "hist", "Max fractional deviation")
def plotMaxFracDevHist(cameraDataDict, cameraObj):
    values = extractVals(cameraDataDict, 'maxFracDev')
    fig, ax = plotHist(values, logx=False, title='(Run), max_frac_dev', xlabel='max_frac_dev')
    return fig


@EoPlotMethod(EoFlatPairData, "row_mean_var_slope_hist", "camera", "hist", "Slope of rowwise-mean variance")
def plotRowMeanVarSlopeHist(cameraDataDict, cameraObj):
    values = extractVals(cameraDataDict, 'rowMeanVarSlope')
    fig, ax = plotHist(values, logx=False, title='(Run), row_mean_var_slope', xlabel='row_mean_var_slope')
    return fig


@EoPlotMethod(EoFlatPairData, "max_observed_signal_hist", "camera", "hist", "Max observed signal")
def plotMaxObservedSignalHist(cameraDataDict, cameraObj):
    values = extractVals(cameraDataDict, 'maxObservedSignal')
    fig, ax = plotHist(values, logx=False, title='(Run), max_observed_signal (ADU)', xlabel='max_observed_signal')
    return fig


@EoPlotMethod(EoFlatPairData, "linearity_turnoff_hist", "camera", "hist", "Linearity turnoff")
def plotLinearityTurnoffHist(cameraDataDict, cameraObj):
    values = extractVals(cameraDataDict, 'linearityTurnoff')
    fig, ax = plotHist(values, logx=False, title='(Run), linearity_turnoff (ADU)', xlabel='linearity_turnoff')
    return fig


@EoPlotMethod(EoFlatPairData, "linearity", "raft", "linearity", "Maximum fractional deviation")
def plotMaxFracDev(raftDataDict):
    raftValues = extractVals(raftDataDict, 'maxFracDev', extractFrom='raft')
    fig, ax = plotRaftPerAmp(raftValues, '(Run, Raft)', 'non-linearity (max. fractional deviation)')
    return fig


RegisterEoCalibSchema(EoFlatPairData)


AMPS = ["%02i" % i for i in range(16)]
NEXPOSURE = 10
EoFlatPairData.testData = dict(testCtor=dict(amps=AMPS, nAmp=len(AMPS), nExposure=NEXPOSURE))
