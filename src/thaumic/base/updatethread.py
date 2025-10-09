from _queue import Empty
from datetime import datetime
from queue import Queue
from threading import Thread, Lock

import pyodbc

from thaumic import get_sqlmanager

class TableUpdaterThread:
	WRITEPROC = None
	TABLENAME = "TablenameFromTableUpdaterThread"
	CHILDCLASSES = dict()
	UPDATE_COUNT = 0
	UPDATE_MUTEX = Lock()

	@classmethod
	def init_writequeue(cls, dbspec):
		cls.WRITEPROC = UpdateWriter(cls, dbspec)
		cls.WRITEPROC.start()

	@classmethod
	def put_update(cls, dbspec, record):
		with cls.UPDATE_MUTEX:
			if cls.WRITEPROC is None:
				cls.init_writequeue(dbspec)
			cls.WRITEPROC.put(record)
			cls.UPDATE_COUNT += 1

	@classmethod
	def shutdown(cls, context):
		context.logger.info(f"Updated {cls.UPDATE_COUNT} rows for {cls.TABLENAME}")
		if cls.WRITEPROC is not None:
			cls.WRITEPROC.shutdown()
		#	context.logger.debug(f"Writeproc {cls.TABLENAME} ending, waiting to join")
			cls.WRITEPROC.join()
		#	context.logger.debug(f"Writeproc {cls.TABLENAME} joined")
		#else:
		#	context.logger.debug(f"No writeproc for {cls.TABLENAME}")
		#print(f"Child classes of {cls.TABLENAME} are {cls.CHILDCLASSES.keys()}")
		allclasses = set()
		for clsname, subcls in cls.CHILDCLASSES.items():
			if subcls in allclasses:
				continue
		#	context.logger.debug(f"calling shutdown for {clsname}")
			subcls.shutdown(context)
			allclasses.add(subcls)


class UpdateWriter(Thread):
	MAX_SHUTDOWN_WAIT = 600 # ten minutes
	def __init__(self, clientclass, dbspec, context=None):
		super().__init__(name=f"UW-{clientclass.TABLENAME}")
		self.clientclass = clientclass
		self.context = context
		self.dbspec = dbspec
		self.updatequeue = Queue()
		self.shutdown_flag = False
		self.writecount = 0

	def debugpnt(self, text):
		if self.context and self.dbspec.debugme:
			self.context.info(text)

	def run(self):
		dbmgr = get_sqlmanager(self.dbspec)
		shutdowntime = None
		while not self.shutdown_flag or self.updatequeue.qsize() > 0:
			if self.shutdown_flag:
				if shutdowntime is None:
					shutdowntime = datetime.now()
				else:
					now = datetime.now()
					if (now - shutdowntime).total_seconds() > self.MAX_SHUTDOWN_WAIT:
						self.debugpnt(f"Maximum shutdown time reached for {self.name}, exiting thread")
						break
			try:
				writerecord = self.updatequeue.get(block=True, timeout=5)
			except Empty:
				if self.shutdown_flag:
					break
				continue
			try:
				writerecord.store(dbmgr)
			except pyodbc.DataError as pode:
				self.updatequeue.task_done()
				self.debugpnt(f"Exception: {pode}\n{self.clientclass.TABLENAME}: {writerecord.v}")
				continue
			# Gotta tell the queue that this task is done.
			self.updatequeue.task_done()
			self.writecount += 1
#			if self.writecount % 1000 == 0:
				# self.debugpnt(f"Wrote {self.writecount} records to {self.clientclass.TABLENAME}")
		self.debugpnt(f"Exiting {self.name}")

	def put(self, record):
		if self.shutdown_flag:
			return
		self.updatequeue.put(record)

	def shutdown(self):
		self.shutdown_flag = True
		self.updatequeue.join()
