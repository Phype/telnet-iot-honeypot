import os
import sys
import signal
import json

from honeypot.telnet  import Telnetd
from honeypot.client  import Client
from honeypot.session import Session
from util.dbg import dbg

srv = None

def import_file(fname):
	with open(fname, "rb") as fp:
		client = Client()
		for line in fp:
			line = line.strip()
			obj  = json.loads(line)
			if obj["type"] == "connection":
				if obj["ip"] != None:
					print "conn   " + obj["ip"]
					client.put_session(obj)
			if obj["type"] == "sample":
				print "sample " + obj["sha256"]
				client.put_sample_info(obj)
				
def rerun_file(fname):
	with open(fname, "rb") as fp:
		for line in fp:
			line = line.strip()
			obj  = json.loads(line)
			if obj["type"] == "connection":
				if obj["ip"] == None: continue
				session = Session(sys.stdout.write, obj["ip"])
				session.login(obj["user"], obj["pass"])
				for event in obj["stream"]:
					if not(event["in"]): continue
					sys.stdout.write(event["data"])		
					session.shell(event["data"].strip())
				session.end()


def signal_handler(signal, frame):
	dbg('Ctrl+C')
	srv.stop()

if not os.path.exists("samples"):
	os.makedirs("samples")

if __name__ == "__main__":
	action = None

	if len(sys.argv) > 1:
		action = sys.argv[1]

	if action == None:
		srv = Telnetd(2223)
		signal.signal(signal.SIGINT, signal_handler)
		srv.run()
	elif action == "import":
		fname = sys.argv[2]
		import_file(fname)
	elif action == "rerun":
		fname = sys.argv[2]
		rerun_file(fname)
	else:
		print "Command " + action + " unknown."

