""" Base classes for Electrical Optical (EO) calibration data
"""

import sys

from typing import Mapping

from collections import OrderedDict

from astropy.table import Table, Column

__all__ = ["EoCalibField", "EoCalibTableSchema", "EoCalibTable",
           "GetEoCalibTableSchema", "RegisterEoCalibTableSchema"]


class EoCalibField:

    @staticmethod
    def _format_shape(shape, **kwargs):
        outShape = []
        if shape is None:
            return tuple(outShape)
        for axis in shape:
            if isinstance(axis, int):
                outShape.append(axis)
                continue
            if isinstance(axis, str):
                try:
                    outShape.append(kwargs[axis])
                except KeyError as msg:
                    raise KeyError("Failed to convert EoCalibField column shape %s." % str(shape)) from msg
                continue
            raise TypeError("Axis shape items must be either int or str, not %s" % type(axis))
        return tuple(outShape)

    def __init__(self, **kwargs):
        kwcopy = kwargs.copy()
        self._name = kwcopy.pop('name')
        self._dtype = kwcopy.pop('dtype', float)
        self._shape = kwcopy.pop('shape', None)
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
        if column.dtype != self._dtype:
            raise ValueError("Column %s data type not equal to schema data type %s != %s" %
                             (column.name, column.dtype, self._dtype))

    def validateValue(self, value):
        if not isinstance(value, self._dtype):
            raise ValueError("Item %s data type not equal to schema data type %s != %s" %
                             (self._name, type(value), self._dtype))

    def makeColumn(self, **kwargs):
        return Column(name=self._name, dtype=self._dtype,
                      shape=self._format_shape(self._shape, **kwargs),
                      length=kwargs.get('length', None),
                      **self._kwds)

    def convertToValue(self, column, **kwargs):
        if kwargs.get('validate', False):
            self.validateColumn(column)
        return column.data

    def convertToColumn(self, value, **kwargs):
        if kwargs.get('validate', False):
            self.validateValue(value)
        return Column(name=self._name, dtype=self._dtype,
                      data=value, **self._kwds)

    def writeMarkdownLine(self, varName, stream=sys.stdout):
        md_dict = dict(varName=varName,
                       name=self._name,
                       dtype=self._dtype.__name__,
                       shape=self._shape,
                       unit="", description="")
        md_dict.update(self._kwds)
        tmpl = "| {varName} | {name} | {dtype} | {shape} | {unit} | {description} | \n".format(**md_dict)
        stream.write(tmpl)


class EoCalibTableSchema:

    NAME = ""
    VERSION = 0
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
        return "%s_%s" % (cls.NAME, cls.VERSION)

    def __init__(self):
        self._fieldDict = self.findFields()
        self._columnDict = OrderedDict([(val.name, key) for key, val in self._fieldDict.items()])

    @property
    def fieldDict(self):
        return self._fieldDict

    @property
    def columnDict(self):
        return self._columnDict

    def validateTable(self, table):
        unused = set(self._fieldDict.keys())
        for col in table.columns:
            try:
                key = self._columnDict[col.name]
                field = self._fieldDict[key]
                unused.pop(key)
            except KeyError as msg:
                raise KeyError("Column %s in table is not defined in schema %s" %
                               (col.name, type(self))) from msg
            field.validateColumn(col)
        if unused:
            raise ValueError("%s.validateTable() failed because some columns were not provided %s" %
                             (type(self), str(unused)))

    def validateDict(self, dictionary):
        unused = set(self._fieldDict.keys())
        for key, val in dictionary.items():
            try:
                field = self._fieldDict[key]
                unused.pop(key)
            except KeyError as msg:
                raise KeyError("Column %s in table is not defined in schema %s" %
                               (key, type(self))) from msg
            field.validateValue(val)
        if unused:
            raise ValueError("%s.validateDict() failed because some columns were not provided %s" %
                             (type(self), str(unused)))

    def makeTable(self, **kwargs):
        kwcopy = kwargs.copy()
        length = kwcopy.pop(self.TABLELENGTH, None)
        return Table([val.makeColumn(length=length, **kwcopy) for val in self._fieldDict.values()])

    def convertToTable(self, dictionary, **kwargs):
        unused = set(self._fieldDict.keys())
        columns = []
        for key, val in dictionary.items():
            try:
                field = self._fieldDict[key]
                unused.pop(key)
            except KeyError as msg:
                raise KeyError("Column %s in table is not defined in schema %s" %
                               (key, type(self))) from msg
            columns.append(field.convertToColumn(val), **kwargs)
        if unused:
            raise ValueError("%s.validateDict() failed because some columns were not provided %s" %
                             (type(self), str(unused)))
        return Table(columns)

    def convertToDict(self, table, **kwargs):
        outDict = OrderedDict()
        for col in table.columns:
            try:
                key = self._columnDict[col.name]
                field = self._fieldDict[key]
            except KeyError as msg:
                raise KeyError("Column %s in table is not defined in schema %s" %
                               (col.name, type(self))) from msg
            outDict[key] = field.convertToValue(col, **kwargs)
        return outDict

    def writeMarkdown(self, name, stream=sys.stdout):
        stream.write("|| Name || <td colspan=3>Class<\\td> || Version  || Length ||\n")
        stream.write("| %s | <td colspan=3>%s<\\td> | %i | %s |\n" %
                     (name, self.NAME, self.VERSION, self.TABLELENGTH))
        stream.write("|| Name || Column || Datatype || Shape || Units || Description ||\n")
        for key, val in self._fieldDict.items():
            val.writeMarkdownLine(key, stream)


class EoCalibTable:

    SCHEMA_CLASS = EoCalibTableSchema
    PREVIOUS_SCHEMAS = []

    def __init__(self, data=None, **kwargs):
        self._schema = self.SCHEMA_CLASS()
        self._version = self._schema.VERSION
        if isinstance(data, Table):
            self._schema.validateTable(data)
            self._table = data
        elif isinstance(data, Mapping):
            self._schema.validateDict(data)
            self._table = self._schema.convertToTable(data)
        elif data is None:
            self._table = self._schema.makeTable(**kwargs)
        else:
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

    def attachAttribute(self):
        for key, val in self._schema.fieldDict.items():  # pylint: disable=no-member
            self.__dict__[key] = self._table[val.name]


EO_CALIB_TABLE_SHEMA_DICT = OrderedDict()


def GetEoCalibTableSchema(schemaName):

    try:
        return EO_CALIB_TABLE_SHEMA_DICT[schemaName]
    except KeyError as msg:
        raise KeyError("Failed to get EoCalibTableSchema") from msg


def RegisterEoCalibTableSchema(tableClass):

    if not issubclass(tableClass, EoCalibTable):
        msg = "Can only register EoCalibTable sub-classes not %s" % (type(tableClass))
        raise TypeError(msg)

    for schemaClass in tableClass.allSchemaClasses():
        if not issubclass(schemaClass, EoCalibTableSchema):
            msg = "Can only register EoCalibTableSchema sub-classes not %s" % (type(schemaClass))
            raise TypeError(msg)
        schemaName = schemaClass.fullName()
        if schemaName in EO_CALIB_TABLE_SHEMA_DICT:
            if EO_CALIB_TABLE_SHEMA_DICT[schemaName] == schemaClass:
                continue
            raise KeyError("Tried to add %s with name %s to EoCalibTableSchema, but it already points to %s" %
                           (schemaClass, schemaName, EO_CALIB_TABLE_SHEMA_DICT[schemaName]))
        EO_CALIB_TABLE_SHEMA_DICT[schemaName] = schemaClass
