import re
from thaumic.util.logger import LOGGER

PRIMARY_KEY = re.compile('\\bPRIMARY[ ]+KEY\\b', re.IGNORECASE)
NOT_NULL = re.compile('\\bNOT[ ]+NULL\\b', re.IGNORECASE)
NULL_OK = re.compile('\\bNULL\\b', re.IGNORECASE)
IDENTITY = re.compile('\\bIDENTITY', re.IGNORECASE)
AUTO_INCREMENT = re.compile('\\bAUTO[_]?INCREMENT', re.IGNORECASE)

# Standard columns for infoschema.columns

C_TABLE_CATALOG = 0
C_TABLE_SCHEMA =  1
C_TABLE_NAME = 2
C_COLUMN_NAME = 3
C_4 =  4
C_DATA_TYPE =  5
C_NUMERIC_PRECISION = 6
C_CHARACTER_MAXIMUM_LENGTH = 7
C_NUMERIC_SCALE =  8
C_NUMERIC_PRECISION_RADIX = 9
C_10 = 10
C_11 =  11
C_COLUMN_DEFAULT = 12
C_13 =  13
C_DATETIME_PRECISION = 14
C_CHARACTER_OCTET_LENGTH = 15
C_ORDINAL_POSITION =  16
C_IS_NULLABLE =  17
C_18 = 18


def extract_quoted(source, start_idx):
	''' extract content within a single-quoted string
	source: containing string
	start_idx: the index of the initial single-quote
	'''
	retval = []
	idx = start_idx + 1
	maxlen = len(source)
	if LOGGER:
		LOGGER.debug(f'Looking at {source}, {start_idx}')
	while idx < maxlen:
		if LOGGER:
			LOGGER.debug(f'iterating: idx = {idx}')
		if source[idx] == "'":
			idx += 1
			if idx >= maxlen or source[idx] != "'":
				return ''.join(retval)
		retval.append(source[idx])
		idx += 1
	return retval


def extract_params(source, start_idx):
	end_idx = source.find(')', start_idx)
	if end_idx == -1:
		return None
	maxlen = len(source)
	preretval = []
	itr = start_idx
	start = itr
	while itr < maxlen and source[itr] != ')':
		if source[itr] == ',':
			preretval.append(source[start:itr])
			start = itr + 1
		itr += 1
	if start < itr:
		preretval.append(source[start:itr])
	if len(preretval) == 0:
		return preretval
	retval = []
	for itr in preretval:
		try:
			retval.append(int(itr))
		except ValueError:
			retval.append(itr)
	return retval

BASE_FD_SELECT = [
	"SELECT ",
	"TABLE_CATALOG,",
	"TABLE_SCHEMA,",
	"TABLE_NAME,",
	"COLUMN_NAME,",
	"0,",
	"DATA_TYPE,",
	"NUMERIC_PRECISION,",
	"CHARACTER_MAXIMUM_LENGTH,",
	"NUMERIC_SCALE,",
	"NUMERIC_PRECISION_RADIX,",
	"0,",
	"'',",
	"COLUMN_DEFAULT,",
	"0,",
	"DATETIME_PRECISION,",
	"CHARACTER_OCTET_LENGTH,",
	"ORDINAL_POSITION,",
	"IS_NULLABLE, 0",
	" FROM INFORMATION_SCHEMA.columns "
]


