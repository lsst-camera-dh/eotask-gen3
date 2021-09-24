"""This module utility functions to make plots for EO test data.

"""

import matplotlib.pyplot as plt

def nullFigure(*args):
    """ Make an empty placeholder figure """
    fig = plt.figure()
    return fig


class EoPlotHandle:

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

