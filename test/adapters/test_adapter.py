import unittest

from thaumic import SQLTable, SQLField
from thaumic.adapters.sqlite_mgr.manager import SqliteManager


class FauxTable(SQLTable):
	TABLENAME = 'fauxtable'
	SCHEMA = 'fauxschema'
	FIELDLIST = [
		SQLField('seqid', 'INTEGER PRIMARY KEY'),
		SQLField('incremental', 'INT', 1),
		SQLField('somestr', 'VARCHAR(200)'),
		SQLField('someint', 'INT', 1),
		SQLField('somereal', 'FLOAT'),
	]

class AutoincrementFail(SQLTable):
	TABLENAME = 'fauxtable'
	SCHEMA = 'fauxschema'
	FIELDLIST = [
		SQLField('seqid', 'INTEGER PRIMARY KEY'),
		SQLField('incremental', 'INT AUTOINCREMENT', 1),
		SQLField('somestr', 'VARCHAR(200)'),
		SQLField('someint', 'INT'),
		SQLField('somereal', 'FLOAT'),
	]


class FauxTableLessIncremental(SQLTable):
	TABLENAME = 'fauxtable'
	SCHEMA = 'fauxschema'
	FIELDLIST = [
		SQLField('seqid', 'INTEGER PRIMARY KEY'),
		SQLField('somestr', 'VARCHAR(200)'),
		SQLField('someint', 'INT'),
		SQLField('somereal', 'FLOAT'),
	]

class FauxTableLessStr(SQLTable):
	TABLENAME = 'fauxtable'
	SCHEMA = 'fauxschema'
	FIELDLIST = [
		SQLField('seqid', 'INTEGER PRIMARY KEY'),
		SQLField('incremental', 'INT', 1),
		SQLField('someint', 'INT'),
		SQLField('somereal', 'FLOAT'),
	]

class FauxTableLessInt(SQLTable):
	TABLENAME = 'fauxtable'
	SCHEMA = 'fauxschema'
	FIELDLIST = [
		SQLField('seqid', 'INTEGER PRIMARY KEY'),
		SQLField('incremental', 'INT', 1),
		SQLField('somestr', 'VARCHAR(200)'),
		SQLField('somereal', 'FLOAT'),
	]

class FauxTableLessFloat(SQLTable):
	TABLENAME = 'fauxtable'
	SCHEMA = 'fauxschema'
	FIELDLIST = [
		SQLField('seqid', 'INTEGER PRIMARY KEY'),
		SQLField('incremental', 'INT', 1),
		SQLField('somestr', 'VARCHAR(200)'),
		SQLField('someint', 'INT', 1),
	]


DBSPEC = { 'ENGINE': 'sqlite_mgr', 'DBFILE': 'sqlite_test.db', 'DEBUGME': 'true'}

CD_FULL = "[['incremental', 'INTEGER', True], ['seqid', 'INTEGER', True], ['someint', 'INTEGER', True], ['somereal', 'REAL', True], ['somestr', 'TEXT', True]]"
CD_MinInc = "[['seqid', 'INTEGER', True], ['someint', 'INTEGER', True], ['somereal', 'REAL', True], ['somestr', 'TEXT', True]]"
CD_MinStr = "[['incremental', 'INTEGER', True], ['seqid', 'INTEGER', True], ['someint', 'INTEGER', True], ['somereal', 'REAL', True]]"
CD_MinInt = "[['incremental', 'INTEGER', True], ['seqid', 'INTEGER', True], ['somereal', 'REAL', True], ['somestr', 'TEXT', True]]"
CD_MinFloat = "[['incremental', 'INTEGER', True], ['seqid', 'INTEGER', True], ['someint', 'INTEGER', True], ['somestr', 'TEXT', True]]"

FULL_CREATE = 'CREATE TABLE IF NOT EXISTS "fauxschema_fauxtable" ( "seqid" INTEGER PRIMARY KEY,"incremental" INTEGER,"somestr" TEXT,"someint" INTEGER,"somereal" REAL , CONSTRAINT thaumkey_fauxschema_fauxtable UNIQUE ( incremental,someint ) )'


cd_all = [[0, 'seqid', 'INTEGER', 0, None, 1],
          [1, 'incremental', 'INTEGER', 0, None, 0],
          [2, 'somestr', 'TEXT', 0, None, 0],
          [3, 'someint', 'INTEGER', 0, None, 0],
          [4, 'somereal', 'REAL', 0, None, 0]]


def describe_column_details(cd):
	cd = sorted(cd, key=lambda c: c['COLUMN_NAME'])
	retval = []
	for row in cd:
		newrow = []
		newrow.append(row['COLUMN_NAME'])
		newrow.append(row['DATA_TYPE'])
		newrow.append(row['IS_NULLABLE'])
		retval.append(newrow)
	return str(retval)

