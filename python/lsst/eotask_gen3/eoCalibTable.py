""" Base classes for Electrical Optical (EO) calibration data

These classes define the interface between the transient data classes used
in EO test code, and the `astropy.table.Table` classes used for persistent
storage.

Specifically they provide ways to define table structures in schema, and the
use those schema to facilitate backwards compatibility.
"""

import sys

from typing import Mapping

from collections import OrderedDict

from astropy.table import Table, Column

__all__ = ["EoCalibField", "EoCalibTableSchema", "EoCalibTable", "EoCalibTableHandle"]


class EoCalibField:
    """ Defines a single field and provide the information needed to connect
    a Class attribute (e.g., self.aVariable) to an
    `astropy.table.Column` (e.g., 'VARIABLE')

    Parameters
    ----------
    name : `str`
        Name of the column.  In UPPER by convention.
    dtype : `type`
        Data type for elements in the Column.  E.g., `float` or `int`.
    shape : `list`
        Define the shape of each element in the Column.
        List elements can be either `int` or `str`
        `str` elements will replaced with `int` at construction using keywords
    kwds : `dict` , [`str`, `Any`]
        These will be passed to `astropy.table.Column` constructor.

    Notes
    -----
    This class should be used as class attribute in defining table schema
    classes,  I.e., it should only ever appear as a class attribute in a
    sub-class of `EoCalibTableSchema`

    """

    @staticmethod
    def _format_shape(shape, **kwargs):
        """ Format the list of shape elements, replacing any `str` using
        keywords

        Parameters
        ----------
        shape : `list`
            Define the shape of each element in the Column.
        kwargs : `dict`,  [`str`, `Any`]
            Used to replace the str elements in shape

        Returns
        -------
        outShape : `tuple`, [`int`]
            The shape of each element in the column
        """
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
        """ C'tor,  Fills class parameters """
        kwcopy = kwargs.copy()
        self._name = kwcopy.pop('name')
        self._dtype = kwcopy.pop('dtype', float)
        self._shape = kwcopy.pop('shape', [1])
        self._kwds = kwcopy

    @property
    def name(self):
        """ Name of the Column. """
        return self._name

    @property
    def dtype(self):
        """ Data type for elements in the Column. """
        return self._dtype

    @property
    def shape(self):
        """ Template shape of each element in the Column. """
        return self._shape

    @property
    def kwds(self):
        """ Remaining keywords passed to Column constructor. """
        return self._kwds

    def validateColumn(self, column):
        """ Check that a column matches the definition.

        Raises
        ------
        ValueError : Column data type does not match definition.
        """
        if 'unit' in self._kwds:
            column.unit = self._kwds['unit']
        if 'description' in self._kwds:
            column.description = self._kwds['description']
        # if column.dtype.type != self._dtype:
        #    raise ValueError("Column %s data type not equal to schema data type %s != %s" %   # noqa
        #                     (column.name, column.dtype.type, self._dtype))

    def validateValue(self, value):
        """ Check that a value matches the definition and can be
        used to fill a column.

        Raises
        ------
        ValueError : value data type does not match definition.
        """
        # if value.dtype.type != self._dtype:
        #    raise ValueError("Item %s data type not equal to schema data type %s != %s" %   # noqa
        #                     (self._name, type(value), self._dtype))

    def makeColumn(self, **kwargs):
        """ Construct and return an `astropy.table.Column`

        Notes
        -----
        Uses keyword arguements in two ways:
             1. Replace string in shape template
             2. `length' is used to set column lenght
        """
        return Column(name=self._name, dtype=self._dtype,
                      shape=self._format_shape(self._shape, **kwargs),
                      length=kwargs.get('length', 0),
                      **self._kwds)

    def convertToValue(self, column, **kwargs):
        """ Return data from column as a `numpy.array`

        Keywords
        --------
        validate : `bool`
            If true, will validate the column
        """
        if kwargs.get('validate', False):  # pragma: no cover
            self.validateColumn(column)
        return column.data

    def convertToColumn(self, value, **kwargs):
        """ Construct and return an `astropy.table.Column` from value.

        Keywords
        --------
        validate : `bool`
            If true, will validate the value
        """
        if kwargs.get('validate', False):  # pragma: no cover
            self.validateValue(value)
        return Column(name=self._name, dtype=self._dtype,
                      data=value, **self._kwds)

    def writeMarkdownLine(self, varName, stream=sys.stdout):
        """ Write a line of markdown describing self to stream

        Parameters
        ----------
        varName : `str`
            The name of the variable associated to this field.
        """
        md_dict = dict(varName=varName,
                       name=self._name,
                       dtype=self.dtype.__name__,
                       shape=self.shape,
                       unit="", description="")
        md_dict.update(self._kwds)
        tmpl = "| {varName} | {name} | {dtype} | {shape} | {unit} | {description} | \n".format(**md_dict)
        stream.write(tmpl)

    def copy(self, **kwargs):
        """ Return an udpated copy of self using keyword to override fields """
        kwcopy = dict(name=self._name, dtype=self._dtype, shape=self._shape)
        kwcopy.update(self.kwds)
        kwcopy.update(kwargs)
        return EoCalibField(**kwcopy)


