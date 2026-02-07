import sqlite3

from thaumic.adapters.sqlite_mgr.sqlitedialect import SqliteDialect
from thaumic.base.manager import CnxnManager
from thaumic.base.typemappings import CHAR_TYPES, FLOAT_TYPES, DECIMAL_TYPES, INTEGER_TYPES, \
	TIME_TYPES
from thaumic.adapters.sqlite_mgr.fielddata import DATATYPES
from thaumic.base.fielddata import FieldData

import thaumic.base.exceptions as thaumex

DB_INST = None
DEBUG = False
MAX_SYSNAME_LEN = 2000

def getinstance(spec_in, logger=None):
	return SqliteManager(spec_in, logger)

# noinspection PyAbstractClass
class SqliteManager(CnxnManager):
	COLUMNLIST_FIELDS = ["TABLE_CATALOG", "TABLE_SCHEMA", "TABLE_NAME",
			"COLUMN_NAME", "nonse", "DATA_TYPE", "NUMERIC_PRECISION",
			"CHARACTER_MAXIMUM_LENGTH", "NUMERIC_SCALE", "NUMERIC_PRECISION_RADIX", "nonse",
			"nonse", "COLUMN_DEFAULT", "nonse", "DATETIME_PRECISION", "CHARACTER_OCTET_LENGTH",
			"ORDINAL_POSITION", "IS_NULLABLE", "nonse"]

	def __init__(self, dbspec, logger=None):
		super().__init__(dbspec, logger)
#		self.debug = True
		self.engine = 'sqlite_mgr'
		self.dbfile = dbspec.get('DBFILE', None)
		self.authentication = dbspec.get('AUTHENTICATION', None)
		self.cnxn = None
		self.OperationalError = sqlite3.OperationalError
		self.IntegrityError = sqlite3.IntegrityError
		self.ProgrammingError = sqlite3.ProgrammingError
		self.BaseError = sqlite3.Error
		self.connect()
		self.gen = SqliteDialect()

	def add_column(self, ts, sqlfield):
		sql = self.gen.add_column(ts.ftn, sqlfield)
		self.execute(sql)

	def add_unique_constraint(self, ts, column_list, constraintname):
		self.execute(self.gen.add_unique_constraint(ts.ftn), column_list, constraintname)

	def alter_column(self, ts, sqlfield):
		# self.mktblnm(dbmgr)
		sql = self.gen.alter_column(ts.ftn, sqlfield)
		self.execute(sql)

	def check_thaumkey(self, ts):
		result = self.fetch(f'PRAGMA index_list({ts.ftn});')

		print(f"{result}")

	def cnx(self):
		if self.cnxn is None:
			self.connect()

	def connect(self):
		''' Get a new connection, close old connection if it exists
		'''
		if self.cnxn:
			self.cnxn.close()

		print(f"Sqlite3 connecting to {self.dbfile}")
		try:
			self.cnxn = sqlite3.connect(self.dbfile)
#		except OperationalError as oper:
#			if self.debug:
#				print(f"Operational error: Something is wrong with your user name or password: {oper}")
		except self.BaseError as err:
			print(f"error: {err} {err.args[0]}")
			if err.args[0] == 1698:
				self.logger.error("Something is wrong with your user name or password")
			# elif err.errno == errorcode.ER_BAD_DB_ERROR:
			# 	self.logger.error("Database does not exist")
			else:
				self.logger.error(err)

	# noinspection PyMethodMayBeStatic,PyUnusedLocal
	def create_schema(self, schemaname):
		# sqlite_mgr doesn't have schemas, so this is a no-op
		return True

	def create_table(self, ts):
		# if self.table_exists(ts):
