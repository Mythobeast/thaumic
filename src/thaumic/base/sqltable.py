from datetime import datetime

from pytz import UTC

from thaumic.base.sqldialect import SQLDialect
from thaumic.base.sqlfield import fix_field_name
from thaumic.base.sqlrow import SQLRow
from thaumic.base.tablespec import TableSpec
from thaumic.base.exceptions import IntegrityError

RETFORM_LIST = 0
RETFORM_DICT = 1
RETFORM_OBJ = 2


class SQLTable:
	TABLENAME = None
	SCHEMA = None
	FIELDLIST = [
		# SQLField('id', 'INT PRIMARY KEY IDENTITY', 0),
		# SQLField('type', 'VARCHAR(250)', 0),
		# SQLField('start_datetime', 'DATETIME', 1),
		# SQLField('member_id', 'INT', 1)
	]
	CONSTRAINTS = []
	TS = None

	def __init__(self, ts=None, v=None, dialect=None):
		self.ftn = None
		if dialect is None:
			self.gen = SQLDialect()
		if self.TS is None:
			if ts is not None:
				self.TS = ts
			else:
				self.TS = TableSpec(self.SCHEMA, self.TABLENAME, self.FIELDLIST)
				self.TS.ftn = self.gen.fulltablename(self.SCHEMA, self.TABLENAME)
		if ts is None:
			self.ts = self.TS
		else:
			self.ts = ts
		self.neuro_insert = 0.0
		self.neuro_update = 0.0
		self.neuro_leak = 0.95
		if v is None:
			self.v = dict()
		else:
			self.v = v

	def __getattr__(self, item):
		if item[:2] == 'v_':
			chopped = item[2:]
			if chopped in self.ts.f:
				if chopped not in self.v:
					self.v[chopped] = None
				return self.v[chopped]
			raise AttributeError(f'{self.__class__} has no attribute {item}')
		else:
			super(SQLTable, self).__getattribute__(item)

	def __setattr__(self, name, value):
		if name[:2] == 'v_':
			chopped = name[2:]
			if chopped in self.f:
				self.v[chopped] = value
				return

		super().__setattr__(name, value)


	def set(self, key, value):
		if key not in self.ts.f:
			raise AttributeError(f'{self.__class__} has no field {key}')
		self.v[key] = value

	def get(self, key, default=None):
		if key not in self.ts.f:
			raise AttributeError(f'{self.__class__} has no field {key}')
		if key not in self.v or self.v[key] is None:
			return default
		return self.v[key]

	def clear(self):
		self.v = dict()

	def validate(self, dbmgr):
		''' Assures that all local fields exist in the databse
		Will add missing fields
		Does NOT check for type equivalence. (e.g. VARCHAR(20) vs VARCHAR(40) or INT vs BIGINT
		:param dbmgr: Database manager
		:returns the list of columns in the database,
			in case the calling function wishes to perform further analysis and validation
		'''
		# for line in traceback.format_stack():
		# 	print(line.strip())
		dbmgr.logger.temp_debug(False)

		self.ensure_table_exists(dbmgr)
		# Load the database's list of fields
		columndetails = dbmgr.get_column_details(self.ts)
		db_fielddict = dict()
		for onecolumn in columndetails:
			db_fielddict[fix_field_name(onecolumn["COLUMN_NAME"])] = onecolumn

		# Generate a list of fields that exist locally but not in database
		missingfields = []
		for onefield in self.ts.fieldlist:
			if onefield.fixedname not in db_fielddict:
				missingfields.append(onefield)

		if len(missingfields) > 0:
			for onefield in missingfields:
				self.add_column(dbmgr, onefield)
				db_fielddict[onefield.fixedname] = onefield
		dbmgr.logger.reset_debug()

		return db_fielddict

	def ensure_table_exists(self, dbmgr):
		table_list = dbmgr.fetch(self.gen.list_tables(self.ts.schemaname))

		flat_list = [x for x in table_list]
		if  self.ts.tablename in flat_list:
			return True
		try:
			dbmgr.execute(self.gen.create_schema(self.ts.schemaname))
		except IntegrityError:
			pass
		try:
			dbmgr.execute(self.gen.create_table(dbmgr))
		except IntegrityError:
			pass

	def truncate(self, dbmgr):
		dbmgr.execute(self.gen.truncate(self.ts.ftn))

	def drop(self, dbmgr):
		try:
			dbmgr.execute(self.gen.drop(self.ts.ftn))
		except dbmgr.OperationalError as e:
			if 'no such table' not in str(e):
				raise

	def ensure_thaumkey(self, dbmgr):
		if len(self.ts.dimensions) == 0:
			return

		# get a list of constraints with thaumkey tag
		# Return format: database_name, table_name, index_name, columns, constraint_type "
		result = dbmgr.fetch(self.gen.thaumkey_details(), [self.ts.tablename, self.ts.schemaname])
		if len(result) == 1:
			therow = result[0]
			columns = set(therow.columns.split(","))
			if len(columns) == len(self.ts.dimensions):
				dims = set(self.ts.dimensions)
				union_dims = dims.intersection(columns)
				if len(union_dims) == len(self.ts.dimensions):
					return
			# Thaumkey didn't match the expected, so delete and recreate
			dbmgr.execute(self.gen.drop_constraint(therow[1], therow[2]))
		elif len(result) > 1:
			# If there are multiple, deleting all and
			for row in result:
				dbmgr.execute(self.gen.drop_constraint(row[1], row[2]))

		dbmgr.add_unique_constraint(self.ts.dimensions, constraint_name=f'thaumkey_{self.ts.schemaname}_{self.ts.tablename}')

	def add_column(self, dbmgr, fielddef):
		# self.mktblnm(dbmgr)
		sql = self.gen.add_column(self.ts.ftn, fielddef, dbmgr.type_declaration(fielddef.fd))
		dbmgr.execute(sql)
		self.ensure_thaumkey(dbmgr)

	def alter_column(self, dbmgr, fielddef):
		# self.mktblnm(dbmgr)
		sql = self.gen.alter_column(self.ts.ftn, fielddef, dbmgr.type_declaration(fielddef.fd))
		dbmgr.execute(sql)

	def drop_constraint(self, dbmgr, constraint_name):
		dbmgr.execute(self.gen.drop_constraint(self.ts.tablename, constraint_name))

	def assure_pk(self, dbmgr):
		''' Will return the primary key value if it is set.
		If it isn't set, it will retrieve it from the database.
		If this row doesn't exist in the database, it will create the row and then retrieve it.
		Can be processor intensive, so it is always better to write all rows, then get the
		generated id's.
		'''
		if self.ts.pk is None:
			raise ValueError(f"Table {self.ts.ftn}: Attempt to retrieve/generate a primary key when none assigned")
		# Check if pk already has a value
		if self.ts.pk.name in self.v and self.v[self.ts.pk.name] is not None:
			return self.v[self.ts.pk.name]

		for itr in self.ts.dimensions:
			if itr not in self.v:
				raise ValueError(f"Table {self.ts.ftn}: Cannot store without dimension {itr} being populated")
		
		select_sql, select_values = self.gen.select_by_dim(self.ts, self.v)
		response = dbmgr.fetch(select_sql, select_values)

		if len(response) == 0:
			self.do_insert(dbmgr)
			response = dbmgr.fetch(select_sql, select_values)
			if len(response) == 0:
				raise ValueError("Failed to insert row into database: {self.v}")

		self.set_values(response[0])
		return self.v[self.ts.pk.name]

	def has_pk(self):
		if self.ts.pk is None:
			return False
		if self.ts.pk.name in self.v and self.v[self.ts.pk.name] is not None:
			return True
		return False

	def derive_primary_key(self, tablename):
		"""Returns the name of the primary key as a string when the underlying database
		 does not have that information. This might involve looking up the table name
		 in a configuration file, or a fancy algorithm run on the contents.
		 If no primary key is found, returns 'none'"""
		raise NotImplementedError

	def load_by_dimensions(self, dbmgr):
		result = self.select_by_dimensions(dbmgr)
		if len(result) > 0:
			self.set_values(result[0])

	def do_insert(self, dbmgr):
		sql, values = self.gen.insert(self.ts, self.v)
		dbmgr.logger.debug(f"Performing do_insert by keys {sql}, {values}")
		try:
			dbmgr.execute(sql, values)
			self.balance("i")
			return 1
		except IntegrityError:
			return 0

	def do_pk_update(self, dbmgr):
		sql, values = self.gen.update_by_pk(self.ts, self.v)
		dbmgr.execute(sql, values)
		return dbmgr.rowcount

	def do_dim_update(self, dbmgr):
		sql, values = self.gen.update_by_dim(self.ts, self.v)
		dbmgr.execute(sql, values)
		return dbmgr.rowcount

	def do_update(self, dbmgr):
		''' Performs and update based on the thaumkey '''
		if self.has_pk():
			if self.do_pk_update(dbmgr) > 0:
				self.balance("u")
			return dbmgr.rowcount
		if self.do_dim_update(dbmgr) > 0:
			self.balance("u")
		return dbmgr.rowcount

	def store(self, dbmgr, values=None):
		"""This will make the upsert/indate preferentially attempt whichever is more likely to succeed
		based on recent attempts. Successful updates and inserts will increment the neuro values
		neuro values will degrade over time.
		"""
		if values is not None:
			self.set_values(values)
		# any thaum_update_ts field is a datetime field that tells you when the
		# last time this row was updated
		if 'thaum_update_ts' in self.ts.f:
			self.v['thaum_update_ts'] = dbmgr.format_datetime(datetime.now(tz=UTC))
		if self.has_pk():
			self.pk_update(dbmgr)
			return
		for fieldname in self.ts.dimensions:
			if fieldname not in self.v or self.v[fieldname] is None:
				raise ValueError(f"Attempt to upsert table {self.fulltablename(dbmgr)} "
								f"without setting dimension {fieldname}")

		# If there are no metrics, there are no values to update.
		# If there are no dimensions, there is no way to identify a row to update
		if len(self.ts.metrics) == 0 or len(self.ts.dimensions) == 0:
			self.do_insert(dbmgr)
			return

		if self.neuro_insert > self.neuro_update:
			self.indate(dbmgr)
		else:
			self.upsert(dbmgr)

	def upsert(self, dbmgr):
		if self.do_update(dbmgr) == 1:
			return 1
		return self.do_insert(dbmgr)

	def indate(self, dbmgr):
		if self.do_insert(dbmgr) == 1:
			dbmgr.logger.debug(f"insert from indate successful")
			return 1
		dbmgr.logger.debug(f"insert from indate failed, updating")
		self.do_update(dbmgr)
		return dbmgr.rowcount

	def delete(self, dbmgr):
		'''
		Deletes based on either primary key or all dimensions. Will fail if neither primary key
		nor dimensions are fully populated
		:param dbmgr:
		:return:
		'''

		if self.has_pk():
			sql, values = self.gen.delete_by_pk(self.ts, self.v)
		else:
			sql, values = self.gen.delete_by_dim(self.ts, self.v)
		dbmgr.execute(sql, values)


	def load_from_dict(self, content):
		usedkeys = []
		issues = dict()
		for key, value in content.items():
			lowkey = key.lower()
			if hasattr(self, 'IGNORED_FIELDS'):
				if lowkey in self.IGNORED_FIELDS:
					usedkeys.append(key)
					continue
			if lowkey in self.ts.f:
				self.v[lowkey] = value
				usedkeys.append(key)
			else:
				print(f"Field {lowkey} not found in fields")
		for key, value in content.items():
			if key not in usedkeys:
				if value is not None or not isinstance(value, str) or len(value) > 0:
					issues[key] = f'Non-empty value for field expected to be empty: {key}: "{value}"'
		return issues

	def get_text_key(self):
		retval = []
		for field in self.dimensions:
			if field in self.v:
				retval.append(str(self.v[field]))
			else:
				retval.append('_')
		return '|'.join(retval)

	@classmethod
	def load_from_csvfile(cls, dbmgr, filename):
		''' Open filename as csvreader
		get column names
		validate that columns exist in this class
		for row:
			put row into values
			insert values if not exists (don't update)
		'''
		raise NotImplementedError

	def select(self, dbmgr, sqlwhere=None, sqlorderby=None, params=None, retform=RETFORM_LIST):
		''' An arbitrary select function, byo clauses'''
		query = self.gen.select(self.ts, sqlwhere, sqlorderby)
		try:
			response = dbmgr.fetch(query, params)
		except dbmgr.ProgrammingError:
			raise
		if len(response) == 0:
			return response
		ret_list = self.format_from_db(dbmgr, response)

		if retform == RETFORM_LIST:
			return ret_list

		ret_dict = []
		for row in response:
			ret_dict.append(self.csv_to_dict(dbmgr, self.ts, row))

		if retform == RETFORM_DICT:
			return ret_dict

		if retform != RETFORM_OBJ:
			raise ValueError(f"Unexpected retform {retform}")

		ret_obj = []
		for row in ret_dict:
			holder = SQLRow(self.ts)
			holder.v = row
			ret_obj.append(holder)
		return ret_obj


	def select_objects(self, dbmgr, sqlwhere=None, sqlorderby=None, params=None):
		return self.select(dbmgr, sqlwhere=sqlwhere,
		        sqlorderby=sqlorderby, params=params, retform=RETFORM_OBJ)

	def select_by_dimensions(self, dbmgr):
		if len(self.ts.dimensions) == 0:
			raise ValueError("select_by_dimensions: No dimensions to select")
		sql, values = self.gen.select_by_dim(self.ts, self.v)
		return dbmgr.fetch(sql, values)


	def format_from_db(self, dbmgr, values):
		''' Presumes a list of values that matches the data types of this table '''
		if isinstance(values, dict):
			return self.format_from_dict(dbmgr, values)
		if isinstance(values, list):
			if len(values) == 0:
				return values
			if isinstance(values[0], list):
				retval = []
				for row in values:
					retval.append(self.format_from_db(dbmgr, row))
				return retval
			if len(values) != len(self.ts.fieldnames):
				raise ValueError('format_from_db: this function requires a list of values '
				                 'that exactly matches the data types of this table')
			cursor = 0
			retval = []
			while cursor < len(self.ts.fieldnames):
				fn = self.ts.fieldnames[cursor]
				retval.append(dbmgr.interpret_from_db(self.ts.f[fn], values[cursor]))
				cursor += 1
			return retval
		raise ValueError('format_from_db: this function requires a list or dictionary of values')


	@staticmethod
	def format_dict_from_db(self, dbmgr, values):
		retval = dict()
		for key, value in values.items():
			if key not in self.ts.f:
				raise ValueError(f"format_dict_from_db: Field {key} not found in fields {self.ts.fieldnames} for table {self.fulltablename(dbmgr)}")
			retval[key] = dbmgr.interpret_from_db(self.ts.f[key], value)

		return retval

	def set_primary_key(self, fieldname):
		self.ts.set_primary_key(fieldname)

	def set_values(self, values):
		if len(values) != len(self.ts.f):
			raise ValueError(f"set_values expected {len(self.ts.f)} values, got {len(values)}")
		if isinstance(values, dict):
			for key, value in values.items():
				if key in self.ts.f:
					self.v[key] = value
			return
		elif isinstance(values, list):
			self.v = self.list_to_dict(self.ts, values)

	def delete_where(self, dbmgr, sqlwhere, params=None):
		sql = self.gen.delete(self.ts, sqlwhere=sqlwhere)
		if params is None:
			retval = dbmgr.execute(sql)
		else:
			retval = dbmgr.execute(sql, params=params)
		return retval

	def establish_seqid(self, dbmgr):
		if 'seqid' not in self.ts.f:
			raise ValueError(f'establish_seqid: {self.tablename} has no seqid.')
		if 'seqid' in self.v and self.v_seqid is not None:
			return self.v_seqid
		for field in self.ts.dimensions:
			if field not in self.v or self.v[field] is None:
				raise ValueError("Attempt to retrieve seqid without first settng all dimensions")
		self.store(dbmgr)
		result = self.select_by_dimensions(dbmgr)
		self.set_values(result[0])


	def balance(self, iu):
		"""Any success from an upsert/indate should call this to accumulate the probability
		of an update or insert succeeding.
		"""
		self.neuro_update *= self.neuro_leak
		self.neuro_insert *= self.neuro_leak
		keyletter = iu.lower()[0]
		if keyletter == "i":
			self.neuro_insert += 1
		elif keyletter == "u":
			self.neuro_update += 1

	@classmethod
	def list_to_dict(cls, ts, lst):
		retval = dict()
		for cursor in range(len(ts.fieldlist)):
			fn = ts.fieldnames[cursor]
			retval[fn] = lst[cursor]
		return retval

