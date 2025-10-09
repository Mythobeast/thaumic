
import ceODBC

from thaumic.base.manager import CnxnManager

DB_INST = None

def getinstance(dbname, spec_in):
	global DB_INST
	if DB_INST is None:
		DB_INST = dict()
	if dbname not in DB_INST:
		DB_INST[dbname] = MsSqlManager(spec_in)
	return DB_INST[dbname]


def getpersonal(spec_in, logger=None):
	return MsSqlManager(spec_in, logger)


class MsSqlManager(SqlManager):
	def __init__(self, dbspec, logger=None):
		super().__init__(dbspec, logger)
		self.engine = 'mssql'
		self.auto_increment = 'IDENTITY(1,1)'
		self.cnxn = None
		self.connect()

	def connect(self):
		if self.cnxn:
			self.cnxn.close()

		# print(f"Connecting to DSN={self.dsn};UID={self.username};PWD=naestrai")
		try:
			self.cnxn = ceODBC.connect(f'DSN={self.dsn};UID={self.username};PWD={self.password};DATABASE={self.dbname}',
			                           autocommit=False)
			# alternative:
			# self.cnxn = ceODBC.connect(
			# 	server=self.host,
			# 	database=self.dbname,
			# 	user=self.username,
			# 	tds_version='7.3',
			# 	password=self.password,
			# 	port=self.port,
			# 	driver='/usr/local/lib/libtdsodbc.so'
			# )
		except ceODBC.InterfaceError as ie:
			print(f"Failure to connect to database with conn string DSN={self.dsn};UID={self.username};PWD=naestrai")
			raise ie

	def fetch(self, query, vargs=None, raw=False, retries=0):
		with self.cnxn.cursor() as cursor:
			if vargs:
				cursor.execute(query, vargs)
			else:
				cursor.execute(query)
			self.rowcount = cursor.rowcount
			retval = []
			for oneitem in cursor:
				retval.append(list(oneitem))
		return retval

	def execute(self, query, vargs=None):
		with self.cnxn.cursor() as cursor:
			if vargs:
				retval = cursor.execute(query, tuple(vargs))
			else:
				retval = cursor.execute(query)
			self.cnxn.commit()
			self.rowcount = cursor.rowcount
		return retval

	def executemany(self, query, vargs):
		self.rowcount = 0
		with self.cnxn.cursor() as cursor:
			print(f"Inserting {vargs}")
			cursor.executemany(query, list(vargs))
			self.rowcount = cursor.rowcount
			self.cnxn.commit()
		# return retval


	def schema_exists(self, schemaname):
		schemalist = self.fetch("SELECT * FROM sys.schemas WHERE name='{schemaname}'")
		return len(schemalist) > 0

	def create_schema(self, schemaname):
		try:
			self.execute(f"CREATE SCHEMA {schemaname}")
		except:
			return

	def get_rowcount(self, ts):
		sql = f"SELECT count(*) FROM [{ts.schemaname}].[{ts.tablename}];"
		rowcount = self.fetch(sql)
		return rowcount

	def drop_table(self, ts):
		sql = f"DROP TABLE [{ts.schemaname}].[{ts.tablename}];"
		print(f"Dropping table [{ts.schemaname}].[{ts.tablename}]")
		self.execute(sql)

	def table_exists(self, ts):
		sql = f"SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA='{ts.schemaname}' AND TABLE_NAME = '{ts.tablename}'"
		tablelist = self.fetch(sql)
		return len(tablelist) > 0

	def list_tables(self):
		# alltables = self.fetch("SELECT * FROM %s.INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'" % self.dbname)
		alltables = self.fetch("SELECT * FROM %s.INFORMATION_SCHEMA.TABLES" % self.dbname)
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
			thiscol = {}
			for itr in range(0,len(self.COLUMNLIST_FIELDS)):
				thiscol[self.COLUMNLIST_FIELDS[itr]] = row[itr]
			retval.append(thiscol)
		return retval

	def get_columns(self, ts):
		if schema is None:
			schema = self.schema
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
			"NUMERIC_PRECISION_RADIX, ",
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
			f"and table_schema='{schema}';"]
		retval = self.fetch(" ".join(sql))
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
		return 'jdbc:sqlserver://%s;database=%s' % (self.host, self.dbname)

	def drop_table(self, ts):
		if self.table_exists(ts):
			self.execute(f"DROP TABLE {ts.schemaname}.{ts.tablename}")

	def adjust_quoting(self, query):
		query = query.replace('%s', '?')
		query = query.replace('AUTO_INCREMENT', 'IDENTITY(1,1)')
		return query


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
