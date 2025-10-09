from collections import OrderedDict

from thaumic.typemappings.fielddata import CHAR_TYPES

DEFAULT_DELIMITER = '\\t'

class BcpNativeField:
	def __init__(self, fd, ordinal, delimiter=DEFAULT_DELIMITER):
		self.ordinal = ordinal
		self.target_ordinal = fd.ordinal_position
		self.fieldname = fd.column_name
		self.length = 0
		self.max_length = 0
		self.delimiter = f'"{delimiter}"'
		self.datatype = 'SQLCHAR'
		self.max_length = 20
		if fd.type_name in CHAR_TYPES:
			self.coalation = 'SQL_Latin1_General_CP1_CI_AS'
			self.max_length = fd.length
		else:
			self.coalation = '""'

	def output(self):
		example = ('1       SQLCHAR             0       7       ","    1     '
		           '_Action                                                                          '
		           'SQL_Latin1_General_CP1_CI_AS'
		    )
		return (f"{str(self.ordinal):<8} {self.datatype:<20} "
		          f"{str(self.length):<8} {str(self.max_length):<8} "
		          f"{self.delimiter:<10} {str(self.target_ordinal):<6} "
		          f"{str(self.fieldname):<81} {str(self.coalation)}")


def generate_bcp_format(sqltable, columnlist, delimiter, terminator='\\n'):
	retval = ['14.0',f'{len(columnlist)}']
	counter = 0
	fieldlist = []
	for columnname in columnlist:
		counter += 1
		if columnname not in sqltable.fielddict:
			raise ValueError(f"Column {columnname} not found in {sqltable.tablename}")

		fieldlist.append(BcpNativeField(sqltable.fielddict[columnname].fd, counter, delimiter))
	fieldlist[-1].delimiter = f'"{terminator}"'
	for onefield in fieldlist:
		retval.append(onefield.output())
	retval.append('')
	return '\n'.join(retval)


def generate_bcp_format_xml(sqltable, columnlist):
	fieldwords = []
	columnwords = []
	columnname_copy = columnlist[:]
	lastfield = columnlist[-1]
	counter = 0
	for field in sqltable.fieldlist:
		counter += 1
		if field.name not in columnname_copy:
			continue
		columnname_copy.remove(field.name)
		newfield = BcpField(str(counter))
		newcolumn = BcpColumn(field.name, newfield)
		newcolumn.set_from_fd(field.fd)
		if field == lastfield:
			newfield.terminator = '\\n'
		fieldwords.append(repr(newfield))
		columnwords.append(repr(newcolumn))
	if len(columnname_copy) > 0:
		raise ValueError(f'Leftover columns: {columnname_copy}')

	retval = ['<?xml version="1.0"?>',
	          '<BCPFORMAT xmlns="http://schemas.microsoft.com/sqlserver/2004/bulkload/format" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">',
	          '<RECORD>'
		]
	retval.extend(fieldwords)
	retval.extend(['</RECORD>','<ROW>'])
	retval.extend(columnwords)
	retval.extend(['</ROW>','</BCPFORMAT>'])
	return '\r\n'.join(retval)


class BcpField:
	def __init__(self, name, xsi_type='CharTerm', terminator=',', maxlength=None):
		self.id = name                # Specifies the logical name of the field in the data file. The ID of a field is the key used to refer to the field.
		self.xsi_type = xsi_type      # Will always be CharTerm for our purposes
		self.length = None            # This attribute defines the length for an instance of a fixed-length data type. The value of n must be a positive integer.
		self.prefix_length = None     # This attribute defines the prefix length for a binary data representation. The PREFIX_LENGTH value, p, must be one of the following: 1, 2, 4, or 8.
		self.max_length = maxlength   # This attribute is the maximum number of bytes that can be stored in a given field. Without a target table, the column max-length is not known. The MAX_LENGTH attribute restricts the maximum length of an output character column, limiting the storage allocated for the column value. This is especially convenient when using the OPENROWSET function's BULK option in a SELECT FROM clause. The value of m must be a positive integer. By default, the maximum length is 8000 characters for a char column and 4000 characters for an nchar column.
		self.collation = None         # COLLATION is only allowed for character fields.For a list of the SQL collation names, see SQL Server Collation Name (Transact-SQL).
		self.terminator = terminator  # This attribute specifies the terminator of a data field. The terminator can be any character. The terminator must be a unique character that is not part of the data. By default, the field terminator is the tab character (represented as \t). To represent a paragraph mark, use \r\n.

	def __repr__(self):
		attributes = OrderedDict()
		attributes['ID'] = self.id
		attributes['xsi:type'] = self.xsi_type
		if self.length is not None:
			attributes['LENGTH'] = f"{self.length}"
		if self.prefix_length is not None:
			attributes['PREFIX_LENGTH'] = f"{self.prefix_length}"
		if self.max_length is not None:
			attributes['MAX_LENGTH'] = f"{self.max_length}"
		if self.collation is not None:
			attributes['COLLATION'] = f"{self.collation}"
		if self.terminator is not None:
			attributes['TERMINATOR'] = f"{self.terminator}"
		attrlist = []
		for key, value in attributes.items():
			attrlist.append(f'{key}="{value}"')
		attrstr = ' '.join(attrlist)
		return f'<FIELD {attrstr} />'