class EoCalibTableSchema:
    """ Stores schema for a single `astropy.table.Table`

    Each sub-class will define one version of the schema.
    The naming convention for the sub-classes is:
    {DataClassName}SchemaV{VERSION} e.g., 'EoTableDataSchemaV0'

    Parameters
    ----------
    TABLELENGTH : `str`
        Name of the keyword to use to extract table length
    fieldDict : `OrderedDict`, [`str`, `EoCalibField`]
        Maps field names (e.g., 'aVariable') to EoCalibField objects
    columnDict : `OrderedDict`, [`str`, `str`]
        Maps column names (e.g., 'VARIABLE') to field names
    """

    TABLELENGTH = ""

    @classmethod
    def findFields(cls):
        """ Find and return the EoCalibField objects in a class

        Returns
        -------
        fields : `OrderedDict`, [`str`, `EoCalibField`]
        """
        theClasses = cls.mro()
        fields = OrderedDict()
        for theClass in theClasses:
            for key, val in theClass.__dict__.items():
                if isinstance(val, EoCalibField):
                    fields[key] = val
        return fields

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
        return int(cStr[cStr.find("SchemaV")+7:])

    @classmethod
    def dataClassName(cls):
        """ Return the name of the associated data class

        This relies on the naming convention: {DataClassName}SchemaV{VERSION}
        """
        cStr = cls.__name__
        return cStr[:cStr.find("SchemaV")]

    def __init__(self):
        """ C'tor,  Fills class parameters """
        self._fieldDict = self.findFields()
        self._columnDict = OrderedDict([(val.name, key) for key, val in self._fieldDict.items()])

    def validateTable(self, table):
        """ Check that table matches this schema

        Raises
        ------
        KeyError : Columns names in table do not match schema
        """
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
            raise KeyError("%s.validateTable() failed because some columns were not provided %s" %
                           (type(self), str(unused)))

    def validateDict(self, dictionary):
        """ Check that dictionary matches this schema

        Raises
        ------
        KeyError : dictionary keys in table do not match schema
        """
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
            raise KeyError("%s.validateDict() failed because some columns were not provided %s" %
                           (type(self), str(unused)))

    def makeTable(self, **kwargs):
        """ Make and return an `astropy.table.Table`

        Notes
        -----
        keywords are used to define table length and element shapes
        """
        kwcopy = kwargs.copy()
        length = kwcopy.pop(self.TABLELENGTH, 0)
        table = Table([val.makeColumn(length=length, **kwcopy) for val in self._fieldDict.values()])
        table.meta['schema'] = self.fullName()
        table.meta['name'] = kwcopy.pop('name', None)
        table.meta['handle'] = kwcopy.pop('handle', None)
        return table

    def convertToTable(self, dictionary, **kwargs):
        """ Convert dictionary to `astropy.table.Table` and return it

        Keywords
        --------
        validate : `bool`
            If true, will validate the columns

        Raises
        ------
        KeyError : dictionary keys in table do not match schema
        """
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
            raise KeyError("%s.validateDict() failed because some columns were not provided %s" %
                           (type(self), str(unused)))
        table = Table(columns)
        if meta:
            table.meta.update(meta)
        return table

    def convertToDict(self, table, **kwargs):
        """ Convert table to `OrderedDict` and return it

        Keywords
        --------
        validate : `bool`
            If true, will validate the columns

        Raises
        ------
        KeyError : column names in table do not match schema
        """
        unused = {key: True for key in self._fieldDict.keys()}
        outDict = OrderedDict()
        for colName in table.columns:
            try:
                key = self._columnDict[colName]
                field = self._fieldDict[key]
                col = table[colName]
                unused.pop(key)
            except KeyError as msg:  # pragma: no cover
                raise KeyError("Column %s in table is not defined in schema %s" %
                               (colName, type(self))) from msg
            outDict[key] = field.convertToValue(col, **kwargs)
        if unused:  # pragma: no cover
            raise KeyError("%s.convertToDict() failed because some columns were not provided %s" %
                           (type(self), str(unused)))
        outDict['meta'] = table.meta
        return outDict

    def writeMarkdown(self, name, stream=sys.stdout):
        """ Write a table of markdown describing self to stream

        Parameters
        ----------
        name : `str`
            Name of field associated to this schema
        """
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
    """ Provides interface between `astropy.table.Table` and
    `EoCalibTableSchema`

    Each sub-class will define one all the versions of a particular
    data table, and provide backward compatibility
    to older versions of the schema.

    Parameters
    ----------
    SCHEMA_CLASS : `type`
        Current schema class
    PREVIOUS_SCHEMAS : `list`, [`type`]
        Previous schema classes
    schema : `EoCalibTableSchema`
        Schema for this data structure
    table : `astropy.table.Table`
        Table with actual data

    Notes
    -----
    By default this class will construct a table using the current
    version of the schema.  However, it can also use older version,
    e.g., when being constructed from a table being read from an
    old file.
    """

    SCHEMA_CLASS = EoCalibTableSchema
    PREVIOUS_SCHEMAS = []

    def __init__(self, data=None, **kwargs):
        """ C'tor,  Fills class parameters

        Parameters
        ----------
        data : `Union`, [`astropy.table.Table`, `Mapping`, `None`]
            If provided, the data used to build the table
            If `None`, table will be constructed using shape parameters
            taken for kwargs

        Keywords
        --------
        schema : `EoCalibTableSchema`
            If provided will override schema class
        """
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
        """ Return the underlying `astropy.table.Table` """
        return self._table

    @classmethod
    def schema(cls):
        """ Return an instance of the schema """
        return cls.SCHEMA_CLASS()

    @classmethod
    def allSchemaClasses(cls):
        """ Return a `list` of all the associated schema classes """
        return [cls.SCHEMA_CLASS] + cls.PREVIOUS_SCHEMAS

    @classmethod
    def schemaDict(cls):
        """ Return an `OrderedDict` of all the associated schema classes
        mapped by class name """
        return OrderedDict([(val.fullName(), val) for val in cls.allSchemaClasses()])


