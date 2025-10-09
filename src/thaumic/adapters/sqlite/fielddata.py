
MAX4B = 2147483647

DATATYPES = {
'NUMERIC': ['', '', '', '',  2,   'NUMERIC',    18,     9,     0,   10, 1, None, None,  2, None,     None,     0,    1, 108],
'INTEGER': ['', '', '', '',  4,       'INT',    10,     4,     0,   10, 1, None, None,  4, None,     None,     0,    1,  38],
'TEXT':    ['', '', '', '', -1,      'TEXT', MAX4B, MAX4B,  None, None, 1, None, None, -1, None,    MAX4B,     0,    1,  61],
'REAL':    ['', '', '', '',  6,     'FLOAT',    15,     8,  None,   10, 1, None, None,  6, None,     None,     0,    1, 109],
'BLOB':    ['', '', '', '', -2,    'BINARY',     1,     1,  None, None, 1, None, None, -2, None,        1,     0,    1,  37]
}
table_info_header = ["name",  "type", "notnull",  "dflt_value" , "pk"]
