""" Data selections for EO Tasks
"""

from collections import OrderedDict

__all__ = ["EoDataSelection"]

class EoDataSelection:
    """ Specifies data for an EO Task

    Parameters
    ----------
    queryString : `str`
        The string used in the 'pipetask' -d query
    selectionFunction : `function(expandedDataRef) -> bool`
        A function that returns True for data to be used
    """
    _selectionDict = OrderedDict()
    
    def __init__(self, doc, queryString, selectionFunction):
        self._doc = doc
        self._queryString = queryString
        self._selectionFunction = selectionFunction

    @property
    def doc(self):
        return self._doc
        
    @property
    def queryString(self):
        return self._queryString

    @property
    def selectionFunction(self):
        return self._selectionFunction

    def selectData(self, dataRefs):
        return [aDataRef for aDataRef in dataRefs if self._selectionFunction(aDataRef)]

    @classmethod
    def getSelection(cls, key):
        return cls._selectionDict[key]

    @classmethod
    def addSelection(cls, key, queryString, selectionFuncion)
        cls._selectionDict[key] = cls(queryString, selectionFuncion)

    @classmethod
    def choiceDict(cls):
        return {key: val.doc for key, val in cls._selectionDict.items()}

    
def eoSelectAny(deferredDatasetRef):
    return True
    
def eoSelectAnyBias(deferredDatasetRef):
    return deferredDatasetRef.datasetRef.dataId.records["exposure"].observation_type == 'bias'

def eoSelectBiasBias(deferredDatasetRef):
    exposure = deferredDatasetRef.datasetRef.dataId.records["exposure"]
    return exposure.observation_type == 'bias' and exposure.observation_reason == 'bias'

def eoSelectBotPersistanceBias(deferredDatasetRef):
    exposure = deferredDatasetRef.datasetRef.dataId.records["exposure"]
    return exposure.observation_type == 'bias' and exposure.observation_reason == 'bot_persistence'

def eoSelectFe55Bias(deferredDatasetRef):
    exposure = deferredDatasetRef.datasetRef.dataId.records["exposure"]
    return exposure.observation_type == 'bias' and exposure.observation_reason == 'fe55_flat'

def eoSelectDarkDark(deferredDatasetRef):
    exposure = deferredDatasetRef.datasetRef.dataId.records["exposure"]
    return exposure.observation_type == 'dark' and exposure.observation_reason == 'dark'

def eoSelectBotPersitenceDark(deferredDatasetRef):
    exposure = deferredDatasetRef.datasetRef.dataId.records["exposure"]
    return exposure.observation_type == 'dark' and exposure.observation_reason == 'bot_persistence'

def eoSelectFlatFlat(deferredDatasetRef):
    exposure = deferredDatasetRef.datasetRef.dataId.records["exposure"]
    return exposure.observation_type == 'flat' and exposure.observation_reason == 'flat'

def eoSelectAnySuperFlat(deferredDatasetRef):
    exposure = deferredDatasetRef.datasetRef.dataId.records["exposure"]
    return exposure.observation_type == 'flat' and exposure.observation_reason == 'sflat'

def eoSelectSuperFlatLow(deferredDatasetRef):
    exposure = deferredDatasetRef.datasetRef.dataId.records["exposure"]
    return exposure.observation_type == 'flat' and exposure.observation_reason == 'sflat' and exposure.exposure_time < 30.

def eoSelectSuperFlatHigh(deferredDatasetRef):
    exposure = deferredDatasetRef.datasetRef.dataId.records["exposure"]
    return exposure.observation_type == 'flat' and exposure.observation_reason == 'sflat' and exposure.exposure_time < 30.

def eoSelectFe55Flat(deferredDatasetRef):
    exposure = deferredDatasetRef.datasetRef.dataId.records["exposure"]
    return exposure.observation_type == 'fe55_flat' and exposure.observation_reason == 'fe55'


EoDataSelection.addSelection("any",
                             "True"
                             eoSelectAny)
EoDataSelection.addSelection("anyBias",
                             "exposure.observation_type = 'bias'",
                             eoSelectAnyBias)
EoDataSelection.addSelection("biasBias",
                             "exposure.observation_type = 'bias' AND exposure.observation_reason = 'bias'",
                             eoSelectBiasBias)
EoDataSelection.addSelection("botPersistenceBias",
                             "exposure.observation_type = 'bias' AND exposure.observation_reason = 'bot_persistence'",
                             eoSelectBotPersistanceBias)
EoDataSelection.addSelection("fe55Bias",
                             "exposure.observation_type = 'bias' AND exposure.observation_reason = 'fe55_flat'",
                             eoSelectFe55Bias)
EoDataSelection.addSelection("darkDark",
                             "exposure.observation_type = 'dark' AND exposure.observation_reason = 'dark'",
                             eoSelectDarkDark)
EoDataSelection.addSelection("botPersistenceDark",
                             "exposure.observation_type = 'dark' AND exposure.observation_reason = 'bot_persistence'",
                             eoSelectDarkDark)
EoDataSelection.addSelection("flatFlat",
                             "exposure.observation_type = 'flat' AND exposure.observation_reason = 'flat'",
                             eoSelectDarkDark)
EoDataSelection.addSelection("anySuperFlat",
                             "exposure.observation_type = 'flat' AND exposure.observation_reason = 'sflat'",
                             eoSelectAnySuperFlat)
EoDataSelection.addSelection("superFlatLow",
                             "exposure.observation_type = 'flat' AND exposure.observation_reason = 'sflat' AND exposure.exposure_time < 30.",
                             eoSelectSuperFlatLow)
EoDataSelection.addSelection("superFlatHigh",
                             "exposure.observation_type = 'flat' AND exposure.observation_reason = 'sflat' AND exposure.exposure_time >= 30.",
                             eoSelectSuperFlatHigh)
EoDataSelection.addSelection("fe55Flat",
                             "exposure.observation_type = 'fe55_flat' AND exposure.observation_reason = 'fe55'",
                             eoSelectFe55Flat)



