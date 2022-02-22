# from lsst.ip.isr import IsrCalib

from .eoCalibTable import EoCalibField, EoCalibTableSchema, EoCalibTable, EoCalibTableHandle
from .eoCalib import EoCalibSchema, EoCalib, RegisterEoCalibSchema
from .eoPlotUtils import *

# TEMPORARY, UNTIL THE FUNCTION IS MERGED TO THE MAIN BRANCH
from .TEMPafwutils import plotAmpFocalPlane

import matplotlib.pyplot as plt

__all__ = ["EoBrighterFatterAmpPairData",
           "EoBrighterFatterAmpRunData",
           "EoBrighterFatterData"]


class EoBrighterFatterAmpPairDataSchemaV0(EoCalibTableSchema):
    """Schema definitions for output data for per-amp, per-exposure-pair tables
    for EoBrighterFatterTask

    These are the covariances (and their errors) from the imaging region data
    """

    TABLELENGTH = "nPair"

    mean = EoCalibField(name="MEAN", dtype=float, unit='electron')
    covarience = EoCalibField(name="COV", dtype=float, unit='electron**2', shape=['nCov', 'nCov'])
    covarienceError = EoCalibField(name="COV_ERROR", dtype=float, unit='electron**2', shape=['nCov', 'nCov'])


class EoBrighterFatterAmpPairData(EoCalibTable):
    """Container class and interface for per-amp, per-exposure-pair tables
    for EoBrighterFatterTask."""

    SCHEMA_CLASS = EoBrighterFatterAmpPairDataSchemaV0

    def __init__(self, data=None, **kwargs):
        """C'tor, arguments are passed to base class.

        This just associates class properties with columns
        """
        super(EoBrighterFatterAmpPairData, self).__init__(data=data, **kwargs)
        self.mean = self.table[self.SCHEMA_CLASS.mean.name]
        self.covarience = self.table[self.SCHEMA_CLASS.covarience.name]
        self.covarienceError = self.table[self.SCHEMA_CLASS.covarienceError.name]


class EoBrighterFatterAmpRunDataSchemaV0(EoCalibTableSchema):
    """Schema definitions for output data for per-amplifier, per-run table
    for EoBrighterFatterTask.

    These are the correlations, the trends on those correlations
    with increasing signal level and the uncertainties.
    """

    TABLELENGTH = "nAmp"

    bfMean = EoCalibField(name='BF_MEAN', dtype=float)
    bfXCorr = EoCalibField(name='BF_XCORR', dtype=float)
    bfXCorrErr = EoCalibField(name='BF_XCORR_ERR', dtype=float)
    bfXSlope = EoCalibField(name='BF_SLOPEX', dtype=float)
    bfXSlopeErr = EoCalibField(name='BF_SLOPEX_ERR', dtype=float)
    bfYCorr = EoCalibField(name='BF_YCORR', dtype=float)
    bfYCorrErr = EoCalibField(name='BF_YCORR_ERR', dtype=float)
    bfYSlope = EoCalibField(name='BF_SLOPEY', dtype=float)
    bfYSlopeErr = EoCalibField(name='BF_SLOPEY_ERR', dtype=float)


class EoBrighterFatterAmpRunData(EoCalibTable):
    """Container class and interface for per-amp, per-run table
    for EoBrighterFatterTask."""

    SCHEMA_CLASS = EoBrighterFatterAmpRunDataSchemaV0

    def __init__(self, data=None, **kwargs):
        """C'tor, arguments are passed to base class.

        This just associates class properties with columns
        """
        super(EoBrighterFatterAmpRunData, self).__init__(data=data, **kwargs)
        self.bfMean = self.table[self.SCHEMA_CLASS.bfMean.name]
        self.bfXCorr = self.table[self.SCHEMA_CLASS.bfXCorr.name]
        self.bfXCorrErr = self.table[self.SCHEMA_CLASS.bfXCorrErr.name]
        self.bfXSlope = self.table[self.SCHEMA_CLASS.bfXSlope.name]
        self.bfXSlopeErr = self.table[self.SCHEMA_CLASS.bfXSlopeErr.name]
        self.bfYCorr = self.table[self.SCHEMA_CLASS.bfYCorr.name]
        self.bfYCorrErr = self.table[self.SCHEMA_CLASS.bfYCorrErr.name]
        self.bfYSlope = self.table[self.SCHEMA_CLASS.bfYSlope.name]
        self.bfYSlopeErr = self.table[self.SCHEMA_CLASS.bfYSlopeErr.name]


