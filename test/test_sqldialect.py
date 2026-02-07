import unittest
from datetime import datetime

from thaumic import SQLTable, SQLField
from thaumic.base.exceptions import IntegrityError
from thaumic.base.sqldialect import SQLDialect
from test.sqltablemock import SQLTableTester1, SQLTableTester2, SQLTableTester3

ARBITRARY_DT = datetime(2001, 2, 3, 4, 5, 6)


class Test_ProcControl(unittest.TestCase):

	def setUp(self) -> None:
		# self.mockdbspec = Mock()
		# self.mockdbspec.dbname = 'mockdbname'
		# self.mockdbspec.schema = 'mockschema'
		# self.mockdbspec.engine = 'mssql_mgr'
		self.mockdbspec = dict()
		self.mockdbspec['DATABASE'] = 'mockdbname'
		self.mockdbspec['SCHEMA'] = 'mockschema'
		self.mockdbspec['ENGINE'] = 'mssql_mgr'

		self.tablename = 'mocktablename'
		self.table1 = SQLTableTester1()
		self.table2 = SQLTableTester2()
		self.table3 = SQLTableTester3()

		self.table1.set('testint', 16662)
		self.table1.set('testdouble', 2.3)
		self.table1.set('testvarchar', 'varcharvalue')
		self.table1.set('testdatetime', '2020-01-01')

	def test_fulltablename(self):
		response = SQLDialect.fulltablename('schemaname', 'tablename')
		self.assertEqual('"schemaname"."tablename"', response)

	def test_table_exists(self):
		sql, fields = SQLDialect.table_exists(self.table1.ts)
		self.assertEqual("select stat.table_schema as database_name, "
			       "stat.table_name, "
			       "from information_schema.statistics stat "
			       "and stat.table_schema = ? "
			       "and stat.table_name = ? "
			       "group by stat.table_schema, stat.table_name, "
			       "order by stat.table_schema, stat.table_name; ", sql)
		self.assertEqual(['testschema', 'table1test'], fields)

	def test_get_field_list(self):
		sql, params = SQLDialect.get_field_list(self.table1.ts)
		comparable = ''.join(['SELECT "TABLE_CATALOG", "TABLE_SCHEMA", "TABLE_NAME", '
		    '"COLUMN_NAME", 0, "DATA_TYPE", "NUMERIC_PRECISION", '
		    '"CHARACTER_MAXIMUM_LENGTH", "NUMERIC_SCALE", "NUMERIC_PRECISION_RADIX", '
		    "0, '', ",
		    '"COLUMN_DEFAULT", 0, "DATETIME_PRECISION", '
			'"CHARACTER_OCTET_LENGTH", "ORDINAL_POSITION", ',
			'"IS_NULLABLE", 0 FROM "information_schema"."columns" WHERE "table_name"=? ',
			'AND "table_schema"=?'])
		self.assertEqual(comparable, sql)
		self.assertEqual(['table1test', 'testschema'], params)

	def test_create_schema(self):
		retval = SQLDialect.create_schema('testschema')
		self.assertEqual('CREATE SCHEMA testschema', retval)

	def test_list_tables(self, schema=None):
		''' This is the ansi-standard way to get a list of tables in a database.'''
		expected_without = ('SELECT "table_name" FROM "information_schema"."tables" '
				"WHERE \"table_type\"='BASE TABLE' GROUP BY \"table_name\"")
		expected_with = ('SELECT "table_name" FROM "information_schema"."tables" '
				"WHERE \"table_type\"='BASE TABLE' AND \"table_schema\" = 'testschema'"
				' GROUP BY "table_name"')
		retval = SQLDialect.list_tables(schema='testschema')
		self.assertEqual(expected_with, retval)

		retval = SQLDialect.list_tables()
		self.assertEqual(expected_without, retval)


	def test_create_table(self):
		holdfields = self.table1.ts.f
		self.table1.ts.f = dict()

		self.assertRaises(ValueError, SQLDialect.create_table, self.table1.ts)
		self.table1.ts.f = holdfields

		actual = SQLDialect.create_table(self.table1.ts)

		expected = 	('CREATE TABLE "testschema"."table1test" ('
		               ' "testint" INT AUTO_INCREMENT PRIMARY KEY,'
		               '"testdatetime" DATETIME,'
		               '"testdouble" FLOAT,'
		               '"testvarchar" VARCHAR(250) )')

		self.assertEqual(expected, actual)

		expected = ('CREATE TABLE "testschema"."table2test" '
		            '( "testint" INT,'
		            '"testdatetime" DATETIME,'
		            '"testdouble" FLOAT,'
		            '"testvarchar" VARCHAR(250) , '
		            'CONSTRAINT "thaumkey_testschema_table2test" '
		            'UNIQUE ( testdouble,testvarchar ) )')
		actual = SQLDialect.create_table(self.table2.ts)
		self.assertEqual(actual, expected)

		expected = 'CREATE TABLE "testschema"."table3test" ( "testint" INT AUTO_INCREMENT PRIMARY KEY,"testdatetime" DATETIME,"testdouble" FLOAT,"testvarchar" VARCHAR(250) , CONSTRAINT "thaumkey_testschema_table3test" UNIQUE ( testdouble,testvarchar ) )'
		actual = SQLDialect.create_table(self.table3.ts)
		self.assertEqual(expected, actual)

	def test_drop_constraint(self):
		actual = SQLDialect.drop_constraint("mytable", "hard_constraint")
		expected = 'ALTER TABLE "mytable" DROP CONSTRAINT "hard_constraint"'
		self.assertEqual(expected, actual)


	def test_truncate(self):
		actual = SQLDialect.truncate(self.table1.ts.ftn)
		expected = 'TRUNCATE TABLE "testschema"."table1test"'
		self.assertEqual(expected, actual)

	def test_drop(self):
		actual = SQLDialect.drop(self.table1.ts.ftn)
		expected = 'DROP TABLE "testschema"."table1test"'
		self.assertEqual(expected, actual)

	def test_add_column(self):
		actual = SQLDialect.add_column(self.table1.ts.ftn, self.table1.ts.f['testint'])
		expected = 'ALTER TABLE "testschema"."table1test" ADD "testint" INT AUTO_INCREMENT PRIMARY KEY'
		self.assertEqual(expected, actual)

	def test_alter_column(self):
		actual = SQLDialect.alter_column(self.table1.ts.ftn, self.table1.ts.f['testint'])
		expected = 'ALTER TABLE "testschema"."table1test" ALTER COLUMN "testint" INT AUTO_INCREMENT PRIMARY KEY'
		self.assertEqual(expected, actual)

	def test_type_declaration(self):

		actual = SQLDialect.type_declaration(self.table1.ts.f['testint'].fd)
		expected = "INT AUTO_INCREMENT PRIMARY KEY"
		self.assertEqual(expected, actual)

		actual = SQLDialect.type_declaration(self.table1.ts.f['testdatetime'].fd)
		expected = "DATETIME"
		self.assertEqual(expected, actual)

		actual = SQLDialect.type_declaration(self.table1.ts.f['testdouble'].fd)
		expected = "FLOAT"
		self.assertEqual(expected, actual)

		actual = SQLDialect.type_declaration(self.table1.ts.f['testvarchar'].fd)
		expected = "VARCHAR(250)"
		self.assertEqual(expected, actual)


	def test_delete(self):
		retval = SQLDialect.delete(self.table1.ts, sqlwhere='"wrongthing"=2')

		return 'DELETE FROM "testschema"."testtable1" WHERE "wrongthing"=?'


	def test_select(self):
		actual = SQLDialect.select(self.table1.ts)
		expected = 'SELECT "testint","testdatetime","testdouble","testvarchar" FROM "testschema"."table1test"'
		self.assertEqual(expected, actual)

		actual = SQLDialect.select(self.table1.ts, sqlwhere='"wrongthing"=?')
		expected = 'SELECT "testint","testdatetime","testdouble","testvarchar" FROM "testschema"."table1test" WHERE "wrongthing"=?'
		self.assertEqual(expected, actual)

		actual = SQLDialect.select(self.table1.ts, sqlwhere='"wrongthing"=?', sqlorderby='"testdatetime"')
		expected = 'SELECT "testint","testdatetime","testdouble","testvarchar" FROM "testschema"."table1test" WHERE "wrongthing"=? ORDER BY "testdatetime"'
		self.assertEqual(expected, actual)


		actual = SQLDialect.select(self.table1.ts, sqlorderby='"testdatetime"')
		expected = 'SELECT "testint","testdatetime","testdouble","testvarchar" FROM "testschema"."table1test" ORDER BY "testdatetime"'
		self.assertEqual(expected, actual)


	def test_insert(self):
		values1 = {'testint': 1, 'testdatetime': ARBITRARY_DT, 'testdouble': 1.1, 'testvarchar': 'testvalue'}
		values2 = {              'testdatetime': ARBITRARY_DT, 'testdouble': 1.1, 'testvarchar': 'testvalue'}
		values3 = {              'testdatetime': ARBITRARY_DT, 'testdouble': 1.1}

		self.assertRaises(IntegrityError, SQLDialect.insert, self.table1.ts, values1)
		self.assertRaises(IntegrityError, SQLDialect.insert, self.table3.ts, values3)


		actual, params = SQLDialect.insert(self.table2.ts, values1)

		exparams = [1, ARBITRARY_DT, 1.1, 'testvalue']
		expected = 'INSERT INTO "testschema"."table2test" ("testint","testdatetime","testdouble","testvarchar") VALUES (?,?,?,?)'
		self.assertEqual(expected, actual)
		self.assertEqual(exparams, params)

		actual, params = SQLDialect.insert(self.table1.ts, values2)

		exparams = [ARBITRARY_DT, 1.1, 'testvalue']
		expected = 'INSERT INTO "testschema"."table1test" ("testdatetime","testdouble","testvarchar") VALUES (?,?,?)'
		self.assertEqual(expected, actual)
		self.assertEqual(exparams, params)


	def test_where_by_pk(self):
		values1 = {'testint': 1, 'testdatetime': ARBITRARY_DT, 'testdouble': 1.1, 'testvarchar': 'testvalue'}
		values2 = {'testdatetime': ARBITRARY_DT, 'testdouble': 1.1, 'testvarchar': 'testvalue'}
		values3 = {'testint': None, 'testdatetime': ARBITRARY_DT, 'testdouble': 1.1, 'testvarchar': 'testvalue'}

		actual, params = SQLDialect.where_by_pk(self.table1.ts, values1)
		expected = '"testint"=?'
		exparams = [1]
		self.assertEqual(expected, actual)
		self.assertEqual(exparams, params)

		self.assertRaises(IntegrityError, SQLDialect.where_by_pk, self.table2.ts, values1)
		self.assertRaises(IntegrityError, SQLDialect.where_by_pk, self.table1.ts, values2)
		self.assertRaises(IntegrityError, SQLDialect.where_by_pk, self.table1.ts, values3)


	def test_select_by_pk(self):
		values1 = {'testint': 1, 'testdatetime': ARBITRARY_DT, 'testdouble': 1.1, 'testvarchar': 'testvalue'}

		actual, retvals = SQLDialect.select_by_pk(self.table1.ts, values1)
		expected = 'SELECT "testint","testdatetime","testdouble","testvarchar" FROM "testschema"."table1test" WHERE "testint"=?'
		exparams = [1]
		self.assertEqual(expected, actual)
		self.assertEqual(exparams, retvals)

	def test_delete_by_pk(self):
		values1 = {'testint': 1, 'testdatetime': ARBITRARY_DT, 'testdouble': 1.1, 'testvarchar': 'testvalue'}

		actual, retvals = SQLDialect.delete_by_pk(self.table1.ts, values1)
		expected = 'DELETE FROM "testschema"."table1test" WHERE "testint"=?'
		exparams = [1]
		self.assertEqual(expected, actual)
		self.assertEqual(exparams, retvals)

	def test_update_by_pk(self):

		values1 = {'testint': 1, 'testdatetime': ARBITRARY_DT, 'testdouble': 1.1, 'testvarchar': 'testvalue'}
		values2 = {'testint': 1, 'testdatetime': ARBITRARY_DT, 'testdouble': 1.1}
		values3 = {'testint': 1, 'testdatetime': ARBITRARY_DT}
		values4 = {'testdatetime': ARBITRARY_DT, 'testdouble': 1.1, 'testvarchar': 'testvalue'}

		expected = 'UPDATE "testschema"."table1test" SET "testdatetime"=?,"testdouble"=?,"testvarchar"=? WHERE "testint"=?'
		exparams = [ARBITRARY_DT, 1.1, 'testvalue', 1]
		actual, params = SQLDialect.update_by_pk(self.table1.ts, values1)
		self.assertEqual(expected, actual)
		self.assertEqual(exparams, params)


		expected = 'UPDATE "testschema"."table1test" SET "testdatetime"=?,"testdouble"=? WHERE "testint"=?'
		exparams = [ARBITRARY_DT, 1.1, 1]
		actual, params = SQLDialect.update_by_pk(self.table1.ts, values2)
		self.assertEqual(expected, actual)
		self.assertEqual(exparams, params)

		expected = 'UPDATE "testschema"."table1test" SET "testdatetime"=? WHERE "testint"=?'
		exparams = [ARBITRARY_DT, 1]
		actual, params = SQLDialect.update_by_pk(self.table1.ts, values3)
		self.assertEqual(expected, actual)
		self.assertEqual(exparams, params)


		self.assertRaises(IntegrityError, SQLDialect.where_by_pk, self.table1.ts, values4)

	def test_where_by_dims(self):
		values1x = {'testint': 1,   'testdatetime': ARBITRARY_DT, 'testdouble': 1.1}

		values1 = {'testint': 1,    'testdatetime': ARBITRARY_DT, 'testdouble': 1.1, 'testvarchar': 'testvalue'}
		values2 = {'testint': None, 'testdatetime': ARBITRARY_DT, 'testdouble': 1.1, 'testvarchar': 'testvalue'}

		self.assertRaises(IntegrityError, SQLDialect.where_by_dims, self.table1.ts, values1)
		self.assertRaises(IntegrityError, SQLDialect.where_by_dims, self.table2.ts, values1x)

		actual, params = SQLDialect.where_by_dims(self.table2.ts, values1)
		expected = '"testdouble"=? AND "testvarchar"=?'
		exparams = [1.1, 'testvalue']
		self.assertEqual(expected, actual)
		self.assertEqual(exparams, params)

		actual, params = SQLDialect.where_by_dims(self.table2.ts, values2)
		self.assertEqual(expected, actual)
		self.assertEqual(exparams, params)


	def test_select_by_dim(self):
		values1 = {'testint': 1,    'testdatetime': ARBITRARY_DT, 'testdouble': 1.1, 'testvarchar': 'testvalue'}

		self.assertRaises(IntegrityError, SQLDialect.where_by_dims, self.table1.ts, values1)

		actual, params = SQLDialect.select_by_dim(self.table2.ts, values1)
		expected = 'SELECT "testint","testdatetime","testdouble","testvarchar" FROM "testschema"."table2test" WHERE "testdouble"=? AND "testvarchar"=?'
		exparams = [1.1, 'testvalue']
		self.assertEqual(expected, actual)
		self.assertEqual(exparams, params)

	def test_delete_by_dim(self):
		values1 = {'testint': 1,    'testdatetime': ARBITRARY_DT, 'testdouble': 1.1, 'testvarchar': 'testvalue'}

		self.assertRaises(IntegrityError, SQLDialect.where_by_dims, self.table1.ts, values1)

		actual, params = SQLDialect.delete_by_dim(self.table2.ts, values1)
		expected = 'DELETE FROM "testschema"."table2test" WHERE "testdouble"=? AND "testvarchar"=?'
		exparams = [1.1, 'testvalue']
		self.assertEqual(expected, actual)
		self.assertEqual(exparams, params)

	def test_update_by_dim(self):
		values1 = {'testint': 1, 'testdatetime': ARBITRARY_DT, 'testdouble': 1.1, 'testvarchar': 'testvalue'}

		self.assertRaises(IntegrityError, SQLDialect.where_by_dims, self.table1.ts, values1)

		actual, params = SQLDialect.update_by_dim(self.table2.ts, values1)
		expected = 'UPDATE "testschema"."table2test" SET "testint"=?,"testdatetime"=? WHERE "testdouble"=? AND "testvarchar"=?'
		exparams = [1, ARBITRARY_DT, 1.1, 'testvalue']
		self.assertEqual(expected, actual)
		self.assertEqual(exparams, params)
