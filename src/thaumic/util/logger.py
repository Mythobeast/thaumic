''' An extra logging layer to evaluate table information, which isn't available in
the default LogRecord object.
For normal run-time logging, use the built-in Python Logger library.
'''
from logging import Logger
import traceback

LOGGER = None

class ConditionalLogger:
	def __init__(self, logspec):
		self.logspec = logspec
		self.offswitch = logspec.get('offswitch', False)
		self.active = logspec.get('init_active', True)
		self.log_flag_stack = [True]
		self.table_whitelist = logspec.get('table_whitelist', [])
		self.table_blacklist = logspec.get('table_blacklist', [])
		self.method_whitelist = logspec.get('method_whitelist', [])
		self.method_blacklist = logspec.get('method_blacklist', [])
		if len(logspec) == 0:
			self.logger = Logger("Thaumic Debugger")
			return

	def temp_debug(self, value):
		self.log_flag_stack.append(self.active)
		self.active = value

	def reset_debug(self):
		if len(self.log_flag_stack) > 1:
			self.active = self.log_flag_stack.pop()
		else:
			self.active = self.log_flag_stack[0]
			self.logger.error(f"")

	def filter(self, tablename):

		# Grab the first frame in the call stack that isn't a function in this file.
		# This is the calling function
		callstack = traceback.extract_stack()
		pathname = __name__.replace('.', '/')
		caller = None
		cursor = len(callstack) - 2
		while cursor >= 0:
			if pathname in callstack[cursor].filename:
				cursor -= 1
				continue
			caller = callstack[cursor]
			break
		caller_name = caller.name
		# The logic for ordering the whitelists and blacklists is designed to allow
		# the programmer to get logging only for the tables that they're currently
		# working with, without too much clutter.

		# If the active flag is false, no logging should be done
		# This is the universal off switch for entering sections that don't
		# need debugging
		if not self.active:
			return False

		# Put a function in the method whitelist if you're specifically trying to
		# debug that method.
		for item in self.method_whitelist:
			if caller_name in item:
				return True

		# Eliminate the methods in the blacklist. This eliminates
		# deep functions that are pretty much called by everyone.
		for item in self.method_blacklist:
			if caller_name in item:
				return False

		# Next, we allow all logging tables in the table whitelist
		if tablename in self.table_whitelist:
			return True

		# Tables that we're definitely tired of hearing about
		if tablename in self.table_blacklist:
			return False

		return True

	def critical(self, message, table=None):
		if not self.filter(table):
			return
		if self.logger is None:
			print(f"critical: No logger specified, {message}")
			return
		self.logger.critical(message)

	def error(self, message, table=None):
		if not self.filter(table):
			return
		if self.logger is None:
			print(f"error: No logger specified, {message}")
			return
		self.logger.error(message)

	def debug(self, message, table=None):
		if not self.filter(table):
			return
		if self.logger is None:
			print(f"debug: No logger specified, {message}")
			return
		self.logger.debug(message)

	def info(self, message, table=None):
		if not self.filter(table):
			return
		if self.logger is None:
			print(f"info: No logger specified, {message}")
			return
		self.logger.info(message)

	def warning(self, message, table=None):
		if not self.filter(table):
			return
		if self.logger is None:
			print(f"warning: No logger specified, {message}")
			return
		self.logger.warning(message)

	def trace(self, message, table=None):
		self.debug(message, table)

	def warn(self, message, table=None):
		self.warning(message, table)


class LoggingScope:
	DETAILTABLE = dict()

	def __init__(self, conditionallogger, state):
		self.conditionallogger = conditionallogger
		self.state = state

	def __enter__(self):
		self.conditionallogger.temp_debug(self.state)
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.conditionallogger.reset_debug()
		return False


def main():
	logspec = dict()
	logspec['name'] = "mydebugger"
	logspec['init_active'] = True
	logspec['activation_flags'] = []
	cb = ConditionalLogger(logspec)
	cb.info("this is a message")

if __name__ == '__main__':
	main()