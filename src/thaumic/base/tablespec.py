''' A tablespec object stores the names and column listing of a table.
'''

class TableSpec:
	def __init__(self, schemaname, tablename, fielddatalist):
		super().__init__()
		self.schemaname    = schemaname
		self.tablename     = tablename
		self.fieldlist     = fielddatalist
		self.ftn = None
		self.f = dict()
		self.pk = None
		# List of all field names
		self.fieldnames    = []
		# List of fields that can be inserted
		# Excludes auto-increment
		self.insert_fields = []
		self.non_seqids    = []
		self.dimensions    = []
		self.metrics       = []
		for itr in self.fieldlist:
			# Sort out the dimensions, metrics, and primary key
			itr.table_owner = schemaname
			itr.table_name = tablename
			self.f[itr.column_name] = itr
			self.fieldnames.append(itr.column_name)
			if itr.autoinc_seed is None:
				self.non_seqids.append(itr.column_name)
			if itr.is_dimension:
				self.dimensions.append(itr.column_name)
				self.insert_fields.append(itr.column_name)
			elif itr.is_pk:
				if self.pk is not None:
					raise ValueError(f"Multiple fields marked primary key in table {schemaname}.{tablename}")
				self.pk = itr
			else:
				self.metrics.append(itr.column_name)
				self.insert_fields.append(itr.column_name)
		self.fieldnames_str = '"%s"' % '","'.join(self.fieldnames)
		self.nonseqid_str = '"%s"' % '","'.join(self.non_seqids)
		self.create_query = None

	def set_primary_key(self, fieldname):
		if fieldname not in self.f:
			raise ValueError(f"Attempting to set non-existent field {fieldname} as primary key" )
		self.pk = self.f[fieldname]
		self.pk.is_pk = True

	def has_pk(self):
		return self.pk is not None