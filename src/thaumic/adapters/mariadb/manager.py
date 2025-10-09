

from sys import platform
from thaumic.base.manager import CnxnManager
from thaumic.typemappings.fielddata import PARAMLESS_TYPES, CHAR_TYPES, FLOAT_TYPES, DECIMAL_TYPES


if platform == "linux" or platform == "linux2":
	import MySQLdb as sql
	from mysql.connector import errorcode
	from MySQLdb._exceptions import OperationalError
elif platform == "darwin":
	# OS X
	import pymysql as sql
#	import MySQLdb as sql
#	from MySQLdb._exceptions import OperationalError
elif platform == "win32":
	# Windows...
	pass

DB_INST = None
DEBUG = False

def getinstance(dbname, spec_in=None):
	global DB_INST
	if DB_INST is None:
		DB_INST = dict()
	if dbname not in DB_INST:
		DB_INST[dbname] = MySqlManager(spec_in)
	return DB_INST[dbname]

#def preconnect()

def getpersonal(spec_in, logger=None):
	return MySqlManager(spec_in, logger)


# noinspection PyAbstractClass
class MySqlManager(CnxnManager):
	def __init__(self, dbspec, logger=None):
		super().__init__(dbspec, logger)
		self.engine = 'mariadb'
		self.trusted = dbspec.get('TRUSTED', False)
		self.authentication = dbspec.get('AUTHENTICATION', None)
		self.auto_increment = 'AUTO_INCREMENT'
		self.plhd = '%s'
		self.cnxn = None
		self.connect()

	def cnx(self):
		if self.cnxn is None:
			self.connect()

	def connect(self):
		''' Get a new connection, close old connection if it exists
		'''
		if self.cnxn:
			self.cnxn.close()

		print(f"Connecting to {self.host}/{self.dbname} as {self.username}:{self.password}")
		try:
			self.cnxn = sql.connect(user=self.username, password=self.password,
										host=self.host, database=self.dbname)
