from unittest.mock import Mock

from thaumic.base.manager import CnxnManager


DB_INST = None

def getinstance(dbspec, logger_in=None):
	return MockSqlManager(dbspec, logger_in)


def getpersonal(dbspec, logger_in=None):
	return MockSqlManager(dbspec, logger_in)


# noinspection PyAbstractClass
class MockSqlManager(CnxnManager):
	def __init__(self, dbspec, logger=None):
		super().__init__(dbspec, logger)
		self.engine = 'mocksql'
		self.cnxn = Mock()
		self.executed = None
		self.params = None
		self.plhd = '%s'

	def execute(self, query, vargs=None):
		self.executed = query
		self.params = vargs

	def executemany(self, query, vargs):
		self.executed = query
		self.params = vargs

	def schema_exists(self, schema):
		return True

	def create_schema(self, schemaname):
		return True

	def table_exists(self, ts):
		raise NotImplemented

	def fetch(self, query, vargs=None, raw=False, retries=0):
		raise NotImplemented

	def get_jdbc_connstr(self):
		raise NotImplemented

	def drop_table(self, ts):
		raise NotImplemented

	def adjust_quoting(self, sql):
		return sql