class FieldData:
	def __init__(self, fs=None):
		# Initialize all members to None before we figure out what to do with fs
		self.engine = None
		self.table_qualifier = None
		self.table_owner = None
		self.table_name = None
		self.column_name = None
		self.data_type = None
		self.type_name = None
		self.precision = None
		self.length = None
		self.scale = None
		self.radix = None
		self.nullable = None
		self.remarks = None
		self.default = None
		self.sql_data_type = None
		self.sql_datetime_sub = None
		self.char_octet_length = None
		self.ordinal_position = None
		self.is_nullable = None
		self.ss_data_type = None
		self.is_pk = 0
		self.is_dimension = None
		self.column_family = None
		self.column_def = None
		self.autoinc_seed = None
		self.autoinc_inc = None
		self.collation = None

		if isinstance(fs, list) or isinstance(fs, tuple):
			if len(fs) != 19:
				raise ValueError("Received a list as a parameter to FieldData that is length {len(fs)} instead of 19")
			self.set_values(fs)

		if isinstance(fs, str):
			self.parse_declaration(fs)

	def set_values(self, row):
		self.table_qualifier = row[0]
		self.table_owner = row[1]
		self.table_name = row[2]
		self.column_name = row[3].lower()
		self.data_type = row[5]
		self.type_name = row[5]
		self.precision = row[6]
		self.length = row[7]
		self.scale = row[8]
		self.radix = row[9]
		self.nullable = row[17]
		self.remarks = row[11]
		self.default = row[12]
		self.sql_data_type = None
		self.sql_datetime_sub = None
		self.char_octet_length = row[15]
		self.ordinal_position = row[16]
		self.is_nullable = row[17]
		self.ss_data_type = None
		self.is_pk = 0
		self.is_dimension = None
		self.column_family = None
		self.column_def = None
		self.autoinc_seed = None
		self.autoinc_inc = None
		self.collation = None

	def init_from_list(self, fs):
		self.set_from_prototype(fs)
		self.parse_column_definition(self.type_name)

	def set_from_prototype(self, proto):
		self.table_qualifier = proto[0]
		self.table_owner = proto[1]
		self.table_name = proto[2]
		self.column_name = proto[3]
		self.data_type = proto[4]
		self.type_name = proto[5]
		self.precision = proto[6]
		self.length = proto[7]
		self.scale = proto[8]
		self.radix = proto[9]
		self.nullable = proto[10]
		self.remarks = proto[11]
		self.default = proto[12]
		self.sql_data_type = proto[13]
		self.sql_datetime_sub = proto[14]
		self.char_octet_length = proto[15]
		self.ordinal_position = proto[16]
		self.is_nullable = proto[17]
		self.ss_data_type = proto[18]
		self.is_pk = 0
		self.is_dimension = False
		self.autoinc_seed = None
		self.autoinc_inc = None
		self.column_family = None

	def parse_declaration(self, decl):
		parts = decl.upper().split()
		if len(parts) == 0:
			return
		#	raise ValueError(f"Empty declaration for {self.table_name}.{self.column_name}")
		basepart = parts.pop(0)
		startidx = basepart.find('(')
		if startidx > 0:
			basetype = basepart[:startidx]
			params = extract_params(basepart, startidx+1)
		else:
			basetype = basepart
			params = []

		if basetype not in DECL_BASES or DECL_BASES[basetype] is None:
			raise ValueError(f"Attempt to specify {basetype} as a base datatype, not found in {ODBC_DATATYPES}")

		self.set_from_prototype(DECL_BASES[basetype])
		self.parse_column_definition(decl)
		self.spot_primarykey(decl)

		if basepart in PARAMLESS_TYPES or len(params) == 0:
			return

		if basetype in VARLENCHAR_TYPES:
			if isinstance(params[0], str) and params[0] == 'MAX':
				if basepart[0] == 'N':
					self.length = 4000
				else:
					self.length = 8000

			else:
				self.length = params[0]
			self.precision = self.length
			if basepart[0] == 'N':
				self.char_octet_length = self.length * 2
			else:
				self.char_octet_length = self.length
			return

		if basetype in DECIMAL_TYPES:
			self.precision = params[0]
			if self.precision < 10:
				self.char_octet_length = 5
			elif self.precision < 20:
				self.char_octet_length = 9
			elif self.precision < 29:
				self.char_octet_length = 13
			else:
				self.char_octet_length = 17

			if len(params) > 1:
				self.scale = params[1]
			return

		if basetype in FLOAT_TYPES:
			if params[0] < 25:
				self.precision = 7
				self.length = 4
			else:
				self.precision = 15
				self.length = 8
			self.char_octet_length = self.length
			return

	def spot_primarykey(self, definition):
		if PRIMARY_KEY.search(definition) is not None:
			self.is_pk = 1

	def spot_rowguidcol(self, definition):
		upperstuff = definition.upper().replace(' ', '')
		if ' ROWGUIDCOL' not in upperstuff:
			return False
		raise NotImplementedError

	def spot_autoinc(self, definition):
		if AUTO_INCREMENT.search(definition) is None:
			return False
		self.autoinc_seed = 1
		self.autoinc_inc = 1

	def spot_identity(self, definition):
		upperstuff = definition.upper()
		if ' IDENTITY' not in upperstuff:
			return False
		upperstuff = upperstuff.replace(' ', '')
		self.is_pk = 1
		self.is_nullable = False
		self.nullable = False
		self.autoinc_seed = 1
		self.autoinc_inc = 1

		ididx = upperstuff.find('IDENTITY') + 8
		if len(upperstuff) <= ididx or upperstuff[ididx] != '(':
			self.autoinc_seed = 1
			self.autoinc_inc = 1
			return True

		parms = extract_params(upperstuff, ididx+1)

		self.autoinc_seed = parms[0]
		if len(parms) > 1:
			self.autoinc_inc = parms[1]
		else:
			self.autoinc_inc = 1
		return True

	def spot_collation(self, definition):
		if ' COLLATION' not in definition.upper():
			return False
		upperstuff = definition.upper()
		idx = upperstuff.find(' COLLATION') + 11
		collation = []
		while idx < len(definition) and definition[idx] != ' ':
			collation.append(definition[idx])
		self.collation = ''.join(collation)
		return True

	def spot_default(self, definition):
		if ' DEFAULT ' not in definition.upper():
			return False
		upperstuff = definition.upper()
		idx = upperstuff.find(' DEFAULT ') + 9
		while definition[idx] in (' ', '\t'):
			idx += 1
		if definition[idx] == "'":
			self.default = extract_quoted(definition, idx)
			return True
		default = []
		while idx < len(definition) and definition[idx] != ' ':
			default.append(definition[idx])
			idx += 1
		self.default = ''.join(default)
		try:
			if self.type_name in INTEGER_TYPES:
				self.default = int(self.default)
			elif self.type_name in FLOAT_TYPES or self.type_name in DECIMAL_TYPES:
				self.default = float(self.default)
		except:
			print(f"Excessive exception, fielddata.py, line 340")

		return True

	def spot_nulls(self, definition):
		if ' NULL' not in definition.upper():
			return False
		upperstuff = definition.upper()
		idx = upperstuff.find(' NULL')
		while idx > 0 and upperstuff[idx] == ' ':
			idx -= 1
		if idx < 2 or upperstuff[idx-2:idx+1] != 'NOT':
			self.is_nullable = True
			self.nullable = True
			return True
		self.is_nullable = False
		self.nullable = False
		# This true means that NULL or NOT NULL was specified, not which of them was specified
		return True

	def parse_column_definition(self, definition):
		self.spot_collation(definition)
		self.spot_rowguidcol(definition)
		self.spot_default(definition)
		self.spot_autoinc(definition)
		if self.spot_identity(definition):
			return
		self.spot_nulls(definition)

	def __str__(self):
		return self.serialize()
