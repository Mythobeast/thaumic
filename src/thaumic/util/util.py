from datetime import datetime


TS_FORMAT = "%Y-%m-%d %H:%M:%S"

def epoch_to_ts(field):
	retval = datetime.fromtimestamp(float(field))
	return retval.strftime(TS_FORMAT)


def chop(name, maxlen):
	if len(name) <= maxlen:
		return name
	return name[:maxlen]


def make_obname(namelist, maxlen):
	retval = '_'.join(namelist)
	if len(retval) <= maxlen:
		return retval
	maxsub = 0
	for name in namelist:
		if len(name) > maxsub:
			maxsub = len(name)
	while len(retval) > maxlen:
		maxsub -= 1
		newlist = [chop(name, maxsub) for name in namelist]
		retval = '_'.join(newlist)
	return retval
