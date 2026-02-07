from thaumic.base.sqldialect import SQLDialect
from thaumic.base.typemappings import DECIMAL_TYPES, FLOAT_TYPES, CHAR_TYPES, \
	PARAMLESS_TYPES
from thaumic.base.exceptions import IntegrityError


class SqliteDialect(SQLDialect):

	@classmethod
	def add_column(cls, ftn, field):
		return f"ALTER TABLE {ftn} ADD {cls.IQO}{field.fixedname}{cls.IQC} {cls.type_declaration(field.fd)}"

	@classmethod
	def add_unique_constraint(cls, ftn, column_list, constraintname):
		col_list_str = f"{cls.IQC},{cls.IQO}".join(column_list)
		return f'CREATE UNIQUE INDEX {constraintname} ON {ftn}({cls.IQO}{col_list_str}{cls.IQC})'

	@classmethod
	def alter_column(cls, ftn, field):
		return f"ALTER TABLE {ftn} ALTER COLUMN {cls.IQO}{field.fixedname}{cls.IQC} {cls.type_declaration(field.fd)}"

	@classmethod
	def create_schema(cls, schema):
		return f"CREATE SCHEMA {schema}"

	@classmethod
	def create_table(cls, ts):
		if ts.f is None or len(ts.f) == 0:
			raise ValueError("Cannot create table with no fields")
		fields = []
		for field in ts.f.values():
			fields.append(f"{cls.IQO}{field.fixedname}{cls.IQC} {cls.type_declaration(field.fd)}")

		holder = [ "CREATE TABLE", ts.ftn, "(", ",".join(fields), ")" ]
		return " ".join(holder)

	@classmethod
	def create_thaumkey(cls, ts):
		constraintname = f"thaumkey_{ts.ftn}"
		fieldlist = "{cls.IQC},{cls.IQO}".join(ts.dimensions)
		return f"CREATE INDEX {constraintname} ON {ts.ftn}({cls.IQO}{fieldlist}{cls.IQC})"

	@classmethod
	def delete(cls, ts, sqlwhere):
		'''
		Deletes based on arbitrary where clause
		'''
		return f"DELETE FROM {ts.ftn} WHERE {sqlwhere}"

	@classmethod
	def delete_by_dim(cls, ts, values):
		whereclause, wherevals = cls.where_by_dims(ts, values)
		sql = f"DELETE FROM {ts.ftn} WHERE {whereclause}" # nosec
		return sql, wherevals

	@classmethod
	def delete_by_pk(cls, ts, values):
		whereclause, wherevals = cls.where_by_pk(ts, values)
		sql = f"DELETE FROM {ts.ftn} WHERE {whereclause}" # nosec
		return sql, wherevals

	@classmethod
	def drop(cls, ftn):
		return f"DROP TABLE {ftn}"

	@classmethod
	def drop_constraint(cls, table_name, constraint_name):
		return f"ALTER TABLE {cls.IQO}{table_name}{cls.IQC} DROP CONSTRAINT {cls.IQO}{constraint_name}{cls.IQC}"


	@classmethod
	def fulltablename(cls, schema, tablename):
		return f'{cls.IQO}{schema}_{tablename}{cls.IQC}'

	@classmethod
	def get_field_list(cls, ts):
		sql = [
			"SELECT",
			f'{cls.IQO}TABLE_CATALOG{cls.IQC},',
			f'{cls.IQO}TABLE_SCHEMA{cls.IQC},',
			f'{cls.IQO}TABLE_NAME{cls.IQC},',
			f'{cls.IQO}COLUMN_NAME{cls.IQC},',
			'0,',
			f'{cls.IQO}DATA_TYPE{cls.IQC},',
			f'{cls.IQO}NUMERIC_PRECISION{cls.IQC},',
			f'{cls.IQO}CHARACTER_MAXIMUM_LENGTH{cls.IQC},',
			f'{cls.IQO}NUMERIC_SCALE{cls.IQC},',
			f'{cls.IQO}NUMERIC_PRECISION_RADIX{cls.IQC},',
			'0,',
			"'',",
			f'{cls.IQO}COLUMN_DEFAULT{cls.IQC},',
			'0,',
			f'{cls.IQO}DATETIME_PRECISION{cls.IQC},',
			f'{cls.IQO}CHARACTER_OCTET_LENGTH{cls.IQC},',
			f'{cls.IQO}ORDINAL_POSITION{cls.IQC},',
			f'{cls.IQO}IS_NULLABLE{cls.IQC},',
			'0',
			f"FROM {cls.IQO}information_schema{cls.IQC}.{cls.IQO}columns{cls.IQC}",
			f"WHERE {cls.IQO}table_name{cls.IQC}={cls.PLHD}",
			f"AND {cls.IQO}table_schema{cls.IQC}={cls.PLHD}"]
		sqltxt = ' '.join(sql)
		return sqltxt, [ts.tablename, ts.schemaname]

	@classmethod
	def insert(cls, ts, values : dict):
		sql = f"INSERT INTO {ts.ftn}"
		if ts.has_pk():
			pk = ts.pk.fixedname
			if pk in values and values[pk] is not None:
				raise IntegrityError(f"Table {ts.ftn}, cannot insert a primary key. Key {pk} was set as {values[pk]}.")
		else:
			pk = ''
		for key in ts.dimensions:
			if key not in values or values[key] is None:
				raise IntegrityError(f"Attempt to insert to {ts.ftn} without setting dimension {key}.")
		fieldnames = []
		valuelist = []
		for key, value in values.items():
			if key == pk:
				continue
			fieldnames.append(f"{cls.IQO}{key}{cls.IQC}")
			valuelist.append(value)
		fn_str = ",".join(fieldnames)
		plhds = ','.join([cls.PLHD] * len(fieldnames))
		sql += f" ({fn_str}) VALUES ({plhds})"
		return sql, valuelist

	@classmethod
	def list_tables(cls, schema=None):
		query = [f"SELECT {cls.IQO}name{cls.IQC} FROM {cls.IQO}sqlite_schema{cls.IQC} ",
				f"WHERE {cls.IQO}type{cls.IQC}='table' AND "]
		if schema:
			query.append(f"{cls.IQO}name{cls.IQC} LIKE '{schema}_%'")
		else:
			query.append(f"{cls.IQO}name{cls.IQC} NOT LIKE 'sqlite_%'")
		return ' '.join(query)

	@classmethod
	def select(cls, ts, sqlwhere=None, sqlorderby=None):
		''' Selects based on arbitrary where and orderby clause'''
		query = [f"SELECT {ts.fieldnames_str} FROM {ts.ftn}"]
		if sqlwhere is not None:
			query.append(f"WHERE {sqlwhere}")
		if sqlorderby is not None:
			query.append(f"ORDER BY {sqlorderby}")
		return ' '.join(query)

	@classmethod
	def select_by_dim(cls, ts, values):
		whereclause, wherevals = cls.where_by_dims(ts, values)
		sql = f"SELECT {ts.fieldnames_str} FROM {ts.ftn} WHERE {whereclause}"
		return sql, wherevals

	@classmethod
	def select_by_pk(cls, ts, values):
		whereclause, wherevals = cls.where_by_pk(ts, values)
		sql = f"SELECT {ts.fieldnames_str} FROM {ts.ftn} WHERE {whereclause}"
		return sql, wherevals

	@classmethod
	def table_exists(cls, ts):
		return f"SELECT name FROM sqlite_master WHERE type='table' AND name={cls.PLHD}"

	@classmethod
	def thaumkey_details(cls):
		''' information_schema based check for unique key
		with all dimensions'''
		return ("select stat.table_schema as database_name, "
            "stat.table_name, "
			"stat.index_name, "
			"group_concat(stat.column_name order by stat.seq_in_index separator ', ') as columns, "
			"tco.constraint_type "
			"from information_schema.statistics stat "
			"join information_schema.table_constraints tco "
			"on stat.table_schema = tco.table_schema "
				"and stat.table_name = tco.table_name "
				"and stat.index_name = tco.constraint_name "
			"where stat.non_unique = 0 "
				f"and stat.table_schema = {cls.PLHD} "
				f"and stat.table_name = {cls.PLHD} "
				"and stat.index_name like 'thaumkey_%' "
			"group by stat.table_schema, stat.table_name, "
				"stat.index_name, tco.constraint_type "
			"order by stat.table_schema, stat.table_name")

	@classmethod
	def truncate(cls, ftn):
		return f"TRUNCATE TABLE {ftn}"

	@classmethod
	def type_declaration(cls, fd):
		tn_upper = fd.type_name.upper()
		parts = tn_upper.split()
		typename = parts[0]

		# Add parameters to type name
		if typename not in PARAMLESS_TYPES:
			if typename in CHAR_TYPES and fd.length != 1:
				maxlen = 8000
				if typename[0] == 'N':
					maxlen = 4000
				if fd.length >= maxlen or fd.length == -1:
					fd.length = maxlen
				typename = f"{typename}({fd.length})"
			elif typename in FLOAT_TYPES:
				if fd.precision <= 7:
					typename = 'REAL'
				else:
					typename = 'FLOAT'
			elif typename in DECIMAL_TYPES:
				if fd.precision == 18 and fd.scale == 0:
					typename = 'DECIMAL'
				else:
					typename = f'DECIMAL({fd.precision},{fd.scale})'

		retval = [typename]
		if 'AUTO_INCREMENT' in tn_upper or 'IDENTITY' in tn_upper or fd.autoinc_seed is not None:
			retval.append('AUTO_INCREMENT')

		if fd.is_pk:
			retval.append('PRIMARY KEY')

		return ' '.join(retval)


	@classmethod
	def update_by_dim(cls, ts, values: dict):
		metrics = []
		valuelist = []

		for fieldname in ts.metrics:
			if fieldname not in values:
				continue
			metrics.append(f"{cls.IQO}{fieldname}{cls.IQC}={cls.PLHD}")
			valuelist.append(values[fieldname])
		setstr = ",".join(metrics)

		whereclause, wherevals = cls.where_by_dims(ts, values)
		valuelist.extend(wherevals)

		sql = f"UPDATE {ts.ftn} SET {setstr} WHERE {whereclause}"
		return sql, valuelist

	@classmethod
	def update_by_pk(cls, ts, values: dict):
		whereclause, wherevals = cls.where_by_pk(ts, values)
		pk = ts.pk.fixedname

		setlist = []
		valuelist = []

		for fieldname in ts.fieldnames:
			if fieldname not in values or fieldname == pk:
				continue
			setlist.append(f"{cls.IQO}{fieldname}{cls.IQC}={cls.PLHD}")
			valuelist.append(values[fieldname])
		if len(setlist) == 0:
			raise ValueError("No values to update")
		setstr = ",".join(setlist)
		valuelist.extend(wherevals)

		sql = f"UPDATE {ts.ftn} SET {setstr} WHERE {whereclause}"
		return sql, valuelist

	@classmethod
	def where_by_dims(cls, ts, values):
		where_bits = []
		vallist = []
		if len(ts.dimensions) == 0:
			raise IntegrityError(f"Cannot attemt dimension operation on a table with no dimensions")

		for field in ts.dimensions:
			if field not in values or values[field] is None:
				raise IntegrityError(f"Dimension {field} missing when attemting dimension operation")
			where_bits.append(f"{cls.IQO}{field}{cls.IQC}={cls.PLHD}")
			vallist.append(values[field])
		return " AND ".join(where_bits), vallist

	@classmethod
	def where_by_pk(cls, ts, values):
		if not ts.has_pk():
			raise IntegrityError("Cannot operate on primary key when none assigned")
		pk = ts.pk.fixedname
		if pk not in values or values[pk] is None:
			raise IntegrityError("Cannot perform pk operation unless pk is set")
		return f"{cls.IQO}{pk}{cls.IQC}={cls.PLHD}", [values[pk]]


