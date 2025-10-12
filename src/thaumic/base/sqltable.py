from datetime import datetime

from pytz import UTC

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

	def __init__(self, ts=None, v=None):
		self.ftn = None

		if ts is None:
			self.ts = TableSpec(self.SCHEMA, self.TABLENAME, self.FIELDLIST)
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

	def fulltablename(self, dbmgr):
		if self.ftn is None:
			self.ftn = dbmgr.mk_tablename(self.ts)
		return self.ftn

	def validate(self, dbmgr):
		''' Assures that all local fields exist in the databse
		Will add missing fields,
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
				dbmgr.add_column(onefield)
				db_fielddict[onefield.fixedname] = onefield
		dbmgr.logger.reset_debug()

		return db_fielddict

	def ensure_table_exists(self, dbmgr):

		self.ftn = dbmgr.mk_tablename(self.ts)
		if dbmgr.table_exists(self.ts):
			return True

		dbmgr.create_schema(self.ts.schemaname)
		dbmgr.execute(self.generate_create(dbmgr))


	def truncate_table(self, dbmgr):
		dbmgr.execute(f"TRUNCATE TABLE {self.ftn};")

	def drop(self, dbmgr):
		try:
			dbmgr.execute(f"DROP TABLE {self.ftn};")
		except dbmgr.OperationalError as e:
			if 'no such table' not in str(e):
				raise

	def ensure_thaumkey(self, dbmgr):
		if len(self.ts.dimensions) == 0:
			return
		query = ("select stat.table_schema as database_name, "
            "stat.table_name, "
			"stat.index_name,"
            "group_concat(stat.column_name "
                "order by stat.seq_in_index separator ', ') as columns, "
            "tco.constraint_type "
			"from information_schema.statistics stat "
			"join information_schema.table_constraints tco "
                "on stat.table_schema = tco.table_schema "
                "and stat.table_name = tco.table_name "
                "and stat.index_name = tco.constraint_name "
			"where stat.non_unique = 0 "
                "and stat.table_schema = %s "
		         "and stat.table_name = %s "
		         "and stat.index_name like 'thaumkey_%' "
			"group by stat.table_schema, stat.table_name, "
		         "stat.index_name, tco.constraint_type "
			"order by stat.table_schema, stat.table_name; ")

		result = dbmgr.fetch(query, (self.ts.tablename, self.ts.schemaname))
		if len(result) > 1:
			for row in result:
				dbmgr.drop_constraint(row[2])
		elif len(result) == 1:
			therow = result[0]
			columns = set(therow.columns.split(","))
			if len(columns) == len(self.ts.dimensions):
				dims = set(self.ts.dimensions)
				union_dims = dims.intersection(columns)
				if len(union_dims) == len(self.ts.dimensions):
					return
			dbmgr.drop_constraint(therow[2])

		dbmgr.add_unique_constraint(self.ts.dimensions, constraint_name=f'thaumkey_{self.ts.schemaname}_{self.ts.tablename}')

	def add_column(self, dbmgr, fielddef):
		# self.mktblnm(dbmgr)
		sql = f"ALTER TABLE {self.ftn} ADD {fielddef.fixedname} {dbmgr.type_declaration(fielddef.fd)}"
		dbmgr.execute(sql)
		self.ensure_thaumkey(dbmgr)

	def alter_column(self, dbmgr, sqlfield):
		# self.mktblnm(dbmgr)
		sql = f"ALTER TABLE {self.ftn} ALTER COLUMN {sqlfield.fixedname} {dbmgr.type_declaration(sqlfield.fd)}"
		dbmgr.execute(sql)

	def drop_constraint(self, constraint_name):
		raise NotImplementedError

	def generate_create(self, dbmgr):
		# self.mktblnm(dbmgr)
		if self.ts.fieldlist is None:
			raise NotImplementedError
		fields = []
		for itr in self.ts.fieldlist:
			fields.append(f"[{itr.name}] {dbmgr.type_declaration(itr.fd)}")

		holder = [
			dbmgr.sql_create_if_not_exists(self.ts),
			dbmgr.mk_tablename(self.ts),
			"(",
			",".join(fields),
		]
		if len(self.ts.dimensions) > 0:
			holder.append(f", CONSTRAINT thaumkey_{self.ts.schemaname}_{self.ts.tablename} UNIQUE (")
			holder.append(",".join(self.ts.dimensions))
			holder.append(')')
		holder.append(')')
		return dbmgr.adjust_query(" ".join(holder))

	def assure_pk(self, dbmgr):
		''' Will return the primary key value if it is set.
		If it isn't set, it will retrieve it from the database.
		If this row doesn't exist in the database, it will create the row and then retrieve it.
		Can be processor intensive, so it is always better to write all rows, then get the
		generated id's.
		'''
		if self.ts.pk is None:
			raise ValueError(f"Table {self.fulltablename(dbmgr)}: Attempt to retrieve a primary key when none assigned")
		if self.ts.pk.name in self.v and self.v[self.ts.pk.name] is not None:
			return self.v[self.ts.pk.name]

		for itr in self.ts.dimensions:
			if itr not in self.v:
				raise ValueError(f"Table {self.fulltablename(dbmgr)}: Cannot store without dimension {itr} being populated")
		
		select_sql, select_values = self.generate_select(dbmgr)
		response = dbmgr.fetch(select_sql, select_values)
		if len(response) == 0:
			insert_sql, insert_values = self.generate_insert(dbmgr)
			dbmgr.execute(insert_sql, insert_values)
			response = dbmgr.fetch(select_sql, select_values)
			if len(response) == 0:
				raise ValueError("Failed to insert row into database: {self.v}")
		self.set_values(response[0])
		return self.v[self.ts.pk.name]

	def get_primary_key(self, tablename):
		"""Returns the name of the primary key as a string when the underlying database
		 does not have that information. This might involve looking up the table name
		 in a configuration file, or a fancy algorithm run on the contents.
		 If no primary key is found, returns 'none'"""
		raise NotImplementedError

	def load_by_dimensions(self, dbmgr):
		result = self.select_by_dimensions(dbmgr)
		if len(result) > 0:
			self.set_values(result[0])

	def pk_update(self, dbmgr):
		''' This function will overwrite whatever is in the row identified by the primary key
		'''
		if not self.has_pk():
			raise ValueError(f"Table {self.fulltablename(dbmgr)}: Attempt to store by primary key when none assigned")
		setlist = []
		valuelist = []
		pkname = self.ts.pk.name
		for key, value in self.v.items():
			if key == pkname:
				continue
			setlist.append(f"[{key}]={dbmgr.plhd}")
			valuelist.append(value)
		valuelist.append(self.v[pkname])
		fullset = ",".join(setlist)
		sql = [f"UPDATE {self.fulltablename(dbmgr)}",
		       f"SET {fullset} WHERE [{pkname}]={dbmgr.plhd}"
		       ]
		dbmgr.execute(' '.join(sql), valuelist)
		return dbmgr.rowcount

	def do_insert(self, dbmgr):
		insertstr, values = self.generate_insert(dbmgr)
		dbmgr.logger.debug(f"Performing do_insert by keys {insertstr}, {values}")
		try:
			dbmgr.execute(dbmgr.adjust_query(insertstr), values)
			self.balance("i")
			return 1
		except IntegrityError:
			return 0

	def do_update(self, dbmgr):
		''' Performs and update based on the thaumkey '''
		updatestr, values = self.generate_update(dbmgr)
		try:
			dbmgr.execute(dbmgr.adjust_query(updatestr), values)
			if dbmgr.rowcount > 0:
				self.balance("u")
			return dbmgr.rowcount
		except dbmgr.IntegrityError:
			return 0

	def store(self, dbmgr, values=None):
		"""This will make the upsert/indate preferentially attempt whichever is more likely to succeed
		based on recent attempts. Successful updates and inserts will increment the neuro values
		neuro values will degrade over time.
		"""
		if 'thaum_update_ts' in self.ts.f:
			self.v['thaum_update_ts'] = dbmgr.format_datetime(datetime.now(tz=UTC))
		if len(self.ts.metrics) == 0:
			self.do_insert(dbmgr)
			return
		if self.has_pk():
			self.pk_update(dbmgr)
			return
		if self.neuro_insert > self.neuro_update:
			self.indate(dbmgr, values)
		else:
			self.upsert(dbmgr, values)

	def has_pk(self):
		if self.ts.pk is None:
			return False
		if self.ts.pk.name in self.v and self.v[self.ts.pk.name] is not None:
			return True
		return False

	def upsert(self, dbmgr, values=None):
		if values is not None:
			self.set_values(values)
		if self.has_pk():
				# print(f"Performing PK upsert")
			return self.pk_update(dbmgr)

		for fieldname in self.ts.dimensions:
			if fieldname not in self.v:
				raise ValueError(f"Attempt to upsert table {self.fulltablename(dbmgr)} "
								f"without setting dimension {fieldname}")

		if self.do_update(dbmgr) == 1:
			return 1
		return self.do_insert(dbmgr)

	def indate(self, dbmgr, values=None):
		if values is not None:
			self.set_values(values)

		for onefield in self.FIELDLIST:
			if onefield.fd.is_pk and onefield.name in self.v and self.v[onefield.name] is not None:
				# print(f"Performing PK upsert")
				return self.pk_upsert(dbmgr, onefield)

		for fieldname in self.ts.dimensions:
			if fieldname not in self.v:
				raise ValueError(f"Attempt to upsert table {self.fulltablename(dbmgr)} "
								f"without setting dimension {fieldname}")
		if self.do_insert(dbmgr) == 1:
			dbmgr.logger.debug(f"insert from indate successful")
			return 1
		dbmgr.logger.debug(f"insert from indate failed, updating")
		if self.has_pk():
				# If primary key is populated, then this will definitely be an update
			return self.pk_update(dbmgr)
		self.do_update(dbmgr)
		return dbmgr.rowcount

	def fetch_to_dict(self, columnnames, query, params=None, raw=False, retries=0):
		if not raw:
			query = self.adjust_query(query)
		if self.cnxn is None:
			self.connect()
		retval = None
		while retries > 0:
			retries -= 1
			retval = self._fetch_to_dict(columnnames, query, params)
		return retval

	def _fetch_to_dict(self, columnnames, query, params):
		self.last_query = query
		self.last_parameters = params
		self.logger.debug(f"{self.__class__.__name__}, fetching {query}, {params}", end=",")

		retval = []
		with self.connection.cursor() as cursor:
			if params:
				cursor.execute(query, params)
			else:
				cursor.execute(query)
			self.rowcount = 0
		for row in cursor.fetchall():
			self.rowcount += 1
			retval.append(dict(zip(columnnames, row)))

		return retval

	def delete(self, dbmgr):
		'''
		Deletes based on either primary key or all dimensions. Will fail if neither primary key
		nor dimensions are fully populated
		:param dbmgr:
		:return:
		'''

		if self.has_pk():
			pk = self.ts.pk.name
			# If primary key is populated delete by this value
			sql = f"DELETE FROM {self.fulltablename(dbmgr)} WHERE [{pk}] = ?" # nosec
			dbmgr.execute(sql, [self.v[pk]])
			return

		whereclause = []
		values = []
		for key in self.dimensions:
			if key not in self.v or self.v[key] is None:
				raise ValueError(f"Table {self.tablename} cannot perform blind delete unless all keys are populated. " 
				                 f"Key {key} was not set.")
			whereclause.append(f"[{key}] = {dbmgr.plhd}")
			values.append(self.v[key])
		whereclause = ' AND '.join(whereclause)
		sql = f"DELETE FROM {self.fulltablename(dbmgr)} WHERE {whereclause}" # nosec
		dbmgr.execute(sql, values)

	# SQL Generators
	def generate_insert(self, dbmgr):
		#		self.mktblnm(dbmgr)
		fieldnames = []
		plhd = []
		values = []
		#		print(f"self.v = {self.v}")
		for itr in self.ts.non_seqids:
			fd = self.ts.f[itr].fd
			#			print(f"fd = {fd}")
			if itr in self.v and self.v[itr] is not None:
				fieldnames.append(itr)
				plhd.append(dbmgr.plhd)
				values.append(self.v[itr])
			elif not fd.nullable:
				if fd.default is not None:
					self.v[itr] = fd.default
					fieldnames.append(itr)
					plhd.append(dbmgr.plhd)
					values.append(self.v[itr])
				else:
					raise ValueError(f"Attempting to write to table {self.fulltablename(dbmgr)}, " 
									f"but field {itr} is not nullable and has no value")

		insert_field_str = "[%s]" % "],[".join(fieldnames)
		insert_plhd_str = ','.join(plhd)
		insert_str = f'INSERT INTO {self.fulltablename(dbmgr)} ({insert_field_str}) VALUES ({insert_plhd_str})'

		return insert_str, values

	def generate_whereconditions(self, dbmgr):
		#		self.mktblnm(dbmgr)
		dimensions = []
		values = []
		for key in self.ts.dimensions:
			fd = self.ts.f[key].fd
			if key not in self.v:
				continue
			if self.v[key] is None and not fd.nullable:
				raise ValueError(
					f"Attempting to update or delete from table {self.fulltablename(dbmgr)}, " # nosec
					f"but field {key} is not nullable and where clause is looking for null"
				)
			if self.v[key] is None:
				dimensions.append(f"[{key}] is null")
			else:
				dimensions.append(f"[{key}] = {dbmgr.plhd}")
				values.append(self.v[key])
		return dimensions, values

	def generate_blind_whereclause(self, dbmgr):
		# 		self.mktblnm(dbmgr)
		dimensions = []
		values = []
		for key in self.dimensions:
			if key not in self.v or self.v[key] is None:
				raise ValueError(
					f"Attempting to update or delete from table {self.fulltablename(dbmgr)}, " # nosec
					f"but field {key} is not nullable and where clause is looking for null"
				)
			dimensions.append(f"[{key}] = {dbmgr.plhd}")
			values.append(self.v[key])
		return dimensions, values

	def generate_update(self, dbmgr):
		# 		self.mktblnm(dbmgr)
		metrics = []
		dimensions = []
		values = []

		for itr in self.ts.metrics:
			fd = self.ts.f[itr].fd
			if itr not in self.v:
				continue
			if self.v[itr] is None and not fd.nullable:
				raise ValueError(f"Attempting to update table {self.fulltablename(dbmgr)}, " 
								f"but field {itr} is not nullable and has no value")
			metrics.append(f"[{itr}] = {dbmgr.plhd}")
			values.append(self.v[itr])

		if len(metrics) == 0:
			# There's no difference between an update and an insert if there are no metrics to update
			return None, "no metrics to update"

		dimensions, wherevalues = self.generate_whereconditions(dbmgr)
		if len(wherevalues) > 0:
			values.extend(wherevalues)

		metrics_str = ','.join(metrics)
		if len(dimensions) > 0:
			dimensions_str = ' and '.join(dimensions)
			update_str = f'UPDATE {self.fulltablename(dbmgr)} SET {metrics_str} WHERE {dimensions_str}'
		else:
			update_str = f'UPDATE {self.fulltablename(dbmgr)} SET {metrics_str}'
		return update_str, values

	def generate_select(self, dbmgr):
		# self.mktblnm(dbmgr)
		whereconditions, values = self.generate_whereconditions(dbmgr)
		whereclause = ' AND '.join(whereconditions)
		sql = ' '.join([
			f"SELECT {self.ts.fieldnames_str}",
			f"FROM {self.fulltablename(dbmgr)}",
			f"WHERE {whereclause}"])
		return sql, values

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
	def load_from_csv(cls, dbmgr, filename):
		''' Open filename as csvreader
		get column names
		validate that columns exist in this class
		for row:
			put row into values
			insert values if not exists (don't update)
		'''
		raise NotImplementedError

	def select(self, dbmgr, sqlwhere=None, sqlorderby=None, params=None, retform=RETFORM_LIST):
		query = [f"SELECT {self.ts.fieldnames_str} FROM {self.fulltablename(dbmgr)}"]
		if sqlwhere is not None:
			query.append(f"WHERE {sqlwhere}")
		if sqlorderby is not None:
			query.append(f"ORDER BY {sqlorderby}")
		query = ' '.join(query)
		try:
			retval = dbmgr.fetch(query, params)
		except dbmgr.ProgrammingError:
			raise
		if retform == RETFORM_LIST:
			return retval

		if retform == RETFORM_OBJ or retform == RETFORM_DICT:
			ret_obj = []
			for row in retval:
				holder = SQLRow(self.ts)
				holder.set_values(row)
				ret_obj.append(holder)
			return ret_obj

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
			itr = 0
			for field in self.ts.fieldnames:
				self.v[field] = values[itr]
				itr += 1

	def select_objects(self, dbmgr, sqlwhere=None, sqlorderby=None, params=None):
		return self.select(dbmgr, sqlwhere=sqlwhere,
		        sqlorderby=sqlorderby, params=params, retform=RETFORM_OBJ)

	def select_by_dimensions(self, dbmgr):
		if len(self.ts.dimensions) == 0:
			raise ValueError("select_by_dimensions: No dimensions to select")
		wheredats = []
		params = []
		for field in self.ts.dimensions:
			if field in self.v:
				wheredats.append(f"{field}=?")
				params.append(self.v[field])
			else:
				raise ValueError(f"Dimension {field} missing when selecting by dimensions")

		return self.select(dbmgr, sqlwhere=' and '.join(wheredats), params=params)

	def delete_where(self, dbmgr, sqlwhere, params=None):
		sql = f"DELETE FROM {self.ts.ftn} WHERE {sqlwhere}" # nosec
		retval = dbmgr.execute(sql, params=params)
		return retval

	def update_from_csv(self, dbmgr, filename, headerlist=None):
		''' Open filename as csvreader
		get column names
		validate that columns exist in this class
		for row:
			put row into values
			upsert values
		'''
		raise NotImplementedError

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

