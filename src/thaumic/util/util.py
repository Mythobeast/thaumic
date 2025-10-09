from datetime import datetime


TS_FORMAT = "%Y-%m-%d %H:%M:%S"

def epoch_to_ts(field):
	retval = datetime.fromtimestamp(float(field))
	return retval.strftime(TS_FORMAT)
