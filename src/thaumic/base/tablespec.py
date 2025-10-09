''' A tablespec object stores the names and column listing of a table.
'''

from thaumic.base.sqlfield import fix_field_name


class TableSpec:
	def __init__(self, schemaname, tablename, fieldlist):
		super().__init__()
		self.schemaname = schemaname
		self.tablename = tablename
		self.fieldlist = fieldlist
		self.f = dict()
		self.pk = None
		self.fieldnames = []
		self.non_seqids = []
		self.dimensions = []
		self.metrics = []
		for itr in self.fieldlist:
			itr.fd.table_owner = schemaname
			itr.fd.table_name = tablename
			self.f[itr.fixedname] = itr
			self.fieldnames.append(itr.fixedname)
			if itr.fd.autoinc_seed is None:
				self.non_seqids.append(itr.fixedname)
			if itr.is_dimension:
				self.dimensions.append(itr.fixedname)
			elif itr.fd.is_pk:
				if self.pk is not None:
					raise ValueError(f"Multiple fields marked primary key in table {schemaname}.{tablename}")
				self.pk = itr
			else:
				self.metrics.append(itr.fixedname)
		self.fieldnames_str = '"%s"' % '","'.join(self.fieldnames)
		self.nonseqid_str = '"%s]"' % '","'.join(self.non_seqids)
		self.placeholders = ','.join(['%s'] * len(self.fieldnames))
		self.create_query = None


	def set_primary_key(self, fieldname):
		if fieldname in self.f:
			self.f[fieldname].fd.is_pk = True


	def select_all(self, dbmgr):
		sql = f"SELECT {self.fieldnames_str} FROM {self.fulltablename(dbmgr)};"
		try:
			retval = dbmgr.fetch(sql)
		except pyodbc.ProgrammingError:
#			print(f"Programming error executing |{sql}")
			raise
		return retval

	def generate_create(self, dbmgr):
		# self.mktblnm(dbmgr)
		if self.fieldlist is None:
			raise NotImplementedError
		fields = []
		for itr in self.fieldlist:
			fields.append(f"[{itr.name}] {dbmgr.type_declaration(itr.fd)}")
			# if itr.a:
			# 	fields.append(f"[{itr.fieldname}] {itr.datatype} {itr.attributes}")
			# else:
			# 	fields.append(f"[{itr.fieldname}] {itr.datatype}")

		holder = [
			"CREATE TABLE",
#			self.sql_create_table_prelude(),
			self.fulltablename(dbmgr),
			"(", ",".join(fields), ")"
		]
		return " ".join(holder)

	def validate_fields(self, dbmgr):
		columndetails = dbmgr.get_column_details(self.tablename, self.schema)
		columns = dict()
		for onecolumn in columndetails:
			columns[fix_field_name(onecolumn['COLUMN_NAME'])] = onecolumn
		missingfields = []
		for onefield in self.fieldlist:
			if onefield.fixedname not in columns:
				missingfields.append(onefield)
		if len(missingfields) == 0:
			return True
		for onefield in missingfields:
			self.add_column(dbmgr, onefield)

	def add_column(self, dbmgr, fielddef):
		# self.mktblnm(dbmgr)
		sql = f"ALTER TABLE {self.fulltablename(dbmgr)} ADD {fielddef.fixedname} {dbmgr.type_declaration(fielddef.fd)}"
		dbmgr.execute(sql)
