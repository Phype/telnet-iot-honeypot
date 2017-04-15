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

def get_sample_db():
	if is_local:
		return Sampledb(ClientController())
	else:
		return Sampledb(client.Client())

class Sampledb:
	def __init__(self, back):
		self.back = back
				
	def put_session(self, session):
		session_obj = {
			"ip"            : session.remote_addr,
			"user"          : session.user,
			"pass"          : session.password,
			"date"          : session.date,
			"urls"          : session.urls,

			"text_in"       : session.text_in,
			"text_out"      : session.text_out,
			"text_combined" : session.text_combined
		}
		
		upload_req = self.back.put_session(session_obj)
		
		for url in upload_req:
			dbg("Upload requested: " + url)
			self.get_sample(url)
			
	def get_sample(self, url):
		f, data = self.download(url)
		if f:
			print(f)
			if self.back.put_sample_info(f):
				if config["save_samples"]:
					self.back.put_sample(data)
		
	# DONWLOAD
	
	def download(self, url):
		dbg("Downloading " + url)
		
		try:
			if url.startswith("http://") or url.startswith("https://"):
				f, data = self.download_http(url)
			else:
				return None
		except requests.exceptions.ReadTimeout:
			return None
		except:
			traceback.print_exc()
			return None
		
		dbg("Downlod finished. length: " + str(f["length"]) + " sha256: " + f["sha256"])
		return f, data
		
	def download_http(self, url):
		url  = url.strip()
		hdr  = { "User-Agent" : "Wget/1.15 (linux-gnu)" }
		r    = requests.get(url, stream=True, timeout=5.0)
		f    = {}
		h    = hashlib.sha256()
		info = ""

		f["url"]  = url
		f["name"] = url.split("/")[-1].strip()
		f["date"] = int(time.time())
		f["length"]  = 0
		if len(f["name"]) < 1:
			f["name"] = "index.html"

		for his in r.history:
			info = info + "HTTP " + str(his.status_code) + "\n"
			for k,v in his.headers.iteritems():
				info = info + k + ": " + v + "\n"

		info = info + "HTTP " + str(r.status_code) + "\n"
		for k,v in r.headers.iteritems():
			info = info + k + ": " + v + "\n"

		data = ""
		for chunk in r.iter_content(chunk_size = 4096):
			f["length"] = f["length"] + len(chunk)
			data = data + chunk
			h.update(chunk)

		f["sha256"] = h.hexdigest()
		f["info"]   = info

		return f, data