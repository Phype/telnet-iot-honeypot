import client
import time
import traceback
import os
import requests
import hashlib

from dbg import dbg
from db import DB
from clientcontroller import ClientController
from config import config

is_local = config["use_local_db"]

def get_sample_db():
	if is_local:
		return Sampledb(ClientController())
	else:
		return Sampledb(client.Client())

class Sampledb:
	def __init__(self, back):
		self.dir = "samples/"
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
		f = self.download(url)
		if f:
			print(f)
			if self.back.put_sample_info(f):
				self.back.put_sample(f["sha256"], f["file"])
		
	# DONWLOAD
	
	def download(self, url):
		dbg("Downloading " + url)
		
		try:
			if url.startswith("http://") or url.startswith("https://"):
				f = self.download_http(url)
			elif url.startswith("tftp://"):
				f = self.download_tftp(url)
			else:
				return None
		except requests.exceptions.ReadTimeout:
			return None
		except:
			traceback.print_exc()
			return None
		
		dbg("Downlod finished. length: " + str(f["length"]) + " sha256: " + f["sha256"])
		return f
		
	def download_tftp(self, url):
		r = re.compile("tftp://([^:/]+):?([0-9]*)/(.*)")	
		m = r.match(url)
		if m:
			host  = m.group(1)
			port  = m.group(2)
			fname = m.group(3)
			
			if port == "":
				port = 69
			
			f = {}
			
			f["url"]  = url
			f["name"] = url.split("/")[-1].strip()
			f["date"] = int(time.time())
			f["length"]  = 0
			f["file"] = self.dir + str(f["date"]) + "_" + f["name"]
			f["info"] = None
			
			client = tftpy.TftpClient(host, int(port))
			client.download(fname, f["file"])
			
			h = hashlib.sha256()
			with open(f["file"], 'rb') as fd:
				chunk = fd.read(4096)
				h.update(chunk)
			
			f["sha256"] = h.hexdigest()
			
			return f
		else:
			raise ValueError("Invalid tftp url")
		
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

		f["file"] = self.dir + str(f["date"]) + "_" + f["name"]

		for his in r.history:
			info = info + "HTTP " + str(his.status_code) + "\n"
			for k,v in his.headers.iteritems():
				info = info + k + ": " + v + "\n"

		info = info + "HTTP " + str(r.status_code) + "\n"
		for k,v in r.headers.iteritems():
			info = info + k + ": " + v + "\n"

		with open(f["file"], 'wb') as fd:
			for chunk in r.iter_content(chunk_size = 4096):
				f["length"] = f["length"] + len(chunk)
				fd.write(chunk)
				h.update(chunk)

		f["sha256"] = h.hexdigest()
		f["info"]   = info

		return f