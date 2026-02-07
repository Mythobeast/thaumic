import unittest
from thaumic.base.sqlfield import fix_field_name, handle_boolean_strings, SQLField, move_attribute


class TestField(unittest.TestCase):

	# Replaces all non-alphanumeric characters to underscores
	def test_fix_field_name(self):
		test_cases = ['onename', 'name two', 'Some  GoofyName']
		test_results = ['onename', 'name_two', 'some_goofyname']
		for itr in len(test_cases):
			retval = fix_field_name(test_cases[itr])
			self.assertEqual(retval, test_results[itr])

	def test_handle_boolean_strings(self):
		test_cases = ['true', 'false', 'yes', 'no', 1, 0, 9, -1]
		test_results = [1, 0, 1, 0, 1, 0, 1, 1]
		for itr in len(test_cases):
			retval = handle_boolean_strings(test_cases[itr])
			self.assertEqual(retval, test_results[itr])

	def test_move_attribute(self):

		(retdat, retattr) = move_attribute('something', 'something is here', 'nothing is here')
		self.assertEqual(retdat, ' is here')
		self.assertEqual(retattr, 'nothing is here something')
		(retdat, retattr) = move_attribute('notthere', 'something is here', 'nothing is here')
		self.assertEqual(retdat, 'something is here')
		self.assertEqual(retattr, 'nothing is here')

		(retdat, retattr) = move_attribute('notthere', 'something is here', 'nothing is here')
		self.assertEqual(retdat, 'something is here')
		self.assertEqual(retattr, 'nothing is here')

		(retdat, retattr) = move_attribute('something', 'something is here', '')
		self.assertEqual(retdat, ' is here')
		self.assertEqual(retattr, 'something')


	def test_sqlfield_init(self):


#		retval = SQLField(first, datatype=None, dimension=False, attributes='', required=False, default=None, engine=None)  # noqa: C901
		retval = SQLField(mock_fd)  # noqa: C901

#
# if isinstance(first, FieldData):
# 	''' If the first column is a fielddata, datatype must be None '''
# 	fd = first
# 	self.fd = fd
# 	self.name = fix_field_name(fd.column_name)
# 	self.datatype = fd.type_name
# 	self.fixedname = self.name
# 	self.is_dimension = dimension
# 	return

raises
ValueError:
duncil = SQLField('fieldname')  # noqa: C901
raises ValueError:
# First is not int or fd
			duncil = SQLField(2)  # noqa: C901

	raises ValueError:
	# first is str, datatype is none
			duncil = SQLField('fieldname')  # noqa: C901
	raises ValueError:
	# first is str, attributes is not str
			duncil = SQLField('fieldname', 'int', attributes = 4)  # noqa: C901

	# happy path
	retval = SQLField('fieldname', datatype=int, dimension=False, attributes='', required=False, default=None, engine=None)  # noqa: C901

	fieldname needs fixing
	is/is not dimension
	default is/is not none
	is/is not nullable

change required to nullable

		retval = SQLField(first, datatype=None, dimension=False, attributes='', required=False, default=None, engine=None)  # noqa: C901
		retval = SQLField(first, datatype=None, dimension=False, attributes='', required=False, default=None, engine=None)  # noqa: C901
		retval = SQLField(first, datatype=None, dimension=False, attributes='', required=False, default=None, engine=None)  # noqa: C901
		self.engine = engine

		self.fd = FieldData(f"{datatype} {attributes}")
		self.name = fix_field_name(first)
		self.fixedname = self.name
		# Remove unfriendly characters
		self.fd.column_name = self.fixedname

		if required:
			self.fd.is_nullable = False
			self.fd.nullable = False

	def move_attributes_from_datatype(self):
		ATTRIBLIST = ['PRIMARY KEY', 'IDENTITY(1,1)', 'IDENTITY', 'NOT NULL', 'NULL', 'UNIQUE', 'AUTO_INCREMENT']
		for oneattr in ATTRIBLIST:
			self.datatype, self.attributes = move_attribute(oneattr, self.datatype.upper(), self.attributes.upper())

	def __str__(self):
		return self.__repr__()

	def __repr__(self):
		decl = str(self.fd)
		if 'INT PRIMARY KEY IDENTITY(1,1)' in decl:
			return decl
		if self.attributes is None or len(self.attributes) == 0:
			return decl
		else:
			return f"{decl} {self.attributes}"

	def iskey(self):
		return self.fd.is_pk

	def default_value(self):
		return self.fd.default

	def set_required(self, value):
		trueval = handle_boolean_strings(value)
		self.fd.nullable = trueval
		self.fd.is_nullable = trueval

	def isrequired(self):
		return not self.fd.nullable

	def format_chartype(self, value):
		if not isinstance(value, str):
			value = str(value)
		if len(value) == 0:
			return value
		if isinstance(self.fd.length, str):
			raise ValueError(f"Fielddata length is a string: {self.fd.serialize()}")
		utf_val = value.encode()
		if self.fd.length < len(utf_val):
			utf_val = utf_val[:self.fd.length]
		while 1:
			try:
				retval = utf_val.decode()
				return retval
			except UnicodeDecodeError:
				if len(utf_val) == 0:
					return ''
				utf_val = utf_val[:-1]

	def formatvalue(self, value):  # noqa: C901
		# This function should be moved to the DatabaseManager objects
		if self.fd.type_name in CHAR_TYPES:
			return self.format_chartype(value)
		if isinstance(value, str) and len(value) == 0:
			return None
		if self.fd.type_name == 'BIT':
			if isinstance(value, str):
				if value.lower() == 'true' or value.lower() == 'yes' or value.lower() == '1':
					return True
				return False
			try:
				retval = int(value)
				if retval == 0:
					return False
				return True
			except ValueError:
				retval = False
			return retval
		if self.fd.type_name in INTEGER_TYPES:
			if isinstance(value, int):
				return value
			return handle_boolean_strings(value)
		if self.fd.type_name in FLOAT_TYPES:
			if isinstance(value, float):
				return value
			return float(value)
		if self.fd.type_name in TIME_TYPES:
			if isinstance(value, str):
				if len(value) == 0:
					return None
				if self.engine == 'mssql_mgr':
					if self.fd.type_name in ['DATETIME']:
						return datetime.strptime(value[:19], "%Y-%m-%dT%H:%M:%S")
					elif self.fd.type_name == 'DATE':
						return datetime.strptime(value, "%Y-%m-%d")
					elif self.fd.type_name in ['TIME']:
						return datetime.strptime(value, "%H:%M:%S")
				if self.engine == 'mariadb_mgr':
					if self.fd.type_name in ['DATETIME', 'TIMESTAMP']:
						return datetime.strptime(value[:19], "%Y-%m-%dT%H:%M:%S")
		return value

