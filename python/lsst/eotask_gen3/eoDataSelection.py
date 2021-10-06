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
        """Select and return only those dataRefs passing the
        selectionFunction"""
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
    except Exception:
        return refOrDeferred


def eoSelectAny(deferredDatasetRef):
    """Always returns True"""
    return True


def eoSelectAnyBias(deferredDatasetRef):
    """Returns true iff observation_type == 'bias'"""
    return getRef(deferredDatasetRef).dataId.records["exposure"].observation_type == 'bias'


def eoSelectBiasBias(deferredDatasetRef):
    """Returns true iff observation_type == 'bias'
    and observation_reason == 'bias'"""
    exposure = getRef(deferredDatasetRef).dataId.records["exposure"]
    return exposure.observation_type == 'bias'\
        and exposure.observation_reason == 'bias'


def eoSelectBotPersistanceBias(deferredDatasetRef):
    """Returns true iff observation_type == 'bias'
    and observation_reason == 'bot_persistence'"""
    exposure = getRef(deferredDatasetRef).dataId.records["exposure"]
    return exposure.observation_type == 'bias'\
        and exposure.observation_reason == 'bot_persistence'


def eoSelectFe55Bias(deferredDatasetRef):
    """Returns true iff observation_type == 'bias'
    and observation_reason == 'fe55_flat'"""
    exposure = getRef(deferredDatasetRef).dataId.records["exposure"]
    return exposure.observation_type == 'bias'\
        and exposure.observation_reason == 'fe55_flat'


def eoSelectDarkDark(deferredDatasetRef):
    """Returns true iff observation_type == 'dark'
    and observation_reason == 'dark'"""
    exposure = getRef(deferredDatasetRef).dataId.records["exposure"]
    return exposure.observation_type == 'dark'\
        and exposure.observation_reason == 'dark'


def eoSelectBotPersistenceDark(deferredDatasetRef):
    """Returns true iff observation_type == 'dark'
    and observation_reason == 'bot_persistence'"""
    exposure = getRef(deferredDatasetRef).dataId.records["exposure"]
    return exposure.observation_type == 'dark'\
        and exposure.observation_reason == 'bot_persistence'


def eoSelectFlatFlat(deferredDatasetRef):
    """Returns true iff observation_type == 'flat'
    and observation_reason == 'flat'"""
    exposure = getRef(deferredDatasetRef).dataId.records["exposure"]
    return exposure.observation_type == 'flat'\
        and exposure.observation_reason == 'flat'


def eoSelectAnySuperFlat(deferredDatasetRef):
    """Returns true iff observation_type == 'flat'
    and observation_reason == 'sflat'"""
    exposure = getRef(deferredDatasetRef).dataId.records["exposure"]
    return exposure.observation_type == 'flat'\
        and exposure.observation_reason == 'sflat'


def eoSelectSuperFlatLow(deferredDatasetRef):
    """Returns true iff observation_type == 'flat'
    and observation_reason == 'sflat'
    and the exposure time is less than 30 seconds"""
    exposure = getRef(deferredDatasetRef).dataId.records["exposure"]
    return exposure.observation_type == 'flat'\
        and exposure.observation_reason == 'sflat'\
        and exposure.exposure_time < 30.


def eoSelectSuperFlatHigh(deferredDatasetRef):
    """Returns true iff observation_type == 'flat'
    and observation_reason == 'sflat'
    and the exposure time is greater than 30 seconds"""
    exposure = getRef(deferredDatasetRef).dataId.records["exposure"]
    return exposure.observation_type == 'flat'\
        and exposure.observation_reason == 'sflat'\
        and exposure.exposure_time < 30.


def eoSelectFe55Flat(deferredDatasetRef):
    """Returns true iff observation_type == 'fe55_flat'
    and observation_reason == 'fe55'"""
    exposure = getRef(deferredDatasetRef).dataId.records["exposure"]
    return exposure.observation_type == 'fe55_flat'\
        and exposure.observation_reason == 'fe55'


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
                             "exposure.observation_type = 'bias' AND exposure.observation_reason = 'bias'",  # noqa
                             eoSelectBiasBias)
EoDataSelection.addSelection("botPersistenceBias",
                             "Select bias exposures from bot_persistence acquistions",
                             "exposure.observation_type = 'bias' AND exposure.observation_reason = 'bot_persistence'",  # noqa
                             eoSelectBotPersistanceBias)
EoDataSelection.addSelection("fe55Bias",
                             "Select bias exposures from Fe55 acquistions",
                             "exposure.observation_type = 'bias' AND exposure.observation_reason = 'fe55_flat'",  # noqa
                             eoSelectFe55Bias)
EoDataSelection.addSelection("darkDark",
                             "Select dark exposures from dark acquistions",
                             "exposure.observation_type = 'dark' AND exposure.observation_reason = 'dark'",  # noqa
                             eoSelectDarkDark)
EoDataSelection.addSelection("botPersistenceDark",
                             "Select dark exposures from bot_persistence acquistions",
                             "exposure.observation_type = 'dark' AND exposure.observation_reason = 'bot_persistence'",  # noqa
                             eoSelectBotPersistenceDark)
EoDataSelection.addSelection("flatFlat",
                             "Select flat exposures from flat pair acquistions",
                             "exposure.observation_type = 'flat' AND exposure.observation_reason = 'flat'",  # noqa
                             eoSelectFlatFlat)
EoDataSelection.addSelection("anySuperFlat",
                             "Select flat exposures from any superflat acquistions",
                             "exposure.observation_type = 'flat' AND exposure.observation_reason = 'sflat'",  # noqa
                             eoSelectAnySuperFlat)
EoDataSelection.addSelection("superFlatLow",
                             "Select flat exposures from low-intensity superflat acquistions",
                             "exposure.observation_type = 'flat' AND exposure.observation_reason = 'sflat' AND exposure.exposure_time < 30.",  # noqa
                             eoSelectSuperFlatLow)
EoDataSelection.addSelection("superFlatHigh",
                             "Select flat exposures from high-intensity superflat acquistions",
                             "exposure.observation_type = 'flat' AND exposure.observation_reason = 'sflat' AND exposure.exposure_time >= 30.",  # noqa
                             eoSelectSuperFlatHigh)
EoDataSelection.addSelection("fe55Flat",
                             "Select fe55 exposures acquistions",
                             "exposure.observation_type = 'fe55_flat' AND exposure.observation_reason = 'fe55'",  # noqa
                             eoSelectFe55Flat)
