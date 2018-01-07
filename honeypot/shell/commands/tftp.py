#!/usr/bin/env python

import io
import traceback

from getopt import gnu_getopt, GetoptError
from tftpy  import TftpClient

from util   import easy_getopt
from base   import Proc

class DummyIO(io.RawIOBase):
	
	def __init__(self):
		self.data = ""
		
	def write(self, s):
		self.data += s
		
class StaticTftp(Proc):

	def run(self, env, args):
		Tftp().run(env, args)	

class Tftp:

	help = """BusyBox v1.22.1 (Ubuntu 1:1.22.0-15ubuntu1) multi-call binary.

Usage: tftp [OPTIONS] HOST [PORT]

Transfer a file from/to tftp server

	-l FILE	Local FILE
	-r FILE	Remote FILE
	-g	Get file
	-p	Put file
	-b SIZE	Transfer blocks of SIZE octets

"""

	def run(self, env, args):
		self.env       = env
		self.connected = False
		self.chunks    = 0
	
		try:
			opts, args = easy_getopt(args, "l:r:gpb:")
		except GetoptError as e:
			env.write("tftp: " + str(e) + "\n")
			env.write(Tftp.help)
			return
		
		if len(args) == 0:
			env.write(Tftp.help)
			return
		elif len(args) == 1:
			host = args[0]
			port = 69
			
			if ":" in host:
				parts = host.split(":")
				host  = parts[0]
				port  = int(parts[1])
			
		else:
			host = args[0]
			port = int(args[1])
			
		if "-p" in opts:
			env.write("tftp: option 'p' not implemented\n")
			return
		if "-b" in opts:
			env.write("tftp: option 'b' not implemented\n")
			return
		
		if "-r" in opts:
			path = opts["-r"]
		else:
			print Tftp.help
			return
			
		if "-l" in opts:
			fname = opts["-l"]
		else:
			fname = path
		
		try:
			data = self.download(host, port, path)
			env.writeFile(fname, data)

			env.action("download", {
				"url":  "tftp://" + host + ":" + str(port) + "/" + path,
				"path": fname,
				"info": None
			})
			
			self.env.write("\nFinished. Saved to " + fname + ".\n")
		except:
			env.write("tftp: timeout\n")
			traceback.print_exc()

	def download(self, host, port, fname):
		output = DummyIO()
		client = TftpClient(host, port)
		
		self.env.write("Trying " + host + ":" + str(port) + " ... ")
		client.download(fname, output, timeout=5, packethook=self.pkt)
		return output.data
		
	def pkt(self, data):
		if not(self.connected):
			self.env.write("OK\n")
			self.connected = True
		#if self.chunks % 60 == 0:
		#	self.env.write("\n")
		self.chunks += 1
		#self.env.write(".")

Proc.register("tftp", StaticTftp())

