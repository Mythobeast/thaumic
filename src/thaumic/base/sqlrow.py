

class SQLRow:
	def __init__(self, tablespec):
		self.ts = tablespec
		self.v = dict()

	def __getattr__(self, item):
		''' This allows values to be read BUT NOT WRITTEN via object.v_fieldname syntax'''
		if item[:2] == 'v_':
			chopped = item[2:]
			if chopped in self.ts.f:
				if chopped not in self.v:
					self.v[chopped] = None
				return self.v[chopped]
			raise AttributeError(f'{self.__class__} has no attribute {item}')
		else:
			super(SQLRow, self).__getattribute__(item)

	def set_insert_values(self, row):
		''' This function will shunt to set_values for a dictionary
		For a list, will presume correct ordering, but skip non-writable fields like autoincrements. '''
		if isinstance(row, list):
			if len(row) != len(self.ts.non_seqids):
				raise ValueError(f"Attempt to set values for a table with {len(self.ts.insert_fields)} columns, "
								f"but {len(row)} values supplied")
			for itr in range(0, len(row)):
				# print(f"Setting {self.insert_fields[itr]} with value {row[itr]}")
				self.v[self.ts.insert_fields[itr]] = row[itr]
		elif isinstance(row, dict):
			self.set_values(row)
		else:
			raise ValueError(f'set_insert_values requires a list or dict, but received {type(row)}. ')

	def set_values(self, row):
		''' Takes either dictionary or list. Will insert by name for dictionaries,
		will presume correct ordering for lists.'''
		if isinstance(row, dict):
			for key, value in row.items():
				if key in self.ts.all_fields:
					self.v[key] = value
		elif isinstance(row, list):
			if len(row) != len(self.ts.fieldlist):
				raise ValueError(f"Attempt to set values for a table with {len(self.ts.fieldlist)} columns, "
								f"but {len(row)} values supplied. Maybe you meant to use set_insert_values?")
			for itr in range(0, len(row)):
				self.v[self.ts.fieldnames[itr]] = row[itr]
		else:
			raise ValueError(f'set_values requires a list or dict, but received {type(row)}.')

	def set(self, key, value):
		self.v[key] = value

	def get(self, key, default=None):
		if key in self.v:
			return self.v[key]
		else:
			return default

	def has_pk(self):
		return self.ts.pk is not None and self.ts.pk.fixedname in self.v and self.v[self.ts.pk.fixedname] is not None

	def populate_pk(self, dbmgr):
		''' This can be very expensive when performed one row at a time. '''
		if self.pk is None:
			raise ValueError("{self.ts.tablename}: Cannot populate primary key when none has been defined")
		if self.has_pk():
			return
		self.store(dbmgr)
		result = self.select(dbmgr)
		if len(result) == 0:
			raise ValueError(f"{self.ts.tablename}: Attempt to populate primary key has failed")
		if len(result) > 1:
			raise ValueError(f"{self.ts.tablename}: Multiple results returned from pk selection")
		self.set_values(result[0])


