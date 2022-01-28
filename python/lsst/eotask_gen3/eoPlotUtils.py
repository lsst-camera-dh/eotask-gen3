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


def plot3x3(title='', xlabel='', ylabel=''):
    '''
    Function to create 9 subplots, one for each CCD in a raft.
    Returns a matplotlib Figure and a dictionary of Axes, labeled S20 - S02.
    '''
    fig = plt.figure(figsize=(16, 16))
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


def plot4x4(title='', xlabel='', ylabel=''):
    '''
    Function to create 16 subplots, one for each amp in CCD.
    Returns a matplotlib Figure and a dictionary of Axes, labeled 1-16.
    
    At some point labelling amps numerically will be replaced by whatever becomes standardized...
    '''
    fig = plt.figure(figsize=(16, 16))
    ax = {amp: fig.add_subplot(4, 4, amp) for amp in range(1, 17)}
    for amp in ax:
        ax[amp].set_title(f'amp {amp}')
    plt.suptitle(title, fontsize=14)
    fig.add_subplot(111, frameon=False)
    plt.tick_params(labelcolor='none', which='both', top=False, bottom=False, left=False, right=False)
    plt.xlabel(xlabel, fontsize=14)
    plt.ylabel(ylabel, fontsize=14)
    plt.tight_layout(rect=(0, 0, 1, 0.98))
    return fig, ax


def moreColors(ax):
    '''
    Function to extend the matplotlib color cycle to 20 colors, so that figures
    can have distinct colors for each amplifier.
    Uses the default color cycle (plt.cm.tab10) followed by the additional colors
    in plt.cm.tab20.
    '''
    colors = np.vstack((plt.cm.tab10(np.arange(10)), plt.cm.tab20(np.arange(1,20,2))))
    ax.set_prop_cycle('color', colors)