#		raise DeprecationWarning
#		typedecl = self.type_declaration()
#		return f"[{self.column_name}] {typedecl}"

	def __repr__(self):
		return self.__str__()

	def declaration(self):
		return self.__str__()

	def type_declaration(self):
		# This has been moved to the implementation specific database manager
		raise DeprecationWarning


	def set_engine(self, engine):
		self.engine = engine

	def set_value(self, column_name, value):

		if column_name == 'TABLE_QUALIFIER':
			self.table_qualifier = value
		if column_name == 'TABLE_OWNER':
			self.table_owner = value
		if column_name == 'TABLE_NAME':
			self.table_name = value
		if column_name == 'COLUMN_NAME':
			self.column_name = value
		if column_name == 'DATA_TYPE':
			self.data_type = int(value)
		if column_name == 'TYPE_NAME':
			self.parse_column_definition(value)
			self.type_name = value

		if column_name == 'PRECISION':
			self.precision = int(value)
		if column_name == 'LENGTH':
			self.length = int(value)
		if column_name == 'SCALE':
			if value == 'NA':
				self.scale = None
			else:
				self.scale = value
		if column_name == 'RADIX':
			if value == 'NA':
				self.radix = None
			else:
				self.radix = value
		if column_name == 'NULLABLE':
			self.nullable = value
		if column_name == 'REMARKS':
			self.remarks = value
		if column_name == 'COLUMN_DEF':
			self.column_def = value
		if column_name == 'SQL_DATA_TYPE':
			self.sql_data_type = value
		if column_name == 'SQL_DATETIME_SUB':
			if value == 'NA':
				self.sql_datetime_sub = None
			else:
				self.sql_datetime_sub = value
		if column_name == 'CHAR_OCTET_LENGTH':
			if value == 'NA':
				self.char_octet_length = None
			else:
				self.char_octet_length = value
		if column_name == 'ORDINAL_POSITION':
			self.ordinal_position = int(value)
		if column_name == 'IS_NULLABLE':
			self.is_nullable = value
		if column_name == 'SS_DATA_TYPE':
			self.ss_data_type = value

	def serialize(self):
		content = [f'"{self.table_qualifier}"',
			f'"{self.table_owner}"',
			f'"{self.table_name}"',
			f'"{self.column_name}"',
			f'"{self.data_type}"',
			f'"{self.type_name}"',
			f'{self.precision}',
			f'{self.length}',
			f'{self.scale}',
			f'{self.radix}',
			f'"{self.nullable}"',
			f'"{self.remarks}"',
			f'"{self.default}"',
			f'"{self.sql_data_type}"',
			f'"{self.sql_datetime_sub}"',
			f'{self.char_octet_length}',
			f'{self.ordinal_position}',
			f'"{self.is_nullable}"',
			f'"{self.ss_data_type}"',
			f'"{self.is_pk}"',
			f'"{self.column_family}"']
		return '[%s]' % ",".join(content)

	def parse(self, oneline):
		parts = oneline.split(",")
		if len(parts) != 19:
			raise ValueError("Field descriptor should be comma delimited, 19 columns: %s" % parts)

		self.table_qualifier = parts[0][1:-2]
		self.table_owner = parts[1][1:-2]
		self.table_name = parts[2][1:-2]
		self.column_name = parts[3][1:-2]
		self.data_type = parts[4][1:-2]
		self.type_name = parts[5][1:-2]
		self.precision = parts[6][1:-2]
		self.length = parts[7][1:-2]
		self.scale = parts[8][1:-2]
		self.radix = parts[9][1:-2]
		self.nullable = parts[10][1:-2]
		self.remarks = parts[11][1:-2]
		self.default = parts[12][1:-2]
		self.sql_data_type = parts[13][1:-2]
		self.sql_datetime_sub = parts[14][1:-2]
		self.char_octet_length = parts[15][1:-2]
		self.ordinal_position = parts[16][1:-2]
		self.is_nullable = parts[17][1:-2]
		self.ss_data_type = parts[18][1:-2]
		self.is_pk = 0

	def standardize_name(self, name=None):
		if name is None:
			cand = self.table_name
		else:
			cand = name
		cand = cand.lower()
		cand = cand.replace("-_()$#*", " ")
		cand = cand.strip()
		cand = cand.replace("  ", "_")
		cand = cand.replace(" ", "_")
		if name is None:
			self.table_name = cand
		else:
			return cand

	def get_values(self):
		retval = dict()
		retval["TABLE_CATALOG"]            = self.table_qualifier
		retval["TABLE_SCHEMA"]             = self.table_owner
		retval["TABLE_NAME"]               = self.table_name
		retval["COLUMN_NAME"]              = self.column_name
		retval["CHARACTER_OCTET_LENGTH"]   = self.char_octet_length
		retval["CHARACTER_MAXIMUM_LENGTH"] = self.length
		retval["COLUMN_DEFAULT"]           = self.default
		retval["DATA_TYPE"]                = self.data_type
		retval["DATETIME_PRECISION"]       = self.sql_datetime_sub
		retval["NUMERIC_PRECISION"]        = self.precision
		retval["NUMERIC_PRECISION_RADIX"]  = self.radix
		retval["NUMERIC_SCALE"]            = self.scale
		retval["ORDINAL_POSITION"]         = self.ordinal_position
		retval["IS_NULLABLE"]              = self.is_nullable
		return retval


