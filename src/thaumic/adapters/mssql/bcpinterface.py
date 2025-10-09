''' Wrapper for the Microsoft bulk copy utility "bcp"
'''

class BcpInterface:
	def __init__(self):
		self.tablename = None
		self.schema = None
		self.database = None
		self.host = None
		self.password = None
		self.dsn = None
		self.user = None
		self.trusted = None

	def set_dbspec(self, dbspec):
		if 'ENGINE' not in dbspec or dbspec['ENGINE'] != 'mssql':
			raise ValueError(f"BcpInterface does not support engine {dbspec['ENGINE']}")
		if 'DSN' in dbspec:
			self.dsn = dbspec['DSN']
		if 'USER' in dbspec:
			self.user = dbspec['USER']
		if 'PASSWORD' in dbspec:
			self.password = dbspec['PASSWORD']
		if 'HOST' in dbspec:
			self.host = dbspec['HOST']
		if 'DATABASE' in dbspec:
			self.database = dbspec['DATABASE']
		if 'TRUSTED' in dbspec:
			self.trusted = dbspec['TRUSTED']

	def set_table(self, ts):
		self.schema = ts.schemaname
		self.tablename = ts.tablename


# Example call:
# bcp analytic_datasets.ldapdupe.ldapgroup
#     format nul
#     -f ldapgroup_format.xml
#     -S dev.edwsql.hosp.dhha.org
#     -U SQOOP
#     -P "Y4v64_X8MuV3FjduQYeH"

