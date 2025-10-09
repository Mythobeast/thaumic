


def scrub_table_name(tablename):
	tn = tablename.lower()
	# hive doesn't tolerate names that start with _
	if tn[0] == '_':
		tn = f"x{tn[1:]}"
	return tn


# noinspection PyUnresolvedReferences
class TableData:
	def __init__(self, dbspec, tablename):
		if dbspec is None:
			self.dbname = None
			self.dbmgr = None
		elif isinstance(dbspec, str):
			self.dbname = dbspec.lower()
			self.dbmgr = getinstance(self.dbname)
		else:
			self.dbmgr = dbspec
			self.dbname = self.dbmgr.dbname

		self.table_name = tablename.lower()
		self.fields = []
		self.primary_key = None
		self.pk_column_name = None

	def load_from_database(self):
		columnlist = self.dbmgr.get_columns(self.table_name)
		for onefield in columnlist:
			self.fields.append(FieldItem(onefield))
		pk_result = self.dbmgr.get_primary_key(self.table_name)
		if pk_result is not None:
			self.set_primary_key(pk_result)

	def set_primary_key(self, columnname):
		self.pk_column_name = columnname.lower()
		for onefield in self.fields:
			if onefield.fd.column_name == columnname:
				onefield.fd.is_pk = True
				self.primary_key = onefield
				return
		self.primary_key = None

	def addcolumn(self, fd):
		raise NotImplementedError("addcolumn must be overridden in TableData subclass")


# def test():
# 	print("Testing")
# 	dbname = "star_prd"
# 	server = "dev.edwsql.hosp.dhha.org"
# 	username = "SQOOP"
# 	password = "none"
#
# 	dbmgr = getinstance(dbname, server, username, password)
# 	testtable = TableData('star_prd', 'ProcedureOrderFact')
# 	testtable.load_from_database()
# 	for onefield in testtable.fields:
# 		print("%s" % onefield)


# if __name__ == '__main__':
# 	test()