#			return
		sql = self.gen.create_table(ts)
		self.execute(sql)
		sql = self.gen.create_thaumkey(ts)
		self.execute(sql)

	def drop_constraint(self, ts, constraint_name):
		''' To create a new table in SQLite using the results of a SELECT statement,
		you can use the syntax:
		CREATE TABLE new_table_name AS SELECT column1, column2 FROM existing_table_name;. This will create a new table with the same columns as the SELECT statement and populate it with the selected data. '''
		raise ValueError("SQLite does not support drop constraints")

	def drop_thaumkey(self, ts, keeper=None):
		raise ValueError("SQLite does not support drop constraints")

	def ensure_thaumkey(self, ts):
		if len(ts.dimensions) == 0:
			return
		sql = f"pragma main.index_list('{ts.ftn}')"
		result = self.fetch(sql)
		if len(result) == 1:
			if 'thaumkey' in result[0][1]:
				keyname = result[0][1]
				sql = f"pragma main.index_info('{keyname}')"
				result = self.fetch(sql)
				actualset = set()
				for oneitem in result:
					actualset.add(oneitem[2])
				expectedset = set(ts.dimensions)
				if actualset == expectedset:
					return
		# thaumkey determination failed
		holdname = f"{ts.tablename}_tobe_renamed"
		holdftn = ts.ftn.replace(ts.tablename, holdname)
		sql = self.gen.create_table(ts)
		new_sql = sql.replace(ts.tablename, holdname)
		self.execute(new_sql)
		insert_into = f'INSERT INTO {holdftn} ({ts.fieldnames_str}) SELECT {ts.fieldnames_str} FROM {ts.ftn}'
		self.execute(insert_into)
		self.execute(self.gen.drop(ts.ftn))
		self.create_table(ts)
		insert_into = f'INSERT INTO {ts.ftn} ({ts.fieldnames_str}) SELECT {ts.fieldnames_str} FROM {holdftn}'
		self.execute(insert_into)

	def execute(self, query, params=None):
		self.cnx()
		if isinstance(query, list):
			query = ' '.join(query)
		if self.debug:
			print(f"SqliteManager executing {query}, {params}")
		self.last_query = query
		self.last_parameters = params
		self.rowcount = None
		self.lastrowid = None
		try:
			cursor = self.cnxn.cursor()
			if params:
				response = cursor.execute(query, params)
			else:
				response = cursor.execute(query)
			self.rowcount = response.rowcount
			self.lastrowid = cursor.lastrowid
			if self.debug:
				print(f"response: {response.rowcount} rows effected.")
			self.cnxn.commit()
		except sqlite3.IntegrityError as err:
			raise thaumex.IntegrityError(err)
		except sqlite3.OperationalError as err:
			raise thaumex.OperationalError(err)
		except sqlite3.DataError as err:
			raise thaumex.DataError(err)
		except sqlite3.ProgrammingError as err:
			raise thaumex.ProgrammingError(err)
		except BaseException as be:
			if self.debug:
				print(f"Programming error attempting to execute {query}: {be}")
			raise
		return response

	def executemany(self, query, params, raw=False):
		self.cnx()

		if isinstance(query, list):
			query = self.adjust_quoting(' '.join(query))
		elif not raw:
			query = self.adjust_quoting(query)
		if self.debug:
			print(f"MySQL executing many {query}: {params}")
		self.rowcount = 0
		cursor = self.cnxn.cursor()
		try:
			for itr in params:
				cursor.execute(query, itr)
				self.rowcount += 1
		except TypeError as te:
			if self.debug:
				print(f"Programming error attempting to execute {query}: {te}")
			raise te
		self.cnxn.commit()

	def fetch(self, query, params=None, retries=0):
		self.cnx()
		if self.debug:
			print(f"SqliteManager fetching {query}, {params}")

		try:
			cursor = self.cnxn.cursor()
			if params:
				cursor.execute(query, params)
			else:
				cursor.execute(query)
		except sqlite3.IntegrityError as err:
			raise thaumex.IntegrityError(err)
		except sqlite3.OperationalError as err:
			raise thaumex.OperationalError(err)
		except sqlite3.DataError as err:
			raise thaumex.DataError(err)
		except sqlite3.ProgrammingError as err:
			raise thaumex.ProgrammingError(err)

		retval = []
		self.rowcount = 0
		for oneitem in cursor:
			self.rowcount += 1
			retval.append(list(oneitem))

		if self.debug:
			print(f"SqliteManager returning from fetch {retval}")
		return retval

	def format_datetime(self, value):
		# Should always receive a date and return that date
		return value

	def get_column_details(self, ts):
		response = self.get_columns(ts)
		retval = []
		for row in response:
			if self.debug:
				print(f"row = {row}")
			thiscol = {}
			for itr in range(0,len(self.COLUMNLIST_FIELDS)):
				thiscol[self.COLUMNLIST_FIELDS[itr]] = row[itr]
			retval.append(thiscol)
		if self.debug:
			print(f"get_column_details({ts.tablename}, {ts.schemaname}) returning {retval}")
		return retval

	def get_column_list(self, ts):
		''' Output should be equivalent to the output from sp_columns
		'''
		sql = f'PRAGMA table_info({ts.ftn});'

		sqltxt = sql
		# if self.debug:
		results = self.fetch(sqltxt)
		if self.debug:
			print(f"get_columns({ts.tablename}, {ts.schemaname}) returning {results}")
		retval = []
		ordinal = 0
		for row in results:
			newrow = DATATYPES[row[2]][:]
			newrow[FieldData.C_TABLE_SCHEMA] = ts.schemaname.strip('"')
			newrow[FieldData.C_TABLE_NAME]   = ts.tablename.strip('"')
			newrow[FieldData.C_COLUMN_NAME]  = row[1] # columnname
			newrow[FieldData.C_DATA_TYPE]    = row[2] # datatype
			newrow[FieldData.C_IS_NULLABLE]  = row[3] == 0 # notnull
			newrow[FieldData.C_COLUMN_DEFAULT] = row[4] # default
			newrow[FieldData.C_ORDINAL_POSITION] = ordinal
			ordinal += 1
			retval.append(newrow)
		# table_info_header = ["name", "type", "notnull", "dflt_value", "pk"]

		return retval

	def get_jdbc_connstr(self):
		return f'jdbc:sqlite_mgr:{self.dbfile}'

	def get_rowcount(self, ts):
		fulltablename = self.mk_tablename(ts)
		sql = f'SELECT count(*) FROM "{fulltablename}"'
		rowcount = self.fetch(sql)
		return rowcount

	# noinspection PyUnusedLocal,PyMethodMayBeStatic
	def identify_possible_keys(self, tablename):
		"""This relies upon get_columns being implemented."""
		tablename = tablename.lower()
		columns = self.get_columns(tablename)
		query = "SELECT count(*) FROM %s" % tablename
		rawcount = self.fetch(query)[0]
		candidates = []
		for onecolumn in columns:
			columnname = onecolumn[3]
			query = "SELECT count(distinct %s) from %s" % (columnname, tablename)
			uniquecount = self.fetch(query)[0]
			if uniquecount == rawcount:
				candidates.append(columnname)
		self.logger.debug("Candidates for %s: %s" % (tablename, candidates))
		return candidates

	def interpret_from_db(self, fd, value):
		''' converts values from the database into a Python type. Usually does nothing,
		except for fancy types that simple databases doesn't handle well. '''
		return value

	# noinspection PyMethodMayBeStatic,PyUnusedLocal
	def interpret_to_db(self, fd, value):
		''' converts the incomming to a type the database can handle.
		Usually does nothing, but for datetimes in sqlite_mgr, it does the conversion'''
		return value

	# noinspection PyMethodMayBeStatic
	def list_tables(self, schema=None):
		tablelist = self.fetch(self.gen.list_tables(schema))
		return [x[0] for x in tablelist]

	def refresh_schemacache(self):
		pass

	def rollback(self):
		self.cnx()
		self.cnxn.rollback()

	# noinspection PyUnusedLocal,PyMethodMayBeStatic
	def schema_exists(self, schema):
		''' MariaDB has no concept of schema, so this driver simulates it
		 by adjusting table names.
		 Schemas don't need to be created or verified.
		 '''
		return True

	def table_exists(self, ts):
		sql = self.gen.table_exists(ts)
		tablelist = self.fetch(sql, [ts.ftn])
		return len(tablelist) > 0

	@classmethod
	def type_declaration(cls, fd):
		tn_upper = fd.type_name.upper()
		parts = tn_upper.split()
		basetype = parts[0]

		# Add parameters to type name
		if basetype in INTEGER_TYPES:
			basetype = 'INTEGER'
		elif basetype in CHAR_TYPES or basetype in TIME_TYPES:
			basetype = 'TEXT'
		elif basetype in FLOAT_TYPES or basetype in DECIMAL_TYPES:
			basetype = 'REAL'

		retval = [basetype]
		if fd.is_pk:
			retval.append('PRIMARY KEY')
			if fd.autoinc_inc is not None and fd.autoinc_inc > 0:
				retval.append('AUTOINCREMENT')
		else:
			if fd.autoinc_inc is not None and fd.autoinc_inc > 0:
				raise ValueError(f"Sqlite can only assign AUTOINCREMENT to Primary Keys. {fd.schemaname}, {fd.tablename}, {fd.type_name}")

		return ' '.join(retval)

	# noinspection PyMethodMayBeStatic,PyUnusedLocal
