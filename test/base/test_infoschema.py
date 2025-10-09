import unittest
from unittest.mock import Mock

from thaumic.base.infoschema import InfoschemaColumns

class TestInfoschemaColumns(unittest.TestCase):
	def setUp(self):
		self.infoschema_columns = InfoschemaColumns()

	def test_get_column_info(self):
		mock_dbmgr = Mock()
		mock_dbmgr.fetch = Mock()
		mock_dbmgr.dq = '"'
		column_info = InfoschemaColumns.get_column_info(mock_dbmgr, "mytable", "public")
		sql = ('SELECT "TABLE_CATALOG","TABLE_SCHEMA","TABLE_NAME","COLUMN_NAME","ORDINAL_POSITION",'
		     '"COLUMN_DEFAULT","IS_NULLABLE","DATA_TYPE","CHARACTER_MAXIMUM_LENGTH","CHARACTER_OCTET_LENGTH","NUMERIC_PRECISION","NUMERIC_SCALE","DATETIME_PRECISION","CHARACTER_SET_NAME","COLLATION_NAME","COLUMN_TYPE","COLUMN_KEY","PRIVILEGES","COLUMN_COMMENT","GENERATION_EXPRESSION","SRS_ID" '
		     'FROM "INFORMATION_SCHEMA"."columns" '
		     "WHERE table_name='mytable' AND table_schema='public';")
		mock_dbmgr.fetch.assert_called_with(sql)

		
		
