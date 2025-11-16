


VARLENCHAR_TYPES = ['VARBINARY', 'BINARY', 'CHAR', 'VARCHAR', 'NCHAR', 'NVARCHAR']

PARAMLESS_TYPES = ['TEXT', 'NTEXT', 'LONGVARCHAR', 'LONGVARBINARY',
			'DATETIME', 'DATE', 'TIME', 'TIMESTAMP',
			'BIT', 'TINYINT', 'SMALLINT', 'INTEGER', 'INT', 'BIGINT',
			'MONEY', 'SMALLMONEY', 'GUID']
CHAR_TYPES      = ['LONGVARBINARY', 'VARBINARY', 'BINARY', 'LONGVARCHAR',
                   'CHAR', 'VARCHAR', 'NCHAR', 'NVARCHAR', 'TEXT']
UNICODE_TYPES    = ['NCHAR', 'NVARCHAR']
FLOAT_TYPES   = ['FLOAT', 'DOUBLE', 'REAL']
DECIMAL_TYPES = ['NUMERIC', 'DECIMAL', 'DEC', 'SMALLMONEY', 'MONEY']
INTEGER_TYPES = ['BIT', 'TINYINT', 'SMALLINT', 'INTEGER', 'INT', 'BIGINT']
TIME_TYPES    = ['DATE', 'TIME', 'DATETIME', 'TIMESTAMP']

# Just using this to shorten the lines below
MAX4B = 2147483647

ODBC_DATATYPES = {
	'GUID': -11,
	'BIT': -7,
	'TINYINT': -6,
	'BIGINT': -5,
	'LONGVARBINARY': -4,
	'VARBINARY': -3,
	'BINARY': -2,
	'LONGVARCHAR': -1,
	'Unknown type': 0,
	'CHAR': 1,

	'NUMERIC': 2,
	'DECIMAL': 3,
	'INTEGER': 4,
	'INT': 4,
	'SMALLINT': 5,

	'FLOAT': 6,
	'REAL': 7,
	'DOUBLE': 8,

	'DATE': 9,
	'TIME': 10,
	'TIMESTAMP': 11,
	'VARCHAR': 12
}


