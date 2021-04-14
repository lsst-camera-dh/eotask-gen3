""" Base classes for Electrical Optical (EO) calibration data
"""

import sys

from typing import Mapping

from collections import OrderedDict

from astropy.table import Table, Column

__all__ = ["EoCalibField", "EoCalibTableSchema", "EoCalibTable", "EoCalibTableHandle"]


class EoCalibField:

    @staticmethod
    def _format_shape(shape, **kwargs):
        outShape = []
        for axis in shape:
            if isinstance(axis, int):
                outShape.append(axis)
                continue
            if isinstance(axis, str):
                try:
                    outShape.append(kwargs[axis])
                    continue
                except KeyError as msg:  # pragma: no cover
                    raise KeyError("Failed to convert EoCalibField column shape %s." % str(shape)) from msg
            raise TypeError("Axis shape items must be either int or str, not %s" % type(axis))  # pragma: no cover # noqa
        return tuple(outShape)

    def __init__(self, **kwargs):
        kwcopy = kwargs.copy()
        self._name = kwcopy.pop('name')
        self._dtype = kwcopy.pop('dtype', float)
        self._shape = kwcopy.pop('shape', [1])
        self._kwds = kwcopy

    @property
    def name(self):
        return self._name

    @property
    def dtype(self):
        return self._dtype

    @property
    def shape(self):
        return self._shape

    @property
    def kwds(self):
        return self._kwds

    def validateColumn(self, column):
        if 'unit' in self._kwds:
            column.unit = self._kwds['unit']
        if 'description' in self._kwds:
            column.description = self._kwds['description']
        # if column.dtype.type != self._dtype:
        #    raise ValueError("Column %s data type not equal to schema data type %s != %s" %   # noqa
        #                     (column.name, column.dtype.type, self._dtype))

    def validateValue(self, value):
        pass
        # if value.dtype.type != self._dtype:
        #    raise ValueError("Item %s data type not equal to schema data type %s != %s" %   # noqa
        #                     (self._name, type(value), self._dtype))

    def makeColumn(self, **kwargs):
        return Column(name=self._name, dtype=self._dtype,
                      shape=self._format_shape(self._shape, **kwargs),
                      length=kwargs.get('length', 0),
                      **self._kwds)

    def convertToValue(self, column, **kwargs):
        if kwargs.get('validate', False):  # pragma: no cover
            self.validateColumn(column)
        return column.data

    def convertToColumn(self, value, **kwargs):
        if kwargs.get('validate', False):  # pragma: no cover
            self.validateValue(value)
        return Column(name=self._name, dtype=self._dtype,
                      data=value, **self._kwds)

    def writeMarkdownLine(self, varName, stream=sys.stdout):
        md_dict = dict(varName=varName,
                       name=self._name,
                       dtype=self.dtype.__name__,
                       shape=self.shape,
                       unit="", description="")
        md_dict.update(self._kwds)
        tmpl = "| {varName} | {name} | {dtype} | {shape} | {unit} | {description} | \n".format(**md_dict)
        stream.write(tmpl)

    def copy(self, **kwargs):
        kwcopy = dict(name=self._name, dtype=self._dtype, shape=self._shape)
        kwcopy.update(self.kwds)
        kwcopy.update(kwargs)
        return EoCalibField(**kwcopy)


class EoCalibTableSchema:

    TABLELENGTH = ""

    @classmethod
    def findFields(cls):
        theClasses = cls.mro()
        fields = OrderedDict()
        for theClass in theClasses:
            for key, val in theClass.__dict__.items():
                if isinstance(val, EoCalibField):
                    fields[key] = val
        return fields

    @classmethod
    def fullName(cls):
        return cls.__name__

    @classmethod
    def version(cls):
        cStr = cls.__name__
        return int(cStr[cStr.find("SchemaV")+7:])

    @classmethod
    def dataClassName(cls):
        cStr = cls.__name__
        return cStr[:cStr.find("SchemaV")]

    def __init__(self):
        self._fieldDict = self.findFields()
        self._columnDict = OrderedDict([(val.name, key) for key, val in self._fieldDict.items()])

    def validateTable(self, table):
        unused = {key: True for key in self._fieldDict.keys()}
        for col in table.columns:
            try:
                key = self._columnDict[col]
                field = self._fieldDict[key]
                unused.pop(key, None)
            except KeyError as msg:  # pragma: no cover
                raise KeyError("Column %s in table is not defined in schema %s" %
                               (col.name, type(self))) from msg
            field.validateColumn(table[col])
        if unused:  # pragma: no cover
            raise ValueError("%s.validateTable() failed because some columns were not provided %s" %
                             (type(self), str(unused)))

    def validateDict(self, dictionary):
        unused = {key: True for key in self._fieldDict.keys()}
        for key, val in dictionary.items():
            if key == 'meta':
                continue
            try:
                field = self._fieldDict[key]
                unused.pop(key, None)
            except KeyError as msg:  # pragma: no cover
                raise KeyError("Column %s in table is not defined in schema %s" %
                               (key, type(self))) from msg
            field.validateValue(val)
        if unused:  # pragma: no cover
            raise ValueError("%s.validateDict() failed because some columns were not provided %s" %
                             (type(self), str(unused)))

    def makeTable(self, **kwargs):
        kwcopy = kwargs.copy()
        length = kwcopy.pop(self.TABLELENGTH, 0)
        table = Table([val.makeColumn(length=length, **kwcopy) for val in self._fieldDict.values()])
        table.meta['schema'] = self.fullName()
        table.meta['name'] = kwcopy.pop('name', None)
        table.meta['handle'] = kwcopy.pop('handle', None)
        return table

    def convertToTable(self, dictionary, **kwargs):
        unused = {key: True for key in self._fieldDict.keys()}
        columns = []
        meta = None
        for key, val in dictionary.items():
            if key == 'meta':
                meta = val
                continue
            try:
                field = self._fieldDict[key]
                unused.pop(key)
            except KeyError as msg:  # pragma: no cover
                raise KeyError("Column %s in table is not defined in schema %s" %
                               (key, type(self))) from msg
            columns.append(field.convertToColumn(val), **kwargs)
        if unused:  # pragma: no cover
            raise ValueError("%s.validateDict() failed because some columns were not provided %s" %
                             (type(self), str(unused)))
        table = Table(columns)
        if meta:
            table.meta.update(meta)
        return table

    def convertToDict(self, table, **kwargs):
        outDict = OrderedDict()
        for colName in table.columns:
            try:
                key = self._columnDict[colName]
                field = self._fieldDict[key]
                col = table[colName]
            except KeyError as msg:  # pragma: no cover
                raise KeyError("Column %s in table is not defined in schema %s" %
                               (colName, type(self))) from msg
            outDict[key] = field.convertToValue(col, **kwargs)
        outDict['meta'] = table.meta
        return outDict

    def writeMarkdown(self, name, stream=sys.stdout):
        stream.write("| Name | Class | Version | Length |\n")
        stream.write("|-|-|-|-|\n")
        stream.write("| %s | %s | %i | %s |\n" %
                     (name, self.dataClassName(), self.version(), self.TABLELENGTH))
        stream.write("\n\n")
        stream.write("| Name | Column | Datatype | Shape | Units | Description |\n")
        stream.write("|-|-|-|-|-|-|\n")
        for key, val in self._fieldDict.items():
            val.writeMarkdownLine(key, stream)
        stream.write("\n\n")

