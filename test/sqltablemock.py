from thaumic import SQLField, SQLTable

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
