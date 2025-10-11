import unittest
from datetime import datetime
from unittest.mock import Mock, call

from thaumic.base.sqlfield import SQLField
from thaumic.base.sqltable import SQLTable


class SQLTableTester1(SQLTable):
	TABLENAME = 'tabletest'
	SCHEMA = 'testschema'
	FIELDLIST = [
		SQLField('testint', 'INT', 0, 'IDENTITY'),
		SQLField('testdatetime', 'DATETIME', 0),
		SQLField('testdouble', 'DOUBLE', 1),
		SQLField('testvarchar', 'VARCHAR(250)', 1, 'UNIQUE')
	]

class SQLTableTester2(SQLTable):
	TABLENAME = 'tabletest'
	SCHEMA = 'testschema'
	FIELDLIST = [
		SQLField('testint', 'INT', 0, 'PRIMARY KEY'),
		SQLField('testdatetime', 'DATETIME', 0),
		SQLField('testdouble', 'DOUBLE', 1),
		SQLField('testvarchar', 'VARCHAR(250)', 1, 'UNIQUE')
	]
class SQLTableTester3(SQLTable):
	TABLENAME = 'tabletest'
	SCHEMA = 'testschema'
	FIELDLIST = [
		SQLField('testint', 'INT PRIMARY KEY AUTO_INCREMENT', 0),
		SQLField('testdatetime', 'DATETIME', 0),
		SQLField('testdouble', 'DOUBLE', 1),
		SQLField('testvarchar', 'VARCHAR(250)', 1, 'UNIQUE')
	]


class Test_ProcControl(unittest.TestCase):

	def setUp(self) -> None:
		# self.mockdbspec = Mock()
		# self.mockdbspec.dbname = 'mockdbname'
		# self.mockdbspec.schema = 'mockschema'
		# self.mockdbspec.engine = 'mssql'
		self.mockdbspec = dict()
		self.mockdbspec['DATABASE'] = 'mockdbname'
		self.mockdbspec['SCHEMA'] = 'mockschema'
		self.mockdbspec['ENGINE'] = 'mssql'

		self.tablename = 'mocktablename'
		self.testee1 = SQLTableTester1()
		self.testee2 = SQLTableTester2()
		self.testee3 = SQLTableTester3()

