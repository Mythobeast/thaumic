''' A tablespec object stores the names and column listing of a table.
'''

from thaumic.base.sqlfield import fix_field_name


class TableSpec:
	def __init__(self, schemaname, tablename, fieldlist):
		super().__init__()
		self.schemaname = schemaname
		self.tablename = tablename
		self.fieldlist = fieldlist
		self.ftn = None
		self.f = dict()
		self.pk = None
		# List of all field names
		self.fieldnames = []
		# List of fields that can be inserted
		# Excludes auto-increment
		self.insert_fields = []
		self.non_seqids = []
		self.dimensions = []
		self.metrics = []
		for itr in fieldlist:
			itr.fd.table_owner = schemaname
			itr.fd.table_name = tablename
			self.f[itr.fixedname] = itr
			self.fieldnames.append(itr.fixedname)
			if itr.fd.autoinc_seed is None:
				self.non_seqids.append(itr.fixedname)
			if itr.is_dimension:
				self.dimensions.append(itr.fixedname)
				self.insert_fields.append(itr.fixedname)
			elif itr.fd.is_pk:
				if self.pk is not None:
					raise ValueError(f"Multiple fields marked primary key in table {schemaname}.{tablename}")
				self.pk = itr
			else:
				self.metrics.append(itr.fixedname)
				self.insert_fields.append(itr.fixedname)
		self.fieldnames_str = '"%s"' % '","'.join(self.fieldnames)
		self.nonseqid_str = '"%s"' % '","'.join(self.non_seqids)
		self.create_query = None


	def set_primary_key(self, fieldname):
		if fieldname not in self.f:
			raise ValueError(f"Attempting to set non-existent field {fieldname} as primary key" )
		self.pk = self.f[fieldname]
		self.pk.fd.is_pk = True

	def has_pk(self):
		return self.pk is not None