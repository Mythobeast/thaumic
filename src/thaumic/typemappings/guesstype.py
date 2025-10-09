from datetime import datetime

INT = 0
FLOAT = 1
TIMESTAMP = 2
DATETIME = 3
VARCHAR = 4


def guess_ansi_type(list_of_values):
	unviable = False
	for value in list_of_values:
		if isinstance(value, int):
			continue
		if isinstance(value, float) or isinstance(value, datetime):
			unviable = True
			break
		if not isinstance(value, str):
			raise ValueError(f"Found a value of type {type(value)}, cannot guess how that would translate")
		stripped = value.strip()
		for onechar in list(stripped):
			if not onechar.isdigit():
				unviable = True
				break
	if not unviable:
		return "INT"


# noinspection PyUnusedLocal
def guess_numerics(oneval):
	pass
