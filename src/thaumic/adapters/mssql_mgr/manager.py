import pyodbc
import time

from thaumic.base.manager import CnxnManager
from thaumic.base.typemappings import DECIMAL_TYPES, FLOAT_TYPES, CHAR_TYPES, \
	PARAMLESS_TYPES

from thaumic.base.fielddata import FieldData

DB_INST = None
DEBUG = False

def getinstance(dbname, spec_in=None):
	global DB_INST
	if DB_INST is None:
		DB_INST = dict()
	if dbname not in DB_INST:
		DB_INST[dbname] = MsSqlManager(spec_in)
	return DB_INST[dbname]


def getpersonal(spec_in, logger=None):
	return MsSqlManager(spec_in, logger)

class SchemaCache:
	def __init__(self, schemaname):
		self.name = schemaname
		self.lastcheck = 0
		self.tablelist = set()

	def hastable(self, tablename):
		return tablename in self.tablelist

	def add(self, tablename):
		self.tablelist.add(tablename)


class MsSqlManager(CnxnManager):

	def __init__(self, dbspec, logger=None):
		super().__init__(dbspec, logger)
		self.engine = 'mssql_mgr'
		self.trusted = dbspec.get('TRUSTED', False)
		self.authentication = dbspec.get('AUTHENTICATION', None)
		self.auto_increment = 'IDENTITY(1,1)'
		self.plhd = '?'
		self.cnxn = None
		self.connect()
		self.schemacache = dict()
		self.lastcachecheck = 0
		self.debug = dbspec.get('DEBUGME', DEBUG)

	def connect(self):
		''' Get a new connection, close old connection if it exists
		'''
		if self.cnxn:
			self.cnxn.close()

		constr_list = []
		if self.dsn:
			constr_list.append(f'DSN={self.dsn}')
		if self.user:
			constr_list.append(f'UID={self.user}')
		if self.pw:
			constr_list.append(f"PWD={self.pw}")
		if self.host:
			constr_list.append(f'HOST={self.host}')
		if self.database:
			constr_list.append(f'DATABASE={self.database}')
		if self.trusted:
			constr_list.append('Trusted_Connection=yes')
		if self.authentication:
			constr_list.append(f'Authentication={self.authentication}')
		if self.odbc_driver:
			constr_list.append(f'DRIVER={self.odbc_driver}')

		constr = ';'.join(constr_list)
#		print(f"Connecting to {constr}")
		try:
			self.cnxn = pyodbc.connect(constr, autocommit=False)
			# alternative:
			# self.cnxn = pyodbc.connect(
			# 	server=self.host,
			# 	database=self.dbname,
			# 	user=self.username,
			# 	tds_version='7.3',
			# 	password=self.password,
			# 	port=self.port,
			# 	driver='/usr/local/lib/libtdsodbc.so'
			# )
		except pyodbc.InterfaceError as ie:
			self.logger.debug(f"Failure to connect to database with conn string DSN={self.dsn};UID={self.user};PWD=naestrai")
			raise ie

	def fetch(self, query, params=None, raw=False, retries=0):
		if not raw:
			query = self.adjust_quoting(query)
			self.logger.debug(f"MsSqlManager fetching {query}, {params}")

		with self.cnxn.cursor() as cursor:
			if params:
				cursor.execute(query, params)
			else:
				cursor.execute(query)

			retval = []
			self.rowcount = 0
			for oneitem in cursor:
				self.rowcount += 1
				retval.append(list(oneitem))
		self.logger.debug(f"MsSqlManager returning from fetch {retval}")
		return retval

	def execute(self, query, params=None, raw=False):
		if not raw:
			query = self.adjust_quoting(query)
			self.logger.debug(f"MsSqlManager executing {query}, {params}")
		try:
			with self.cnxn.cursor() as cursor:
				if params:
					response = cursor.execute(query, tuple(params))
				else:
					response = cursor.execute(query)

				self.rowcount = cursor.rowcount
			self.logger.debug(f"response: {response}")
			self.cnxn.commit()
		except pyodbc.ProgrammingError:
			if self.debug:
				print(f"Programming error attempting to execute {query}")
			raise
		return self.rowcount

	def executemany(self, query, params, raw=False):
		self.rowcount = 0
		if not raw:
			query = self.adjust_quoting(query)

		self.logger.debug(f"MsSQL executing many: {query}: {params}")
		with self.cnxn.cursor() as cursor:
			try:
				cursor.executemany(query, params)
				self.rowcount = cursor.rowcount
			except pyodbc.ProgrammingError as pe:
				if self.debug:
					print(f"Programming error attempting to execute {query}: {pe}")
				raise pe
		self.cnxn.commit()

	def rollback(self):
		self.cnxn.rollback()

	def refresh_schemacache(self):
		now = int(time.time())
		if now - self.lastcachecheck < 300:
			return
		self.schemacache = dict()
		schemalist = self.fetch('SELECT * FROM [sys].[schemas]')
		for schema in schemalist:
			sn = schema[0].lower()
			self.schemacache[sn] = SchemaCache(sn)
		self.lastcachecheck = now

	def schema_exists(self, schemaname):
