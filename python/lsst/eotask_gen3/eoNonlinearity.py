
import numpy as np
from scipy.optimize import leastsq
from scipy.interpolate import UnivariateSpline

import lsst.pex.config as pexConfig
import lsst.pipe.base as pipeBase
import lsst.pipe.base.connectionTypes as cT
import lsst.afw.detection as afwDetect

from lsst.ip.isr import Defects

from .eoCalibBase import (EoDetRunCalibTaskConfig, EoDetRunCalibTaskConnections, EoDetRunCalibTask,\
                          extractAmpImage, OUTPUT_DEFECTS_CONNECT, copyConnect)
from .eoNonlinearityData import EoNonlinearityData

__all__ = ["EoNonlinearityTask", "EoNonlinearityTaskConfig"]


def lin_func(pars, xvals):
    """Return a line whose slope is pars[0]"""
    return pars[0]*xvals

def chi2_model(pars, xvals, yvals):
    """Return the chi2 w.r.t. the model"""
    return (yvals - lin_func(pars, xvals))/np.sqrt(yvals)

def makeProfileHist(xbin_edges, xdata, ydata, **kwargs):
    """Build a profile historgram

    Parameters
    ----------
    xbin_edges : `array`
        The bin edges
    xdata : `array`
        The x-axis data
    ydata : `array`
        The y-axis data

    Keywords
    --------
    yerrs :  `array`
        The errors on the y-axis points

    stderr : `bool`
        Set error bars to standard error instead of RMS

    Returns
    -------
    x_vals : `array`
        The x-bin centers
    y_vals : `array`
        The y-bin values
    y_errs : `array`
        The y-bin errors
    """
    yerrs = kwargs.get('yerrs', None)
    stderr = kwargs.get('stderr', False)

    nx = len(xbin_edges) - 1
    x_vals = (xbin_edges[0:-1] + xbin_edges[1:])/2.
    y_vals = np.ndarray((nx))
    y_errs = np.ndarray((nx))

    if yerrs is None:
        weights = np.ones(ydata.shape)
    else:
        weights = 1./(yerrs*yerrs)

    y_w = ydata*weights

    for i, (xmin, xmax) in enumerate(zip(xbin_edges[0:-1], xbin_edges[1:])):
        mask = (xdata >= xmin) * (xdata < xmax)
        if mask.sum() < 2:
            y_vals[i] = 0.
            y_errs[i] = -1.
            continue
        y_vals[i] = y_w[mask].sum() / weights[mask].sum()
        y_errs[i] = ydata[mask].std()
        if stderr:
            y_errs[i] /= np.sqrt(mask.sum())

    return x_vals, y_vals, y_errs


def correctNullPoint(profile_x, profile_y, profile_yerr, null_point):
    """Force the spline to go through zero at a particular x-xvalue

    Parameters
    ----------
    profile_x : `array`
        The x-bin centers
    profile_y : `array`
        The b-bin values
    profile_yerr : `array`
        The y-bin errors
    null_point : `float`
        The x-value where the spline should go through zero       
    
    Returns
    -------
    y_vals_corr
        The adjusted y-values
    y_errs_corr
        The adjusted y-errors
    """
    uni_spline = UnivariateSpline(profile_x, profile_y)
    offset = uni_spline(null_point)
    
    y_vals_corr = ((1 + profile_y) / (1 + offset)) - 1.
    y_errs_corr = profile_yerr
    return y_vals_corr, y_errs_corr




class EoNonlinearityTaskConnections(EoDetRunCalibTaskConnections):

    ptcData = cT.Input(
        name="eoPtc",
        doc="Electrial Optical Calibration Output",
        storageClass="IsrCalib",
        dimensions=("instrument", "detector"),
    )
    
    outputData = cT.Output(
        name="eoNonlinearity",
        doc="Electrial Optical Calibration Output",
        storageClass="IsrCalib",
        dimensions=("instrument", "detector"),
    )    

class EoNonlinearityTaskConfig(EoDetRunCalibTaskConfig,
                               pipelineConnections=EoNonlinearityTaskConnections):

    nProfileBins = pexConfig.Field("Number of bins for Nonlinearity profile", int, default=30)
    fitMin = pexConfig.Field("Mininum of range to fit [ADU]", float, default=0.)
    fitMax = pexConfig.Field("Maximum of range to fit [ADU]", float, default=9.e4)
    nullPoint = pexConfig.Field("Signal value at which to set correction to zero", float, default=0.)    
    
    def setDefaults(self):
        self.connections.ptcData = "eoPtc"
        self.connections.outputData = "eoNonlinearity"
    

class EoNonlinearityTask(EoDetRunCalibTask):

    ConfigClass = EoNonlinearityTaskConfig
    _DefaultName = "eoNonlinearity"
    
    def run(self, ptcData, **kwargs):
        """ Run method

        Parameters
        ----------
        flatPairData :
            Input data

        Keywords
        --------
        camera : `lsst.obs.lsst.camera`

        Returns
        -------
        outputData : `EoCalib`
            Output data in formatted tables
        """
        camera = kwargs.get('camera')
        if camera is not None:
            det = camera.get(ptcData._detectorId)
        else:
            det = None
        inputAmpTables = ptcData.ampExp
        outputData = self.makeOutputData(nAmp=len(inputAmpTables), nProf=self.config.nProfileBins,
                                         camera=camera, detector=det)
        outputTable = outputData.amps['amps']
        for iamp, (ampName, ampData) in enumerate(inputAmpTables.items()):
            ampMean = ampData.mean
            ampVar = ampData.var
            profX, profYCorr, profYErr = self.findNonlinearity(ampMean, ampVar)
            outputTable.profX[iamp] = profX
            outputTable.profYCorr[iamp] = profYCorr
            outputTable.profYErr[iamp] = profYErr
        return pipeBase.Struct(outputData=outputData)

    def makeOutputData(self, nAmp, nProf, **kwargs):
        return EoNonlinearityData(nAmp=nAmp, nProf=nProf, **kwargs)

    def findNonlinearity(self, xdata, ydata):

        xbins = np.linspace(self.config.fitMin, self.config.fitMax, self.config.nProfileBins+1)

        mask = (self.config.fitMin < xdata) * (self.config.fitMax > xdata)
        xdata_fit = xdata[mask]
        ydata_fit = ydata[mask]
        mean_slope = (ydata_fit/xdata_fit).mean()
        pars = (mean_slope,)
        results = leastsq(chi2_model, pars, full_output=1, args=(xdata_fit, ydata_fit))
        model_yvals = lin_func(results[0], xdata)
        frac_resid = (ydata - model_yvals)/model_yvals
        frac_resid_err = 1./xdata

        prof_x, prof_y, prof_yerr = makeProfileHist(xbins, xdata, frac_resid, y_errs=frac_resid_err, stderr=True)        
        prof_y, prof_yerr = correctNullPoint(prof_x, prof_y, prof_yerr, self.config.nullPoint)                

        return (prof_x, prof_y, prof_yerr)

        
