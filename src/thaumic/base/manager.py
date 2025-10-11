''' Creates and maintains connections to a database.
	Also handles top-level dialect differences
'''
from datetime import datetime, date, time

import pyodbc
from thaumic.util.logger import ConditionalLogger


# noinspection SqlNoDataSourceInspection
class CnxnManager:
	def __init__(self, dbspec, logger=None):
		self.dsn = dbspec.get('DSN', None)
		self.host = dbspec.get('HOST', None)
		self.port = dbspec.get('PORT', None)
		self.user = dbspec.get('USER', None)
		self.pw = dbspec.get('PW', None)
		self.database = dbspec.get('DATABASE', None)
		self.schema = dbspec.get('SCHEMA', None)
		self.driver = dbspec.get('DRIVER', None)
		self.retries = dbspec.get('RETRIES', 0)
		self.autocommit = dbspec.get('AUTOCOMMIT', True)
		self.encoding = dbspec.get('ENCODING', None)
		self.enc_ctype = dbspec.get('CTYPE', None)
		self.debug = dbspec.get('DEBUGME', None)
		if logger is None:
			logspec = dbspec.get('LOGSPEC')
			if logspec is None:
				self.logger = ConditionalLogger(dict())
			else:
				self.logger = ConditionalLogger(logspec)
		else:
			self.logger = logger

		self.connection = None
		self.rowcount = -1
		self.last_query = None
		self.last_parameters = None
		self.lastrowid = None
		self.IntegrityError = pyodbc.IntegrityError
		self.ProgrammingError = pyodbc.ProgrammingError
		self.plhd = "%s"
		self.dq = '"'

	def __del__(self):
		self.close()

	def connect(self):
		if self.connection and self.connection.connected:
			return
		params = []
		if self.dsn:
			params.append(f"DSN={self.dsn}")
		else:
			params.append(f"DRIVER={self.driver}")
			params.append(f"SERVER={self.host}")
		if self.database:
			params.append(f"DATABASE={self.database}")
		params.append(f"UID={self.user}")
		params.append(f"PWD={self.pw}")

		connection_string = ';'.join(params)
		self.connection = pyodbc.connect(connection_string)
		self.connection.autocommit = self.autocommit
		if self.encoding or self.enc_ctype:
			self.connection.setencoding(encoding=self.encoding, ctype=self.enc_ctype)

	@classmethod
	def class_ftn(cls, tableclass):
		raise NotImplementedError

	def close(self):
		''' Close this connection and null out the variable'''
		if self.connection:
			self.connection.close()
		self.connection = None

	def cnxn(self):
		''' Get a connected connection object'''
		self.connect()
		return self.connection

	def execute(self, query, params=None, raw=False):
		self._execute(query, params, raw)

	def _execute(self, query, params=None, raw=False):
		if not raw:
			query = self.adjust_quoting(query)
		self.last_query = query
		self.last_parameters = params
		self.last_rowid = None
		self.logger.debug(f"{self.__class__.__name__} Executing {query}, {params}")

		with self.cnxn().cursor() as cursor:
			if params:
				result = cursor.execute(query, params)
			else:
				result = cursor.execute(query)
			if hasattr(cursor, 'lastrowid'):
				self.lastrowid = cursor.lastrowid
			if hasattr(cursor, 'rowcount'):
				self.rowcount = cursor.rowcount

			if isinstance(result, int):
				self.rowcount = result
			elif isinstance(result, pyodbc.Cursor):
				self.rowcount = result.rowcount

	def executemany(self, query, vargs):
		'''In the absence of a universally supported method of running
		multi-set queries, we have to just iterate through them.'''
		self.logger.debug("Running executemany: \n%s\n%s" % (query, vargs))
		with self.cnxn().cursor() as cursor:
			cursor.executemany(query, vargs)

	def fetch(self, query, vargs=None, raw=False, retries=0):
		if not raw:
			query = self.adjust_quoting(query)
		retval = None
		while retries > 0:
			retries -= 1
			retval = self._fetch(query, vargs)

		return retval

	def _fetch(self, query, vargs):
		self.last_query = query
		self.last_parameters = vargs
		self.logger.debug(f"{self.__class__.__name__} fetching {query}, {vargs}")

		retval = []
		with self.cnxn().cursor() as cursor:
			if vargs:
				cursor.execute(query, vargs)
			else:
				cursor.execute(query)
			self.rowcount = 0

			for oneitem in cursor:
				self.rowcount += 1
				retval.append(list(oneitem))
		return retval

	def adjust_query(self, query):
		''' Adjust quoting first, in case that needs to be considered before adjusting parameter marks'''
		query = self.adjust_quoting(query)
		return self.adjust_parameter_marks(query)

	@staticmethod
	def adjust_quoting(query):
		''' Queries from generators should always create them with double-quote
		identifier quoting. If a language uses something besides double-quotes
		to surround identifiers like column names, this must adjust the generated
		query
		'''
		return query

	@staticmethod
	def adjust_parameter_marks(query):
		''' There is no ANSI parameterized query marker. Generators within this library will
		use %s as the marker. If your database uses something different, change it here.
		'''
		return query

	def list_tables(self, schema=None):
		''' This is the ansi-standard way to get a list of tables in a database.'''
		query = ("SELECT TABLE_NAME FROM \"INFORMATION_SCHEMA\".\"TABLES\" "
		         "WHERE TABLE_TYPE='BASE TABLE' ")
		if schema:
			query += f" AND TABLE_SCHEMA = '{schema}'"
		alltables = self.fetch(query)

		retval = []
		for row in alltables:
			retval.append(row[0])
		return retval

	def drop_constraint(self, table_name, constraint_name):
		query = "ALTER TABLE %s DROP CONSTRAINT %s"
		self.execute(query, (table_name, constraint_name))

	def debug_out(self, message):
		if self.debug:
			self.logger.debug(message)

	def recoonnect(self):
		''' In the event of a connection distruption or a failed query, close and
		restart the connection '''
		if self.connection and self.connection.connected:
			self.connection.close()
		self.connection = None
		self.connect()

	@staticmethod
	def format_datetime(self, value):
		return value

	@staticmethod
	def format_timestamp(value):
		if isinstance(value, int) or isinstance(value, float):
			return value
		if isinstance(value, date):
			value = datetime.combine(value, time(0, 0, 0))
		if isinstance(value, datetime):
			return value.timestamp()

	@staticmethod
	def format_value(self, datatype, value):
		if datatype.fd.type_name == 'DATETIME':
			return self.format_datetime(value)
		if datatype.fd.type_name == 'TIMESTAMP':
			return self.format_timestamp(value)
		if datatype.fd.type_name == 'VARCHAR':
			value = str(value)
			if len(value) > datatype.fd.length:
				value = value[:datatype.fd.length - 3] + '...'
			return value
		return value
