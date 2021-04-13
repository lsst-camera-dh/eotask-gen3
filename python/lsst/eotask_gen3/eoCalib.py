""" Base class for Electrical Optical (EO) calibration data
"""

import sys

from typing import Mapping

from collections import OrderedDict

from astropy.table import Table


__all__ = ["EoCalibTableHandle", "EoCalibSchema", "EoCalib"]


class EoCalibTableHandle:

    def __init__(self, **kwargs):
        self._tableName = kwargs.get('tableName')
        self._tableClass = kwargs.get('tableClass')
        self._schema = self._tableClass.schema()
        self._multiKey = kwargs.get('multiKey', None)
        if self._multiKey is not None:
            if self._tableName.find('{key}') < 0:
                raise ValueError("EoCalibTableHandle has _multiKey, but tableName does not contain '{key}'")

    @property
    def schema(self):
        return self._schema
            
    def validateTable(self, table):
        if self._schema is None:
            return
        self._schema.validateTable(table)

    def validateDict(self, dictionary):
        if self._schema is None:
            return
        self._schema.validateDict(dictionary)

    def castToTable(self, tableObj):
        if isinstance(tableObj, Table):
            self.validateTable(tableObj)
            return tableObj
        if isinstance(tableObj, Mapping):
            self.validateDict(tableObj)
            tableObj = Table(tableObj)
            return tableObj
        raise ValueError("EoCalibTableHandle.castToTable requires Table or Mapping, not %s" % type(tableObj))

    def makeTables(self, **kwargs):
        kwcopy = kwargs.copy()
        if self._multiKey is None:
            return self._tableClass(**kwcopy)
        tableKeys = kwcopy.pop(self._multiKey, [])
        return OrderedDict([(self._tableName.format(key=tableKey), self._tableClass(**kwcopy))
                           for tableKey in tableKeys])


class EoCalibSchema:

    NAME = ""
    VERSION = None

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
        return "%s_%s" % (cls.NAME, cls.VERSION)

    def __init__(self):
        self._allTableHandles = self.findTableHandles()

    def getTableSchema(self, tableSchemaName):
        if tableSchemaName is None:
            return None
        try:
            tableHandle = self._allTableHandles[tableSchemaName]
        except KeyError as msg:
            raise KeyError("Could not find tableSchema %s in eoCalibSchema %s" %
                           (tableSchemaName, type(self))) from msg
        return tableHandle.schema

    def validateTable(self, table, tableSchemaName):
        tableSchema = self.getTableSchema(tableSchemaName)
        if tableSchema is None:
            return
        tableSchema.validateTable(table)

    def validateTables(self, tableList):
        for table in tableList:
            tableSchemaName = table.meta['schema']
            self.validateTable(table, tableSchemaName)

    def validateDict(self, dictionary, tableSchemaName):
        tableSchema = self.getTableSchema(tableSchemaName)
        if tableSchema is None:
            return
        tableSchema.validateDict(dictionary)

    def validateDicts(self, dictionary):
        for val in dictionary.values():
            tableSchemaName = val['schema']
            self.validateDict(val, tableSchemaName)

    def castToTable(self, tableObj):
        if tableObj is None:
            return None
        if isinstance(tableObj, Table):
            tableSchemaName = tableObj.meta['schema']
            self.validateTable(tableObj, tableSchemaName)
            return tableObj
        if isinstance(tableObj, Mapping):
            tableSchemaName = tableObj['schema']
            self.validateDict(tableObj, tableSchemaName)
            tableObj = Table(tableObj)
            return tableObj
        raise TypeError('Can only cast Mapping and Table to Table, not %s' % type(tableObj))

    def castToTables(self, tableObjs):
        return [self.castToTable(tableObj) for tableObj in tableObjs]

    def tableToDict(self, table):
        if table is None:
            return None
        if not isinstance(table, Table):
            raise TypeError('tableToDict was passed a %s, which is not a Table' % type(table))
        tableSchemaName = table.meta['schema']
        tableSchema = self.getTableSchema(tableSchemaName)
        if tableSchema is None:
            return table.to_dict()
        return tableSchema.toDict(table)

    def tablesToDicts(self, tables):
        return OrderedDict([(table.extname, self.tableToDict(table)) for table in tables])

    def makeTables(self, **kwargs):
        tables = OrderedDict()
        for key, val in self._allTableHandles.items():
            tables[key] = val.makeTables(**kwargs)
        return tables

    def writeMarkdown(self, stream=sys.stdout):
        for key, val in self._allTableHandles.items():
            val.schema.writeMarkdown(key, stream)
            stream.write("|-|-|-|-|-|-|\n")


class EoCalib:

    SCHEMA_CLASS = EoCalibSchema
    PREVIOUS_SCHEMAS = []

    _OBSTYPE = 'eoGeneric'
    _SCHEMA = SCHEMA_CLASS.fullName()
    _VERSION = SCHEMA_CLASS.VERSION

    def __init__(self, data=None, **kwargs):
        self._schema = kwargs.get('schema', self.SCHEMA_CLASS())
        self._version = self._schema.VERSION
        if isinstance(data, list):
            self._tables = self._schema.castToTables(data)
        elif isinstance(data, Mapping):
            self._tables = self._schema.castToTables(data)
        elif data is None:
            self._tables = self._schema.makeTables(**kwargs)
        else:
            raise TypeError("EoCalib input data must be None, Table or dict, not %s" % (type(data)))

    @property
    def schema(self):
        return self._schema

    def __eq__(self, other):
        return False

    def updateMetadata(self, setDate=False, **kwargs):
        pass

    @classmethod
    def fromDict(cls, dictionary, **kwargs):
        return cls(data=dictionary, **kwargs)

    def toDict(self):
        return self._schema.tablesToDicts(self._tables)

    @classmethod
    def fromTable(cls, tableList, **kwargs):
        return cls(data=tableList, **kwargs)

    def toTable(self):
        return self._tables

    @classmethod
    def allSchemaClasses(cls):
        return [cls.SCHEMA_CLASS] + cls.PREVIOUS_SCHEMAS


EO_CALIB_SCHEMA_DICT = OrderedDict()


def GetEoCalibSchema(schemaName):
    try:
        return EO_CALIB_SCHEMA_DICT[schemaName]
    except KeyError as msg:
        raise KeyError("Failed to get EoCalibSchema") from msg


def RegisterEoCalibSchema(calibClass):

    if not issubclass(calibClass, EoCalib):
        msg = "Can only register EoCalib sub-classes, not %s" % (type(calibClass))
        raise TypeError(msg)

    for schemaClass in calibClass.allSchemaClasses():
        if not issubclass(schemaClass, EoCalibSchema):
            msg = "Can only register EoCalibSchema sub-classes, not %s" % (type(schemaClass))
            raise TypeError(msg)

        schemaName = schemaClass.fullName()
        if schemaName in EO_CALIB_SCHEMA_DICT:
            if EO_CALIB_SCHEMA_DICT[schemaName] == schemaClass:
                continue
            raise KeyError("Tried to add %s with name %s to EoCalibSchema, but it already points to %s" %
                           (schemaClass, schemaName, EO_CALIB_SCHEMA_DICT[schemaName]))
        EO_CALIB_SCHEMA_DICT[schemaName] = schemaClass
