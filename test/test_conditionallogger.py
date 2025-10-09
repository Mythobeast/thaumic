import unittest
from unittest import TestCase
from unittest.mock import MagicMock, patch
from logging import Logger
from thaumic.util.logger import ConditionalLogger, LoggingScope


class TestLoggingScope(TestCase):
	def setUp(self):
		self.logspec = {
			'name': "test_logger",
			'init_active': True,
			'table_whitelist': [],
			'table_blacklist': [],
			'method_whitelist': [],
			'method_blacklist': [],
		}
		self.logger = ConditionalLogger(self.logspec)



class TestConditionalLogger(TestCase):
	def setUp(self):
		self.logspec = {
			'name': "test_logger",
			'init_active': True,
			'table_whitelist': [],
			'table_blacklist': [],
			'method_whitelist': [],
			'method_blacklist': [],
		}
		self.logger = ConditionalLogger(self.logspec)

	def test_temp_debug(self):
		self.logger.log_flag_stack = [True, False]
		self.logger.temp_debug(True)
		self.assertEqual([True, False, True], self.logger.log_flag_stack)
		self.assertEqual(True, self.logger.active)
		self.logger.reset_debug()
		self.assertEqual([True, False], self.logger.log_flag_stack)
		self.assertEqual(True, self.logger.active)
		self.logger.reset_debug()
		self.assertEqual([True], self.logger.log_flag_stack)
		self.assertEqual(False, self.logger.active)
		self.logger.reset_debug()
		self.assertEqual([True], self.logger.log_flag_stack)
		self.assertEqual(True, self.logger.active)
		self.logger.temp_debug(False)
		self.assertEqual([True, True], self.logger.log_flag_stack)
		self.assertEqual(False, self.logger.active)

	def test_initialization(self):
		self.assertEqual(self.logger.logger.name, "test_logger")
		self.assertEqual(self.logger.logspec, self.logspec)

		self.assertEqual([True], self.logger.log_flag_stack)
		self.assertEqual(self.logger.table_whitelist, [])
		self.assertEqual(self.logger.table_blacklist, [])
		self.assertEqual(self.logger.method_whitelist, [])
		self.assertEqual(self.logger.method_blacklist, [])
		self.assertTrue(self.logger.active)

	@patch.object(Logger, 'info')
	def test_logs_when_active(self, mock_info):
		self.logger.active = True
		self.logger.info("Test message")
		mock_info.assert_called_once_with("Test message")

	@patch.object(Logger, 'info')
	def test_does_not_log_when_inactive(self, mock_info):
		self.logger.active = False
		self.logger.table_whitelist = ['notable']
		self.logger.method_whitelist = ['test_does_not_log_when_inactive']
		self.logger.info("Test message", 'notable')
		mock_info.assert_not_called()

	def test_filter_fails_tableblacklist(self):
		self.logger.table_blacklist = ['notable']
		self.assertFalse(self.logger.filter('notable'))

	def test_filter_ignores_othertables(self):
		self.logger.table_blacklist = ['wrongtable']
		self.assertTrue(self.logger.filter('notable'))

	def test_filter_method_fails_blacklist(self):
		self.logger.method_blacklist = ['test_filter_method_fails_blacklist']
		self.assertFalse(self.logger.filter('notable'))

	def test_filter_method_ignores_othermoethods(self):
		self.logger.method_blacklist = ['test_filter_method_fails_blacklist']
		self.assertTrue(self.logger.filter('notable'))

	def test_filter_table_whitelist_supercedes_blacklist(self):
		self.logger.table_whitelist = ['notable']
		self.logger.table_blacklist = ['notable']
		self.assertTrue(self.logger.filter('notable'))

	def test_filter_method_whitelist_supercedes_blacklist(self):
		self.logger.method_whitelist = ['test_filter_method_whitelist_supercedes_blacklist']
		self.logger.method_blacklist = ['test_filter_method_whitelist_supercedes_blacklist']
		self.assertTrue(self.logger.filter('notable'))

	def test_filter_method_whitelist_supercedes_table_blacklist(self):
		self.logger.method_whitelist = ['test_filter_method_whitelist_supercedes_table_blacklist']
		self.logger.table_blacklist = ['notable']
		self.assertTrue(self.logger.filter('notable'))

	def test_scope(self):
		self.assertTrue(self.logger.active)
		with LoggingScope(self.logger, False):
			self.assertFalse(self.logger.active)
		self.assertTrue(self.logger.active)


if __name__ == '__main__':
	unittest.main()