ODBC_DATATYPES = {
	'GUID': -11,
	'BIT': -7,
	'TINYINT': -6,
	'BIGINT': -5,
	'LONGVARBINARY': -4,
	'VARBINARY': -3,
	'BINARY': -2,
	'LONGVARCHAR': -1,
	'Unknown type': 0,
	'CHAR': 1,

	'NUMERIC': 2,
	'DECIMAL': 3,
	'INTEGER': 4,
	'INT': 4,
	'SMALLINT': 5,

	'FLOAT': 6,
	'REAL': 7,
	'DOUBLE': 8,

	'DATE': 9,
	'TIME': 10,
	'TIMESTAMP': 11,
	'VARCHAR': 12
}

VARLENCHAR_TYPES = ['VARBINARY', 'BINARY', 'CHAR', 'VARCHAR', 'NCHAR', 'NVARCHAR']

PARAMLESS_TYPES = ['TEXT', 'NTEXT', 'LONGVARCHAR', 'LONGVARBINARY',
			'DATETIME', 'DATE', 'TIME', 'TIMESTAMP',
			'BIT', 'TINYINT', 'SMALLINT', 'INTEGER', 'INT', 'BIGINT',
			'MONEY', 'SMALLMONEY', 'GUID']
CHAR_TYPES      = ['LONGVARBINARY', 'VARBINARY', 'BINARY', 'LONGVARCHAR', 'CHAR', 'VARCHAR',
			'NCHAR', 'NVARCHAR', 'TEXT']
