import client
import time
import traceback
import os
import requests
import hashlib
import json

from util.dbg import dbg
from util.config import config

_BACKEND = None
def get_backend():
	global _BACKEND
	if _BACKEND:
		return _BACKEND
	elif config.get("backend", optional=True) != None:
		_BACKEND = client.Client()
		return _BACKEND
	else:
		return None

def sha256(data):
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()
    
class SampleRecord:

	def __init__(self, url, name, info, data):
		self.url    = url
		self.name   = name
		self.date   = int(time.time())
		self.info   = info
		self.data   = data
		self.sha256 = sha256(data)
	
	def json(self):
		return {
			"type":   "sample",
			"url":    self.url,
			"name":   self.name,
			"date":   self.date,
			"sha256": self.sha256,
			"info":   self.info,
			"length": len(self.data)
		}

class SessionRecord:

	def __init__(self):
		self.back    = get_backend()
		self.logfile = config.get("log_raw", optional=True)
	
		self.urlset = {}
		
		self.ip = None
		self.user = None
		self.password = None
		self.date = None
		self.urls = []
		self.stream = []
		
	def log_raw(self, obj):
		if self.logfile != None:
			with open(self.logfile, "ab") as fp:
				fp.write(json.dumps(obj).replace("\n", "") + "\n")
		
		
	def json(self):
		return {
			"type"          : "connection",
			"ip"            : self.ip,
			"user"          : self.user,
			"pass"          : self.password,
			"date"          : self.date,
			"urls"          : self.urls,
			"stream"        : self.stream,
		}

	def addInput(self, text):
		self.stream.append({
			"in":   True,
			"ts":   round((time.time() - self.date) * 1000) / 1000,
			"data": text.decode('ascii', 'ignore')
		})

	def addOutput(self, text):
		self.stream.append({
			"in":   False,
			"ts":   round((time.time() - self.date) * 1000) / 1000,
			"data": text.decode('ascii', 'ignore')
		})

	def set_login(self, ip, user, password):
		self.ip       = ip
		self.user     = user
		self.password = password
		self.date     = int(time.time())
	
	def add_file(self, data, url=None, name=None, info=None):
		if url == None:
			shahash = sha256(data)
			# Hack, must be unique somehow, so just use the hash ..."
			url = "telnet://" + self.ip + "/" + shahash[0:8]
		if name == None:
			name = url.split("/")[-1].strip()

		self.urlset[url] = SampleRecord(url, name, info, data)
		self.urls.append(url)

	def commit(self):
		self.log_raw(self.json())
		
		for url in self.urls:
			self.log_raw(self.urlset[url].json())
	
		# Ignore connections without any input
		if len(self.stream) > 1 and self.back != None:
			upload_req = self.back.put_session(self.json())
	
			for url in upload_req:
				dbg("Upload requested: " + url)

				sample = self.urlset[url]
				self.back.put_sample_info(sample.json())
				self.back.put_sample(sample.data)

