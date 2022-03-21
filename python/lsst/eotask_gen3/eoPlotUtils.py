"""This module utility functions to make plots for EO test data.

"""

import matplotlib.pyplot as plt
import numpy as np


def nullFigure(*args):
    """ Make an empty placeholder figure """
    fig = plt.figure()
    return fig


class EoPlotHandle:
    """ Utility class to wrap a plotting function with context """

    def __init__(self, name, level, family, description, func):

        self._name = name
        self._level = level
        self._family = family
        self._description = description
        self._func = func
        self._figure = None

    @property
    def name(self):
        return self._name

    @property
    def level(self):
        return self._level

    @property
    def family(self):
        return self._family

    @property
    def description(self):
        return self._description

    @property
    def func(self):
        return self._func

    @property
    def figure(self):
        return self._figure

    def __call__(self, *args):
        self._figure = self._func(*args)
        return self._figure


def EoPlotMethod(theClass, name, level, family, description):
    """ Decorator function to attach a plotting function to a data class
    with context """
    class _EoPlot:
        def __init__(self, method):
            self.method = method
            if hasattr(theClass, 'figHandles'):
                theClass.figHandles.append(EoPlotHandle(name, level, family, description, method))
            else:
                theClass.figHandles = [EoPlotHandle(name, level, family, description, method)]

        def __get__(self, instance, cls):
            return lambda *args, **kwargs: self.method(cls, *args, *kwargs)
    return _EoPlot


def plot3x3(title='', xlabel='', ylabel='', figsize=(16,16)):
    '''
    Function to create 9 subplots, one for each CCD in a raft.
    Returns a matplotlib Figure and a dictionary of Axes, labeled S20 - S02.
    '''
    fig = plt.figure(figsize=figsize)
    ccdNames = ['S20', 'S21', 'S22', 'S10', 'S11', 'S12', 'S00', 'S01', 'S02']
    ax = {ccd: fig.add_subplot(3, 3, i+1) for i,ccd in enumerate(ccdNames)}
    for ccd in ax:
        ax[ccd].set_title(ccd)
    plt.suptitle(title, fontsize=14)
    fig.add_subplot(111, frameon=False)
    plt.tick_params(labelcolor='none', which='both', top=False, bottom=False, left=False, right=False)
    plt.xlabel(xlabel, fontsize=14)
    plt.ylabel(ylabel, fontsize=14)
    plt.tight_layout(rect=(0, 0, 1, 0.98))
    return fig, ax


def plot4x4(title='', xlabel='', ylabel='', figsize=(16,16)):
    '''
    Function to create 16 subplots, one for each amp in CCD.
    Returns a matplotlib Figure and a dictionary of Axes, labeled 1-16.
    
    At some point labelling amps numerically will be replaced by whatever becomes standardized...
    '''
    fig = plt.figure(figsize=figsize)
    ax = {amp: fig.add_subplot(4, 4, amp) for amp in range(1, 17)}
    ampNames = {1:'C00', 2:'C01', 3:'C02', 4:'C03', 5:'C04', 6:'C05', 7:'C06', 8:'C07',
               9:'C17', 10:'C16', 11:'C15', 12:'C14', 13:'C13', 14:'C12', 15:'C11', 16:'C10'}
    for amp in ax:
        ax[amp].set_title(ampNames[amp])
    plt.suptitle(title, fontsize=14)
    fig.add_subplot(111, frameon=False)
    plt.tick_params(labelcolor='none', which='both', top=False, bottom=False, left=False, right=False)
    plt.xlabel(xlabel, fontsize=14)
    plt.ylabel(ylabel, fontsize=14)
    plt.tight_layout(rect=(0, 0, 1, 0.98))
    return fig, ax


