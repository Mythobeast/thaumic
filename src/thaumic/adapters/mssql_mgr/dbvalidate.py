
from thaumic.adapters.mssql_mgr.dbschema import DbSchema


def load_tabledefs(dbspec):
	schema = DbSchema()
	schema.load_from_database(dbspec)
	return schema


# Destructive comparison.
# If you don't want the objects passed in stripped bare, pass in copies instead
def compare_schemas(dbspec, dbfile):
	schema1 = DbSchema()
	schema1.load_from_database(dbspec)
	schema2 = DbSchema()
	schema2.load_from_file(dbfile)

	for onetable in schema1.tables.values():
		if onetable.tablename not in schema2.tables:
			print(f"Table {onetable.tablename} not found in the db file")
			continue
		# compare_tables(onetable, schema2.tables[onetable.tablename])
		del schema2.tables[onetable.tablename]

	for onetable in schema2.tables.values():
		print(f"Table {onetable.tablename} not found in the db schema")


# def compare_tables(table1, table2):
# 	for onefield in table1.fields:
# 		if onefield.name not in table2.fields:
# 			print(f"Table {table2.tablename} is missing field {onefield.name} in the db file")
# 			continue
# 		compare_tables(onetable, schema2.tables[onetable.tablename])
# 		del schema2.tables[onetable.tablename]
#
# 	for onetable in table2.tables.values():
# 		print(f"Table {table2.tablename} is missing field {onefield.name} in the db schema")


if __name__ == '__main__':
	compare_schemas('DWPHSQL01.dbo', 'testresult.txt')
