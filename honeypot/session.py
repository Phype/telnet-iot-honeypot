
import re
import random
import time

from util.dbg import dbg

from sampledb_client import SessionRecord

from grammar.shell import Env, parse

MIN_FILE_SIZE = 0
			
class Session:
	def __init__(self, output, remote_addr):
		dbg("New Session")
		self.output      = output
		self.remote_addr = remote_addr
		self.record      = SessionRecord()
		self.env         = Env(self.send_string)

		self.env.listen("download", self.download)

		# Data gathered
		self.text_in       = ""
		self.text_out      = ""
		self.text_combined = ""

		# Files already commited
		self.files = []

	def login(self, user, password):
		dbg("Session login: user=" + user + " password=" + password)
		self.record.set_login(self.remote_addr, user, password)

	def download(self, data):
		path = data["path"]
		url  = data["url"]
		info = data["info"]

		dbg("DOWNLOAD " + url + " to " + path)

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
					self.record.add_file(data, name=path)
		
		# Do not report non-login connections
		if self.text_combined != "":
			self.record.commit(self.text_in, self.text_out, self.text_combined)

	def send_string(self, text):
		self.text_combined = self.text_combined + text
		self.text_out      = self.text_out + text
		self.output(text)

	def shell(self, l):
		self.text_combined = self.text_combined + " # " + l + "\n"
		self.text_in       = self.text_in + l + "\n"

		tree = parse(l)
		tree.run(self.env)