def plotRaftPerAmp(raftDataDict, fig=None, title='', ylabel='', figsize=(10,8)):
    '''
    Function to plot all amplifier values in a raft, split into vertical
    divisions for each CCD. raftDataDict should be a nested dict of values,
    the result of e.g. extractVals(..., extractFrom='raft')
    
    fig is a plt.Figure object
    '''
    if fig is None:
        fig = plt.figure(figsize=figsize)
    ccdShifts = {'S00': 0,
                'S01': 20,
                'S02': 40,
                'S10': 60,
                'S11': 80,
                'S12': 100,
                'S20': 120,
                'S21': 140,
                'S22': 160}
    for ccd in raftDataDict:
        plt.scatter(np.arange(16)+ccdShifts[ccd]+2, raftDataDict[ccd].values(), c='C0')
    
    for ccd, sh in ccdShifts.items():
        plt.axvline(sh, ls='--', c='k')
    plt.axvline(180, ls='--', c='k')
    
    plt.xticks(np.array(list(ccdShifts.values())) + 10, ccdShifts.keys())
    plt.ylabel(ylabel)
    plt.title(title)
    
    return fig, plt.gca()


def plotHist(data, logx, bins=50, title='', xlabel='', ylabel='entries / bin', figsize=(12,9)):
    '''
    Function to plot a histogram of values.
    
    Parameters:
    data : `dict`
        Nested dictionary of values, e.g. the result of extractVals()
    logx: `bool`
        Boolean, whether to use log scale for x-axis
    bins: `int`
        Number of bins to use in the histogram
    
    Returns: matplotlib Figure and Axes objects
    '''
    fig = plt.figure(figsize=figsize)
    values = list(NestedDictValues(data))
    if logx: bins = np.geomspace(max((min(values),1)), max(values), bins)
    
    plt.hist(values, log=logx, bins=bins, histtype='step')
    
    plt.yscale('log')
    if logx: plt.xscale('log')
    plt.ylabel(ylabel)
    plt.xlabel(xlabel)
    plt.title(title)
    
    return fig, plt.gca()


def moreColors(ax):
    '''
    Function to extend the matplotlib color cycle to 20 colors, so that figures
    can have distinct colors for each amplifier.
    Uses the default color cycle (plt.cm.tab10) followed by the additional colors
    in plt.cm.tab20.
    '''
    colors = np.vstack((plt.cm.tab10(np.arange(10)), plt.cm.tab20(np.arange(1,20,2))))
    ax.set_prop_cycle('color', colors)
    
    
def extractVals(cDict, value, extractFrom='camera'):
    '''
    Extract amplifier float values from cDict, a nested OrderedDict of
    raft > detector > eo(data_type)Data object to the dict format used for
    per-amp mosaic plotting. 'value' is the string name of the data object
    attribute to be plotted.
    
    Specifying extractFrom='raft' requires removing the outermost layer of
    this type of dict, i.e., cDict should be a dict of detectors > eoData objects.
    
    E.g. for cDict containing eoBrightPixelsData objects, to get the number
    of bright pixels in each amp:
        dataValues = extractVals(cDict, 'nBrightPixel')
    '''
    amps = ['C1%s'%i for i in range(8)] + ['C0%s'%i for i in range(7,-1,-1)]
    if extractFrom=='camera':
        cameraVals = {}
        for raftName in cDict:
            raft = cDict[raftName]
            for detName in raft:
                det = raft[detName]
                ampTable = getattr(det.amps, value)
                ampVals = {}
                for i in range(len(ampTable)):
                    ampVals[amps[i]] = ampTable[i][0]
                cameraVals['%s_%s'%(raftName,detName)] = ampVals
        return cameraVals
    if extractFrom=='raft':
        raftVals = {}
        for detName in cDict:
            det = cDict[detName]
            ampTable = getattr(det.amps, value)
            ampVals = {}
            for i in range(len(ampTable)):
                ampVals[amps[i]] = ampTable[i][0]
            raftVals[detName] = ampVals
        return raftVals
    raise ValueError('Extract values from either "camera" or "raft"')


def NestedDictValues(d):
    """Copied from afw.utils
    Extract all values from a nested dictionary.
    Parameters
    ----------
    d : `dict`
        A dictionary, possibly contining additional dictionaries.
    Yields
    -------
    v : obj
        Any non-dictionary entries in the input.
    """
    for v in d.values():
        if isinstance(v, dict):
            yield from NestedDictValues(v)
        else:
            yield v