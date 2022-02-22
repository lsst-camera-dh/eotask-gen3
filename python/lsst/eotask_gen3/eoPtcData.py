# from lsst.ip.isr import IsrCalib

from .eoCalibTable import EoCalibField, EoCalibTableSchema, EoCalibTable, EoCalibTableHandle
from .eoCalib import EoCalibSchema, EoCalib, RegisterEoCalibSchema
from .eoPlotUtils import *
from lsst.cp.pipe.utils import funcAstier

# TEMPORARY, UNTIL THE FUNCTION IS MERGED TO THE MAIN BRANCH
from .TEMPafwutils import plotAmpFocalPlane

__all__ = ["EoPtcAmpPairData",
           "EoPtcAmpRunData",
           "EoPtcDetPairData",
           "EoPtcData"]


class EoPtcAmpPairDataSchemaV0(EoCalibTableSchema):
    """Schema definitions for output data for per-amp, per-exposure-pair tables
    for EoPtcData.

    These are summary statistics about the signal in the
    imaging region of the difference image
    """

    TABLELENGTH = "nPair"

    mean = EoCalibField(name="MEAN", dtype=float, unit='adu')
    var = EoCalibField(name="VAR", dtype=float, unit='adu**2')
    discard = EoCalibField(name="DISCARD", dtype=int, unit='pixel')


class EoPtcAmpPairData(EoCalibTable):
    """Container class and interface for per-amp, per-exposure tables
    for EoPtcTask."""

    SCHEMA_CLASS = EoPtcAmpPairDataSchemaV0

    def __init__(self, data=None, **kwargs):
        """C'tor, arguments are passed to base class.

        Class specialization just associates class properties with columns
        """
        super(EoPtcAmpPairData, self).__init__(data=data, **kwargs)
        self.mean = self.table[self.SCHEMA_CLASS.mean.name]
        self.var = self.table[self.SCHEMA_CLASS.var.name]
        self.discard = self.table[self.SCHEMA_CLASS.discard.name]


class EoPtcAmpRunDataSchemaV0(EoCalibTableSchema):
    """Schema definitions for output data for per-amp, per-run tables
    for EoOverscanTask.

    These are results of the PTC fits
    """

    TABLELENGTH = 'nAmp'

    ptcGain = EoCalibField(name="PTC_GAIN", dtype=float, unit='adu/electron')
    ptcGainError = EoCalibField(name="PTC_GAIN_ERROR", dtype=float, unit='adu/electron')
    ptcA00 = EoCalibField(name="PTC_A00", dtype=float)
    ptcA00Error = EoCalibField(name="PTC_A00_ERROR", dtype=float)
    ptcNoise = EoCalibField(name="PTC_NOISE", dtype=float, unit='adu')
    ptcNoiseError = EoCalibField(name="PTC_NOISE_ERROR", dtype=float, unit='adu')
    ptcTurnoff = EoCalibField(name="PTC_TURNOFF", dtype=float, unit='adu')


class EoPtcAmpRunData(EoCalibTable):
    """Container class and interface for per-amp, per-run tables
    for EoPtcTask."""

    SCHEMA_CLASS = EoPtcAmpRunDataSchemaV0

    def __init__(self, data=None, **kwargs):
        """C'tor, arguments are passed to base class.

        Class specialization just associates class properties with columns
        """
        super(EoPtcAmpRunData, self).__init__(data=data, **kwargs)
        self.ptcGain = self.table[self.SCHEMA_CLASS.ptcGain.name]
        self.ptcGainError = self.table[self.SCHEMA_CLASS.ptcGainError.name]
        self.ptcA00 = self.table[self.SCHEMA_CLASS.ptcA00.name]
        self.ptcA00Error = self.table[self.SCHEMA_CLASS.ptcA00Error.name]
        self.ptcNoise = self.table[self.SCHEMA_CLASS.ptcNoise.name]
        self.ptcNoiseError = self.table[self.SCHEMA_CLASS.ptcNoiseError.name]
        self.ptcTurnoff = self.table[self.SCHEMA_CLASS.ptcTurnoff.name]


class EoPtcDetPairDataSchemaV0(EoCalibTableSchema):

    TABLELENGTH = 'nPair'

    flux = EoCalibField(name="FLUX", dtype=float)
    seqnum = EoCalibField(name="SEQNUM", dtype=int)
    dayobs = EoCalibField(name="DAYOBS", dtype=int)


class EoPtcDetPairData(EoCalibTable):
    """Schema definitions for output data for per-ccd, per-exposure-pair tables
    for EoPtcTask.

    The flux is computed from the photodiode data.

    As for the other quantities, these are copied from the
    EO-analysis-jobs code and in part
    are retained to allow for possible conversion of old data.

    Note that these data actually discernable from the dataId, but having
    them here makes it easier to make plots of trends.
    """

    SCHEMA_CLASS = EoPtcDetPairDataSchemaV0

    def __init__(self, data=None, **kwargs):
        """C'tor, arguments are passed to base class.

        This just associates class properties with columns
        """
        super(EoPtcDetPairData, self).__init__(data=data, **kwargs)
        self.flux = self.table[self.SCHEMA_CLASS.flux.name]
        self.seqnum = self.table[self.SCHEMA_CLASS.seqnum.name]
        self.dayobs = self.table[self.SCHEMA_CLASS.dayobs.name]


class EoPtcDataSchemaV0(EoCalibSchema):
    """Schema definitions for output data for EoPtcTask

    This defines correct versions of the sub-tables"""

    ampExp = EoCalibTableHandle(tableName="ampExp_{key}",
                                tableClass=EoPtcAmpPairData,
                                multiKey="amps")

    amps = EoCalibTableHandle(tableName="amps",
                              tableClass=EoPtcAmpRunData)

    detExp = EoCalibTableHandle(tableName="detExp",
                                tableClass=EoPtcDetPairData)


