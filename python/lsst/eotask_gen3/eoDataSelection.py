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
    def addSelection(cls, key, doc, queryString, selectionFunction):
        cls._selectionDict[key] = cls(doc, queryString, selectionFunction)

    @classmethod
    def choiceDict(cls):
        return {key: val.doc for key, val in cls._selectionDict.items()}


def getRef(refOrDeferred):
    try:
        return refOrDeferred.datasetRef
    except:
        return refOrDeferred
    
def eoSelectAny(deferredDatasetRef):
    return True
    
def eoSelectAnyBias(deferredDatasetRef):
    return getRef(deferredDatasetRef).dataId.records["exposure"].observation_type == 'bias'

def eoSelectBiasBias(deferredDatasetRef):
    exposure = getRef(deferredDatasetRef).dataId.records["exposure"]
    return exposure.observation_type == 'bias' and exposure.observation_reason == 'bias'

def eoSelectBotPersistanceBias(deferredDatasetRef):
    exposure = getRef(deferredDatasetRef).dataId.records["exposure"]
    return exposure.observation_type == 'bias' and exposure.observation_reason == 'bot_persistence'

def eoSelectFe55Bias(deferredDatasetRef):
    exposure = getRef(deferredDatasetRef).dataId.records["exposure"]
    return exposure.observation_type == 'bias' and exposure.observation_reason == 'fe55_flat'

def eoSelectDarkDark(deferredDatasetRef):
    exposure = getRef(deferredDatasetRef).dataId.records["exposure"]
    return exposure.observation_type == 'dark' and exposure.observation_reason == 'dark'

def eoSelectBotPersistenceDark(deferredDatasetRef):
    exposure = getRef(deferredDatasetRef).dataId.records["exposure"]
    return exposure.observation_type == 'dark' and exposure.observation_reason == 'bot_persistence'

def eoSelectFlatFlat(deferredDatasetRef):
    exposure = getRef(deferredDatasetRef).dataId.records["exposure"]
    return exposure.observation_type == 'flat' and exposure.observation_reason == 'flat'

def eoSelectAnySuperFlat(deferredDatasetRef):
    exposure = getRef(deferredDatasetRef).dataId.records["exposure"]
    return exposure.observation_type == 'flat' and exposure.observation_reason == 'sflat'

def eoSelectSuperFlatLow(deferredDatasetRef):
    exposure = getRef(deferredDatasetRef).dataId.records["exposure"]
    return exposure.observation_type == 'flat' and exposure.observation_reason == 'sflat' and exposure.exposure_time < 30.

def eoSelectSuperFlatHigh(deferredDatasetRef):
    exposure = getRef(deferredDatasetRef).dataId.records["exposure"]
    return exposure.observation_type == 'flat' and exposure.observation_reason == 'sflat' and exposure.exposure_time < 30.

def eoSelectFe55Flat(deferredDatasetRef):
    exposure = getRef(deferredDatasetRef).dataId.records["exposure"]
    return exposure.observation_type == 'fe55_flat' and exposure.observation_reason == 'fe55'


EoDataSelection.addSelection("any",
                             "Select all exposures",
                             "",
                             eoSelectAny)
EoDataSelection.addSelection("anyBias",
                             "Select all bias exposures",
                             "exposure.observation_type = 'bias'",
                             eoSelectAnyBias)
EoDataSelection.addSelection("biasBias",
                             "Select bias exposures from bias acquistions", 
                             "exposure.observation_type = 'bias' AND exposure.observation_reason = 'bias'",
                             eoSelectBiasBias)
EoDataSelection.addSelection("botPersistenceBias",
                             "Select bias exposures from bot_persistence acquistions",
                             "exposure.observation_type = 'bias' AND exposure.observation_reason = 'bot_persistence'",
                             eoSelectBotPersistanceBias)
EoDataSelection.addSelection("fe55Bias",
                             "Select bias exposures from Fe55 acquistions",
                             "exposure.observation_type = 'bias' AND exposure.observation_reason = 'fe55_flat'",
                             eoSelectFe55Bias)
EoDataSelection.addSelection("darkDark",
                             "Select dark exposures from dark acquistions",
                             "exposure.observation_type = 'dark' AND exposure.observation_reason = 'dark'",
                             eoSelectDarkDark)
EoDataSelection.addSelection("botPersistenceDark",
                             "Select dark exposures from bot_persistence acquistions",
                             "exposure.observation_type = 'dark' AND exposure.observation_reason = 'bot_persistence'",
                             eoSelectBotPersistenceDark)
EoDataSelection.addSelection("flatFlat",
                             "Select flat exposures from flat pair acquistions",
                             "exposure.observation_type = 'flat' AND exposure.observation_reason = 'flat'",
                             eoSelectFlatFlat)
EoDataSelection.addSelection("anySuperFlat",
                             "Select flat exposures from any superflat acquistions",
                             "exposure.observation_type = 'flat' AND exposure.observation_reason = 'sflat'",
                             eoSelectAnySuperFlat)
EoDataSelection.addSelection("superFlatLow",
                             "Select flat exposures from low-intensity superflat acquistions",
                             "exposure.observation_type = 'flat' AND exposure.observation_reason = 'sflat' AND exposure.exposure_time < 30.",
                             eoSelectSuperFlatLow)
EoDataSelection.addSelection("superFlatHigh",
                             "Select flat exposures from high-intensity superflat acquistions",
                             "exposure.observation_type = 'flat' AND exposure.observation_reason = 'sflat' AND exposure.exposure_time >= 30.",
                             eoSelectSuperFlatHigh)
EoDataSelection.addSelection("fe55Flat",
                             "Select fe55 exposures acquistions",
                             "exposure.observation_type = 'fe55_flat' AND exposure.observation_reason = 'fe55'",
                             eoSelectFe55Flat)



