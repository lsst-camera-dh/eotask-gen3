""" Base class for Electrical Optical (EO) calibration data
"""

import os
import sys
import yaml

from typing import Mapping

from collections import OrderedDict

from astropy.table import Table
from astropy.utils.diff import report_diff_values
from lsst.utils.introspection import get_full_type_name
from lsst.ip.isr import IsrCalib

from .eoCalibTable import EoCalibTableHandle


__all__ = ["EoCalibSchema", "EoCalib",
           "GetEoCalibClassDict",
           "RegisterEoCalibSchema", "WriteSchemaMarkdown"]


class EoCalibSchema:
    """ Stores schema for a `EoCalib` object

    Each sub-class will define one version of the schema.
    The naming convention for the sub-classes is:
    {DataClassName}SchemaV{VERSION} e.g., 'EoCalibDataSchemaV0'

    Parameters
    ----------
    allTableHandles : `OrderedDict`, [`str`, `EoCalibTableHandle`]
        Mapping between handle names and object
    """

    @classmethod
    def findTableHandles(cls):
        """ Find and return the EoCalibTableHandle objects in a class

        Returns
        -------
        tableHandles : `OrderedDict`, [`str`, `EoCalibTableHandle`]
        """
        theClasses = cls.mro()
        tableHandles = OrderedDict()
        for theClass in theClasses:
            for key, val in theClass.__dict__.items():
                if isinstance(val, EoCalibTableHandle):
                    tableHandles[key] = val
        return tableHandles

    @classmethod
    def fullName(cls):
        """ Return the name of this class """
        return cls.__name__

    @classmethod
    def version(cls):
        """ Return the version number of this schema

        This relies on the naming convention: {DataClassName}SchemaV{VERSION}
        """
        cStr = cls.__name__
        try:
            return int(cStr[cStr.find("SchemaV")+7:])
        except ValueError:
            pass
        return None

    @classmethod
    def dataClassName(cls):
        """ Return the name of the associated data class

        This relies on the naming convention: {DataClassName}SchemaV{VERSION}
        """
        cStr = cls.__name__
        return cStr[:cStr.find("SchemaV")]

    def __init__(self):
        """ C'tor,  Fills class parameters """
        self._allTableHandles = self.findTableHandles()

    def getTableHandle(self, tableObj):
        """ Return the `EoCalibTableHandle` associated to tableObj

        This uses the meta data field 'handle' """
        tableHandleName = EoCalibTableHandle.findTableMeta(tableObj, 'handle')
        return self._allTableHandles[tableHandleName]

    def castToTable(self, tableObj):
        """ Use a `EoCalibTableHandle` to cast tableObj to
        `astropy.table.Table` """
        tableHandle = self.getTableHandle(tableObj)
        if isinstance(tableObj, Table):
            tableHandle.validateTable(tableObj)
            return tableObj
        if isinstance(tableObj, Mapping):
            tableHandle.validateDict(tableObj)
            return tableHandle.convertToTable(tableObj)
        raise TypeError('Can only cast Mapping and Table to Table, not %s' % type(tableObj))  # pragma: no cover # noqa

    def castToTables(self, tableObjs):
        """ Cast a list of tableObjs to a list of `astropy.table.Table` """
        return [self.castToTable(tableObj) for tableObj in tableObjs]

    def tableToDict(self, table):
        """ Use a `EoCalibTableHandle` to convert table to `OrderedDict` """
        if not isinstance(table, Table):  # pragma: no cover
            raise TypeError('tableToDict was passed a %s, which is not a Table' % type(table))
        tableHandle = self.getTableHandle(table)
        return tableHandle.convertToDict(table)

    def tablesToDicts(self, tables):
        """ Convert tables to `OrderedDict`, keyed by name """
        return OrderedDict([(table.meta['name'], self.tableToDict(table)) for table in tables])

    def makeTables(self, **kwargs):
        """ Construct and return a nested `OrderedDict` of `EoCalibTable`

        It is keyed by 'handle', 'name'
        """
        tables = OrderedDict()
        for key, val in self._allTableHandles.items():
            tables[key] = val.makeTables(handle=key, **kwargs)
        return tables

    def sortTables(self, tableList):
        """ Sort and return tableList into a nested `OrderedDict` of
        `EoCalibTable`

        It is keyed by 'handle', 'name' and matches return result
        of `makeTables`
        """
        tableDict = OrderedDict()
        for table in tableList:
            tableHandleName = EoCalibTableHandle.findTableMeta(table, 'handle')
            tableHandle = self._allTableHandles[tableHandleName]
            if tableHandle.multiKey is None:
                tableDict[tableHandleName] = tableHandle.makeEoCalibTable(table)
                continue
            if tableHandleName not in tableDict:
                tableDict[tableHandleName] = OrderedDict()
            tableName = EoCalibTableHandle.findTableMeta(table, 'name')
            tableDict[tableHandleName][tableName] = tableHandle.makeEoCalibTable(table)
        return tableDict

    def writeMarkdown(self, stream=sys.stdout):
        """ Write description of this class as markdown to stream """
        for key, val in self._allTableHandles.items():
            val.schema.writeMarkdown(key, stream)