DECL_BASES = {
	#                             DT        name    precis   len  scale radix nl  remk  cdef  dt dtsub octet_len ordpos isnul SSdt
	'DATETIME'  : ['', '', '', '', 11,  'DATETIME',    23,    16,     3, None, 1, None, None, 11, None,     None,     0,    1, 111],
	#             mydatetime,      11,   datetime ,    23,    16,     3,     , 1,     ,     ,  9,    3,         ,     x,  YES, 111
	'DATETIME2' : ['', '', '', '', -9, 'DATETIME2',    27,    54,  None, None, 1, None, None, -9, None,        0,     0,    1,  39],
	#            mydatetime2,      -9,  datetime2 ,    27,    54,      ,     , 1,     ,     , -9,     ,         ,     x,  YES,   0
	'DATETIMEOFFSET': ['','','','',-9,'DATETIMEOFFSET',34,    68,  None, None, 1, None, None, -9, None,        0,     0,    1,  39],
	#            mydatetimeoffset, -9,datetimeoffset,  34,    68,      ,     , 1,     ,     , -9,     ,         ,     x,  YES,   0
	'DATE'      : ['', '', '', '', -9,      'DATE',    10,    20,  None, None, 1, None, None, -9, None,     None,     0,    1,   0],
	#            mydate,           -9,       date ,    10,    20,      ,     , 1,     ,     , -9,     ,         ,     x,  YES,   0
	'TIME'      : ['', '', '', '', -9,      'TIME',    16,    32,  None, None, 1, None, None, -9, None,     None,     0,    1,   0],
	#             mytime,          -9,       time ,    16,    32,      ,     , 1,     ,     , -9,     ,         ,     x,  YES,   0
	'TIMESTAMP' : ['', '', '', '', -2, 'TIMESTAMP',     8,     8,  None, None, 1, None, None, -2, None,        8,     0,    1, 45],
	#             mytimestamp,     -2,  timestamp ,     8,     8,      ,     , 0,     ,     , -2,     ,        8,     x,   NO,  45

	'BIT'       : ['', '', '', '', -7,       'BIT',     1,     1,  None, None, 1, None, None, -7, None,     None,     0,    1,  50],
	#             mybit,           -7,        bit ,     1,     1,      ,     , 1,     ,     , -7,     ,         ,     x,  YES,  50
	'TINYINT'   : ['', '', '', '', -6,   'TINYINT',     3,     1,     0, None, 1, None, None, -6, None,     None,     0,    1,  38],
	#             mytinyint,       -6,    tinyint ,     3,     1,     0,   10, 1,     ,     , -6,     ,         ,     2,  YES,  38
	'SMALLINT'  : ['', '', '', '',  5,  'SMALLINT',    10,     2,     0,   10, 1, None, None,  5, None,     None,     0,    1,  38],
	'INT'       : ['', '', '', '',  4,       'INT',    10,     4,     0,   10, 1, None, None,  4, None,     None,     0,    1,  38],
	'INTEGER'   : ['', '', '', '',  4,       'INT',    10,     4,     0,   10, 1, None, None,  4, None,     None,     0,    1,  38],
	#             myint,            4,        int ,    10,     4,     0,   10, 1,     ,     ,  4,     ,         ,     x,  YES,  38
	'BIGINT'    : ['', '', '', '', -5,    'BIGINT',    19,     8,     0,   10, 1, None, None, -5, None,     None,     0,    1,  38],
	#             mybigint,        -5,     bigint ,    19,     8,     0,   10, 1,     ,     , -5,     ,         ,     x,  YES, 108
	'BINARY'    : ['', '', '', '', -2,    'BINARY',     1,     1,  None, None, 1, None, None, -2, None,        1,     0,    1,  37],
	'GUID'      : ['', '', '', '',-11,      'GUID',    16,    16,  None, None, 1, None, None, 12, None,       16,     0,    1,  37],
	#             mybin_10,        -2,     binary ,    10,    10,      ,     , 1,     ,     , -2,     ,       10,     x,  YES,  37
	'CHAR'      : ['', '', '', '',  1,      'CHAR',     1,     1,  None, None, 1, None, None,  1, None,        1,     0,    1,  39],
	#             mychar_50,        1,       char ,    50,    50,      ,     , 1,     ,     ,  1,     ,       50,     x,  YES,  39
	'VARCHAR'   : ['', '', '', '', 12,   'VARCHAR',     1,     1,  None, None, 1, None, None, 12, None,        2,     0,    1,  39],
	#             myvarchar20,     12,    varchar ,    20,    20,      ,     , 1,     ,     , 12,     ,       20,     x,  YES,  39
	#             myvarchar200,    12,    varchar ,   200,   200,      ,     , 1,     ,     , 12,     ,      200,     x,  YES,  39
	'NCHAR'     : ['', '', '', '', -8,     'NCHAR',     1,     1,  None, None, 1, None, None, -8, None,        2,     0,    1,  39],
	#             mynchar_60,      -8,      nchar ,    60,   120,      ,     , 1,     ,     , -8,     ,      120,     x,  YES,  39
	'NVARCHAR'  : ['', '', '', '', -9,  'NVARCHAR',     1,     1,  None, None, 1, None, None, -9, None,        2,     0,    1,  39],
	#            mynvarchar_70,    -9,   nvarchar ,    70,   140,      ,     , 1,     ,     , -9,     ,      140,     x,  YES,  39
	'VARBINARY' : ['', '', '', '', -3, 'VARBINARY',     1,     1,  None, None, 1, None, None, -3, None,        1,     0,    1,  37],
	#             myvarbin_30,     -3,  varbinary ,    30,    30,      ,     , 1,     ,     , -3,     ,       30,     x,  YES,  37
	'TEXT'      : ['', '', '', '', -1,      'TEXT', MAX4B, MAX4B,  None, None, 1, None, None, -1, None,    MAX4B,     0,    1,  61],

	'NUMERIC'   : ['', '', '', '',  2,   'NUMERIC',    18,     9,     0,   10, 1, None, None,  2, None,     None,     0,    1, 108],
	#             mynum,            2,    numeric ,    18,    20,     0,   10, 1,     ,     ,  2,     ,         ,     x,  YES, 108
	'DECIMAL'   : ['', '', '', '',  3,   'DECIMAL',    18,     9,     0,   10, 1, None, None,  2, None,     None,     0,    1, 106],
	'DEC'       : ['', '', '', '',  3,   'DECIMAL',    18,     9,     0,   10, 1, None, None,  2, None,     None,     0,    1, 106],
	#             mydeci_raw,       3,    decimal ,    18,    20,     0,   10, 1,     ,     ,  3,     ,         ,     x,  YES, 106
	#             mydeci_10,        3,    decimal ,    10,    12,     0,   10, 1,     ,     ,  3,     ,         ,     x,  YES, 106
	#             mydeci_19_2,      3,    decimal ,    19,    21,     2,   10, 1,     ,     ,  3,     ,         ,     x,  YES, 106
	'MONEY'     : ['', '', '', '',  3,     'MONEY',    19,    21,     4,   10, 1, None, None,  3, None,     None,     0,    1, 110],
	#             mymoney,          3,      money ,    19,    21,     4,   10, 1,     ,     ,  3,     ,         ,     x,  YES, 110
	'SMALLMONEY': ['', '', '', '',  3,'SMALLMONEY',    10,    12,     4,   10, 1, None, None,  3, None,     None,     0,    1, 110],
	#             mysmallmoney,     3, smallmoney ,    10,    12,     4,   10, 1,     ,     ,  3,     ,         ,     x,  YES, 110
	'FLOAT'     : ['', '', '', '',  6,     'FLOAT',    15,     8,  None,   10, 1, None, None,  6, None,     None,     0,    1, 109],
	#             myfloat,          6,      float ,    15,     8,      ,   10, 1,     ,     ,  6,     ,         ,     x,  YES, 109
	#             myfloat30,        6,      float ,    15,     8,      ,   10, 1,     ,     ,  6,     ,         ,     x,  YES, 109
	'DOUBLE'    : ['', '', '', '',  6,     'FLOAT',    15,     8,  None,   10, 1, None, None,  6, None,     None,     0,    1, 109],
	'REAL'      : ['', '', '', '',  7,      'REAL',     7,     4,  None,   10, 1, None, None,  7, None,     None,     0,    1, 109],
	#             myfloat20,        7,       real ,     7,     4,      ,   10, 1,     ,     ,  7,     ,         ,     x,  YES, 109
}

class Limits:
	lbit = 1
	ltinyint = 1
	lsmallint = 1
	lint = 4
	lbigint = 8

	lfloat = 5
	ldouble = 9
	ldubdub = 13
	lbigdub = 17

	@staticmethod
	def char2int(characters):
		if characters < 3:
			return Limits.ltinyint
		if characters < 5:
			return Limits.lsmallint
		if characters < 9:
			return Limits.lint
		if characters < 19:
			return Limits.lbigint

	@staticmethod
	def char2float(characters):
		if characters < 10:
			return Limits.lfloat
		if characters < 20:
			return Limits.ldouble
		if characters < 29:
			return Limits.ldubdub
		if characters < 39:
			return Limits.lbigdub
