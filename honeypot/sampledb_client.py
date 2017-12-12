import client
import time
import traceback
import os
import requests
import hashlib

from util.dbg import dbg
from util.config import config

is_local = config["use_local_db"]
if is_local:
	from backend.clientcontroller import ClientController

def sha256(data):
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()

class SessionRecord:
	def __init__(self):
		if is_local:
			self.back = ClientController()
		else:
			self.back = client.Client()

		self.session_obj = {
			"ip"            : None,
			"user"          : None,
			"pass"          : None,
			"date"          : None,
			"urls"          : [],

			"text_in"       : "",
			"text_out"      : "",
			"text_combined" : ""
		}
		self.urls = {}

	def set_login(self, ip, user, password):
		self.session_obj["ip"]   = ip
		self.session_obj["user"] = user
		self.session_obj["pass"] = password
		self.session_obj["date"] = int(time.time())
		
	def add_file(self, data, url=None, name=None, info=None):
		shahash = sha256(data)

		if url == None:
		    # Hack, must be unique somehow, so just use the hash ..."
		    url = "telnet://" + self.session_obj["ip"] + "/" + shahash[0:8]
		if name == None:
		    name = url.split("/")[-1].strip()

		f = {
		    "url":    url,
		    "name":   name,
		    "date":   int(time.time()),
		    "length": len(data),
		    "sha256": shahash,
		    "info":   info,
			"data":   data
		}
		self.urls[url] = f
		self.session_obj["urls"].append(url)

	def commit(self, text_in, text_out, text_combined):
		self.session_obj["text_in"]       = text_in.decode('ascii', 'ignore')
		self.session_obj["text_out"]      = text_out.decode('ascii', 'ignore')
		self.session_obj["text_combined"] = text_combined.decode('ascii', 'ignore')
		
		upload_req = self.back.put_session(self.session_obj)
		
		for url in upload_req:
			dbg("Upload requested: " + url)

			sample = self.urls[url]
			data   = sample["data"]
			del sample["data"]

			self.back.put_sample_info(sample)
			self.back.put_sample(data)