class EoCalib(IsrCalib):
    """ Provides interface between `list` of `astropy.table.Table` and
    `EoCalibSchema`

    Each sub-class will define one all the versions of a particular
    data type, and provide backward compatibility
    to older versions of the schema.

    Parameters
    ----------
    SCHEMA_CLASS : `type`
        Current schema class
    PREVIOUS_SCHEMAS : `list`, [`type`]
        Previous schema classes
    schemaDict : `OrderedDict`, [`str`, `type`]

    schema : `EoCalibSchema`

    version : `int`

    tableList : `list`, [`astropy.table.Table`]

    tableDict : `OrderedDict`, [`str`, `OrderedDict`, [`str`, `EoCalibTable`]]

    """

    SCHEMA_CLASS = EoCalibSchema
    PREVIOUS_SCHEMAS = []

    _OBSTYPE = 'eoGeneric'
    _SCHEMA = SCHEMA_CLASS.fullName()
    _VERSION = SCHEMA_CLASS.version()

    def __init__(self, data=None, **kwargs):
        """ C'tor,  Fills class parameters

        Parameters
        ----------
        data : `Union`, [`list`, `Mapping`, `None`]
            If provided, the data used to build the table
            If `None`, table will be constructed using shape parameters
            taken for kwargs

        Keywords
        --------
        schema : `EoCalibSchema`
            If provided will override schema class
        """
        kwcopy = kwargs.copy()
        camera = kwcopy.pop('camera', None)
        detector = kwcopy.pop('detector', None)
        IsrCalib.__init__(self, camera=camera, detector=detector)
        self._schemaDict = OrderedDict([(val.fullName(), val) for val in self.PREVIOUS_SCHEMAS])
        self._schemaDict[self.SCHEMA_CLASS.fullName()] = self.SCHEMA_CLASS
        self._schema = kwcopy.pop('schema', self.SCHEMA_CLASS())
        self._version = self._schema.version()
        if isinstance(data, list):
            self._tableList = self._schema.castToTables(data)
            self._tableDict = self._schema.sortTables(self._tableList)
        elif isinstance(data, Mapping):
            self._tableList = self._schema.castToTables(data.values())
            self._tableDict = self._schema.sortTables(self._tableList)
        elif data is None:
            self._tableDict = self._schema.makeTables(**kwcopy)
            self._tableList = []
            for val in self._tableDict.values():
                for val2 in val.values():
                    self._tableList.append(val2.table)
        else:  # pragma: no cover
            raise TypeError("EoCalib input data must be None, Table or dict, not %s" % (type(data)))
        if self._tableList:
            self._tableList[0].meta['CALIBCLS'] = get_full_type_name(self)
            self._tableList[0].meta['CALIBSCH'] = self._schema.fullName()

    @classmethod
    def shortName(cls):
        """ Return the name of this class """
        return cls.__name__.replace('Eo', '').replace('Data', '')

    @classmethod
    def allSchemaClasses(cls):
        """ Return a `list` of all the associated schema classes """
        return [cls.SCHEMA_CLASS] + cls.PREVIOUS_SCHEMAS

    @classmethod
    def schemaDict(cls):
        """ Return an `OrderedDict` of all the associated schema classes
        mapped by class name """
        return OrderedDict([(val.fullName(), val) for val in cls.allSchemaClasses()])

    @property
    def schema(self):
        """ Return the schema associated to the data """
        return self._schema

    @property
    def tables(self):
        """ Return the underlying `list` of `astropy.io.Table` """
        return self._tableList

    def __eq__(self, other):
        with open(os.devnull, 'w') as fout:
            return self.reportDiffValues(other, fout)

    def __getitem__(self, key):
        return self._tableDict[key]

    def fromDetector(self, detector):
        """Modify the calibration parameters to match the supplied detector.

        Parameters
        ----------
        detector : `lsst.afw.cameraGeom.Detector`
            Detector to use to set parameters from.

        """
        pass

    @classmethod
    def fromDict(cls, dictionary, **kwargs):
        """ Construct from dictionary """
        return cls(data=dictionary, **kwargs)

    def toDict(self):
        """ Convert to `dict` """
        return self._schema.tablesToDicts(self._tableList)

    @classmethod
    def fromTable(cls, tableList, **kwargs):
        """ Construct from a list of `astropy.io.table` """
        schemaName = tableList[0].meta.get('CALIBSCH', None)
        if schemaName is not None:
            kwargs['schema'] = cls.schemaDict()[schemaName]()
        return cls(data=tableList, **kwargs)

    def toTable(self):
        """ 'Convert to a `list` of `astropy.table.Table`

        Actually just returns the undering list of tables """
        return self._tableList

    def reportDiffValues(self, otherCalib, fileObj=sys.stdout):
        """ Report on all differing values between two `EoCalib` objects

        Parameters
        ----------
        otherCalib : `EoCalib`
            Object to compare against
        fileObj : `file-like`
            Stream to write report to.  Can be dev/null

        Returns
        -------
        identical : `bool`
            True if the object are identical, False otherwise
        """
        if self.schema.fullName() != otherCalib.schema.fullName():
            fileObj.write("EoCalib schema do not match %s != %s" %
                          (self.schema.fullName(), otherCalib.schema.fullName()))
            return False
        identical = True
        for (table1, table2) in zip(self.tables, otherCalib.tables):
            if not report_diff_values(table1, table2):
                identical = False
        return identical

    @classmethod
    def writeMarkdown(cls, stream=sys.stdout):
        """ Write description of this class as markdown to stream """
        schema = cls.SCHEMA_CLASS()
        stream.write("#### Current Schema\n")
        stream.write("##### DataClass: %s\n##### SchemaClass: %s\n" %
                     (schema.dataClassName(), schema.fullName()))
        schema.writeMarkdown(stream)

        if cls.PREVIOUS_SCHEMAS:
            stream.write("#### Previous Schema\n")
        for prevSchemaClass in cls.PREVIOUS_SCHEMAS:
            prevSchema = prevSchemaClass()
            stream.write("##### SchemaClass: %s\n" % prevSchema.fullName())
            prevSchema.writeMarkdown(stream)

    @classmethod
    def fillReportConfigDict(cls, configDict):
        """ Write the yaml config for the html report for this class for the
        slot level """

        if not hasattr(cls, 'figHandles'):
            return

        templateMap = dict(slot=os.path.join("camera", "{raft}", "{slot}", "%s_{raft}_{slot}_%s.png"),
                           raft=os.path.join("camera", "{raft}", "%s_{raft}_%s.png"),
                           camera=os.path.join("camera", "%s_camera_%s.png"))
        keyMap = dict(slot='slot_plot_tables',
                      raft='raft_plot_tables',
                      camera='run_plot_tables')

        for figHandle in cls.figHandles:

            tablesKey = keyMap[figHandle.level]
            whichTemplate = templateMap[figHandle.level]

            if tablesKey not in configDict:
                configDict[tablesKey] = {}

            if figHandle.family not in configDict[tablesKey]:
                configDict[tablesKey][figHandle.family] = dict(header_text=figHandle.family, rows=[])
            whichTable = configDict[tablesKey][figHandle.family]

            whichTable['rows'].append(dict(text=figHandle.description,
                                           figure=whichTemplate % (cls.shortName(), figHandle.name)))

    @classmethod
    def makeFigures(cls, baseName, obj):
        """ Make a set of matplotlib figures for this detector """
        if hasattr(cls, 'figHandles'):
            return OrderedDict([('%s_%s' % (baseName, handle.name), handle(obj))
                                for handle in cls.figHandles if handle.level == 'slot'])
        return OrderedDict()

    @classmethod
    def makeRaftFigures(cls, baseName, raftDataDict):
        """ Make a set of matplotlib figures for a raft """
        if hasattr(cls, 'figHandles'):
            return OrderedDict([('%s_%s' % (baseName, handle.name), handle(raftDataDict))
                                for handle in cls.figHandles if handle.level == 'raft'])
        return OrderedDict()

    @classmethod
    def makeCameraFigures(cls, baseName, cameraDataDict):
        """ Make a set of matplotlib figures for the whole focal plane """
        if hasattr(cls, 'figHandles'):
            return OrderedDict([('%s_%s' % (baseName, handle.name), handle(cameraDataDict))
                                for handle in cls.figHandles if handle.level == 'camera'])
        return OrderedDict()

    @staticmethod
    def writeFigures(basePath, figureDict, fileType="png"):
        """ Write all the figures to disk """
        for key, val in figureDict.items():
            fullPath = os.path.join(basePath, "%s.%s" % (key, fileType))
            print("Writing %s" % fullPath)
            val.savefig(fullPath)