#		print(f"Field list = {FIELDLIST}")
		self.testee1.set('testint', 16662)
		self.testee1.set('testdouble', 2.3)
		self.testee1.set('testvarchar', 'varcharvalue')
		self.testee1.set('testdatetime', '2020-01-01')


	def test_accessors(self):
		testee = SQLTableTester3()
		testee.set_values([5, None, 2.2, 'justsometext'])
		self.assertEqual('justsometext',  testee.v['testvarchar'])
		self.assertEqual('justsometext',  testee.get('testvarchar'))
		self.assertEqual('justsometext',  testee.v_testvarchar)
		testee.set('testvarchar', 'different string')
		self.assertEqual('different string',  testee.v['testvarchar'])
		self.assertEqual('different string',  testee.get('testvarchar'))
		self.assertEqual('different string',  testee.v_testvarchar)


	def compare_values(self, values):
		self.assertEqual(values[0], self.testee1.v['testint'])
		self.assertEqual(values[1], self.testee1.v['testdatetime'])
		self.assertEqual(values[2], self.testee1.v['testdouble'])
		self.assertEqual(values[3], self.testee1.v['testvarchar'])

	def mock_dbmgr(self):
		mockdbmgr = Mock()
		mockdbmgr.mk_tablename = Mock(return_value='[testschema].[testtable]')
		mockdbmgr.adjust_sql_for_engine = Mock(return_value='fake_adjusted')
		mockdbmgr.rowcount = 0
		mockdbmgr.plhd = '?'
		return mockdbmgr

	def test_init(self):
		self.assertEqual('tabletest', self.testee1.ts.tablename)
		self.assertEqual('testschema', self.testee1.ts.schemaname)
		self.assertEqual(SQLTableTester1.FIELDLIST, self.testee1.ts.fieldlist)
		self.assertEqual(1, self.testee1.ts.fieldlist[0].fd.is_pk)
		self.assertEqual(4, len(self.testee1.ts.fieldlist))
		self.assertEqual(3, len(self.testee1.ts.insert_fields))
		self.assertEqual(2, len(self.testee1.ts.dimensions))
		self.assertEqual(1, len(self.testee1.ts.metrics))

		self.assertEqual(1, self.testee2.ts.fieldlist[0].fd.is_pk)
		self.assertEqual(4, len(self.testee2.ts.fieldlist))
		self.assertEqual(3, len(self.testee2.ts.insert_fields))
		self.assertEqual(2, len(self.testee2.ts.dimensions))
		self.assertEqual(1, len(self.testee2.ts.metrics))

		self.assertEqual(4, len(self.testee3.ts.fieldlist))
		self.assertEqual(3, len(self.testee3.ts.insert_fields))
		self.assertEqual(2, len(self.testee3.ts.dimensions))
		self.assertEqual(1, len(self.testee3.ts.metrics))

	def test_generators(self):
		mock_dbmgr = self.mock_dbmgr()
		mock_dbmgr.type_declaration = Mock(return_value='mock_type')
		where_result = self.testee1.generate_whereconditions(mock_dbmgr)
		self.assertEqual((['[testdouble] = ?', '[testvarchar] = ?'], [2.3, 'varcharvalue']), where_result)
		insert_result = self.testee1.generate_insert(mock_dbmgr)
		self.assertEqual(('INSERT INTO [testschema].[testtable] ([testdatetime],[testdouble],[testvarchar]) VALUES (?,?,?)',
				['2020-01-01', 2.3, 'varcharvalue']), insert_result)
		update_sql, update_values = self.testee1.generate_update(mock_dbmgr)
		self.assertEqual('UPDATE [testschema].[testtable] SET [testdatetime] = ? WHERE [testdouble] = ? and [testvarchar] = ?',
				update_sql)
		self.assertEqual(['2020-01-01', 2.3, 'varcharvalue'], update_values)
		mock_dbmgr.sql_create_if_not_exists = Mock(return_value='CREATE TABLE')
		mock_dbmgr.adjust_query = Mock(return_value='fake_adjusted')
		mock_dbmgr.mk_tablename = Mock(return_value='[testschema].[testtable]')
		create_sql = self.testee1.generate_create(mock_dbmgr)
#		self.assertEqual('CREATE TABLE [testschema].[testtable] ( [testint] mock_type,[testdatetime] '
#				'mock_type,[testdouble] mock_type,[testvarchar] mock_type )', create_sql)
		mock_dbmgr.adjust_query.assert_called_once_with('CREATE TABLE [testschema].[testtable] ( [testint] mock_type,[testdatetime] mock_type,[testdouble] mock_type,[testvarchar] mock_type , CONSTRAINT thaumkey_testschema_tabletest UNIQUE ( testdouble,testvarchar ) )')


	def test_upsert(self):
		dbmgr = self.mock_dbmgr()
		thisnow = datetime.now()

		self.testee1.set('testint', 16662)
		self.testee1.set('testdatetime', thisnow)
		self.testee1.set('testdouble', 2.3)
		self.testee1.set('testvarchar', 'fakechar')
		data = [thisnow, 2.3, 'fakechar', 16662]
#		print(f"insert fields: {self.testee1.insert_fields}")
		self.testee1.upsert(dbmgr)

		dbmgr.execute.assert_called_with('UPDATE [testschema].[testtable] SET [testdouble]=?,[testvarchar]=?,[testdatetime]=? WHERE [testint]=?',
		                                 [2.3, 'fakechar', thisnow, 16662])

#  execute('UPDATE [testschema].[testtable] SET [testdouble]=?,[testvarchar]=?,[testdatetime]=? WHERE [testint]=?', [2.3, 'fakechar', datetime.datetime(2025, 10, 10, 20, 34, 38, 251441), 16662])
#  Actual: execute(<Mock name='mock.adjust_query()' id='4365882560'>, [datetime.datetime(2025, 10, 10, 20, 34, 38, 251441), 2.3, 'fakechar'])