class EoPtcData(EoCalib):
    """Container class and interface for EoPtcTask outputs."""

    SCHEMA_CLASS = EoPtcDataSchemaV0

    _OBSTYPE = 'flat'
    _SCHEMA = SCHEMA_CLASS.fullName()
    _VERSION = SCHEMA_CLASS.version()

    def __init__(self, **kwargs):
        """C'tor, arguments are passed to base class.

        Class specialization just associates instance properties with
        sub-tables
        """
        super(EoPtcData, self).__init__(**kwargs)
        self.ampExp = self['ampExp']
        self.amps = self['amps']
        self.detExp = self['detExp']


@EoPlotMethod(EoPtcData, "curves", "slot", "ptc", "Photon Transfer Curves")
def plotPTC(obj):
    fig, ax = plot4x4('(Sensor, Run) Photon Transfer Curves', 'mean (ADU)', r'variance (ADU$^2$)')
    ampExpData = obj.ampExp
    ptcData = obj.amps
    for iamp, ampData in enumerate(ampExpData.values()):
        means = ampData.mean
        variances = ampData.var
        gain = ptcData.ptcGain[iamp][0]
        gainErr = ptcData.ptcGainError[iamp][0]
        a00 = ptcData.ptcA00[iamp][0]
        a00Err = ptcData.ptcA00Error[iamp][0]
        noise = ptcData.ptcNoise[iamp][0]
        turnoff = int(ptcData.ptcTurnoff[iamp][0])
        
        ax[iamp+1].scatter(means, variances)
        xx = np.logspace(np.log10(min(means)),np.log10(max(means)))
        ax[iamp+1].plot(xx, funcAstier([a00, gain, noise], xx), '--k')
        ax[iamp+1].set_xscale('log')
        ax[iamp+1].set_yscale('log')
        
        annot = 'Gain = %.2f +/- %.2f\n'%(gain, gainErr) +\
                'a00 = %.1e +/- %.1e\n'%(a00, a00Err) +\
                'Turnoff = %i'%turnoff
        ax[iamp+1].annotate(annot, xy=(0.05, 0.95), xycoords='axes fraction', va='top')
    return fig


@EoPlotMethod(EoPtcData, "gain_mosaic", "camera", "mosaic", "PTC Gain")
def plotPTCGainMosaic(cameraDataDict, cameraObj):
    dataValues = extractVals(cameraDataDict, 'ptcGain')
    plotAmpFocalPlane(cameraObj, level='AMPLIFIER', dataValues=dataValues, showFig=False,
                      figsize=(16,16), colorMapName='hot', colorScale='linear')
    fig = plt.gcf()
    ax = plt.gca()
    ax.set_aspect('equal')
    ax.set_title('(Run) ptc_gain (e-/ADU)')
    return fig


@EoPlotMethod(EoPtcData, "a00_mosaic", "camera", "mosaic", "PTC a00")
def plotPTCa00Mosaic(cameraDataDict, cameraObj):
    dataValues = extractVals(cameraDataDict, 'ptcA00')
    plotAmpFocalPlane(cameraObj, level='AMPLIFIER', dataValues=dataValues, showFig=False,
                      figsize=(16,16), colorMapName='hot', colorScale='linear')
    fig = plt.gcf()
    ax = plt.gca()
    ax.set_aspect('equal')
    ax.set_title('(Run) ptc_a00')
    return fig


@EoPlotMethod(EoPtcData, "turnoff_mosaic", "camera", "mosaic", "PTC Turnoff")
def plotPTCTurnoffMosaic(cameraDataDict, cameraObj):
    dataValues = extractVals(cameraDataDict, 'ptcTurnoff')
    plotAmpFocalPlane(cameraObj, level='AMPLIFIER', dataValues=dataValues, showFig=False,
                      figsize=(16,16), colorMapName='hot', colorScale='linear')
    fig = plt.gcf()
    ax = plt.gca()
    ax.set_aspect('equal')
    ax.set_title('(Run) ptc_turnoff (ADU)')
    return fig


@EoPlotMethod(EoPtcData, "gain_hist", "camera", "hist", "PTC Gain")
def plotPTCGainHist(cameraDataDict, cameraObj):
    values = extractVals(cameraDataDict, 'ptcGain')
    fig, ax = plotHist(values, logx=False, title='(Run), ptc_gain (e-/ADU)', xlabel='ptc_gain')
    return fig


@EoPlotMethod(EoPtcData, "a00_hist", "camera", "hist", "PTC a00")
def plotPTCa00Hist(cameraDataDict, cameraObj):
    values = extractVals(cameraDataDict, 'ptcA00')
    fig, ax = plotHist(values, logx=False, title='(Run), ptc_a00', xlabel='ptc_a00')
    return fig


@EoPlotMethod(EoPtcData, "turnoff_hist", "camera", "hist", "PTC Turnoff")
def plotPTCTurnoffHist(cameraDataDict, cameraObj):
    values = extractVals(cameraDataDict, 'ptcTurnoff')
    fig, ax = plotHist(values, logx=False, title='(Run), ptc_turnoff (ADU)', xlabel='ptc_turnoff')
    return fig


RegisterEoCalibSchema(EoPtcData)

AMPS = ["%02i" % i for i in range(16)]
NPAIR = 10
EoPtcData.testData = dict(testCtor=dict(amps=AMPS, nAmp=len(AMPS), nPair=NPAIR))
