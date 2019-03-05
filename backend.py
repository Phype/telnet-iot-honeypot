import sys
import json
import traceback

from util.config import config

if len(sys.argv) > 1 and sys.argv[1] == "cleardb":
	print "This will DELETE ALL DATA except users and cached asn data"
	print "from the database currently used at:"
	print ""
	print "    " + config.get("sql")
	print ""
	print "If you really want to DELETE ALL DATA, type 'delete' and press enter."
	print ""
	doit = sys.stdin.readline()
	print ""
	if doit.strip() != "delete":
		print "ABORTED"
		sys.exit(0)

	from backend.db import delete_everything
	delete_everything()
	sys.exit(0)

# Import from backend is faster:
# Benchmark:
# 	CPU:        Intel(R) Core(TM) i5-6500 CPU @ 3.20GHz
# 	Storage:    Samsung SSD PM961
#	File size:  7,3M
#	SQLite:
#		honeypot: 0m26,056s
#		backend:  0m21,445s
#	Mariadb:
#		honeypot: 0m32,684s
#		backend:  0m14,849s

if len(sys.argv) > 2 and sys.argv[1] == "import":
	from backend.clientcontroller import ClientController

	fname = sys.argv[2]
	if len(sys.argv) > 3:
		username = sys.argv[3]
	else:
		username = config.get("backend_user")

	print "Importing " + fname + " as user " + username

	with open(fname, "rb") as fp:
		ctrl = ClientController()
		for line in fp:
			line = line.strip()
			obj  = json.loads(line)

			if obj["ip"] != None and obj["date"] >= 1515899912:
				print "conn   " + obj["ip"] + " date " + str(obj["date"])
				obj["backend_username"] = username
				try:
					ctrl.put_session(obj)
				except:
					print "Cannot Put Session"
					print "----------------------------"
					traceback.print_exc()
					print "----------------------------"
					print repr(obj)
					sys.exit(0)
	sys.exit(0)

if len(sys.argv) > 1:
	print "Unknown action '" + sys.argv[1] + "'"
	print "Available commands:"
	print "    import file.json : imports raw og file"
	print "    cleardb          : deletes all data from db"
	print "To simply start the backend, use no command at all"
	sys.exit(0)

from backend.backend import run
run()

