from thaumic.base.fielddata import FieldData
from validation.testspec import SCHEMA, TABLENAME, make_spec

from thaumic.base.sqltable import SQLTable
from thaumic.base.sqlfield import SQLField
from thaumic.adapters.mysql_mgr.manager import MySqlManager
from thaumic.adapters.mysql_mgr.sqldialect import MysqlDialect



def main():
	dbspec = {'ENGINE':   'mysql',
	          'HOST':     'localhost',
	          'PORT':     3306,
	          'DATABASE': 'testdb',
	          'USER':     'root',
	          'PASSWORD': 'badpassword'
	          }
	validation(dbspec, MySqlManager, MysqlDialect, SQLTable, SQLField)

def validation(dbspec, mgrclass, dialect, tableclass, fieldclass):
	dbmgr = mgrclass(dbspec)
	test_ts = make_spec(fieldclass)
	dbtbl = tableclass(test_ts)
	dbtbl.validate(dbmgr)

	rows = dbmgr.fetch(dialect.get_field_list(test_ts))
	itr = 0
	for row in rows:
		result = FieldData(row)
		validate_fielddata(result, test_ts.fieldlist[itr], SCHEMA, TABLENAME)
		itr += 1


def validate_fielddata(fd, schema, tablename, shouldbe):

	assert(fd.table_owner == schema)
	assert(fd.table_name == tablename)
	assert(fd.column_name == shouldbe.column_name)
	assert(fd.data_type == shouldbe.data_type)
	assert(fd.type_name == shouldbe.type_name)
	assert(fd.precision == shouldbe.precision)
	assert(fd.length == shouldbe.length)
	assert(fd.scale == shouldbe.scale)
	assert(fd.radix == shouldbe.radix)
	assert(fd.nullable == shouldbe.nullable)
	assert(fd.remarks == shouldbe.remarks)
	assert(fd.default == shouldbe.default)
	assert(fd.sql_data_type == shouldbe.sql_data_type)
	assert(fd.sql_datetime_sub == shouldbe.sql_datetime_sub)
	assert(fd.char_octet_length == shouldbe.char_octet_length)
	assert(fd.ordinal_position == shouldbe.ordinal_position)
	assert(fd.is_nullable == shouldbe.is_nullable)
	assert(fd.ss_data_type == shouldbe.ss_data_type)
	assert(fd.is_pk == shouldbe.is_pk)
	assert(fd.is_dimension == shouldbe.is_dimension)
	assert(fd.autoinc_seed == shouldbe.autoinc_seed)
	assert(fd.autoinc_inc == shouldbe.autoinc_inc)


# Create table
	# all types

	# identity auto increment primary key
	# dimensions and metrics
	# thaumkey
		# create
		# update
# Alter table
	# add column
		# all types

# fetch
	# all to list
	# all to dict
	# by seqid
	# select by fields
		# all types
# update
# delete
# insert
# upsert
# indate
# with seqid
# Without seqid

# caching
	# get
	# update
	# delete

# store

if __name__ == '__main__':
	main()
