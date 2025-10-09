
class RealTable(SQLTable):
	TABLENAME = 'realtable'
	SCHEMA = 'unittest'
	FIELDLIST = [
		SQLField('intfield', 'INT PRIMARY KEY', 0, 'AUTO_INCREMENT'),
		SQLField('charfield', 'VARCHAR(200)', 1, 'AUTO_INCREMENT'),
	]


class TestSQLTable(TestCase):
	def test_accessor(self):
		testee = RealTable()
