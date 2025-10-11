import unittest

from thaumic.base.manager import CnxnManager


class TestConnectionManager(unittest.TestCase):
	def setUp(self):
		pass
	def tearDown(self):
		pass
	
	def test_init(self):
		dbspec = {
			'DSN': 'somedns',
			'HOST': 'somehost',
			'PORT': 'someport',
			'USER': 'someuser',
			'PW': 'somepw',
			'DATABASE':'somedbname',
			'SCHEMA': 'someschema',
			'DRIVER': 'somedriver',
			'RETRIES': 27,
			'AUTOCOMMIT': False,
			'ENCODING': None,
			'CTYPE': None,
			'LOGSPEC': None
		}
		testee = CnxnManager(dbspec)
		self.assertIsNotNone(testee)
		self.assertEqual('somedns', testee.dsn)
		self.assertEqual('somehost', testee.host)
		self.assertEqual('someport', testee.port)
		self.assertEqual('someuser', testee.user)
		self.assertEqual('somepw', testee.pw)
		self.assertEqual('somedbname', testee.database)
		self.assertEqual('someschema', testee.schema)
		self.assertEqual('somedriver', testee.driver)
		self.assertEqual(27, testee.retries)

