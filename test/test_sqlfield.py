from unittest import TestCase

from thaumic.base.sqlfield import SQLField
from thaumic.base.fielddata import (FieldData)


# Replaces all non-alphanumeric characters to underscores
def fix_field_name(name):
	retval = []
	for onechar in name.strip():
		if onechar.isnumeric() or onechar.isalpha():
			retval.append(onechar)
		else:
			retval.append('_')
	return "".join(retval).lower()


class TestSQLField(TestCase):
	''' SQLField provides information related to the field's place in the world.
	It has a fielddata object, whose job is to identify the data type.
	'''
	def test_init(self):
		test_fd = FieldData(['1','2','3','mockname','5','mocktype','7','8','9','10','11','12','13','14','15','16','17','18','19'])
		testee = SQLField(test_fd)
		self.assertEqual(test_fd, testee.fd)
		self.assertEqual('mockname', testee.name)
		self.assertEqual('mocktype', testee.datatype)
		self.assertEqual('mockname', testee.fixedname)
		self.assertEqual(None, testee.engine)
		self.assertEqual(False, testee.is_dimension)

		testee = SQLField(test_fd, dimension=True)
		self.assertEqual(test_fd, testee.fd)
		self.assertEqual(True, testee.is_dimension)

		self.assertRaises(ValueError, SQLField, dict())
		self.assertRaises(ValueError, SQLField, "fakename")

		self.assertRaises(ValueError, SQLField, "fakename", "invalidtype")

		testee = SQLField('testint', 'INT PRIMARY KEY')
		self.assertEqual('testint', testee.name)
		self.assertEqual('INT', testee.fd.type_name)
		self.assertEqual(1, testee.fd.is_pk)
		self.assertEqual('testint', testee.fixedname)
		self.assertEqual('testint', testee.fd.column_name)
		self.assertEqual(True, testee.fd.is_pk)
		self.assertEqual(True, testee.fd.nullable)


		testee = SQLField('testint', 'INT PRIMARY KEY IDENTITY(1,1)')
		self.assertEqual('testint', testee.name)
		self.assertEqual('INT', testee.fd.type_name)
		self.assertEqual(1, testee.fd.is_pk)
		self.assertEqual(1, testee.fd.autoinc_seed)
		self.assertEqual('testint', testee.fixedname)
		self.assertEqual('testint', testee.fd.column_name)
		self.assertEqual(False, testee.fd.nullable)

		testee = SQLField('testint2', 'INT NOT NULL')
		self.assertEqual('testint2', testee.name)
		self.assertEqual('INT', testee.fd.type_name)
		self.assertEqual('testint2', testee.fixedname)
		self.assertEqual('testint2', testee.fd.column_name)
		self.assertEqual(False, testee.fd.is_pk)
		self.assertEqual(False, testee.fd.nullable)

		testee = SQLField('testdatetime', 'DATETIME')
		self.assertEqual('testdatetime', testee.name)
		self.assertEqual('DATETIME', testee.fd.type_name)
		self.assertEqual('testdatetime', testee.fixedname)
		self.assertEqual('testdatetime', testee.fd.column_name)
		self.assertEqual(False, testee.fd.is_pk)

		testee = SQLField('testtimestamp', 'TIMESTAMP')
		self.assertEqual('testtimestamp', testee.name)
		self.assertEqual('TIMESTAMP', testee.fd.type_name)
		self.assertEqual('testtimestamp', testee.fixedname)
		self.assertEqual('testtimestamp', testee.fd.column_name)


		testee = SQLField('testdouble', 'DOUBLE', 1)
		self.assertEqual('testdouble', testee.name)
		self.assertEqual('FLOAT', testee.fd.type_name)
		self.assertEqual('testdouble', testee.fixedname)
		self.assertEqual('testdouble', testee.fd.column_name)
		self.assertEqual(15, testee.fd.precision)
		self.assertEqual(8, testee.fd.length)

		testee = SQLField('testvarchar', 'VARCHAR(250)', 1, 'UNIQUE')
		self.assertEqual('testvarchar', testee.name)
		self.assertEqual('VARCHAR', testee.fd.type_name)
		self.assertEqual('testvarchar', testee.fixedname)
		self.assertEqual('testvarchar', testee.fd.column_name)
		self.assertEqual(250, testee.fd.precision)
		self.assertEqual(250, testee.fd.length)

		testee = SQLField('testvarchar', 'NVARCHAR(250)', 1, 'UNIQUE')
		self.assertEqual('testvarchar', testee.name)
		self.assertEqual('NVARCHAR', testee.fd.type_name)
		self.assertEqual('testvarchar', testee.fixedname)
		self.assertEqual('testvarchar', testee.fd.column_name)
		self.assertEqual(250, testee.fd.precision)
		self.assertEqual(250, testee.fd.length)
		self.assertEqual(500, testee.fd.char_octet_length)

