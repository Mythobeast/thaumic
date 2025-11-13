from datetime import datetime

import sqlite3


from thaumic.base.manager import CnxnManager
from thaumic.typemappings.fielddata import CHAR_TYPES, FLOAT_TYPES, DECIMAL_TYPES, INTEGER_TYPES, \
	TIME_TYPES
from thaumic.adapters.sqlite.fielddata import DATATYPES
import thaumic.typemappings.fielddata as fd
import thaumic.base.exceptions as thaumex


DB_INST = None
DEBUG = False
MAX_SYSNAME_LEN = 2000

def getinstance(spec_in, logger=None):
	return SqliteManager(spec_in, logger)

def chop(name, maxlen):
	if len(name) <= maxlen:
		return name
	return name[:maxlen]

def make_obname(namelist, maxlen):
	retval = '_'.join(namelist)
	if len(retval) <= maxlen:
		return retval
	maxsub = 0
	for name in namelist:
		if len(name) > maxsub:
			maxsub = len(name)
	while len(retval) > maxlen:
		maxsub -= 1
		newlist = [chop(name, maxsub) for name in namelist]
		retval = '_'.join(newlist)
	return retval


# noinspection PyAbstractClass
class SqliteManager(CnxnManager):
	auto_increment = 'AUTOINCREMENT'
	plhd = '?'
	id_quote = '"'


	def __init__(self, dbspec, logger=None):
		super().__init__(dbspec, logger)