# Should be moved to analysis

	# def identify_possible_keys(self, dbmgr):
	# 	columns = InfoschemaColumn.get_columns(dbmgr, self.ts.tablename, self.ts.schemaname)
	# 	query = "SELECT count(*) FROM %s" % self.ftn # nosec B608
	# 	rawcount = self.fetch(query)[0]
	# 	candidates = []
	# 	for onecolumn in columns:
	# 		columnname = onecolumn[3]
	# 		query = "SELECT count(distinct %s) from %s" % (columnname, tablename) # nosec B608
	# 		uniquecount = self.fetch(query)[0]
	# 		if uniquecount == rawcount:
	# 			candidates.append(columnname)
	# 	self.debug("Candidates for %s: %s" % (tablename, candidates))
	# 	return candidates




class CachedTable(SQLTable):
	CACHE = dict()

	@classmethod
	def load_cache_where(cls, dbmgr, sqlwhere=None, params=None):
		instance = cls()
		dbmgr.logger.debug(f"Loading cache for {cls.TABLENAME}")
		dbmgr.temp_debug(False)
		objects = instance.select_objects(dbmgr, sqlwhere=sqlwhere, params=params)
		for obj in objects:
			cls.CACHE[obj.get_text_key()] = obj
		dbmgr.reset_debug()

	def cached_store(self, dbmgr):
		cache_key = self.get_text_key()
		if cache_key not in self.CACHE:
			self.logger.debug(f'key {cache_key} not cached')
			self.store(dbmgr)
			return True
		cached = self.CACHE[cache_key]
		for key in self.ts.f:
			if key == 'thaum_update_ts' or self.ts.f[key].iskey():
				continue
			if key not in self.v and key not in cached.v:
				continue
			if key not in self.v or key not in cached.v:
				if dbmgr.debugme:
					print(f'Key {key} of {cache_key} out of sync')
				self.store(dbmgr)
				return True
			trueval = str(self.ts.f[key].formatvalue(self.v[key]))
			truecached = str(cached.v[key])
			if trueval != truecached:
				self.logger.debug(f'Key {key} of {cache_key} out of sync: {trueval}{type(self.ts.f[key].formatvalue(self.v[key]))} != {truecached}{type(cached.v[key])}')
				self.store(dbmgr)
				return True
		return False