#		pid = os.getpid()
		self.refresh_schemacache()
		if schemaname in self.schemacache:
			return True
		schemalist = self.fetch('SELECT * FROM [sys].[schemas] WHERE [name]=?', [schemaname])
		if len(schemalist) > 0:
			sn = schemalist[0][0].lower()
			print(f"schema_exists, found {schemaname};{sn} on second look")
			self.schemacache[sn] = SchemaCache(sn)
			return True
		return False

	def create_schema(self, schemaname):
		schemaname = schemaname.lower()
		self.logger.debug(f"create_schema {schemaname}")
		if schemaname is None or schemaname == 'None':
			raise ValueError("Attempt to create None schema!")
		self.refresh_schemacache()
		if schemaname in self.schemacache:
			return
		try:
			self.execute(f"CREATE SCHEMA {schemaname}")
			self.schemacache[schemaname] = SchemaCache(schemaname)
		except pyodbc.IntegrityError as ie:
			return

	# noinspection PyUnusedLocal
	def add_unique_constraint(self, schemaname, tablename, column_list, constraintname = None):
		columns_with_underscore = '_'.join(column_list)
		columns_with_comma = ','.join(column_list)
		constraint_name = f"{tablename}_unique_{columns_with_underscore}"

		sql = ' '.join([
			f"IF NOT EXISTS(SELECT * FROM dbo.sysobjects ",
			f"WHERE id = object_id(N'[dbo].[{constraint_name}]'))",
			f"ALTER TABLE [{schemaname}].[{tablename}]",
			f"ADD CONSTRAINT [{constraint_name}]",
			f"UNIQUE ({columns_with_comma});"])

		self.execute(sql)

	def get_rowcount(self, ts):
		sql = f"SELECT count(*) FROM [{ts.schemaname}].[{ts.tablename}];"
		rowcount = self.fetch(sql)
		return rowcount

	def refresh_tablecache(self, schemaname):
		schemaname = schemaname.lower()
		if schemaname not in self.schemacache:
			self.create_schema(schemaname)
		thisschema = self.schemacache[schemaname]

		if int(time.time()) - thisschema.lastcheck < 300:
			return
