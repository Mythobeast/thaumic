
# Objective: Extract data management objects for everything in a specified schema and/or database
import sys

from pyhocon import ConfigFactory
from thaumic.mssql.dbschema import DbSchema
from thaumic.mssql.manager import getpersonal


def main():
	''' This funtion requires the name of a configuration file
	'''
	if len(sys.argv) < 2:
		configfile = 'generate.cfg'
	else:
		configfile = sys.argv[1]

	conf = ConfigFactory.parse_file(configfile)
	dbspec = conf.dbspec
	if dbspec['ENGINE'] != 'mssql':
		print("This function currently only works for SQL Server")
		return
#	dbmgr = getpersonal(conf.dbspec)

	schema = DbSchema()
	dbmgr = getpersonal(conf.dbspec)
	schema.load_from_database(dbmgr)
	print(f'Writing {schema.tables} to path')
	schema.save_to_path(dbmgr, 'uudb')


# Found [
# 	['master', 1, datetime.datetime(2003, 4, 8, 9, 13, 36, 390000)],
#  ['tempdb', 2, datetime.datetime(2022, 10, 4, 4, 41, 0, 453000)],
#  ['model', 3, datetime.datetime(2003, 4, 8, 9, 13, 36, 390000)],
#  ['msdb', 4, datetime.datetime(2014, 2, 20, 20, 49, 38, 857000)],
#  ['distribution', 5, datetime.datetime(2018, 3, 13, 3, 55, 20, 303000)],
#  ['Document_Warehouse', 6, datetime.datetime(2018, 3, 13, 3, 55, 22, 703000)],
#  ['Messaging_Warehouse', 7, datetime.datetime(2018, 3, 13, 3, 55, 23, 503000)],
#  ['OBI', 8, datetime.datetime(2018, 3, 13, 3, 55, 26, 177000)],
#  ['Proxy_Warehouse', 9, datetime.datetime(2018, 3, 13, 3, 55, 26, 893000)],
#  ['Report', 10, datetime.datetime(2018, 3, 13, 3, 55, 28, 953000)],
#  ['Streets_Warehouse', 11, datetime.datetime(2018, 3, 13, 3, 55, 29, 700000)],
#  ['System_Warehouse', 12, datetime.datetime(2018, 3, 13, 3, 55, 32, 343000)],
#  ['Technologies', 13, datetime.datetime(2018, 3, 13, 3, 55, 52, 477000)]] tables

# RQkwrp76S58yX29Yqd3eDv, push
# 2RpgXvArQHv0iqEOB04P


if __name__ == '__main__':
	main()
