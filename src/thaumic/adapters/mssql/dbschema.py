from thaumic.mssql.sqltable import MsSQLTable

TODOLIST = ['Personnel', 'Response_Master_Incident', 'Response_Vehicles_Assigned']

class DbSchema:
	def __init__(self):
		self.tables = dict()

	def load_from_database(self, dbmgr):
		sql = "SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE';"
		retval = dbmgr.fetch(sql)
		print(f"Found {len(retval)} tables")

		for row in retval:
			database, schema, tablename, type = row
			if tablename not in TODOLIST:
				continue
			self.tables[tablename.lower()] = MsSQLTable(tablename=tablename, schema=schema)
			self.tables[tablename.lower()].load_from_database(dbmgr)

	def load_from_file(self, filename):
		current_table = ""
		table_holder = None
		with open(filename, 'r') as infile:
			for oneline in infile:
				parts = oneline.split('","')
				if parts[2] != current_table:
					if table_holder is not None:
						self.tables[current_table.lower()] = table_holder
					table_holder = MsSQLTable(None, parts[2])
				table_holder.addcolumn(parts)

	def save_to_file(self, filename):
		with open(filename, 'w') as infile:
			for onetable in self.tables.values():
				for onecolumn in onetable.fields:
					infile.write(onecolumn.serialize())

	def save_to_path(self, dbmgr, target):
		for onetable in self.tables.values():
			# Fixfieldname does the operations required to make the table name a good file name
			filename = f"{target}/{onetable.SCHEMA}/{onetable.TABLENAME}.py"
			onetable.generate_python(dbmgr, filename)
			# with open(filename, 'w') as infile:
			# 	for onecolumn in onetable.fields:
			# 		infile.write(onecolumn.serialize())

