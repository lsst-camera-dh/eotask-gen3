# from lsst.ip.isr import IsrCalib

from .eoCalibTable import EoCalibField, EoCalibTableSchema, EoCalibTable, EoCalibTableHandle
from .eoCalib import EoCalibSchema, EoCalib, RegisterEoCalibSchema
from .eoPlotUtils import EoPlotMethod, nullFigure

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
    return nullFigure()


@EoPlotMethod(EoPtcData, "gain_mosaic", "camera", "mosaic", "PTC Gain")
def plotPTCGainMosaic(obj):
    return nullFigure()


@EoPlotMethod(EoPtcData, "a00_mosaic", "camera", "mosaic", "PTC a00")
def plotPTCa00Mosaic(obj):
    return nullFigure()


@EoPlotMethod(EoPtcData, "full_well_mosaic", "camera", "mosaic", "PTC Full Well")
def plotPTCFullWellMosaic(obj):
    return nullFigure()


@EoPlotMethod(EoPtcData, "turnoff_mosaic", "camera", "mosaic", "PTC Turnoff")
def plotPTCTurnoffMosaic(obj):
    return nullFigure()


@EoPlotMethod(EoPtcData, "max_frac_dev_mosaic", "camera", "mosaic", "PTC Max. fractional deviation")
def plotPTCMaxFracDevMosaic(obj):
    return nullFigure()


@EoPlotMethod(EoPtcData, "linearity_turnoff_mosaic", "camera", "mosaic", "PTC Linearity Turnoff")
def plotPTCLinearityTurnoffMosaic(obj):
    return nullFigure()


@EoPlotMethod(EoPtcData, "gain_hist", "camera", "hist", "PTC Gain")
def plotPTCGainHist(obj):
    return nullFigure()


@EoPlotMethod(EoPtcData, "a00_hist", "camera", "hist", "PTC a00")
def plotPTCa00Hist(obj):
    return nullFigure()


@EoPlotMethod(EoPtcData, "full_well_hist", "camera", "hist", "PTC Full Well")
def plotPTCFullWellHist(obj):
    return nullFigure()


@EoPlotMethod(EoPtcData, "turnoff_hist", "camera", "hist", "PTC Turnoff")
def plotPTCTurnoffHist(obj):
    return nullFigure()


@EoPlotMethod(EoPtcData, "max_frac_dev_hist", "camera", "hist", "PTC Max. fractional deviation")
def plotPTCMaxFracDevHist(obj):
    return nullFigure()


@EoPlotMethod(EoPtcData, "linearity_turnoff_hist", "camera", "hist", "PTC Linearity Turnoff")
def plotPTCLinearityTurnoffHist(obj):
    return nullFigure()


RegisterEoCalibSchema(EoPtcData)

AMPS = ["%02i" % i for i in range(16)]
NPAIR = 10
EoPtcData.testData = dict(testCtor=dict(amps=AMPS, nAmp=len(AMPS), nPair=NPAIR))
