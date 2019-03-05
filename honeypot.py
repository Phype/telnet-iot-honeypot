import os
import sys
import signal
import json
import socket

from honeypot.telnet      import Telnetd
from honeypot.client      import Client
from honeypot.session     import Session
from honeypot.shell.shell import test_shell

from util.dbg import dbg
from util.config import config

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
	configFile = None

	i = 0
	while i+1 < len(sys.argv):
		i += 1		
		arg = sys.argv[i]
		
		if arg == "-c":
			if i+1 < len(sys.argv):
				configFile = sys.argv[i+1]
				print "Using config file " + configFile
				i += 1
				continue
			else:
				print "warning: expected argument after \"-c\""
		else:
			action = arg
			
	if configFile:
		config.loadUserConfig(configFile)
	
	if action == None:
		socket.setdefaulttimeout(15)
		
		srv = Telnetd(config.get("telnet_addr"), config.get("telnet_port"))
		signal.signal(signal.SIGINT, signal_handler)
		srv.run()
	elif action == "import":
		fname = sys.argv[2]
		import_file(fname)
	elif action == "rerun":
		fname = sys.argv[2]
		rerun_file(fname)
	elif action == "shell":
		test_shell()
	else:
		print "Command " + action + " unknown."

