


class SQLDialect:
	PLHD = '?'
	IQO = '"'  # Identifier quote open
	IQC = '"'  # Identifier quote close

	@classmethod
	def fulltablename(cls, schema, tablename):
		return f'{cls.IQO}{schema}{cls.IQC}.{cls.IQO}{tablename}{cls.IQC}'

	@classmethod
	def create_table(cls, ts):
		if ts.fieldlist is None:
			raise ValueError("Cannot create table with no fields")
		fields = []
		for field in ts.f:
			fields.append(f"{cls.IQO}{field.fixedname}{cls.IQC} {field.type_declaration()}")

		holder = [
			"CREATE TABLE",
			ts.ftn,
			"(",
			",".join(fields)
		]
		if len(ts.dimensions) > 0:
			holder.append(f", CONSTRAINT thaumkey_{ts.schemaname}_{ts.tablename} UNIQUE (")
			holder.append(",".join(ts.dimensions))
			holder.append(')')
		holder.append(')')
		return " ".join(holder)

	@classmethod
	def truncate(cls, ftn):
		return f"TRUNCATE TABLE {ftn}"

	@classmethod
	def drop(cls, ftn):
		return f"DROP TABLE {ftn}"

	@classmethod
	def add_column(cls, ftn, fd, type_decl):
		return f"ALTER TABLE {ftn} ADD {fd.fixedname} {type_decl}"

	@classmethod
	def alter_column(cls, ftn, fieldname, type_decl):
		return f"ALTER TABLE {ftn} ALTER COLUMN {fieldname} {type_decl}"

	@classmethod
	def drop_constraint(cls, constraint_name):
		raise NotImplementedError

	@classmethod
	def delete(cls, ts, sqlwhere=None, params=None):
		'''
		Deletes based on arbitrary where clause
		'''
		return f"DELETE FROM {ts.ftn} WHERE {whereclause}", params

	@classmethod
	def select(cls, ts, sqlwhere=None, sqlorderby=None):
		query = [f"SELECT {ts.fieldnames_str} FROM {ts.ftn}"]
		if sqlwhere is not None:
			query.append(f"WHERE {sqlwhere}")
		if sqlorderby is not None:
			query.append(f"ORDER BY {sqlorderby}")
		return ' '.join(query)

	@classmethod
	def insert(cls, ts, values : dict):
		sql = f"INSERT INTO {ts.ftn} "
		if ts.has_pk():
			pk = ts.pk.fixedname
			if pk in values and values[pk] is not None:
				raise ValueError(f"Table {ts.ftn}, cannot insert a primary key. Key {pk} was set as {values[pk]}.")
		else:
			pk = ''
		for key in ts.dimensions:
			if key not in values or values[key] is None:
				raise ValueError(f"Attempt to insert to {ts.ftn} without setting dimension {key}.")
		fieldnames = []
		valuelist = []
		for key, value in values.items():
			if key == pk:
				continue
			fieldnames.append(f"{cls.IQO}{key}{cls.IQC}")
			valuelist.append(value)
		fn_str = ",".join(fieldnames)
		plhd_str = [cls.PLHD] * len(fieldnames)
		sql += f" ({fn_str}) VALUES ({plhd_str})"
		return sql, valuelist


	@classmethod
	def where_by_pk(cls, ts, values):
		if not ts.has_pk():
			raise ValueError("Cannot operate on primary key when none assigned")
		pk = ts.pk.fixedname
		if pk not in values or values[pk] is None:
			raise ValueError("Cannot perform pk operation unless pk is set")
		return f"{cls.IQO}{pk}{cls.IQC}={cls.PLHD}", [values[pk]]

	@classmethod
	def select_by_pk(cls, ts, values):
		if len(ts.dimensions) == 0:
			raise ValueError("select_by_dimensions: No dimensions to select")

		whereclause, wherevals = cls.where_by_pk(ts, values)
		sql = f"SELECT {ts.fieldlist_str} FROM {ts.ftn} WHERE {whereclause}"
		return sql, wherevals

	@classmethod
	def delete_by_pk(cls, ts, values):
		whereclause, wherevals = cls.where_by_pk(ts, values)
		sql = f"DELETE FROM {ts.ftn} WHERE {whereclause}" # nosec
		return sql, wherevals

	@classmethod
	def update_by_pk(cls, ts, values: dict):
		whereclause, wherevals = cls.where_by_pk(ts, values)
		pk = ts.pk.fixedname

		setlist = []
		valuelist = []

		for fieldname in ts.fieldnames:
			if fieldname not in values:
				continue
			setlist.append(f"{cls.IQO}{fieldname}{cls.IQC}={cls.PLHD}")
			valuelist.append(values[fieldname])
		setstr = ",".join(setlist)
		valuelist.extend(wherevals)

		sql = f"UPDATE {ts.ftn} SET {setstr} WHERE {whereclause}"
		return sql, valuelist


	@classmethod
	def where_by_dims(cls, ts, values):
		where_bits = []
		vallist = []
		for field in ts.dimensions:
			if field not in values or values[field] is None:
				raise ValueError(f"Dimension {field} missing when selecting by dimensions")
			where_bits.append(f"{field}=?")
			vallist.append(values[field])
		return " AND ".join(where_bits), vallist

	@classmethod
	def select_by_dim(cls, ts, values):
		if len(ts.dimensions) == 0:
			raise ValueError("select_by_dimensions: No dimensions to select")

		whereclause, wherevals = cls.where_by_dims(ts, values)
		sql = f"SELECT {ts.fieldlist_str} FROM {ts.ftn} WHERE {whereclause}"
		return sql, wherevals

	@classmethod
	def delete_by_dim(cls, ts, values):
		whereclause, wherevals = cls.where_by_dims(ts, values)
		sql = f"DELETE FROM {ts.ftn} WHERE {whereclause}" # nosec
		return sql, wherevals

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

	def thaumkey_check(cls):
		raise NotImplementedError
	# Not implement
#		''' information_schema based check for unique key
#		with all dimensions'''
#       return ("select stat.table_schema as database_name, "
#          "stat.table_name, "
#          "stat.index_name, "
#          "group_concat(stat.column_name "
#          "order by stat.seq_in_index separator ', ') as columns, "
#          "tco.constraint_type "
#          "from information_schema.statistics stat "
#          "join information_schema.table_constraints tco "
#          "on stat.table_schema = tco.table_schema "
#          "and stat.table_name = tco.table_name "
#          "and stat.index_name = tco.constraint_name "
#          "where stat.non_unique = 0 "
#          "and stat.table_schema = %s "
#          "and stat.table_name = %s "
#          "and stat.index_name like 'thaumkey_%' "
#          "group by stat.table_schema, stat.table_name, "
#          "stat.index_name, tco.constraint_type "
#          "order by stat.table_schema, stat.table_name; ")