EO_CALIB_CLASS_DICT = OrderedDict()


def GetEoCalibClassDict():
    """ Return the global `OrderedDict` of `EoCalib` sub-classes """
    return EO_CALIB_CLASS_DICT


def RegisterEoCalibSchema(calibClass):
    """ Add calibClass to the global `OrderedDict` of `EoCalib` sub-classes """
    if not issubclass(calibClass, EoCalib):  # pragma: no cover
        msg = "Can only register EoCalib sub-classes, not %s" % (type(calibClass))
        raise TypeError(msg)

    EO_CALIB_CLASS_DICT[calibClass.__name__] = calibClass


def WriteSchemaMarkdown(fileName):
    """ Iterate on the global `OrderedDict` of `EoCalib` sub-classes
    and write description of each to a markdown file """
    with open(fileName, 'w') as fout:

        for key, val in EO_CALIB_CLASS_DICT.items():
            fout.write("## %s\n" % key)
            val.writeMarkdown(fout)
            fout.write("\n\n")


def WriteReportConfigYaml(fileName, dataClasses=None):
    """ Iterate on some `EoCalib` sub-classes
    and for each one iterate on the defined figures and
    generate the correspond yaml need to configure the static report.

    Parameters
    ----------
    fileName : `str`
        The name of the output file
    dataClasses : `Iterable` [`type`]
        The data classes.  If None, will use `EO_CALIB_CLASS_DICT.values()`
    """
    theDict = dict(defaults=dict(action='copy',
                                 header_row_class='header_row',
                                 table_row_class='table_row',
                                 row_class='plot_row',
                                 table_col_class='table_col',
                                 col_desc_class='plot_col_desc',
                                 col_fig_class='plot_col_fig',
                                 col_img_class='plot'))
    if dataClasses is None:
        dataClasses = list(EO_CALIB_CLASS_DICT.values())
    for val in dataClasses:
        val.fillReportConfigDict(theDict)

    with open(fileName, 'w') as fout:
        yaml.dump(theDict, fout)
