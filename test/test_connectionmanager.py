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
		self.assertEqual('somedsn', testee.dsn)
		self.assertEqual('somehost', testee.dsn)
		self.assertEqual('someport', testee.dsn)
		self.assertEqual('someuser', testee.dsn)
		self.assertEqual('somepw', testee.dsn)
		self.assertEqual('somedbname', testee.dsn)
		self.assertEqual('someschema', testee.dsn)
		self.assertEqual('somedriver', testee.dsn)
		self.assertEqual(27, testee.dsn)

