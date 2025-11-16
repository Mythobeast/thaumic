import re

from thaumic.base.typemappings import ODBC_DATATYPES, DECL_BASES, PARAMLESS_TYPES, VARLENCHAR_TYPES, DECIMAL_TYPES, INTEGER_TYPES, FLOAT_TYPES
from thaumic.util.logger import LOGGER


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


class FieldData:
	PRIMARY_KEY = re.compile('\\bPRIMARY[ ]+KEY\\b', re.IGNORECASE)
	NOT_NULL = re.compile('\\bNOT[ ]+NULL\\b', re.IGNORECASE)
	NULL_OK = re.compile('\\bNULL\\b', re.IGNORECASE)
	IDENTITY = re.compile('\\bIDENTITY', re.IGNORECASE)
	AUTO_INCREMENT = re.compile('\\bAUTO[_]?INCREMENT', re.IGNORECASE)

	# Standard columns for infoschema.columns

	C_TABLE_CATALOG = 0
	C_TABLE_SCHEMA = 1
	C_TABLE_NAME = 2
	C_COLUMN_NAME = 3
	C_4 = 4
	C_DATA_TYPE = 5
	C_NUMERIC_PRECISION = 6
	C_CHARACTER_MAXIMUM_LENGTH = 7
	C_NUMERIC_SCALE = 8
	C_NUMERIC_PRECISION_RADIX = 9
	C_10 = 10
	C_11 = 11
	C_COLUMN_DEFAULT = 12
	C_13 = 13
	C_DATETIME_PRECISION = 14
	C_CHARACTER_OCTET_LENGTH = 15
	C_ORDINAL_POSITION = 16
	C_IS_NULLABLE = 17
	C_18 = 18

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
		self.data_type = row[4]
		self.type_name = row[5]
		self.precision = row[6]
		self.length = row[7]
		self.scale = row[8]
		self.radix = row[9]
		self.remarks = row[11]
		self.default = row[12]
		self.sql_data_type = None
		self.sql_datetime_sub = None
		self.char_octet_length = row[15]
		self.ordinal_position = row[16]
		self.is_nullable = row[17]
		self.nullable = row[17]
		self.ss_data_type = None
		self.is_pk = 0
		self.is_dimension = False
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
		if self.PRIMARY_KEY.search(definition) is not None:
			self.is_pk = 1

	def spot_rowguidcol(self, definition):
		upperstuff = definition.upper().replace(' ', '')
		if ' ROWGUIDCOL' not in upperstuff:
			return False
		raise NotImplementedError

	def spot_autoinc(self, definition):
		if self.AUTO_INCREMENT.search(definition) is None:
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
			print(f"Excessive exception, fielddata.py, line 319")

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

