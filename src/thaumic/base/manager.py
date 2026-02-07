''' Creates and maintains connections to a database.
	Also handles top-level dialect differences
'''
from datetime import datetime, date, time

import pyodbc

from thaumic.adapters.mysql_mgr.sqldialect import MysqlDialect
from thaumic.base.typemappings import TIME_TYPES, INTEGER_TYPES, FLOAT_TYPES, CHAR_TYPES, DECIMAL_TYPES
from thaumic.util.logger import ConditionalLogger

def getinstance():
	raise NotImplementedError()

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
		self.odbc_driver = dbspec.get('ODBC_DRIVER', None)
		if logger is None:
			logspec = dbspec.get('LOGSPEC', None)
			if logspec is None:
				self.logger = ConditionalLogger(dict())
			else:
				self.logger = ConditionalLogger(logspec)
		else:
			self.logger = logger
		self.gen = MysqlDialect()
		self.typemap = None

		self.cnxn = None
		self.rowcount = -1
		self.last_query = None
		self.last_parameters = None
		self.lastrowid = None
		self.IntegrityError = pyodbc.IntegrityError
		self.ProgrammingError = pyodbc.ProgrammingError

	def __del__(self):
		self.close()

	### Connection management

	def connect(self):
		if self.cnxn and self.cnxn.connected:
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
		self.cnxn = pyodbc.connect(connection_string)
		self.cnxn.autocommit = self.autocommit
		if self.encoding or self.enc_ctype:
			self.cnxn.setencoding(encoding=self.encoding, ctype=self.enc_ctype)

	def close(self):
		''' Close this connection and null out the variable'''
		if self.cnxn:
			self.cnxn.close()
		self.cnxn = None

	def connection(self):
		''' Get a connected connection object'''
		self.connect()
		return self.cnxn

	def reconnect(self):
		''' In the event of a connection distruption or a failed query, close and
		restart the connection '''
		if self.cnxn and self.cnxn.connected:
			self.cnxn.close()
		self.cnxn = None
		self.connect()

	def debug_out(self, message):
		if self.debug:
			self.logger.debug(message)

	def execute(self, query, params=None):
		self._execute(query, params)

	def _execute(self, query, params=None):

		self.last_query = query
		self.last_parameters = params
		self.last_rowid = None
		self.logger.debug(f"Class {self.__class__.__name__}, Executing {query}, {params}")

		with self.connection().cursor() as cursor:
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

	def executemany(self, query, params):
		'''In the absence of a universally supported method of running
		multi-set queries, we have to just iterate through them.'''
		self.logger.debug("Running executemany: \n%s\n%s" % (query, params))
		with self.connection().cursor() as cursor:
			cursor.executemany(query, params)

	def fetch(self, query, params=None, retries=0):
		retval = None
		while retries > 0:
			retries -= 1
			retval = self._fetch(query, params)

		return retval

	def _fetch(self, query, params):
		self.last_query = query
		self.last_parameters = params
		self.logger.debug(f"{self.__class__.__name__}, fetching {query}, {params}")

		retval = []
		with self.connection().cursor() as cursor:
			if params:
				cursor.execute(query, params)
			else:
				cursor.execute(query)
			self.rowcount = 0

			for oneitem in cursor:
				self.rowcount += 1
				retval.append(list(oneitem))
		return retval

	### Data Definition Language

	def list_tables(self, schema=None):
		''' This is the ansi-standard way to get a list of tables in a database.'''

		alltables = self.fetch(self.gen.list_tables(schema=schema))
		retval = [x[0] for x in alltables]
		return retval

	# noinspection PyUnusedLocal,PyMethodMayBeStatic
	def schema_exists(self, schema):
		''' MariaDB has no concept of schema, so this driver simulates it
		 by adjusting table names.
		 Schemas don't need to be created or verified.
		 '''
		return True

	def table_exists(self, ts):
		sql, params = self.gen.table_exists(ts)
		tablelist = self.fetch(sql, params)
		return len(tablelist) > 0

	def create_table(self, ts):
		sql = self.gen.create_table(ts)
		self.execute(self.gen.create_table(ts))

	def drop_table(self, ts):
		self.execute(self.gen.drop(ts))

	def add_column(self, ts, sqlfield):
		sql = self.gen.add_column(ts, sqlfield)
		self.execute(sql)

	def modify_column(self, ts, sqlfield):
		sql = self.gen.modify_column(ts, sqlfield)
		self.execute(sql)

	def drop_column(self, ts, sqlfield):
		sql = self.gen.drop_column(ts, sqlfield)
		self.execute(sql)

	def add_constraint(self, ts, constraint_name, fieldlist):
		query = self.gen.add_constraint(ts, constraint_name, fieldlist)
		self.execute(query, (ts.ftn, constraint_name))

	def drop_constraint(self, ts, constraint_name):
		query = self.gen.drop_constraint(ts, constraint_name)
		self.execute(query, (ts.ftn, constraint_name))

	def confirm_thaumkey(self, ts):
		thaumkey_fields = self.fetch(self.gen.get_thaumkey_fields(ts))
		for field in ts.dimensions:
			if field.fd.fixedname in thaumkey_fields:
				thaumkey_fields.remove(field.fd.fixedname)
			else:
				return False
		if len(thaumkey_fields) > 0:
			return False
		return True

	def rebuild_thaumkey(self, ts):
		thaumkey_name = self.thaumkey_name(ts)
		self.execute(self.gen.drop_constraint(ts, thaumkey_name))
		self.execute(self.gen.add_constraint(ts, thaumkey_name, ts.dimensions))

	@classmethod
	def thaumkey_name(cls, ts):
		return f"thamkey_{ts.schemaname}_{ts.tablename}"

	def ensure_thaumkey(self, ts):
		if not self.confirm_thaumkey(ts):
			self.rebuild_thaumkey(ts)

	def format_int_todbd(self, fd, value):
		if isinstance(value, int) or isinstance(value, float):
			return int(value)
		if isinstance(value, str):
			if len(value) == 0:
				return None
		try:
			return int(value)
		except ValueError:
			self.logger.error(f"Table {fd.ftn} field {fd.column_name} received non-int value '{value}'")
		return None

	def get_table_schema(self, schemaname, tablename):
		sql = f"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='{schemaname}' AND TABLE_NAME='{tablename}'"
		return self.fetch(sql)

	@classmethod
	def format_time_todb(cls, value):
		return value.strftime("%H:%M:%S")

	@classmethod
	def format_date_todb(cls, value):
		return value.strftime("%Y/%m/%d")

	@classmethod
	def format_datetime_todb(cls, value):
		return value.strftime("%Y/%m/%dT%H:%M:%S")

	@classmethod
	def format_timestamp_todb(cls, value):
		return value.timestamp()

	@classmethod
	def format_float_todb(cls, value):
		return float(value)

	@classmethod
	def format_int_todb(cls, value):
		return int(value)

	@classmethod
	def format_decimal_todb(cls, fd, value):
		if isinstance(value, str):
			return value
		if isinstance(value, int):
			return str(value)
		if isinstance(value, float):
			format_str = f".{fd.precision}f"
			return str(round(value, fd.precision))
		return int(value)

	@classmethod
	def format_char_todb(cls, fd, value):
		working = value
		if isinstance(value, int) or isinstance(value, float):
			working = str(value)
		elif isinstance(value, datetime):
			working = value.strftime("%Y/%m/%dT%H:%M:%S")
		if len(working) > fd.length:
			return working[:fd.length]
		return working

	@classmethod
	def format_todb(cls, fd, value):
		if fd.type_name == 'DATE':
			return cls.format_date_todb(value)
		if fd.type_name == 'TIME':
			return cls.format_time_todb(value)
		if fd.type_name == 'DATETIME':
			return cls.format_datetime_todb(value)
		if fd.type_name == 'TIMESTAMP':
			return cls.format_timestamp_todb(value)

		if fd.type_name in INTEGER_TYPES:
			return cls.format_int_todbd(value)
		if fd.type_name in FLOAT_TYPES:
			return cls.format_float_todb(value)
		if fd.type_name in DECIMAL_TYPES:
			return cls.format_decimal_todb(fd, value)
		if fd.type_name in CHAR_TYPES:
			return cls.format_char_todb(fd, value)
		return cls.format_specialtype_todb(fd, value)

	@classmethod
	def format_specialtype_todb(self, fd, value):
		return value

	def format_fromdb(self, fd, value):
		if fd.type_name in TIME_TYPES:
			return self.format_time_fromdb(self, value)
		if fd.type_name in INTEGER_TYPES:
			return int(value)
		if fd.type_name in FLOAT_TYPES:
			return float(value)
		if fd.type_name in DECIMAL_TYPES:
			return float(value)
		return value

	@classmethod
	def format_time_fromdb(self, fd, value):
		if isinstance(value, datetime):
			return value
		if isinstance(value, str):
			return datetime.strptime(value, "%Y/%m/%d %H:%M:%S")
		if isinstance(value, int):
			return datetime.fromtimestamp(value)
		return value
