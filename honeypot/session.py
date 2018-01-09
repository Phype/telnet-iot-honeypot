import re
import random
import time
import json
import traceback

import struct
import socket

from util.dbg    import dbg
from util.config import config

from sampledb_client import SessionRecord

from shell.shell import Env, run

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
		
	def parse_shellcode(self, data):		
		# Hajime exclusive!
		
		if len(data) == 480:
			sockaddr = data[0xf0:0xf0+8]
			sockaddr = struct.unpack(">HHBBBB", sockaddr)
			
			if sockaddr[0] == 0x0200:
				ip   = str(sockaddr[2]) + "." + str(sockaddr[3]) + "." + str(sockaddr[4]) + "." + str(sockaddr[5])
				port = sockaddr[1]
				url  = "tcp://" + ip + ":" + str(port)
				dbg("Stub downloader started: " + url)
				
				if config.get("fake_dl", optional=True, default=False):
					self.record.add_file(str(hash(url)), url=url)
				else:
					try:
						s = socket.create_connection((ip, port), timeout=10)
				
						data = ""
						while True:
							chunk = s.recv(1024)
							if len(chunk) == 0:
								break
							data += chunk
				
						s.close()
				
						self.record.add_file(data, url=url)
					except:
						traceback.print_exc()
	
	def found_file(self, path, data):
		if path in self.files:
			pass
		else:
			if len(data) > MIN_FILE_SIZE:
				dbg("File created: " + path)
				self.parse_shellcode(data)
				self.record.add_file(data, name=path)
			else:
				dbg("Ignore small file: " + path + " (" + str(len(data)) + ") bytes")
		

	def end(self):
		dbg("Session End")
	
		for path in self.env.files:
			self.found_file(path, self.env.files[path])
			
		for (path, data) in self.env.deleted:
			self.found_file(path, data)
	
		self.record.commit()

	def send_string(self, text):
		self.record.addOutput(text)
		self.output(text)

	def shell(self, l):
		self.record.addInput(l + "\n")
	
		try:
			tree = run(l, self.env)
		except:
			dbg("Could not parse \""+l+"\"")
			self.send_string("sh: syntax error near unexpected token `" + " " + "'\n")
			traceback.print_exc()
		
		self.send_string(PROMPT)

