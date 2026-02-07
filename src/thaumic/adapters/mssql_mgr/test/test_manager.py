from unittest import TestCase

from thaumic.adapters.mssql_mgr.manager import MsSqlManager
from thaumic.base.fielddata import FieldData


class Test_DBManager(TestCase):

	def test_typedef(self):
		testfield = FieldData('INT')
		decl = MsSqlManager.type_declaration(testfield)
		self.assertEqual('INT', decl)

		testfield = FieldData('INT IDENTITY')
		decl = MsSqlManager.type_declaration(testfield)
		self.assertEqual('INT IDENTITY', decl)

		testfield = FieldData('INT IDENTITY(22,33)')
		decl = MsSqlManager.type_declaration(testfield)
		self.assertEqual('INT IDENTITY(22,33)', decl)

		testfield = FieldData('INT PRIMARY KEY')
		decl = MsSqlManager.type_declaration(testfield)
		self.assertEqual('INT PRIMARY KEY', decl)

		testfield = FieldData('BIGINT')
		decl = MsSqlManager.type_declaration(testfield)
		self.assertEqual('BIGINT', decl)

		testfield = FieldData('BIGINT IDENTITY')
		decl = MsSqlManager.type_declaration(testfield)
		self.assertEqual('BIGINT IDENTITY', decl)


		testfield = FieldData('VARCHAR')
		decl = MsSqlManager.type_declaration(testfield)
		self.assertEqual('VARCHAR', decl)

		testfield = FieldData('VARCHAR(20)')
		decl = MsSqlManager.type_declaration(testfield)
		self.assertEqual('VARCHAR(20)', decl)

		testfield = FieldData('VARCHAR(8000)')
		decl = MsSqlManager.type_declaration(testfield)
		self.assertEqual('VARCHAR(MAX)', decl)


		testfield = FieldData('TEXT')
		decl = MsSqlManager.type_declaration(testfield)
		self.assertEqual('TEXT', decl)


		testfield = FieldData('NVARCHAR(8000)')
		decl = MsSqlManager.type_declaration(testfield)
		self.assertEqual('NVARCHAR(MAX)', decl)

		testfield = FieldData('NVARCHAR(4000)')
		decl = MsSqlManager.type_declaration(testfield)
		self.assertEqual('NVARCHAR(MAX)', decl)

		testfield = FieldData('FLOAT')
		decl = MsSqlManager.type_declaration(testfield)
		self.assertEqual('FLOAT', decl)

		testfield = FieldData('DOUBLE')
		decl = MsSqlManager.type_declaration(testfield)
		self.assertEqual('FLOAT', decl)

		testfield = FieldData('REAL')
		decl = MsSqlManager.type_declaration(testfield)
		self.assertEqual('REAL', decl)

