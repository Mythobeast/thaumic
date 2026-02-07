
try:
	from thaumic.adapters.mssql_mgr.manager import getpersonal as get_mssql_dbmgr
	MSSQL = True
except ImportError:
	get_mssql_dbmgr = None
	MSSQL = False
try:
	from thaumic.adapters.mariadb_mgr.manager import getpersonal as get_mysql_dbmgr
	MARIADB = True
except ImportError:
	get_mysql_dbmgr = None
	MARIADB = False
try:
	from thaumic.adapters.mocksql_mgr.manager import getpersonal as get_mocksql_dbmgr
	MOCKSQL = True
except ImportError:
	get_mocksql_dbmgr = None
	MOCKSQL = False

try:
	from thaumic.adapters.sqlite_mgr.manager import getinstance as get_sqlite_dbmgr
	SQLITE = True
except ImportError:
	get_sqlite_dbmgr = None
	SQLITE = False


from thaumic.util.logger import LOGGER

def get_sqlmanager(dbspec, logger=None):
	if dbspec['ENGINE'] == 'mariadb_mgr' and MARIADB:
		return get_mysql_dbmgr(dbspec, logger)
	elif dbspec['ENGINE'] == 'mssql_mgr' and MSSQL:
		return get_mssql_dbmgr(dbspec, logger)
	elif dbspec['ENGINE'] == 'mocksql_mgr' and MOCKSQL:
		return get_mocksql_dbmgr(dbspec, logger)
	elif dbspec['ENGINE'] == 'sqlite_mgr' and SQLITE:
		return get_sqlite_dbmgr(dbspec, logger)
	else:
		if LOGGER:
			LOGGER.error(f"Engine {dbspec['ENGINE']} is not supported")
		else:
			raise ValueError(f"Unsupported Database Engine: '{dbspec['ENGINE']}'")


def resolve_dbmgr(dbspec, dblist):
	if isinstance(dbspec, str):
		if dbspec in dblist:
			dbspec = dblist[dbspec]
		else:
			raise ValueError("dbspec must be one of %s" % ', '.join(dblist.keys()))
	return get_sqlmanager(dbspec)