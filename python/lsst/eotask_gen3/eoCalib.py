""" Base class for Electrical Optical (EO) calibration data
"""

import os
import sys
import warnings

from typing import Mapping

from collections import OrderedDict

from astropy.table import Table
from astropy.io import fits
from astropy.utils.diff import report_diff_values

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


class EoCalib:
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

    def updateMetadata(self, setDate=False, **kwargs):
        """ FIXME, replace once this inherits from IsrCalib """

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
        return cls(data=tableList, **kwargs)

    def toTable(self):
        """ 'Convert to a `list` of `astropy.table.Table`

        Actually just returns the undering list of tables """
        return self._tableList

    @classmethod
    def readFits(cls, filename, **kwargs):
        """ FIXME, temp function copied for IsrCalib

        Remove once this class inherits from IsrCalib
        """
        with fits.open(filename) as fFits:
            try:
                schemaName = fFits[0].header['schema']  # pylint: disable=no-member  # noqa
            except KeyError:  # pragma: no cover
                schemaName = fFits[0].header['SCHEMA']  # pylint: disable=no-member  # noqa

        schema = cls.schemaDict()[schemaName]()

        tableList = []
        tableList.append(Table.read(filename, hdu=1))
        extNum = 2  # Fits indices start at 1, we've read one already.
        keepTrying = True

        while keepTrying:
            with warnings.catch_warnings():
                warnings.simplefilter("error")
                try:
                    newTable = Table.read(filename, hdu=extNum)
                    tableList.append(newTable)
                    extNum += 1
                except Exception:
                    keepTrying = False

        for table in tableList:
            for k, v in table.meta.items():
                if isinstance(v, fits.card.Undefined):
                    table.meta[k] = None  # pragma: no cover

        return cls.fromTable(tableList, schema=schema, **kwargs)

    def writeFits(self, filename):
        """ FIXME, temp function copied for IsrCalib

        Remove once this class inherits from IsrCalib
        """
        tableList = self.toTable()
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=Warning, module="astropy.io")
            astropyList = [fits.table_to_hdu(table) for table in tableList]

            primaryHdu = fits.PrimaryHDU()
            primaryHdu.header['schema'] = self._schema.fullName()
            astropyList.insert(0, primaryHdu)

            writer = fits.HDUList(astropyList)
            writer.writeto(filename, overwrite=True)
        return filename

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
