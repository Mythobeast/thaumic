# Thaumaturge

Thaumaturge is a database management tool that is targeted at filling in a few
gaps left by existing tools.

1. Dynamic creation and maintenance of schema
2. Cross-platform data transfers

It does this by converting all data types to the ANSI standard
column specified in [INFORMATION_SCHEMA](https://en.wikipedia.org/wiki/Information_schema).

This is a work in progress. Don't read too much into it.

## Selects

There are essentially three cases you have to consider when performing non-join queries on a single table.

### Select all
If you use the **SQLTable.select_all** function of the SQLTable object, it will give you all rows in the table.

### Select some by existing keys
The **self.v** dictionary holds values for the fields. When you call the basic **SQLTable.select** function,
it will use the populated **self.v** values to determine the WHERE clause.

For instance, with the example table declared as:

		SQLField('type', 'VARCHAR(250)', 0),
		SQLField('stop_datetime', 'DATETIME', 0),
		SQLField('start_datetime', 'DATETIME', 1),
		SQLField('member_id', 'INT', 1)

If you set a value only for member_id, it will call this.

    query = SELECT type, stop_datetime, start_datetime, member_id from example_table where member_id=?
    values = (some member id)


### Select some by non-keys
This is possible, but not necessarily preferable. In order to use a non-key in the WHERE statement,
you just have to change it to a key. After initialization, the self.f dictionary contains the field
definitions. By setting **self.f['fieldname'].is_dimension** = True, you can include that value as part
of the WHERE clause.

If you do this, be sure to set this field back to is_dimension = False before you do any other 
queries. It has the potential to propagate to all objects of this type. This behavior is not 
thread-safe.

Important: there is no way to do anything besides equality in this system. It wasn't designed to be
a full service query engine.

### Stranger things
If you have to go beyond selecting where something = otherthing, then you should add a new function.
I recommend that you copy the select_all function and add your own WHERE clause, e.g.:

	def select_withindaterange(self, dbmgr, earliest_start, latest_stop):
		fieldnames = "],[".join(self.all_fields)
        whereclause = "([start_datetime] >= ? AND [start_datetime] < ?) OR" \
                      "([stop_datetime] >= ? AND [start_datetime] < ?)"
        values = [earliest_start, latest_stop, earliest_start, latest_stop]
		sql = f"SELECT [{fieldnames}] FROM {self.fulltablename} WHERE {whereclause};"
		return dbmgr.fetch(sql, values)

By using the **self.all_fields** list to specify your field names, you can pass the returned rows to
the **SQLTable.set_all_values** function to set the **self.v** field values.

### Joins
I have found that joins don't translate well to most frameworks. The syntax invariably winds up
more complicated than just writing your own SQL. This library does not perform joins.

### Giving people permission to use the Paramedics database on EDW

- Add a journal entry to add user to security.users.DW_EDW_PARAMEDICS_OWNER_DEV
- punt to DH_Server team
