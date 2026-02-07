import sqlite3
from unittest import TestCase
from unittest.mock import Mock

import pyhocon

from thaumic import SQLTable
from thaumic.adapters.sqlite_mgr.manager import getinstance, SqliteManager

from test.sqltablemock import SQLTableTester1, SQLTableTester2, SQLTableTester3
from thaumic.adapters.sqlite_mgr.sqlitedialect import SqliteDialect

CFG_FILE = "/Users/robertrapplean/workspace/thaumic/test/adapters/props/sqlite.cfg"

class TestSQLiteManager(TestCase):

	def setUp(self) -> None:
		self.cfg = pyhocon.ConfigFactory.parse_file(CFG_FILE)
		# self.mockdbspec = Mock()
		# self.mockdbspec.dbname = 'mockdbname'
		# self.mockdbspec.schema = 'mockschema'
		# self.mockdbspec.engine = 'mssql_mgr'

		SQLTable.DIALECT = SqliteDialect()
		self.testee = None
		self.mockdbspec = dict()
		self.mockdbspec['DATABASE'] = 'mockdbname'
		self.mockdbspec['SCHEMA']   = 'mockschema'
		self.mockdbspec['ENGINE']   = 'mssql_mgr'

		self.tablename = 'mocktablename'

		self.table1 = SQLTableTester1()
		self.table2 = SQLTableTester2()
		self.table3 = SQLTableTester3()

		self.table1.set('testint', 16662)
		self.table1.set('testdouble', 2.3)
		self.table1.set('testvarchar', 'varcharvalue')
		self.table1.set('testdatetime', '2020-01-01')

	def test_init(self):
		self.testee = SqliteManager(dbspec=self.cfg.dbspec)

		self.assertEqual('sqlite_mgr', self.testee.engine)
		self.assertEqual("/Users/robertrapplean/workspace/thaumic/test/adapters/props/sqlite_test.db", self.testee.dbfile)
		self.assertIsNone(self.testee.authentication)
		self.assertIsInstance(self.testee.cnxn, sqlite3.Connection)
		self.assertIs(self.testee.OperationalError, sqlite3.OperationalError)
		self.assertIs(self.testee.IntegrityError, sqlite3.IntegrityError)
		self.assertIs(sqlite3.ProgrammingError, self.testee.ProgrammingError)
		self.assertIs(self.testee.BaseError, sqlite3.Error)
		self.assertIsInstance(self.testee.gen, SqliteDialect)

	def test_add_column_uses_dialect_and_execute(self):
		# Arrange
		self.testee = SqliteManager(dbspec=self.cfg.dbspec)

		# Replace gen and execute with mocks so we don't touch the real DB
		self.testee.gen = Mock()
		self.testee.execute = Mock()

		mock_ts = Mock()
		mock_ts.ftn = '"schema_table"'
		mock_field = Mock()
		mock_sql = 'ALTER TABLE "schema_table" ADD "new_column" TEXT'

		self.testee.gen.add_column.return_value = mock_sql

		# Act
		self.testee.add_column(mock_ts, mock_field)

		# Assert
		self.testee.gen.add_column.assert_called_once_with(mock_ts.ftn, mock_field)
		self.testee.execute.assert_called_once_with(mock_sql)

	def test_create_table(self):
		holdfields = self.table1.ts.f
		self.table1.ts.f = dict()

		self.assertRaises(ValueError, SqliteDialect.create_table, self.table1.ts)
		self.table1.ts.f = holdfields

		actual = SqliteDialect.create_table(self.table1.ts)


	def test_create_table(self):

		holdfields = self.table1.ts.f
		self.table1.ts.f = dict()

		self.assertRaises(ValueError, SqliteDialect.create_table, self.table1.ts)
		self.table1.ts.f = holdfields

		actual = SqliteDialect.create_table(self.table1.ts)

		expected = 	('CREATE TABLE "testschema_table1test" ('
		               ' "testint" INT AUTO_INCREMENT PRIMARY KEY,'
		               '"testdatetime" DATETIME,'
		               '"testdouble" FLOAT,'
		               '"testvarchar" VARCHAR(250) )')

		self.assertEqual(expected, actual)

		expected = ('CREATE TABLE "testschema_table2test" '
		            '( "testint" INT,'
		            '"testdatetime" DATETIME,'
		            '"testdouble" FLOAT,'
		            '"testvarchar" VARCHAR(250) )')
		actual = SqliteDialect.create_table(self.table2.ts)
		self.assertEqual(actual, expected)

		expected = ('CREATE TABLE "testschema_table3test" '
		            '( "testint" INT AUTO_INCREMENT PRIMARY KEY,'
		            '"testdatetime" DATETIME,'
		            '"testdouble" FLOAT,'
		            '"testvarchar" VARCHAR(250) )')
		actual = SqliteDialect.create_table(self.table3.ts)
		self.assertEqual(expected, actual)


	def ensure_thaumkey(self, ts):

		# check for  len(ts.dimensions) == 0  immediate return without call to
		# self.fetch
		mock_ts = Mock()
		mock_ts.dimensions = []
		if mock_ts:
			ts.f = dict()
			ts.f['testint'] = SQLTable.FieldData()


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
