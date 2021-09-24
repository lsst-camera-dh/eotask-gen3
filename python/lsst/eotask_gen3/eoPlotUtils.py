"""This module utility functions to make plots for EO test data.

"""

import matplotlib.pyplot as plt

def nullFigure(*args):
    """ Make an empty placeholder figure """
    fig = plt.figure()
    return fig


class EoPlotHandle:

    def __init__(self, name, description, func):

        self._name = name
        self._description = description
        self._func = func
        self._figure = None

    @property
    def name(self):
        return self._name

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


def EoSlotPlotMethod(theClass, name, description):    
    class _EoSlotPlot:
        def __init__(self, method):
            self.method = method
            if hasattr(theClass, 'slotFigHandles'):
                theClass.slotFigHandles.append(EoPlotHandle(name, description, method))
            else:
                theClass.slotFigHandles = [EoPlotHandle(name, description, method)]
        def __get__(self, instance, cls):
            return lambda *args, **kwargs: self.method(instance, *args, *kwargs)
    return _EoSlotPlot


def EoRaftPlotMethod(theClass, name, description):
    
    class _EoRaftPlot:
        def __init__(self, method):
            self.method = method
            if hasattr(theClass, 'raftFigHandles'):
                theClass.raftFigHandles.append(EoPlotHandle(name, description, method))
            else:
                theClass.raftFigHandles = [EoPlotHandle(name, description, method)]
        def __get__(self, instance, cls):
            return lambda *args, **kwargs: self.method(cls, *args, *kwargs)
    return _EoRaftPlot
        

def EoCameraPlotMethod(theClass, name, description):
    
    class _EoCameraPlot:
        def __init__(self, method):
            self.method = method
            if hasattr(theClass, 'cameraFigHandles'):
                theClass.cameraFigHandles.append(EoPlotHandle(name, description, method))
            else:
                theClass.cameraFigHandles = [EoPlotHandle(name, description, method)]
        def __get__(self, instance, cls):
            return lambda *args, **kwargs: self.method(cls, *args, *kwargs)
    return _EoCameraPlot