class EoBrighterFatterDataSchemaV0(EoCalibSchema):
    """Schema definitions for output data for EoBrighterFatterTask

    This defines correct versions of the sub-tables"""

    ampExp = EoCalibTableHandle(tableName="ampExp_{key}",
                                tableClass=EoBrighterFatterAmpPairData,
                                multiKey="amps")

    amps = EoCalibTableHandle(tableName="amps",
                              tableClass=EoBrighterFatterAmpRunData)


class EoBrighterFatterData(EoCalib):
    """Container class and interface for EoBrighterFatterTask outputs."""

    SCHEMA_CLASS = EoBrighterFatterDataSchemaV0

    _OBSTYPE = 'bias'
    _SCHEMA = SCHEMA_CLASS.fullName()
    _VERSION = SCHEMA_CLASS.version()

    def __init__(self, **kwargs):
        """C'tor, arguments are passed to base class.

        Class specialization just associates instance properties
        with sub-tables
        """
        super(EoBrighterFatterData, self).__init__(**kwargs)
        self.ampExp = self['ampExp']
        self.amps = self['amps']


@EoPlotMethod(EoBrighterFatterData, "bf", "slot", "Brighter Fatter", "Brighter Fatter")
def plotSlotBrighterFatter(obj):
    """Make and return a figure showing brighter-fatter
    covariances against mean signal for all the amps
    on the CCD. Five different covariances are shown.

    Parameters
    ----------
    obj : `EoBrighterFatterData`
        The data being plotted

    Returns
    -------
    fig : `matplotlib.Figure`
        The generated figure
    """
    fig = plt.figure(figsize=(16,12))
    iInds = [1,2,0,0,1]
    jInds = [0,0,1,2,1]
    for k in range(5):
        i = iInds[k]
        j = jInds[k]
        ax = fig.add_subplot(3, 2, k+1)
        moreColors(ax)
        
        ampExpData = obj.ampExp
        for iamp, ampData in enumerate(ampExpData.values()):
            mean = ampData.mean[:,0]
            cov = ampData.covarience[:,i,j]/mean
            ax.plot(mean, cov, label=iamp+1)
            
        ax.legend(loc='upper left', fontsize='small', ncol=2)
        ax.set_xlabel('mean signal (ADU)')
        ax.set_ylabel(f'cov({i}, {j})/mean')
        ax.set_title(f'Brighter-Fatter cov({i}, {j}) {"raft"}_{"det"}_{"run"}')
    plt.tight_layout()
    return fig


@EoPlotMethod(EoBrighterFatterData, "xcorr_mosaic", "camera", "mosaic", "Brighter-Fatter cov10 Mosaic")
def plotBrighterFatterCov10Mosaic(cameraDataDict, cameraObj):
    dataValues = extractVals(cameraDataDict, 'bfXCorr')
    plotAmpFocalPlane(cameraObj, level='AMPLIFIER', dataValues=dataValues, showFig=False,
                      figsize=(16,16), colorMapName='hot', colorScale='linear')
    fig = plt.gcf()
    ax = plt.gca()
    ax.set_aspect('equal')
    ax.set_title('(Run) bf_xcorr')
    return fig


@EoPlotMethod(EoBrighterFatterData, "ycorr_mosaic", "camera", "mosaic", "Brighter-Fatter cov01 Mosaic")
def plotBrighterFatterCov01Mosaic(cameraDataDict, cameraObj):
    dataValues = extractVals(cameraDataDict, 'bfYCorr')
    plotAmpFocalPlane(cameraObj, level='AMPLIFIER', dataValues=dataValues, showFig=False,
                      figsize=(16,16), colorMapName='hot', colorScale='linear')
    fig = plt.gcf()
    ax = plt.gca()
    ax.set_aspect('equal')
    ax.set_title('(Run) bf_ycorr')
    return fig


@EoPlotMethod(EoBrighterFatterData, "xcorr_hist", "camera", "hist", "Brighter-Fatter cov10")
def plotBrighterFatterCov10Hist(cameraDataDict, cameraObj):
    values = extractVals(cameraDataDict, 'bfXCorr')
    fig, ax = plotHist(values, logx=False, title='(Run), bf_xcorr', xlabel='bf_xcorr')
    return fig


@EoPlotMethod(EoBrighterFatterData, "ycorr_hist", "camera", "hist", "Brighter-Fatter cov01")
def plotBrighterFatterCov01Hist(cameraDataDict, cameraObj):
    values = extractVals(cameraDataDict, 'bfYCorr')
    fig, ax = plotHist(values, logx=False, title='(Run), bf_ycorr', xlabel='bf_ycorr')
    return fig


RegisterEoCalibSchema(EoBrighterFatterData)


AMPS = ["%02i" % i for i in range(16)]
NPAIR = 10
NCOV = 3
EoBrighterFatterData.testData = dict(testCtor=dict(amps=AMPS, nAmp=len(AMPS), nPair=NPAIR, nCov=NCOV))