#	datetime(2022, 12, 9, 14, 30, 18, 620964)
#		dbmgr.execute.assert_called_with([call('UPDATE [testschema].[testtable] SET [testdouble]=?,[testvarchar]=?,[testdatetime]=? WHERE testint=?',
#					[2.3, 'fakechar', datetime(2022, 12, 9, 14, 20, 39, 710883), 16662]),
#				call('fake_adjusted', [16662, datetime(2022, 12, 9, 14, 20, 39, 710883), 2.3, 'fakechar'])])

	def test_set_get(self):
		self.assertRaises(ValueError, self.testee1.set_values, [])
		self.testee1.set_values([1, "2022-01-01", 1.1, 'nope'])
		self.compare_values([1, "2022-01-01", 1.1, 'nope'])
		self.assertEqual('nope', self.testee1.get('testvarchar'))
		self.assertRaises(AttributeError, self.testee1.get, 'wrong')
		self.testee1.set('testdouble', 1.5)
		self.assertEqual(1.5, self.testee1.v['testdouble'])
		testdict = {'testint': 5, 'testdatetime': 'doesn\'t matter',
			'testdouble':12.34, 'junk': 'isjunk'}
		self.testee1.set_values(testdict)
		self.assertFalse('junk' in self.testee1.v)

	def test_assure_pk_existing(self):
		testretval = [[16661, 'fakedate', 43.21, 'morestuff']]
		self.testee1.set_values([None, "2022-01-01", 1.1, 'nope'])
		mockdbmgr = self.mock_dbmgr()
		mockdbmgr.fetch = Mock(side_effect=[testretval])
		self.testee1.assure_pk(mockdbmgr)
		self.compare_values(testretval[0])
		mockdbmgr.fetch.assert_called_once()
		mockdbmgr.execute.assert_not_called()

	def test_assure_pk_unexist(self):
		testretval = [[16661, 'fakedate', 43.21, 'morestuff']]
		self.testee1.set_values([None, "2022-01-01", 1.1, 'nope'])
		mockdbmgr = self.mock_dbmgr()
		mockdbmgr.fetch = Mock(side_effect=[[],testretval])
		mockdbmgr.execute = Mock()
		self.testee1.assure_pk(mockdbmgr)
		mockdbmgr.fetch.assert_called()
		mockdbmgr.execute.assert_called()
		self.compare_values(testretval[0])

	def test_assure_pk_exception(self):
		self.testee1.ts.pk = None
		self.testee1.set_values([None, "2022-01-01", 1.1, 'nope'])
		self.assertRaises(ValueError, self.testee1.assure_pk, self.mock_dbmgr())

	def test_pk_update(self):
		self.testee2.set('testint', 16962)
		self.testee2.set('testdouble', 2.4)
		self.testee2.set('testvarchar', 'varcharvalue')
		self.testee2.set('testdatetime', '2020-01-01')

		# positive case, default key field, calls update
		mockdbmgr = self.mock_dbmgr()
		mockdbmgr.execute = Mock()
		mockdbmgr.rowcount = 1
		self.testee2.pk_update(mockdbmgr)
		mockdbmgr.execute.assert_called_with('UPDATE [testschema].[testtable] SET '
				'[testdouble]=?,[testvarchar]=?,[testdatetime]=? WHERE [testint]=?',
				[2.4, 'varcharvalue', '2020-01-01', 16962])

		# positive case, different key field, calls update
		mockdbmgr.execute = Mock()
		mockdbmgr.rowcount = 0
		self.testee2.pk_update(mockdbmgr)

		mockdbmgr.execute.assert_called_with(
			'UPDATE [testschema].[testtable] SET [testdouble]=?,[testvarchar]=?,[testdatetime]=? WHERE [testint]=?',
		                     [2.4, 'varcharvalue', '2020-01-01', 16962])

		# no keyfield should raise value error
		self.testee1.ts.pk = None
		mockdbmgr.execute = Mock()
		self.assertRaises(ValueError, self.testee1.pk_update, mockdbmgr)

		# No value on keyfield should raise value error
		self.testee1.set_primary_key('testint')
		self.assertTrue(self.testee1.ts.f['testint'].fd.is_pk)
		del self.testee1.v['testint']
		mockdbmgr.execute = Mock()
		self.assertRaises(ValueError, self.testee1.pk_update, mockdbmgr)

