import datetime
import traceback
import sys
import os.path

DEBUG = True

def dbg(msg):
	if DEBUG:
		now  = datetime.datetime.now()
		now  = now.strftime('%Y-%m-%d %H:%M:%S')
		line = traceback.extract_stack()[-2]
		line = os.path.basename(line[0]) + ":" + str(line[1])
		print(now + "   " + line.ljust(16, " ") + "  " + msg)
		sys.stdout.flush()
