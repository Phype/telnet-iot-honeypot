
import re
import random
import time
import json
import traceback

from util.dbg import dbg

from sampledb_client import SessionRecord

from grammar.shell import Env, parse

MIN_FILE_SIZE = 128
PROMPT = " # "
			
class Session:
	def __init__(self, output, remote_addr):
		dbg("New Session")
		self.output      = output
		
		self.remote_addr = remote_addr
		self.record      = SessionRecord()
		self.env         = Env(self.send_string)

		self.env.listen("download", self.download)

		# Files already commited
		self.files = []

	def login(self, user, password):
		dbg("Session login: user=" + user + " password=" + password)
		self.record.set_login(self.remote_addr, user, password)
		
		self.send_string(PROMPT)

	def download(self, data):
		path = data["path"]
		url  = data["url"]
		info = data["info"]

		dbg("Downloaded " + url + " to " + path)

		data = self.env.readFile(path)
		self.record.add_file(data, url=url, name=path, info=info)
		self.files.append(path)

	def end(self):
		dbg("Session End")
		
		for path in self.env.files:
			if path in self.files:
				pass
			else:
				data = self.env.files[path]
				if len(data) > MIN_FILE_SIZE:
					dbg("File created: " + path)
					self.record.add_file(data, name=path)
				else:
					dbg("Ignore small file: " + path + " (" + len(data) + ") bytes")
		
		self.record.commit()

	def send_string(self, text):
		self.record.addOutput(text)
		self.output(text)

	def shell(self, l):
		self.record.addInput(l + "\n")
	
		try:
			tree = parse(l)
			tree.run(self.env)
		except:
			dbg("Could not parse \""+l+"\"")
			self.send_string("sh: syntax error near unexpected token `" + " " + "'\n")
		
		self.send_string(PROMPT)