class TestAdapter(unittest.TestCase):
	def setUp(self):
		self.adapter = SqliteManager(DBSPEC)
		self.fulltable = FauxTable()
		self.adapter.drop_table(self.fulltable.ts)

	def test_connect(self):
		self.adapter.connect()
		tablelist = self.adapter.fetch("SELECT name FROM sqlite_master WHERE type='table';")
		self.fulltable.validate(self.adapter)
		self.assertTrue(self.adapter.table_exists(self.fulltable.ts))
		cd = self.adapter.get_column_details(self.fulltable.ts)
		full_cd = describe_column_details(cd)
		self.assertEqual(CD_FULL, full_cd)

		self.adapter.drop_table(self.fulltable.ts)
		self.assertFalse(self.adapter.table_exists(self.fulltable.ts))

		self.fulltable.validate(self.adapter)
		cd = self.adapter.get_column_details(self.fulltable.ts)
		full_cd = describe_column_details(cd)
		self.assertEqual(CD_FULL, full_cd)
		self.adapter.drop_table(self.fulltable.ts)

	def test_create(self):
		create_sql = self.fulltable.generate_create(self.adapter)
		self.assertEqual(FULL_CREATE, create_sql)
		self.adapter.execute(create_sql)


	def test_autoincrement_fail(self):
		failtable = AutoincrementFail()
		self.assertRaises(ValueError, failtable.validate, self.adapter)

	def test_thaumkey(self):
		self.fulltable.validate(self.adapter)
		response = self.adapter.fetch("select sql from sqlite_master where type='table'")
		for row in response:
			if 'fauxschema_fauxtable' in row[0]:
				mktable = row[0]
		self.assertTrue("CONSTRAINT thaumkey_fauxschema_fauxtable UNIQUE ( incremental,someint )" in mktable)


	def test_add_incremental(self):
		table_minusinc = FauxTableLessIncremental()
		table_minusinc.validate(self.adapter)
		cd = self.adapter.get_column_details(self.fulltable.ts)
		cd_mininc = describe_column_details(cd)
		self.assertEqual(CD_MinInc, cd_mininc)

		self.fulltable.validate(self.adapter)
		cd = self.adapter.get_column_details(self.fulltable.ts)
		full_cd = describe_column_details(cd)
		self.assertEqual(CD_FULL, full_cd)
		self.adapter.drop_table(self.fulltable.ts)

	def test_add_str(self):
		table_minusstr = FauxTableLessStr()
		table_minusstr.validate(self.adapter)
		cd = self.adapter.get_column_details(self.fulltable.ts)
		cd_minstr = describe_column_details(cd)
		self.assertEqual(CD_MinStr, cd_minstr)
		self.fulltable.validate(self.adapter)

		cd = self.adapter.get_column_details(self.fulltable.ts)
		cd_minstr = describe_column_details(cd)
		self.assertEqual(CD_FULL, cd_minstr)
		self.adapter.drop_table(self.fulltable.ts)

	def test_add_int(self):
		table_minusint = FauxTableLessInt()
		table_minusint.validate(self.adapter)
		cd = self.adapter.get_column_details(self.fulltable.ts)
		cd_minint = describe_column_details(cd)
		self.assertEqual(CD_MinInt, cd_minint)

		self.fulltable.validate(self.adapter)
		cd = self.adapter.get_column_details(self.fulltable.ts)
		cd_full = describe_column_details(cd)
		self.assertEqual(CD_FULL, cd_full)
		self.adapter.drop_table(self.fulltable.ts)


	def test_add_float(self):
		table_minusfloat = FauxTableLessFloat()
		table_minusfloat.validate(self.adapter)
		cd = self.adapter.get_column_details(table_minusfloat.ts)
		cd_minfloat = describe_column_details(cd)
		self.assertEqual(CD_MinFloat, cd_minfloat)

		self.fulltable.validate(self.adapter)
		cd = self.adapter.get_column_details(self.fulltable.ts)
		cd_full = describe_column_details(cd)
		self.assertEqual(CD_FULL, cd_full)
		self.adapter.drop_table(self.fulltable.ts)


	def test_crud(self):
		self.fulltable.drop(self.adapter)
		self.fulltable.validate(self.adapter)
		self.fulltable.v['incremental'] = 99
		self.fulltable.v['somestr'] = 'some string'
		self.fulltable.v['someint'] = 105
		self.fulltable.v['somereal'] = 123.456
		self.fulltable.store(self.adapter)

		retriever = FauxTable()
		response = retriever.select_objects(self.adapter, sqlwhere='someint=105')
		self.assertEqual(len(response), 1)
		thisob = response[0]
		self.assertEqual(thisob.v_someint, 105)
		self.assertEqual(thisob.v_somereal, 123.456)
		self.assertEqual(thisob.v_incremental, 99)
		self.assertEqual(thisob.v_somestr, 'some string')

		self.fulltable.v = thisob.v
		self.fulltable.v['incremental'] = 101
		self.fulltable.store(self.adapter)

		response = retriever.select_objects(self.adapter, sqlwhere='someint=105')
		self.assertEqual(len(response), 1)
		thisob = response[0]
		self.assertEqual(thisob.v_someint, 105)
		self.assertEqual(thisob.v_somereal, 123.456)
		self.assertEqual(thisob.v_incremental, 101)
		self.assertEqual(thisob.v_somestr, 'some string')

		self.fulltable.v = thisob.v
		self.fulltable.delete(self.adapter)

		response = retriever.select_objects(self.adapter, sqlwhere='someint=105')
		self.assertEqual(len(response), 0)