UNICODE_TYPES    = ['NCHAR', 'NVARCHAR']
FLOAT_TYPES   = ['FLOAT', 'DOUBLE', 'REAL']
DECIMAL_TYPES = ['NUMERIC', 'DECIMAL', 'DEC', 'SMALLMONEY', 'MONEY']
INTEGER_TYPES = ['BIT', 'TINYINT', 'SMALLINT', 'INTEGER', 'INT', 'BIGINT']
TIME_TYPES    = ['DATE', 'TIME', 'DATETIME', 'TIMESTAMP']

# Just using this to shorten the lines below
MAX4B = 2147483647



DECL_BASES = {
	#                             DT        name    precis   len  scale radix nl  remk  cdef  dt dtsub octet_len ordpos isnul SSdt
	'DATETIME'  : ['', '', '', '', 11,  'DATETIME',    23,    16,     3, None, 1, None, None, 11, None,     None,     0,    1, 111],
	#             mydatetime,      11,   datetime ,    23,    16,     3,     , 1,     ,     ,  9,    3,         ,     x,  YES, 111
	'DATETIME2' : ['', '', '', '', -9, 'DATETIME2',    27,    54,  None, None, 1, None, None, -9, None,        0,     0,    1,  39],
	#            mydatetime2,      -9,  datetime2 ,    27,    54,      ,     , 1,     ,     , -9,     ,         ,     x,  YES,   0
	'DATETIMEOFFSET': ['','','','',-9,'DATETIMEOFFSET',34,    68,  None, None, 1, None, None, -9, None,        0,     0,    1,  39],
	#            mydatetimeoffset, -9,datetimeoffset,  34,    68,      ,     , 1,     ,     , -9,     ,         ,     x,  YES,   0
	'DATE'      : ['', '', '', '', -9,      'DATE',    10,    20,  None, None, 1, None, None, -9, None,     None,     0,    1,   0],
	#            mydate,           -9,       date ,    10,    20,      ,     , 1,     ,     , -9,     ,         ,     x,  YES,   0
	'TIME'      : ['', '', '', '', -9,      'TIME',    16,    32,  None, None, 1, None, None, -9, None,     None,     0,    1,   0],
	#             mytime,          -9,       time ,    16,    32,      ,     , 1,     ,     , -9,     ,         ,     x,  YES,   0
	'TIMESTAMP' : ['', '', '', '', -2, 'TIMESTAMP',     8,     8,  None, None, 1, None, None, -2, None,        8,     0,    1, 45],
	#             mytimestamp,     -2,  timestamp ,     8,     8,      ,     , 0,     ,     , -2,     ,        8,     x,   NO,  45

	'BIT'       : ['', '', '', '', -7,       'BIT',     1,     1,  None, None, 1, None, None, -7, None,     None,     0,    1,  50],
	#             mybit,           -7,        bit ,     1,     1,      ,     , 1,     ,     , -7,     ,         ,     x,  YES,  50
	'TINYINT'   : ['', '', '', '', -6,   'TINYINT',     3,     1,     0, None, 1, None, None, -6, None,     None,     0,    1,  38],
	#             mytinyint,       -6,    tinyint ,     3,     1,     0,   10, 1,     ,     , -6,     ,         ,     2,  YES,  38
	'SMALLINT'  : ['', '', '', '',  5,  'SMALLINT',    10,     2,     0,   10, 1, None, None,  5, None,     None,     0,    1,  38],
	'INT'       : ['', '', '', '',  4,       'INT',    10,     4,     0,   10, 1, None, None,  4, None,     None,     0,    1,  38],
	'INTEGER'   : ['', '', '', '',  4,       'INT',    10,     4,     0,   10, 1, None, None,  4, None,     None,     0,    1,  38],
	#             myint,            4,        int ,    10,     4,     0,   10, 1,     ,     ,  4,     ,         ,     x,  YES,  38
	'BIGINT'    : ['', '', '', '', -5,    'BIGINT',    19,     8,     0,   10, 1, None, None, -5, None,     None,     0,    1,  38],
	#             mybigint,        -5,     bigint ,    19,     8,     0,   10, 1,     ,     , -5,     ,         ,     x,  YES, 108
	'BINARY'    : ['', '', '', '', -2,    'BINARY',     1,     1,  None, None, 1, None, None, -2, None,        1,     0,    1,  37],
	'GUID'      : ['', '', '', '',-11,      'GUID',    16,    16,  None, None, 1, None, None, 12, None,       16,     0,    1,  37],
	#             mybin_10,        -2,     binary ,    10,    10,      ,     , 1,     ,     , -2,     ,       10,     x,  YES,  37
	'CHAR'      : ['', '', '', '',  1,      'CHAR',     1,     1,  None, None, 1, None, None,  1, None,        1,     0,    1,  39],
	#             mychar_50,        1,       char ,    50,    50,      ,     , 1,     ,     ,  1,     ,       50,     x,  YES,  39
	'VARCHAR'   : ['', '', '', '', 12,   'VARCHAR',     1,     1,  None, None, 1, None, None, 12, None,        2,     0,    1,  39],
	#             myvarchar20,     12,    varchar ,    20,    20,      ,     , 1,     ,     , 12,     ,       20,     x,  YES,  39
	#             myvarchar200,    12,    varchar ,   200,   200,      ,     , 1,     ,     , 12,     ,      200,     x,  YES,  39
	'NCHAR'     : ['', '', '', '', -8,     'NCHAR',     1,     1,  None, None, 1, None, None, -8, None,        2,     0,    1,  39],
	#             mynchar_60,      -8,      nchar ,    60,   120,      ,     , 1,     ,     , -8,     ,      120,     x,  YES,  39
	'NVARCHAR'  : ['', '', '', '', -9,  'NVARCHAR',     1,     1,  None, None, 1, None, None, -9, None,        2,     0,    1,  39],
	#            mynvarchar_70,    -9,   nvarchar ,    70,   140,      ,     , 1,     ,     , -9,     ,      140,     x,  YES,  39
	'VARBINARY' : ['', '', '', '', -3, 'VARBINARY',     1,     1,  None, None, 1, None, None, -3, None,        1,     0,    1,  37],
	#             myvarbin_30,     -3,  varbinary ,    30,    30,      ,     , 1,     ,     , -3,     ,       30,     x,  YES,  37
	'TEXT'      : ['', '', '', '', -1,      'TEXT', MAX4B, MAX4B,  None, None, 1, None, None, -1, None,    MAX4B,     0,    1,  61],

	'NUMERIC'   : ['', '', '', '',  2,   'NUMERIC',    18,     9,     0,   10, 1, None, None,  2, None,     None,     0,    1, 108],
	#             mynum,            2,    numeric ,    18,    20,     0,   10, 1,     ,     ,  2,     ,         ,     x,  YES, 108
	'DECIMAL'   : ['', '', '', '',  3,   'DECIMAL',    18,     9,     0,   10, 1, None, None,  2, None,     None,     0,    1, 106],
	'DEC'       : ['', '', '', '',  3,   'DECIMAL',    18,     9,     0,   10, 1, None, None,  2, None,     None,     0,    1, 106],
	#             mydeci_raw,       3,    decimal ,    18,    20,     0,   10, 1,     ,     ,  3,     ,         ,     x,  YES, 106
	#             mydeci_10,        3,    decimal ,    10,    12,     0,   10, 1,     ,     ,  3,     ,         ,     x,  YES, 106
	#             mydeci_19_2,      3,    decimal ,    19,    21,     2,   10, 1,     ,     ,  3,     ,         ,     x,  YES, 106
	'MONEY'     : ['', '', '', '',  3,     'MONEY',    19,    21,     4,   10, 1, None, None,  3, None,     None,     0,    1, 110],
	#             mymoney,          3,      money ,    19,    21,     4,   10, 1,     ,     ,  3,     ,         ,     x,  YES, 110
	'SMALLMONEY': ['', '', '', '',  3,'SMALLMONEY',    10,    12,     4,   10, 1, None, None,  3, None,     None,     0,    1, 110],
	#             mysmallmoney,     3, smallmoney ,    10,    12,     4,   10, 1,     ,     ,  3,     ,         ,     x,  YES, 110
	'FLOAT'     : ['', '', '', '',  6,     'FLOAT',    15,     8,  None,   10, 1, None, None,  6, None,     None,     0,    1, 109],
	#             myfloat,          6,      float ,    15,     8,      ,   10, 1,     ,     ,  6,     ,         ,     x,  YES, 109
	#             myfloat30,        6,      float ,    15,     8,      ,   10, 1,     ,     ,  6,     ,         ,     x,  YES, 109
	'DOUBLE'    : ['', '', '', '',  6,     'FLOAT',    15,     8,  None,   10, 1, None, None,  6, None,     None,     0,    1, 109],
	'REAL'      : ['', '', '', '',  7,      'REAL',     7,     4,  None,   10, 1, None, None,  7, None,     None,     0,    1, 109],
	#             myfloat20,        7,       real ,     7,     4,      ,   10, 1,     ,     ,  7,     ,         ,     x,  YES, 109
}
class Limits:
	lbit = 1
	ltinyint = 1
	lsmallint = 1
	lint = 4
	lbigint = 8

	lfloat = 5
	ldouble = 9
	ldubdub = 13
	lbigdub = 17

	@staticmethod
	def char2int(characters):
		if characters < 3:
			return Limits.ltinyint
		if characters < 5:
			return Limits.lsmallint
		if characters < 9:
			return Limits.lint
		if characters < 19:
			return Limits.lbigint

	@staticmethod
	def char2float(characters):
		if characters < 10:
			return Limits.lfloat
		if characters < 20:
			return Limits.ldouble
		if characters < 29:
			return Limits.ldubdub
		if characters < 39:
			return Limits.lbigdub