#		self.debug = True
		self.engine = 'sqlite'
		self.dbfile = dbspec.get('DBFILE', None)
		self.authentication = dbspec.get('AUTHENTICATION', None)
		self.auto_increment = 'AUTOINCREMENT'
		self.plhd = '?'
		self.cnxn = None
		self.OperationalError = sqlite3.OperationalError
		self.IntegrityError = sqlite3.IntegrityError
		self.ProgrammingError = sqlite3.ProgrammingError
		self.BaseError = sqlite3.Error
		self.connect()

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

	def fetch(self, query, params=None, raw=False, retries=0):
		self.cnx()
		if isinstance(query, list):
			query = self.adjust_quoting(' '.join(query))
		elif not raw:
			query = self.adjust_quoting(query)
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

	def execute(self, query, params=None, raw=False):
		self.cnx()
		if isinstance(query, list):
			query = ' '.join(query)
		if not raw:
			query = self.adjust_quoting(query)
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

	def rollback(self):
		self.cnx()
		self.cnxn.rollback()

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

	def refresh_schemacache(self):
		pass

	def schema_exists(self, schema):
		''' MariaDB has no concept of schema, so this driver simulates it
		 by adjusting table names.
		 Schemas don't need to be created or verified.
		 '''
		return True

	# noinspection PyMethodMayBeStatic
	def create_schema(self, schemaname):
		return True

	def add_unique_constraint(self, schemaname, tablename, column_list, constraintname=None):
		raise NotImplementedError

	def get_rowcount(self, ts):
		fulltablename = self.mk_tablename(ts)
		sql = f'SELECT count(*) FROM "{fulltablename}"'
		rowcount = self.fetch(sql)
		return rowcount

	def table_exists(self, ts):
		fulltablename = self.mk_tablename(ts).strip('"')
		if self.debug:
			print(f"Checking if {fulltablename} exists")
		tablelist = self.fetch(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{fulltablename}';")
		for itr in tablelist:
			if fulltablename == itr[0].lower():
				return True
		if self.debug:
			print(f"{fulltablename} not found in tablelist")
		return False

	def ensure_thaumkey(self, ts):
		return True

	def drop_thaumkey(self, ts, keeper=None):
		raise ValueError("SQLite does not support drop constraints")

	def drop_constraint(self, ts, constraint_name):
		raise ValueError("SQLite does not support drop constraints")

	def list_tables(self, schema=None):
		alltables = self.fetch("SELECT name FROM sqlite_schema "
				"WHERE type ='table' AND " 
                "name NOT LIKE 'sqlite_%';")
		retval = []
		for onetable in alltables:
			if onetable[1] == self.schema:
				retval.append(onetable[2])
		return retval

	COLUMNLIST_FIELDS = ["TABLE_CATALOG", "TABLE_SCHEMA", "TABLE_NAME",
			"COLUMN_NAME", "nonse", "DATA_TYPE", "NUMERIC_PRECISION",
			"CHARACTER_MAXIMUM_LENGTH", "NUMERIC_SCALE", "NUMERIC_PRECISION_RADIX", "nonse",
			"nonse", "COLUMN_DEFAULT", "nonse", "DATETIME_PRECISION", "CHARACTER_OCTET_LENGTH",
			"ORDINAL_POSITION", "IS_NULLABLE", "nonse"]

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

	def get_columns(self, ts):
		''' Output should be equivalent to the output from sp_columns
		'''
		fulltablename = self.mk_tablename(ts).strip('"')
		sql = f'PRAGMA table_info({fulltablename});'

		sqltxt = sql
		# if self.debug:
		results = self.fetch(sqltxt)
		if self.debug:
			print(f"get_columns({ts.tablename}, {ts.schemaname}) returning {results}")
		retval = []
		ordinal = 0
		for row in results:
			newrow = DATATYPES[row[2]][:]
			newrow[fd.C_TABLE_SCHEMA] = ts.schemaname.strip('"')
			newrow[fd.C_TABLE_NAME]   = ts.tablename.strip('"')
			newrow[fd.C_COLUMN_NAME]  = row[1] # columnname
			newrow[fd.C_DATA_TYPE]    = row[2] # datatype
			newrow[fd.C_IS_NULLABLE]  = row[3] == 0 # notnull
			newrow[fd.C_COLUMN_DEFAULT] = row[4] # default
			newrow[fd.C_ORDINAL_POSITION] = ordinal
			ordinal += 1
			retval.append(newrow)
		table_info_header = ["name", "type", "notnull", "dflt_value", "pk"]

		return retval

	def get_jdbc_connstr(self):
		return f'jdbc:sqlite:{self.dbfile}'

	def drop_table(self, ts):
		if self.table_exists(ts):
			self.execute(f"DROP TABLE {ts.schemaname}_{ts.tablename};")

	def adjust_quoting(self, query):
		query = query.replace('[', '"')
		query = query.replace(']', '"')
		query = query.replace('%s', '?')
		query = query.replace('IDENTITY(1,1)', self.auto_increment)
		query = query.replace('AUTO_INCREMENT', self.auto_increment)
		return query

	def add_column(self, sqlfield):
		# self.mktblnm(dbmgr)
		sql = f"ALTER TABLE {self.tablename_from_sqlfield(sqlfield)} ADD {sqlfield.fixedname} {self.type_declaration(sqlfield.fd)}"
		sql = self.adjust_quoting(sql)
		self.execute(sql)

	def alter_column(self, sqlfield):
		# self.mktblnm(dbmgr)
		sql = f"ALTER TABLE {self.tablename_from_sqlfield(sqlfield)} ALTER COLUMN {sqlfield.fixedname} {self.type_declaration(sqlfield.fd)}"
		sql = self.adjust_quoting(sql)
		self.execute(sql)

	@classmethod
	def mk_tablename(cls, ts):
		return f'"{ts.schemaname}_{ts.tablename}"'

	@classmethod
	def tablename_from_sqlfield(cls, sqlfield):
		if sqlfield.fd.table_owner is None or sqlfield.fd.table_owner == '':
			schema = 'dbo'
		else:
			schema = sqlfield.fd.table_owner
		return f'"{schema}_{sqlfield.fd.table_name}"'

	@classmethod
	def sql_create_if_not_exists(cls, ts):
		return f"CREATE TABLE IF NOT EXISTS"

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

	@classmethod
	def class_ftn(cls, tableclass):
		if tableclass.ftn is None:
			tableclass.ftn = f'"{tableclass.SCHEMA}_{tableclass.TABLENAME}"'
		return tableclass.ftn

	def interpret_from_db(self, fd, value):
		''' converts values from the database into a Python type. Usually does nothing,
		except for fancy types that simple databases doesn't handle well. '''
		return value

	def interpret_to_db(self, fd, value):
		''' converts the incomming to a type the database can handle.
		Usually does nothing, but for datetimes in sqlite, it does the conversion'''
		return value

	def format_datetime(self, value):
		# Should always receive a date and return that date
		return value