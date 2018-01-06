#!/usr/bin/env python

import tftpy
import io

class DummyIO(io.RawIOBase):
	
	def __init__(self):
		self.data = ""
		
	def write(self, s):
		self.data += s

output = DummyIO()

client = tftpy.TftpClient('59.2.248.208', 23927)
client.download('.i', output)

data = output.data

print data.encode("hex")

