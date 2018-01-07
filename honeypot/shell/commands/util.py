from getopt import gnu_getopt, GetoptError

def easy_getopt(args, opt, longopts=[]):
	optlist, args = gnu_getopt(args, opt, longopts)
	optdict = {}
	
	for item in optlist:
		optdict[item[0]] = item[1]
		
	return optdict, args

