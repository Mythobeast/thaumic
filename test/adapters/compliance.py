from thaumic import SQLTable, SQLField


class SQLTableTester1(SQLTable):
	TABLENAME = 'table1test'
	SCHEMA = 'testschema'
	FIELDLIST = [
		SQLField('testint', 'INT', 0, 'IDENTITY'),
		SQLField('testdatetime', 'DATETIME'),
		SQLField('testdouble', 'DOUBLE'),
		SQLField('testvarchar', 'VARCHAR(250)', 0, 'UNIQUE')
	]

class SQLTableTester2(SQLTable):
	TABLENAME = 'table2test'
	SCHEMA = 'testschema'
	FIELDLIST = [
		SQLField('testint', 'INT'),
		SQLField('testdatetime', 'DATETIME', 0),
		SQLField('testdouble', 'DOUBLE', 1),
		SQLField('testvarchar', 'VARCHAR(250)', 1, 'UNIQUE')
	]

class SQLTableTester3(SQLTable):
	TABLENAME = 'table3test'
	SCHEMA = 'testschema'
	FIELDLIST = [
		SQLField('testint', 'INT PRIMARY KEY AUTO_INCREMENT', 0),
		SQLField('testdatetime', 'DATETIME', 0),
		SQLField('testdouble', 'DOUBLE', 1),
		SQLField('testvarchar', 'VARCHAR(250)', 1, 'UNIQUE')
	]


class WeakThaumkey(SQLTable):
	TABLENAME = 'table1test'
	SCHEMA = 'testschema'
	FIELDLIST = [
		SQLField('testint', 'INT', 0, 'IDENTITY'),
		SQLField('testdatetime', 'DATETIME'),
		SQLField('testdouble', 'DOUBLE', 1),
		SQLField('testvarchar', 'VARCHAR(250)', 0, 'UNIQUE')
	]

class StrongThaumkey(SQLTable):
	TABLENAME = 'table1test'
	SCHEMA = 'testschema'
	FIELDLIST = [
		SQLField('testint', 'INT', 0, 'IDENTITY'),
		SQLField('testdatetime', 'DATETIME'),
		SQLField('testdouble', 'DOUBLE', 1),
		SQLField('testvarchar', 'VARCHAR(250)', 1)
	]

class ComplianceFailure(Exception):
	def __init__(self, message):
		super().__init__(message)


def you_shall_comply(dbmgr):
	table1 = SQLTableTester1()
	ftn1 = dbmgr.gen.ftn(table1)

	alltables = dbmgr.get_table_list()
	if ftn1 in alltables:
		dbmgr.drop_table(ftn1)
	alltables = dbmgr.get_table_list()
	if ftn1 in alltables:
		raise ComplianceFailure("Failed to drop table, or didn't list tables correctly")

	dbmgr.create_table(table1)
	alltables = dbmgr.get_table_list()
	if ftn1 not in alltables:
		raise ComplianceFailure("Create table failed")
	allrows = dbmgr.fetch(dbmgr.get_column_details(table1))
	if len(allrows) != 4:
		raise ComplianceFailure("Create didn't generate 4 rows")
	testint = allrows[0]

		raise ComplianceFailure("Create didn't generate 4 rows")