class EoCalibTableHandle:
    """ Provide interface between an `EoCalibSchema` and the `EoCalibTable`
    and `EoCalibTableSchema` objects that define it

    This allows a particular `EoCalibData` class to have
        1. Table of different types
        2. Multiple tables of the same type, but with different names

    Parameters
    ----------
    tableName : `str`
        Template for the name of the table.
        Should include '{key}' if this handle is used for multiple tables
    tableClass : `type`
        `EoCalibTable` sub-type associated to the table.
    schema : `EoCalibTableSchema`
        Schema associted to the table
    schemaDict : `OrderedDict`, [`str`, `type`]
        Dictionary mapping from class name to `EoCalibTableSchema` sub-class
    multiKey : `Union`, [`str`, `None`]
        Name of keyword used to replace `{key}` when formating table name
    """

    @staticmethod
    def findTableMeta(tableObj, metaKey):
        """ Find and return metaData from a table-like object

        Parameters
        ----------
        tableObj : `Union`, [`astropy.table.Table`, `OrderedDict']
            The table-like object
        metaKey : `str`
            The key for the meta data field

        Raises
        ------
        TypeError : input object is wrong type.
        """
        if isinstance(tableObj, Table):
            if metaKey in tableObj.meta:
                return tableObj.meta[metaKey]
            return tableObj.meta[metaKey.upper()]
        if isinstance(tableObj, Mapping):
            return tableObj['meta'][metaKey]
        raise TypeError("findTableMeta requires Table or Mapping, not %s" % type(tableObj))  # pragma: no cover # noqa

    def __init__(self, **kwargs):
        """ C'tor,  Fills class parameters """
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
        """ Return the associated schema """
        return self._schema

    @property
    def multiKey(self):
        """ Keyword used to replace `{key}` when formating table name

        `None` means that this handle is assocatied to a single table.
        """
        return self._multiKey

    def getTableSchemaClass(self, tableObj):
        """ Return the schema class associated to a table

        Notes
        -----
        This uses the meta data field 'schema' to get the name
        of the schema class
        """
        tableSchemaName = self.findTableMeta(tableObj, "schema")
        return self._schemaDict[tableSchemaName]

    def validateTable(self, table):
        """ Validate a table using schema """
        tableSchema = self.getTableSchemaClass(table)()
        tableSchema.validateTable(table)

    def validateDict(self, dictionary):
        """ Validate a dictionary using schema """
        tableSchema = self.getTableSchemaClass(dictionary)()
        tableSchema.validateDict(dictionary)

    def convertToTable(self, dictionary):
        """ Convert a dictionary to a table using schema """
        tableSchema = self.getTableSchemaClass(dictionary)()
        return tableSchema.convertToTable(dictionary)

    def convertToDict(self, table):
        """ Convert a table to a dictionary using schema """
        tableSchema = self.getTableSchemaClass(table)()
        return tableSchema.convertToDict(table)

    def makeTables(self, **kwargs):
        """ Build and return `OrderedDict` mapping table names to
        newly created `astropy.table.Table` objects """
        kwcopy = kwargs.copy()
        if self._multiKey is None:
            tableNames = [self._tableName]
        else:
            tableKeys = kwcopy.pop(self._multiKey, [])
            tableNames = [self._tableName.format(key=tableKey) for tableKey in tableKeys]
        return OrderedDict([(tableName, self._tableClass(name=tableName, **kwcopy))
                           for tableName in tableNames])

    def makeEoCalibTable(self, table):
        """ Convert table to `EoCalibTable` by attaching the correct schema """
        tableSchema = self.getTableSchemaClass(table)()
        tableName = self.findTableMeta(table, 'name')
        return self._tableClass(name=tableName, schema=tableSchema, data=table)