# NativeFixed	LENGTH	None.
# NativePrefix	PREFIX_LENGTH	MAX_LENGTH
# CharFixed	LENGTH	COLLATION
# NCharFixed	LENGTH	COLLATION
# CharPrefix	PREFIX_LENGTH	MAX_LENGTH, COLLATION
# NCharPrefix	PREFIX_LENGTH	MAX_LENGTH, COLLATION
# CharTerm	TERMINATOR	MAX_LENGTH, COLLATION
# NCharTerm	TERMINATOR	MAX_LENGTH, COLLATION

TYPE_TRANSLATOR = {
	'BIGINT'       : 'SQLBIGINT',
	'BINARY'       : 'SQLBINARY',
	'BIT'          : 'SQLBIT',
	'CHAR'         : 'SQLCHAR',
	'DATETIME'     : 'SQLDATETIME',
	'DEC'          : 'SQLDECIMAL',
	'DECIMAL'      : 'SQLDECIMAL',
	'DOUBLE'       : 'SQLFLT8',
	'FLOAT'        : 'SQLFLT4',
	'INT'          : 'SQLINT',
	'INTEGER'      : 'SQLINT',
	'LONGVARBINARY': 'SQLVARYBIN',
	'LONGVARCHAR'  : 'SQLTEXT',
	'MONEY'        : 'SQLMONEY',
	'NCHAR'        : 'SQLNCHAR',
	'NTEXT'        : 'SQLNTEXT',
	'NUMERIC'      : 'SQLDECIMAL',
	'NVARCHAR'     : 'SQLNVARCHAR',
	'REAL'         : 'SQLFLT8',
	'SMALLINT'     : 'SQLSMALLINT',
	'SMALLMONEY'   : 'SQLMONEY4',
	'TEXT'         : 'SQLTEXT',
	'TINYINT'      : 'SQLTINYINT',
	'VARBINARY'    : 'SQLVARYBIN',
	'VARCHAR'      : 'SQLVARYCHAR',
}



class BcpColumn:
	def __init__(self, name, fieldsource):
		self.name = name         # column name in the database
		self.source = fieldsource.id     # String that matches the id of the matching field
		self.xsi_type = None     # This is an XML construct (used like an attribute) that identifies the type of the instance of the element.
		self.length = None       # can be pulled from FieldDescriptor
		self.precision = None    # can be pulled from FieldDescriptor
		self.scale = None        # can be pulled from FieldDescriptor
		self.nullable = None     # Can it be null? "YES" or "NO"

	def __repr__(self):
		attributes = OrderedDict()
		attributes['SOURCE'] = self.source
		attributes['NAME'] = self.name
		attributes['xsi:type'] = self.xsi_type
		if self.length is not None:
			attributes['LENGTH'] = f"{self.length}"
		if self.precision is not None:
			attributes['PRECISION'] = f"{self.precision}"
		if self.scale is not None:
			attributes['SCALE'] = f"{self.scale}"
		if self.nullable is not None:
			attributes['NULLABLE'] = f"{self.nullable}"
		attrlist = []
		for key, value in attributes.items():
			attrlist.append(f'{key}="{value}"')
		attrstr = ' '.join(attrlist)
		return f'<COLUMN {attrstr} />'

	def set_from_fd(self, fd):
		if fd.nullable:
			self.nullable = 'YES'
		else:
			self.nullable = 'NO'
		self.xsi_type = TYPE_TRANSLATOR[fd.type_name]
		print(f"Converted {fd.type_name} to {self.xsi_type}")
		#
		# if fd.type_name in FLOAT_TYPES:
		# 	self.precision = float(fd.precision)
		# 	self.scale = float(fd.scale)
		# elif fd.typename in VARLENCHAR_TYPES:
		# 	self.length = fd.length

# Type Category	<COLUMN> Data Types	Required XML Attribute(s)
#
# for Data Type	Optional XML Attribute(s)
#
# for Data Type
# Fixed	SQLBIT, SQLTINYINT, SQLSMALLINT, SQLINT, SQLBIGINT, SQLFLT4, SQLFLT8, SQLDATETIME, SQLDATETIM4,
# SQLDATETIM8, SQLMONEY, SQLMONEY4, SQLVARIANT, and SQLUNIQUEID	None.	NULLABLE
# Variable Number	SQLDECIMAL and SQLNUMERIC	None.	NULLABLE, PRECISION, SCALE
# LOB	SQLIMAGE, CharLOB, SQLTEXT, and SQLUDT	None.	NULLABLE
# Character LOB	SQLNTEXT	None.	NULLABLE
# Binary string	SQLBINARY and SQLVARYBIN	None.	NULLABLE, LENGTH
# Character string	SQLCHAR, SQLVARYCHAR, SQLNCHAR, and SQLNVARCHAR	None.	NULLABLE, LENGTH
