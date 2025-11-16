from pathlib import Path

from thaumic.base.sqltable import SQLTable
from thaumic.adapters.mssql.sqlfield import MsSQLField
from thaumic.base.fielddata import FieldData

SP_FORMAT_OUTPUT = 1

class FWColumn:
	def __init__(self, name, start, end):
		self.name = name
		self.start = start
		self.end = end

	def extract_from(self, line):
		return line[self.start:self.end].strip()


def gen_column_defs(headerrow, linenumberoffset):
	retval = []
	cursor = linenumberoffset
	while cursor < len(headerrow):
		start = cursor
		while cursor < len(headerrow) and headerrow[cursor].isspace():
			cursor += 1
		if cursor > len(headerrow):
			break
		while cursor < len(headerrow) and not headerrow[cursor].isspace():
			cursor += 1
		end = cursor
		cursor += 1
		columname = headerrow[start:end].strip()
		retval.append(FWColumn(columname, start, end))
	return retval


class MsSQLTable(SQLTable):

	def __init__(self, tablename=None, schema=None):
		super().__init__(self, ts=None, v=None, dialect=None)
		if tablename is not None:
			self.TABLENAME = tablename
		if schema is not None:
			self.SCHEMA = schema
		super().__init__()

	def load_from_database(self, dbmgr):
		columnlist = dbmgr.get_columns(self.TABLENAME)
		self.ts.f = dict()
		for onefield in columnlist:
			fd = FieldData(onefield)
			self.f[fd.column_name] = MsSQLField(fd)
		pk_result = dbmgr.get_primary_key(self.TABLENAME)
		if pk_result is not None:
			self.set_primary_key(pk_result)


	@classmethod
	def build_fieldlist_from_sp_columns(cls, filename):
		# Because "ordinal" is a 1-based field,
		# we need an empty placeholder in the field list for this to work
		fieldlist = [FieldData()]
		infile = open(filename, 'r')
		nextline = infile.readline().rstrip('\n')
		if 'TABLE_QUALIFIER' not in nextline:
			ValueError('File does not start with a column header')

		# We can only calculate linenumberoffset this way
		# because the table qualifier is always System_Warehouse for the initial read
		linenumberoffset = nextline.find('TABLE_QUALIFIER') - 1
		columndata = None

		while nextline is not None and nextline != '':
#			print(f"Interpreting {nextline}")
			if nextline[0] == ' ':
				columndata = gen_column_defs(nextline, linenumberoffset)
			else:
				field_ordinal = int(nextline.split()[0])
				if len(fieldlist) < field_ordinal+1:
					fieldlist.append(FieldData())
				thisfd = fieldlist[field_ordinal]
				for column in columndata:
					thisfd.set_value(column.name, column.extract_from(nextline))
			nextline = infile.readline().rstrip('\n')
		fieldlist.pop(0)
		retval = []
#		print(f"Field list = {fieldlist}")
		for itr in fieldlist:
			retval.append(MsSQLField(itr.column_name, itr.declaration(), 0, fd=itr))
		return retval

	@classmethod
	def build_from_sp_columns(cls, filename):
#		print(f"Generating fieldlist from {filename}")
		fieldlist = cls.build_fieldlist_from_sp_columns(filename)
#		print(f"Fieldlist =  {fieldlist}")
		firstfield = fieldlist[0]
		dbspec = dict()
		tablename = firstfield.fd.table_name
		dbspec['DATABASE'] = firstfield.fd.table_qualifier
		dbspec['SCHEMA'] = firstfield.fd.table_owner
		dbspec['ENGINE'] = 'mssql'
		return MsSQLTable(tablename=tablename, schema=firstfield.fd.table_owner, fieldlist=fieldlist)


	def generate_python(self, dbmgr, filename):
		filepath = Path(filename)
		filepath.parent.mkdir(parents=True, exist_ok=True)

		outfile = open(filename, 'w')
		outfile.write("from thaumic.base.sqltable import SQLTable, SQLField\n\n")

		outfile.write(f"class {self.TABLENAME.capitalize()}(SQLTable):\n")
		outfile.write(f"\tTABLENAME = '{self.TABLENAME}'\n")
		outfile.write(f"\tSCHEMA = '{self.SCHEMA}'\n")
		outfile.write("\tFIELDLIST = [\n")
		for name, fieldobj in self.f.items():
			decl = dbmgr.type_declaration(fieldobj.fd)
			outputdata = [f"\t\tSQLField('{name}', '{decl}'"]
			if fieldobj.fd.is_pk:
				outputdata.append(", 1),")
			else:
				outputdata.append(", 0),")
			if fieldobj.fd.remarks:
				outputdata.append(f" # {fieldobj.fd.remarks}")
			outfile.write(''.join(outputdata))
			outfile.write("\n")
		outfile.write("\t]\n")
		outfile.write("\n")
		outfile.close()

	# noinspection PyMethodMayBeStatic
	def retrieve_constraints(self):
		return """
select table_view,
       object_type, 
       constraint_type,
       constraint_name,
       details
from (
    select 
        schema_name(t.schema_id) + '.' + t.[name] as table_view, 
        case when t.[type] = 'U' then 'Table'
            when t.[type] = 'V' then 'View'
        end as [object_type],
        case when c.[type] = 'PK' then 'Primary key'
            when c.[type] = 'UQ' then 'Unique constraint'
            when i.[type] = 1 then 'Unique clustered index'
            when i.[type] = 2 then 'Unique index'
        end as constraint_type, 
        isnull(c.[name], i.[name]) as constraint_name,
        substring(column_names, 1, len(column_names)-1) as [details]
    from sys.objects t
        left outer join sys.indexes i on t.object_id = i.object_id
        left outer join sys.key_constraints c
            on i.object_id = c.parent_object_id and i.index_id = c.unique_index_id
    cross apply (
        select col.[name] + ', '
            from sys.index_columns ic
                inner join sys.columns col 
                    on ic.object_id = col.object_id and ic.column_id = col.column_id
        where ic.object_id = t.object_id and ic.index_id = i.index_id
        order by col.column_id
            for xml path ('') 
    ) D (column_names)
            where i.is_unique = 1 and t.is_ms_shipped <> 1
        union all 
            select schema_name(fk_tab.schema_id) + '.'+ fk_tab.name as foreign_table,
                'Table',
                'Foreign key',
                fk.name as fk_constraint_name,
                schema_name(pk_tab.schema_id) + '.' + pk_tab.name
            from sys.foreign_keys fk
                inner join sys.tables fk_tab on fk_tab.object_id = fk.parent_object_id
                inner join sys.tables pk_tab on pk_tab.object_id = fk.referenced_object_id
                inner join sys.foreign_key_columns fk_cols on fk_cols.constraint_object_id = fk.object_id
        union all
		    select schema_name(t.schema_id) + '.' + t.[name],
                'Table',
                'Check constraint',
                con.[name] as constraint_name,
                con.[definition]
            from sys.check_constraints con
                left outer join sys.objects t on con.parent_object_id = t.object_id
                left outer join sys.all_columns col 
                    on con.parent_column_id = col.column_id and con.parent_object_id = col.object_id
	    union all
            select schema_name(t.schema_id) + '.' + t.[name],
                'Table',
                'Default constraint',
                con.[name],
                col.[name] + ' = ' + con.[definition]
            from sys.default_constraints con
                left outer join sys.objects t on con.parent_object_id = t.object_id
                left outer join sys.all_columns col 
                    on con.parent_column_id = col.column_id and con.parent_object_id = col.object_id
        ) a
		order by table_view, constraint_type, constraint_name
"""