class EoCalibTable:

    SCHEMA_CLASS = EoCalibTableSchema
    PREVIOUS_SCHEMAS = []

    def __init__(self, data=None, **kwargs):
        self._schema = kwargs.get('schema', self.SCHEMA_CLASS())
        self._version = self._schema.version()
        if isinstance(data, Table):
            self._schema.validateTable(data)
            self._table = data
        elif isinstance(data, Mapping):
            self._schema.validateDict(data)
            self._table = self._schema.convertToTable(data)
        elif data is None:
            self._table = self._schema.makeTable(**kwargs)
        else:  # pragma: no cover
            raise TypeError("EoCalibTable input data must be None, Table or dict, not %s" % (type(data)))

    @property
    def table(self):
        return self._table

    @classmethod
    def schema(cls):
        return cls.SCHEMA_CLASS()

    @classmethod
    def allSchemaClasses(cls):
        return [cls.SCHEMA_CLASS] + cls.PREVIOUS_SCHEMAS

    @classmethod
    def schemaDict(cls):
        return OrderedDict([(val.fullName(), val) for val in cls.allSchemaClasses()])


class EoCalibTableHandle:

    @staticmethod
    def findTableMeta(tableObj, metaKey):
        if isinstance(tableObj, Table):
            if metaKey in tableObj.meta:
                return tableObj.meta[metaKey]
            return tableObj.meta[metaKey.upper()]
        if isinstance(tableObj, Mapping):
            return tableObj['meta'][metaKey]
        raise TypeError("findTableMeta requires Table or Mapping, not %s" % type(tableObj))  # pragma: no cover # noqa

    def __init__(self, **kwargs):
        self._tableName = kwargs.get('tableName')
        self._tableClass = kwargs.get('tableClass')
        self._schema = self._tableClass.schema()
        self._schemaDict = self._tableClass.schemaDict()
        self._multiKey = kwargs.get('multiKey', None)
        if self._multiKey is not None:
            if self._tableName.find('{key}') < 0:  # pragma: no cover
                raise ValueError("EoCalibTableHandle has _multiKey, but tableName does not contain '{key}'")

    @property
    def schema(self):
        return self._schema

    @property
    def multiKey(self):
        return self._multiKey

    def getTableSchemaClass(self, tableObj):
        tableSchemaName = self.findTableMeta(tableObj, "schema")
        return self._schemaDict[tableSchemaName]

    def validateTable(self, table):
        tableSchema = self.getTableSchemaClass(table)()
        tableSchema.validateTable(table)

    def validateDict(self, dictionary):
        tableSchema = self.getTableSchemaClass(dictionary)()
        tableSchema.validateDict(dictionary)

    def convertToTable(self, dictionary):
        tableSchema = self.getTableSchemaClass(dictionary)()
        return tableSchema.convertToTable(dictionary)

    def convertToDict(self, table):
        tableSchema = self.getTableSchemaClass(table)()
        return tableSchema.convertToDict(table)

    def makeTables(self, **kwargs):
        kwcopy = kwargs.copy()
        if self._multiKey is None:
            tableNames = [self._tableName]
        else:
            tableKeys = kwcopy.pop(self._multiKey, [])
            tableNames = [self._tableName.format(key=tableKey) for tableKey in tableKeys]
        return OrderedDict([(tableName, self._tableClass(name=tableName, **kwcopy))
                           for tableName in tableNames])

    def makeEoCalibTable(self, table):
        tableSchema = self.getTableSchemaClass(table)()
        tableName = self.findTableMeta(table, 'name')
        return self._tableClass(name=tableName, schema=tableSchema, data=table)
