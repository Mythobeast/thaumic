
from thaumic.base.tablespec import TableSpec

SCHEMA = "testschema"
TABLENAME = "testtable"

def make_spec(fieldclass):
	test_seqid      = fieldclass("seqid", "INT IDENTITY").fd
	test_intfield   = fieldclass("testint", "INT").fd
	test_charfield  = fieldclass("testchar", "VARCHAR(200)").fd
	test_floatfield = fieldclass("testfloat", "FLOAT").fd
	test_numfield   = fieldclass("testnum", "NUMERIC").fd
	test_dtfield    = fieldclass("testdatetime", "DATETIME").fd
	test_datefield  = fieldclass("testdate", "DATE").fd
	test_timefield  = fieldclass("testtime", "TIME").fd

	test_table_spec = TableSpec("testschema", "testtable",
	    [test_seqid, test_intfield, test_charfield,
	     test_floatfield, test_numfield, test_dtfield,
	     test_datefield, test_timefield
	])
	return test_table_spec