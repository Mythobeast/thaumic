from unittest import TestCase

from thaumic.base.fielddata import FieldData, extract_params

testsql = ["""drop table testtable;

create table testtable
(
    mybit BIT,
    mytinyint TINYINT,
    mysmallint SMALLINT,
    myint INT,
    mybigint BIGINT,
    myfloat FLOAT,
    myreal REAL,
    myfloat20 FLOAT(20),
    myfloat30 FLOAT(30),
    myvarchar20 VARCHAR(20),
    myvarchar200 VARCHAR(200),
    mynum NUMERIC,
    mydeci_raw DECIMAL,
    mydeci_10 DECIMAL(10),
    mydeci_19_2 DECIMAL(19,2),
    mybin_10 BINARY(10),
    myvarbin_30 VARBINARY(30),
    mychar_50 CHAR(50),
    mynchar_60 NCHAR(60),
    mynvarchar_70 NVARCHAR(70),
    mydate DATE,
    mytime TIME,
    mytimestamp TIMESTAMP,
    mymoney MONEY,
    mysmallmoney SMALLMONEY,
    mydatetime DATETIME,
    mydatetime2 DATETIME2,
    mydatetimeoffset DATETIMEOFFSET
);

sys.sp_columns'testtable';
"""]


class TestFieldData(TestCase):
	def test_extract_params(self):
		testval = extract_params('something(8)', 10)
		self.assertEqual(1, len(testval))
		self.assertEqual(8, testval[0])

		testval = extract_params('something(MAX)', 10)
		self.assertEqual(1, len(testval))
		self.assertEqual('MAX', testval[0])

		testval = extract_params('something(8,2)', 10)
		self.assertEqual(2, len(testval))
		self.assertEqual(8, testval[0])
		self.assertEqual(2, testval[1])

		testval = extract_params('BINARY(10)', 7)
		self.assertEqual(1, len(testval))
		self.assertEqual(10, testval[0])


	def test_init(self):
		testme = FieldData()
		self.assertIsNone(testme.engine)
		self.assertIsNone(testme.table_qualifier)
		self.assertIsNone(testme.table_owner)
		self.assertIsNone(testme.table_name)
		self.assertIsNone(testme.column_name)
		self.assertIsNone(testme.data_type)
		self.assertIsNone(testme.type_name)
		self.assertIsNone(testme.precision)
		self.assertIsNone(testme.length)
		self.assertIsNone(testme.scale)
		self.assertIsNone(testme.radix)
		self.assertIsNone(testme.nullable)
		self.assertIsNone(testme.remarks)
		self.assertIsNone(testme.default)
		self.assertIsNone(testme.sql_data_type)
		self.assertIsNone(testme.sql_datetime_sub)
		self.assertIsNone(testme.char_octet_length)
		self.assertIsNone(testme.ordinal_position)
		self.assertIsNone(testme.is_nullable)
		self.assertIsNone(testme.ss_data_type)
		self.assertEqual(0, testme.is_pk)
		self.assertIsNone(testme.is_dimension)
		self.assertIsNone(testme.column_family)
		testvals = ['1','2','3','4','5','6','7','8','9','10','11','12','13','14','15','16','17','18','19']
		testme = FieldData(testvals)

		self.assertIsNone(testme.engine)
		self.assertEqual('1', testme.table_qualifier)
		self.assertEqual('2', testme.table_owner)
		self.assertEqual('3', testme.table_name)
		self.assertEqual('4', testme.column_name)
		self.assertEqual('5', testme.data_type)
		self.assertEqual('6', testme.type_name)
		self.assertEqual('7', testme.precision)
		self.assertEqual('8', testme.length)
		self.assertEqual('9', testme.scale)
		self.assertEqual('10', testme.radix)
		self.assertEqual('12', testme.remarks)
		self.assertEqual('13', testme.default)
		self.assertIsNone(testme.sql_data_type)
		self.assertIsNone(testme.sql_datetime_sub)
		self.assertEqual('16', testme.char_octet_length)
		self.assertEqual('17', testme.ordinal_position)
		self.assertEqual('18', testme.nullable)
		self.assertEqual('18', testme.is_nullable)
		self.assertIsNone(testme.ss_data_type)
		self.assertEqual(0, testme.is_pk)
		self.assertFalse(testme.is_dimension)
		self.assertIsNone(testme.column_family)
		self.assertIsNone(testme.column_def)
		self.assertIsNone(testme.autoinc_seed)
		self.assertIsNone(testme.autoinc_inc)
		self.assertIsNone(testme.collation)

		shortlist = ['1']

		self.assertRaises(ValueError, FieldData, shortlist)

	def test_parse_declaration(self):
		testme = FieldData('BIT')
		self.assertEqual('BIT', testme.type_name)
		testme = FieldData('TINYINT')
		self.assertEqual('TINYINT', testme.type_name)
		testme = FieldData('SMALLINT')
		self.assertEqual('SMALLINT', testme.type_name)
		testme = FieldData('INT')
		self.assertEqual('INT', testme.type_name)
		testme = FieldData('BIGINT')
		self.assertEqual('BIGINT', testme.type_name)

		testme = FieldData('FLOAT')
		self.assertEqual('FLOAT', testme.type_name)
		self.assertEqual(15, testme.precision)

		testme = FieldData('FLOAT(20)')
		self.assertEqual('FLOAT', testme.type_name)
		self.assertEqual(7, testme.precision)
		testme = FieldData('FLOAT(30)')
		self.assertEqual('FLOAT', testme.type_name)
		self.assertEqual(15, testme.precision)
		testme = FieldData('REAL')
		self.assertEqual('REAL', testme.type_name)

		testme = FieldData('TEXT')
		self.assertEqual('TEXT', testme.type_name)

		testme = FieldData('GUID')
		self.assertEqual('GUID', testme.type_name)
		self.assertEqual(16, testme.length)
		self.assertIsNone(testme.scale)

		testme = FieldData('NUMERIC')
		self.assertEqual('NUMERIC', testme.type_name)
		self.assertEqual(18, testme.precision)
		self.assertEqual(9, testme.length)
		self.assertEqual(0, testme.scale)

		testme = FieldData('NUMERIC(8)')
		self.assertEqual('NUMERIC', testme.type_name)
		self.assertEqual(8, testme.precision)
		self.assertEqual(0, testme.scale)

		testme = FieldData('NUMERIC(8,2)')
		self.assertEqual('NUMERIC', testme.type_name)
		self.assertEqual(8, testme.precision)
		self.assertEqual(2, testme.scale)
		self.assertEqual(5, testme.char_octet_length)

		testme = FieldData('DECIMAL')
		self.assertEqual('DECIMAL', testme.type_name)

		testme = FieldData('BINARY')
		self.assertEqual('BINARY', testme.type_name)
		self.assertEqual(1, testme.length)
		self.assertEqual(1, testme.char_octet_length)

		testme = FieldData('BINARY(10)')
		self.assertEqual('BINARY', testme.type_name)
		self.assertEqual(10, testme.length)
		self.assertEqual(10, testme.char_octet_length)

		testme = FieldData('VARBINARY')
		self.assertEqual('VARBINARY', testme.type_name)
		self.assertEqual(1, testme.length)
		self.assertEqual(1, testme.char_octet_length)
		testme = FieldData('VARBINARY(20)')
		self.assertEqual('VARBINARY', testme.type_name)
		self.assertEqual(20, testme.length)


		testme = FieldData('CHAR')
		self.assertEqual('CHAR', testme.type_name)
		self.assertEqual(1, testme.length)
		self.assertEqual(1, testme.char_octet_length)

		testme = FieldData('CHAR(30)')
		self.assertEqual('CHAR', testme.type_name)
		self.assertEqual(30, testme.length)
		self.assertEqual(30, testme.char_octet_length)

		testme = FieldData('VARCHAR(20)')
		self.assertEqual('VARCHAR', testme.type_name)
		self.assertEqual(20, testme.length)
		self.assertEqual(20, testme.char_octet_length)

		testme = FieldData('NCHAR')
		self.assertEqual('NCHAR', testme.type_name)
		self.assertEqual(1, testme.length)
		self.assertEqual(2, testme.char_octet_length)

		testme = FieldData('NCHAR(40)')
		self.assertEqual('NCHAR', testme.type_name)
		self.assertEqual(40, testme.length)
		self.assertEqual(80, testme.char_octet_length)

		testme = FieldData('NVARCHAR')
		self.assertEqual('NVARCHAR', testme.type_name)
		self.assertEqual(1, testme.length)
		self.assertEqual(2, testme.char_octet_length)

		testme = FieldData('NVARCHAR(50)')
		self.assertEqual('NVARCHAR', testme.type_name)
		self.assertEqual(50, testme.length)
		self.assertEqual(100, testme.char_octet_length)

		testme = FieldData('DATETIME')
		self.assertEqual('DATETIME', testme.type_name)
		testme = FieldData('DATE')
		self.assertEqual('DATE', testme.type_name)
		testme = FieldData('TIME')
		self.assertEqual('TIME', testme.type_name)
		testme = FieldData('TIMESTAMP')
		self.assertEqual('TIMESTAMP', testme.type_name)

	def test_columndefs(self):
		testme = FieldData('INT IDENTITY')
		self.assertEqual(1, testme.autoinc_seed)
		self.assertEqual(1, testme.autoinc_inc)
		self.assertEqual(1, testme.is_pk)
		self.assertEqual(False, testme.is_dimension)

		testme = FieldData('INT PRIMARY KEY')
		self.assertIsNone(testme.autoinc_seed)
		self.assertIsNone(testme.autoinc_inc)
		self.assertEqual(1, testme.is_pk)
		self.assertEqual(False, testme.is_dimension)

		testme = FieldData('INT AUTO_INCREMENT')
		self.assertEqual(1, testme.autoinc_seed)
		self.assertEqual(1, testme.autoinc_inc)
		self.assertEqual(0, testme.is_pk)
		self.assertEqual(False, testme.is_dimension)


		testme = FieldData('INT IDENTITY(1,1)')
		self.assertEqual(1, testme.autoinc_seed)
		self.assertEqual(1, testme.autoinc_inc)

		testme = FieldData('INT IDENTITY(22,33)')
		self.assertEqual(22, testme.autoinc_seed)
		self.assertEqual(33, testme.autoinc_inc)

		testme = FieldData('INT DEFAULT 22')
		self.assertEqual(22, testme.default)

		testme = FieldData('FLOAT DEFAULT 22.2')
		self.assertEqual(22.2, testme.default)


		testme = FieldData("VARCHAR(300) DEFAULT 'wrong'")
		self.assertEqual('wrong', testme.default)

		testme = FieldData("VARCHAR(300) DEFAULT 'didn''t'")
		self.assertEqual("didn't", testme.default)