#		except OperationalError as oper:
#			if self.debugme:
#				print(f"Operational error: Something is wrong with your user name or password: {oper}")
		except sql.Error as err:
			print(f"error: {err} {err.args[0]}")
			if err.args[0] == 1698:
				self.logger.error("Something is wrong with your user name or password")
			# elif err.errno == errorcode.ER_BAD_DB_ERROR:
			# 	self.logger.error("Database does not exist")
			else:
				self.logger.error(err)

	def fetch(self, query, vargs=None, raw=False, retries=0):
		self.cnx()
		if isinstance(query, list):
			query = self.adjust_quoting(' '.join(query))
		elif not raw:
			query = self.adjust_quoting(query)
		if self.debugme:
			print(f"MySqlManager fetching {query}, {vargs}")

		with self.cnxn.cursor() as cursor:
			if vargs:
				cursor.execute(query, vargs)
			else:
				cursor.execute(query)

			retval = []
			self.rowcount = 0
			for oneitem in cursor:
				self.rowcount += 1
				retval.append(list(oneitem))
		if self.debugme:
			print(f"MySqlManager returning from fetch {retval}")
		return retval

	def execute(self, query, vargs=None, raw=False):
		self.cnx()
		if isinstance(query, list):
			query = self.adjust_quoting(' '.join(query))
		elif not raw:
			query = self.adjust_quoting(query)
		if self.debugme:
			print(f"MySqlManager executing {query}, {vargs}")
		try:
			with self.cnxn.cursor() as cursor:
				if vargs:
					response = cursor.execute(query, vargs)
				else:
					response = cursor.execute(query)
				self.rowcount = response
			if self.debugme:
				print(f"response: {response}")
			self.cnxn.commit()
		except BaseException as be:
			if self.debugme:
				print(f"Programming error attempting to execute {query}: {be}")
			raise
		return response

	def executemany(self, query, vargs, raw=False):
		self.cnx()

		if isinstance(query, list):
			query = self.adjust_quoting(' '.join(query))
		elif not raw:
			query = self.adjust_quoting(query)
		if self.debugme:
			print(f"MySQL executing many {query}: {vargs}")
		self.rowcount = 0
		with self.cnxn.cursor() as cursor:
			try:
				for itr in vargs:
					cursor.execute(query, itr)
					self.rowcount += 1
			except TypeError as te:
				if self.debugme:
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
		self.debug("Candidates for %s: %s" % (tablename, candidates))
		return candidates

	def refresh_schemacache(self):
		pass

	def schema_exists(self, schema):
		''' MariaDB has no concept of schema, so this driver simulates it
		 by adjusting table names.
		 Schemas don't need to be created or verified.
		 '''
		return True

	def create_schema(self, schemaname):
		return True

	def add_unique_constraint(self, schemaname, tablename, column_list, constraintname = None):
		raise NotImplementedError

	def get_rowcount(self, ts):
		sql = f"SELECT count(*) FROM [{ts.schemaname}].[{ts.tablename}];"
		rowcount = self.fetch(sql)
		return rowcount

	def table_exists(self, ts):
		fulltablename = self.mk_tablename(ts).replace('`', '')
		if self.debugme:
			print(f"Checking if {fulltablename} exists")
		tablelist = self.fetch("show tables;")
		for itr in tablelist:
			if fulltablename == itr[0].lower():
				return True
		if self.debugme:
			print(f"{fulltablename} not found in tablelist")
		return False

	def list_tables(self):
		alltables = self.fetch("show tables;")
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
			if self.debugme:
				print(f"row = {row}")
			thiscol = {}
			for itr in range(0,len(self.COLUMNLIST_FIELDS)):
				thiscol[self.COLUMNLIST_FIELDS[itr]] = row[itr]
			retval.append(thiscol)
		if self.debugme:
			print(f"get_column_details({ts}) returning {retval}")
		return retval

	def get_columns(self, ts):
		''' Output should be equivalent to the output from sp_columns
		'''
		fulltablename = self.mk_tablename(ts).replace('`', '')

		sql = [
			"SELECT "
			"TABLE_CATALOG,",
			"TABLE_SCHEMA,",
			"TABLE_NAME,",
			"COLUMN_NAME,",
			"0,",
			"DATA_TYPE,",
			"NUMERIC_PRECISION,",
			"CHARACTER_MAXIMUM_LENGTH,",
			"NUMERIC_SCALE,",
			"0,",
			"0,",
			"'',",
			"COLUMN_DEFAULT,",
			"0,",
			"DATETIME_PRECISION,",
			"CHARACTER_OCTET_LENGTH,",
			"ORDINAL_POSITION,",
			"IS_NULLABLE, 0",
			" FROM INFORMATION_SCHEMA.columns ",
			f"where table_name='{fulltablename}';"]
		sqltxt = ' '.join(sql)
		if self.debugme:
			print(f"Running {sqltxt}")
		retval = self.fetch(sqltxt)
		if self.debugme:
			print(f"get_columns({ts}) returning {retval}")
		return retval

	def get_jdbc_connstr(self):
		if self.port == 3306:
			return f'jdbc:mariadb://{self.host}/{self.dbname}'
		else:
			return f'jdbc:mariadb://{self.host}:{self.port}/{self.dbname}'

	def drop_table(self, ts):
		if self.table_exists(ts):
			self.execute(f"DROP TABLE {ts.tablename};")

	def adjust_quoting(self, query):
		query = query.replace('[', '`')
		query = query.replace(']', '`')
		query = query.replace('?', '%s')
		query = query.replace('IDENTITY(1,1)', 'AUTO_INCREMENT')
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
	def tablename_from_sqlfield(cls, sqlfield):
		if sqlfield.fd.table_owner is None or sqlfield.fd.table_owner == '':
			schema = 'dbo'
		else:
			schema = sqlfield.fd.table_owner
		return f"[{schema}].[{sqlfield.fd.table_name}]"

	@classmethod
	def sql_create_table_prelude(cls, ts):
		return f"CREATE TABLE IF NOT EXISTS"

	@classmethod
	def type_declaration(self, fd):
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
					fd.length = maxlen
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
		if 'AUTO_INCREMENT' in tn_upper or 'IDENTITY' in tn_upper or fd.autoinc_seed is not None:
			retval.append('AUTO_INCREMENT')

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
