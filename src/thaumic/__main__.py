
try:
	from thaumic.adapters.mssql.manager import getpersonal as get_mssql_dbmgr
	MSSQL = True
except ImportError:
	MSSQL = False
try:
	from thaumic.adapters.mariadb.manager import getpersonal as get_mysql_dbmgr
	MARIADB = True
except ImportError:
	MARIADB = False
try:
	from thaumic.adapters.mocksql.manager import getpersonal as get_mocksql_dbmgr
	MOCKSQL = True
except ImportError:
	MOCKSQL = False

try:
	from thaumic.adapters.sqlite.manager import getinstance as get_sqlite_dbmgr
	SQLITE = True
except ImportError:
	SQLITE = False


from thaumic.util.logger import LOGGER

def get_sqlmanager(dbspec, logger=None):
	if dbspec['ENGINE'] == 'mariadb' and MARIADB:
		return get_mysql_dbmgr(dbspec)
	elif dbspec['ENGINE'] == 'mssql' and MSSQL:
		return get_mssql_dbmgr(dbspec)
	elif dbspec['ENGINE'] == 'mocksql' and MOCKSQL:
		return get_mocksql_dbmgr(dbspec)
	elif dbspec['ENGINE'] == 'sqlite' and SQLITE:
		return get_sqlite_dbmgr(dbspec)
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