#		print(f"tablecache for {schemaname} expired, reloading, {os.getpid()}")
		sql = f"SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA='{schemaname}' AND TABLE_TYPE='BASE TABLE'"
		tablelist = self.fetch(sql)
		for table in tablelist:
			thisschema.add(table[0].lower())
		thisschema.lastcheck = int(time.time())

	def table_exists(self, ts):
		schema = ts.schemaname.lower()
		tablename = ts.tablename.lower()
		if not self.schema_exists(schema):
			return False
		self.refresh_tablecache(schema)
		thisschema = self.schemacache[schema]
		if thisschema.hastable(tablename):
			return True
		sql = f"SELECT * FROM INFORMATION_SCHEMA.TABLES " \
		      f"WHERE TABLE_SCHEMA='{schema}' AND TABLE_NAME='{tablename}'"
		tablelist = self.fetch(sql)
		if len(tablelist) > 0:
			thisschema.add(tablename)
			return True
		return False

	def list_tables(self, schema=None):
		alltables = self.fetch("SELECT * FROM INFORMATION_SCHEMA.TABLES")
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
		self.logger.debug(f"get_column_details({ts}) returning {retval}")
		return retval

	def get_fielddescriptors(self, ts):
		response = self.get_columns(ts)
		retval = dict()
		for row in response:
			newfd = FieldData()
			newfd.init_from_list(row)
			retval[newfd.column_name] = newfd
		return retval

	def get_columns(self, ts):
		''' Output should be equivalent to the output from sp_columns
		'''
		
		sql = [
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
			" FROM INFORMATION_SCHEMA.columns ",
			f"where table_name='{ts.tablename}' ",
			f"and table_schema='{ts.schema}';"]
		sqltxt = ' '.join(sql)
		self.logger.debug(f"Running {sqltxt}")
		retval = self.fetch(sqltxt)
		self.logger.debug(f"get_columns({ts.tablename}, {ts.schema}) returning {retval}")
		return retval

	def get_primary_key(self, tablename):
		"""Returns a string, the name of the primary key
		If the table is in STAR_PK, it's because the primary key
		isn't defined in the database.
		If no primary key is found, returns 'none' """

		# tablename = tablename.lower()
		# if tablename in STAR_PK:
		# 	if STAR_PK[tablename] is not 'none':
		# 		return STAR_PK[tablename]

		query = [
			"SELECT kcu.column_name FROM information_schema.table_constraints tc "
			"LEFT JOIN information_schema.key_column_usage kcu on (tc.constraint_name=kcu.constraint_name "
			"and tc.table_schema=kcu.table_schema and tc.table_name=kcu.table_name) "
			"WHERE tc.constraint_type='PRIMARY KEY' AND tc.table_schema='%s' "
			"AND tc.table_name='%s';" % (self.schema, tablename)]
		result = self.fetch(" ".join(query))
		if len(result) == 0:
			return "none"
		return result[0][0]

	def identify_possible_keys(self, tablename):
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
		return candidates

	def get_jdbc_connstr(self):
		return 'jdbc:sqlserver://%s;database=%s' % (self.host, self.database)

	def drop_table(self, ts):
		if self.table_exists(ts):
			self.execute(f"DROP TABLE {ts.schemaname}.{ts.tablename}")

	def adjust_quoting(self, query):
		query = query.replace('%s', '?')
		query = query.replace('AUTO_INCREMENT', 'IDENTITY(1,1)')
		return query

	def add_column(self, sqlfield):
		# self.mktblnm(dbmgr)
		sql = f"ALTER TABLE {self.tablename_from_sqlfield(sqlfield)} ADD {sqlfield.fixedname} {self.type_declaration(sqlfield.fd)}"
		self.execute(sql)

	def alter_column(self, sqlfield):
		# self.mktblnm(dbmgr)
		sql = f"ALTER TABLE {self.tablename_from_sqlfield(sqlfield)} ALTER COLUMN {sqlfield.fixedname} {self.type_declaration(sqlfield.fd)}"
		self.execute(sql)

	#
	# # This function will read the database and output an existing python object that describes that table.
	# # This is not in a final version. I still need to read the indexes to figure out which columns
	# # compose the unique key
	### This needs to be adjusted to call type_declaration from dbmgr
	# def extract_table_def(self, tablename, schema = None):
	# 	if schema is None:
	# 		schema = 'dbo'
	# 	retval = [f'class SQLTable_{tablename}(MsSQLTable):',
	# 			f"    TABLENAME = '{tablename}'",
	# 			f"    SCHEMA    = '{schema}'",
	# 			"    FIELDLIST = ["
	# 	]
	# 	columns = self.get_columns(self, tablename)
	# 	for column in columns:
	# 		fd = FieldData(column)
	# 		retval.append(f"        MsSqlField('{fd.column_name}', '{fd.type_declaration()}', 0),")
	# 	retval.append('    ]')

	@classmethod
	def tablename_from_sqlfield(cls, sqlfield):
		if sqlfield.fd.table_owner is None or sqlfield.fd.table_owner == '':
			schema = 'dbo'
		else:
			schema = sqlfield.fd.table_owner
		return f"[{schema}].[{sqlfield.fd.table_name}]"

	@classmethod
	def sql_create_if_not_exists(cls, ts):
		return f"IF NOT (EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{ts.schemaname}' AND  TABLE_NAME = '{ts.tablename}')) CREATE TABLE"

	@classmethod
	def type_declaration(cls, fd):
		tn_upper = fd.type_name.upper()
		parts = tn_upper.split()
		typename = parts[0]

		# Add parameters to type name
		if typename not in PARAMLESS_TYPES:
			if typename in CHAR_TYPES and fd.length != 1:
				maxlen = 8000
				if typename[0] == 'N':
					maxlen = 4000
				if fd.length >= maxlen or fd.length == -1:
					typename = f'{typename}(MAX)'
				else:
					typename = f"{typename}({fd.length})"
			elif typename in FLOAT_TYPES:
				if fd.precision <= 7:
					typename = 'REAL'
				else:
					typename = 'FLOAT'
			elif typename in DECIMAL_TYPES:
				if fd.precision == 18 and fd.scale == 0:
					typename = 'DECIMAL'
				else:
					typename = f'DECIMAL({fd.precision},{fd.scale})'

		retval = [typename]

		if 'IDENTITY' in tn_upper or fd.autoinc_seed is not None:
			if fd.autoinc_seed is None:
				fd.autoinc_seed = 1
				fd.autoinc_inc = 1
			if fd.autoinc_inc == 1 and fd.autoinc_seed == 1:
				retval.append('IDENTITY')
			else:
				retval.append(f'IDENTITY({fd.autoinc_seed},{fd.autoinc_inc})')

		if fd.is_pk:
			retval.append('PRIMARY KEY')

		return ' '.join(retval)


def test():
	print("Getting instance")
	dbmgr = getinstance('DWPHSQL01.aligned')
	print("Instance %s" % dbmgr)

	result = dbmgr.list_tables()
	print("Result %s, %s" % (result, len(result)))
	for tablename in result:
		pk = dbmgr.get_primary_key(tablename)
		if len(pk) > 0:
			print("Primary key %s is %s" % (tablename, pk))
		result = dbmgr.get_columns(tablename)
		for oneline in result:
			print("%s.%s" % (tablename, oneline[3]))


if __name__ == "__main__":
	test()
