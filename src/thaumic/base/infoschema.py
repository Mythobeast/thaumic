


class InfoschemaColumns:
	COLUMN_NAMES = [
		'TABLE_CATALOG',
		# TABLE_CATALOG: The column's catalog database name of the catalog (database) to which the table containing the column belongs.
		'TABLE_SCHEMA',
		# TABLE_SCHEMA: The name of the schema (database) to which the table containing the column belongs.
		'TABLE_NAME',
		# TABLE_NAME: The name of the table containing the column.
		'COLUMN_NAME',
		# COLUMN_NAME: The name of the column.
		'ORDINAL_POSITION',
		# ORDINAL_POSITION: The position of the column within the table. ORDINAL_POSITION is necessary because you might want to say ORDER BY ORDINAL_POSITION. Unlike SHOW COLUMNS, SELECT from the COLUMNS table does not have automatic ordering.
		'COLUMN_DEFAULT',
		# COLUMN_DEFAULT: The default value for the column. This is NULL if the column has an explicit default of NULL, or if the column definition includes no DEFAULT clause.
		'IS_NULLABLE',
		# IS_NULLABLE: The column nullability. The value is YES if NULL values can be stored in the column, NO if not.
		'DATA_TYPE',
		# DATA_TYPE: The column data type.
		#    The DATA_TYPE value is the type name only with no other information. The COLUMN_TYPE value contains the type name and possibly other information such as the precision or length.
		'CHARACTER_MAXIMUM_LENGTH',
		# CHARACTER_MAXIMUM_LENGTH: For string columns, the maximum length in characters.
		'CHARACTER_OCTET_LENGTH',
		# CHARACTER_OCTET_LENGTH: For string columns, the maximum length in bytes.
		'NUMERIC_PRECISION',
		# NUMERIC_PRECISION:  For numeric columns, the numeric precision.
		'NUMERIC_SCALE',
		# NUMERIC_SCALE: For numeric columns, the numeric scale.
		'DATETIME_PRECISION',
		# DATETIME_PRECISION: For temporal columns, the fractional seconds precision.
		'CHARACTER_SET_NAME',
		# CHARACTER_SET_NAME: For character string columns, the character set name.
		'COLLATION_NAME',
		# COLLATION_NAME: For character string columns, the collation name.
		'COLUMN_TYPE',
		# COLUMN_TYPE: The column data type.
		#  The DATA_TYPE value is the type name only with no other information. The COLUMN_TYPE value contains the type name and possibly other information such as the precision or length.
		'COLUMN_KEY',
		# COLUMN_KEY: Whether the column is indexed:
		#  If COLUMN_KEY is empty, the column either is not indexed or is indexed only as a secondary column in a multiple-column, nonunique index.
		#  If COLUMN_KEY is PRI, the column is a PRIMARY KEY or is one of the columns in a multiple-column PRIMARY KEY.
		#  If COLUMN_KEY is UNI, the column is the first column of a UNIQUE index. (A UNIQUE index permits multiple NULL values, but you can tell whether the column permits NULL by checking the Null column.)
		#  If COLUMN_KEY is MUL, the column is the first column of a nonunique index in which multiple occurrences of a given value are permitted within the column.
		#  If more than one of the COLUMN_KEY values applies to a given column of a table, COLUMN_KEY displays the one with the highest priority, in the order PRI, UNI, MUL.
		#  A UNIQUE index may be displayed as PRI if it cannot contain NULL values and there is no PRIMARY KEY in the table. A UNIQUE index may display as MUL if several columns form a composite UNIQUE index; although the combination of the columns is unique, each column can still hold multiple occurrences of a given value.
		'PRIVILEGES',
		# PRIVILEGES: The privileges you have for the column.
		'COLUMN_COMMENT',
		# COLUMN_COMMENT: Any comment included in the column definition.
		'GENERATION_EXPRESSION',
		# GENERATION_EXPRESSION: For generated columns, displays the expression used to compute column values. Empty for nongenerated columns. For information about generated columns, see Section 15.1.20.8, “CREATE TABLE and Generated Columns”.
		'SRS_ID'
		# SRS_ID: This value applies to spatial columns. It contains the column SRID value that indicates the spatial reference system for values stored in the column. See Section 13.4.1, “Spatial Data Types”, and Section 13.4.5, “Spatial Reference System Support”. The value is NULL for nonspatial columns and spatial columns with no SRID attribute.
    # Column "EXTRA" may be appended by some databases
		# EXTRA: Any additional information that is available about a given column. The value is nonempty in these cases:
		#  auto_increment for columns that have the AUTO_INCREMENT attribute.
		#  on update CURRENT_TIMESTAMP for TIMESTAMP or DATETIME columns that have the ON UPDATE CURRENT_TIMESTAMP attribute.
		#  STORED GENERATED or VIRTUAL GENERATED for generated columns.
		#  DEFAULT_GENERATED for columns that have an expression default value.
	]

	def __init__(self, row = None):
		self.v = dict()
		if row:
			for itr in range(len(self.COLUMN_NAMES)):
				self.v[self.COLUMN_NAMES[itr]] = row[itr]

	@classmethod
	def get_column_info(cls, dbmgr, schemaname, tablename):
		columnlist_str = f'{dbmgr.dq},{dbmgr.dq}'.join(cls.COLUMN_NAMES)
		sql = [
			"SELECT", f"{dbmgr.dq}{columnlist_str}{dbmgr.dq}",
			f'FROM {dbmgr.dq}INFORMATION_SCHEMA{dbmgr.dq}.{dbmgr.dq}columns{dbmgr.dq}',
			f"WHERE table_name='{tablename}'",
			f"AND table_schema='{schemaname}';"]
		retval = dbmgr.fetch(' '.join(sql))
		return retval

