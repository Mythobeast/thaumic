

class BcpField:
	def __init__(self, row):
		self.source_ord = 0
		self.target_ord = row[1]
		self.maxlen = row[2]
		self.terminator = '\t'
		self.fieldname = fieldname
		self.coalation = ''

# 1      SQLCHAR      0      7       "\t"     1     sequence     ""
	def write_format(self):
		retval = ['']


class BcpTable:
	def __init__(self, tablename, schema):
		self.tablename = tablename
		self.schema = schema
		self.fields = []

	def import_schema(self, cnxn):
		sql = ("SELECT [column_name], [ordinal_position], [datatype] "
		       "FROM INFORMATION_SCHEMA.COLUMNS WHERE table_schema=? AND table_name=?")
		cursor = cnxn.cursor()
		result = cursor.execute(sql, (self.tablename, self.schema)).fetchall()
		cursor.close()
		for row in result:
			self.fields[row[0].lower()] = BcpField(row)

	def set_input_order(self, fieldlist):
		itr = 0
		for field in fieldlist:
			itr += 1
			fl = field.lower()
			if fl in self.fields:
				self.fields[fl].source_ord = itr
			else:
				self.fields[fl] = BcpField()
