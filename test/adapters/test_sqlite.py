from unittest import TestCase

from thaumic.adapters.sqlite.manager import getinstance


class TestSQLiteManager(TestCase):


	def test_init(self):
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


