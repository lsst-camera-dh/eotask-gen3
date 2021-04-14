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

    @classmethod
    def findTableHandles(cls):
        """Find quanitites that associated with a class"""
        theClasses = cls.mro()
        tableHandles = OrderedDict()
        for theClass in theClasses:
            for key, val in theClass.__dict__.items():
                if isinstance(val, EoCalibTableHandle):
                    tableHandles[key] = val
        return tableHandles

    @classmethod
    def fullName(cls):
        return cls.__name__

    @classmethod
    def version(cls):
        cStr = cls.__name__
        try:
            return int(cStr[cStr.find("SchemaV")+7:])
        except ValueError:
            pass
        return None

    @classmethod
    def dataClassName(cls):
        cStr = cls.__name__
        return cStr[:cStr.find("SchemaV")]

    def __init__(self):
        self._allTableHandles = self.findTableHandles()

    def getTableHandle(self, tableObj):
        tableHandleName = EoCalibTableHandle.findTableMeta(tableObj, 'handle')
        return self._allTableHandles[tableHandleName]

    def castToTable(self, tableObj):
        tableHandle = self.getTableHandle(tableObj)
        if isinstance(tableObj, Table):
            tableHandle.validateTable(tableObj)
            return tableObj
        if isinstance(tableObj, Mapping):
            tableHandle.validateDict(tableObj)
            return tableHandle.convertToTable(tableObj)
        raise TypeError('Can only cast Mapping and Table to Table, not %s' % type(tableObj))  # pragma: no cover # noqa

    def castToTables(self, tableObjs):
        return [self.castToTable(tableObj) for tableObj in tableObjs]

    def tableToDict(self, table):
        if not isinstance(table, Table):  # pragma: no cover
            raise TypeError('tableToDict was passed a %s, which is not a Table' % type(table))
        tableHandle = self.getTableHandle(table)
        return tableHandle.convertToDict(table)

    def tablesToDicts(self, tables):
        return OrderedDict([(table.meta['name'], self.tableToDict(table)) for table in tables])

    def makeTables(self, **kwargs):
        tables = OrderedDict()
        for key, val in self._allTableHandles.items():
            tables[key] = val.makeTables(handle=key, **kwargs)
        return tables

    def sortTables(self, tableList):
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
        for key, val in self._allTableHandles.items():
            val.schema.writeMarkdown(key, stream)
            stream.write("|-|-|-|-|-|-|\n")


class EoCalib:

    SCHEMA_CLASS = EoCalibSchema
    PREVIOUS_SCHEMAS = []

    _OBSTYPE = 'eoGeneric'
    _SCHEMA = SCHEMA_CLASS.fullName()
    _VERSION = SCHEMA_CLASS.version()

    def __init__(self, data=None, **kwargs):
        self._schemaDict = OrderedDict([(val.fullName(), val) for val in self.PREVIOUS_SCHEMAS])
        self._schemaDict[self.SCHEMA_CLASS.fullName()] = self.SCHEMA_CLASS
        self._schema = kwargs.get('schema', self.SCHEMA_CLASS())
        self._version = self._schema.version()
        if isinstance(data, list):
            self._tableList = self._schema.castToTables(data)
            self._tableDict = self._schema.sortTables(self._tableList)
        elif isinstance(data, Mapping):
            self._tableList = self._schema.castToTables(data.values())
            self._tableDict = self._schema.sortTables(self._tableList)
        elif data is None:
            self._tableDict = self._schema.makeTables(**kwargs)
            self._tableList = []
            for val in self._tableDict.values():
                for val2 in val.values():
                    self._tableList.append(val2.table)
        else:  # pragma: no cover
            raise TypeError("EoCalib input data must be None, Table or dict, not %s" % (type(data)))

    @property
    def schema(self):
        return self._schema

    @property
    def tables(self):
        return self._tableList

    def __eq__(self, other):
        with open(os.devnull, 'w') as fout:
            return self.reportDiffValues(other, fout)

    def __getitem__(self, key):
        return self._tableDict[key]

    def updateMetadata(self, setDate=False, **kwargs):
        pass

    @classmethod
    def fromDict(cls, dictionary, **kwargs):
        return cls(data=dictionary, **kwargs)

    def toDict(self):
        return self._schema.tablesToDicts(self._tableList)

    @classmethod
    def fromTable(cls, tableList, **kwargs):
        return cls(data=tableList, **kwargs)

    def toTable(self):
        return self._tableList

    @classmethod
    def readFits(cls, filename, **kwargs):
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

        return cls.fromTable(tableList, **kwargs)

    def writeFits(self, filename):
        tableList = self.toTable()
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=Warning, module="astropy.io")
            astropyList = [fits.table_to_hdu(table) for table in tableList]
            astropyList.insert(0, fits.PrimaryHDU())

            writer = fits.HDUList(astropyList)
            writer.writeto(filename, overwrite=True)
        return filename

    def reportDiffValues(self, otherCalib, fileObj=sys.stdout):
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

        schema = cls.SCHEMA_CLASS()
        stream.write("#### Current Schema\n")
        stream.write("#### %s %s\n" % (schema.dataClassName(), schema.fullName()))
        schema.writeMarkdown(stream)

        if cls.PREVIOUS_SCHEMAS:
            stream.write("#### Previous Schema\n")
        for prevSchemaClass in cls.PREVIOUS_SCHEMAS:
            prevSchema = prevSchemaClass()
            stream.write("#### %s\n" % prevSchema.fullName())
            prevSchema.writeMarkdown(stream)


EO_CALIB_CLASS_DICT = OrderedDict()


def GetEoCalibClassDict():
    return EO_CALIB_CLASS_DICT


def RegisterEoCalibSchema(calibClass):
    if not issubclass(calibClass, EoCalib):  # pragma: no cover
        msg = "Can only register EoCalib sub-classes, not %s" % (type(calibClass))
        raise TypeError(msg)

    EO_CALIB_CLASS_DICT[calibClass.__name__] = calibClass


def WriteSchemaMarkdown(fileName):

    with open(fileName, 'w') as fout:

        for key, val in EO_CALIB_CLASS_DICT.items():
            fout.write("## %s\n" % key)
            val.writeMarkdown(fout)
            fout.write("\n\n")
