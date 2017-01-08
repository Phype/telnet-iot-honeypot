import client
import time
import traceback
import os
import requests
import hashlib

from dbg import dbg

class Sampledb:
	back = client.Client()
	conn = None
	
	url_cache    = {}
	sample_cache = {}
	
	url_cache_time = 24 * 3600 # 1 day
	
	def __init__(self):
		self.dir = "samples/"

	def enable_vt(self):
		pass

	def stop(self):
		pass
	
	def clean(self):
		# TODO: clean sample cache
		
		now = int(time.time())
		for url in self.url_cache.keys():
			if now - self.url_cache[url] > self.url_cache_time:
				dbg("Deleting " + url + " out of url cache")
				del self.url_cache[url]
		
	def put_conn(self, ip, user, password, date = None):
		if not date:
			date = int(time.time())
		if self.conn:
			self.commit()
		self.conn = {
			"ip"   : ip,
			"user" : user,
			"pass" : password,
			"date" : date,
			"urls" : []
		}
		return 0

	def put_url(self, url, id_conn):
		if url in self.url_cache:
			dbg("Url " + url + " already cached")
			sample = None
		else:
			sample = self.download(url)
			self.url_cache[url] = int(time.time())
			self.sample_cache[sample["sha256"]] = sample
		
		url = {
			"url"    : url,
			"sample" : sample
		}
		self.conn["urls"].append(url)
		
	def commit(self):
		# TODO: do async
		try:
			upload_req = self.back.put(self.conn)
			if upload_req:
				for sha256 in upload_req:
					self.upload(sha256)
		except:
			dbg("Backend uplink failed")
			traceback.print_exc()
		self.conn = None
		self.clean()
		
	def upload(self, sha256):
		if sha256 in self.sample_cache:
			self.back.upload(sha256, self.sample_cache[sha256]["file"])
		else:
			print "NOT FOUND"
		
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
			f["name"] = url.split("/")[-1].strip()
			f["date"] = int(time.time())
			f["length"]  = 0
			f["file"] = self.dir + str(f["date"]) + "_" + f["name"]
			
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
		url = url.strip()
		hdr = { "User-Agent" : "Wget/1.15 (linux-gnu)" }
		r   = requests.get(url, stream=True, timeout=5.0)
		f   = {}
		h   = hashlib.sha256()

		f["name"] = url.split("/")[-1].strip()
		f["date"] = int(time.time())
		f["length"]  = 0
		if len(f["name"]) < 1:
			f["name"] = "index.html"

		f["file"] = self.dir + str(f["date"]) + "_" + f["name"]

		for his in r.history:
			dbg("HTTP Response " + str(his.status_code))
			for k,v in his.headers.iteritems():
				dbg("HEADER " + k + ": " + v)

		dbg("HTTP Response " + str(r.status_code))
		for k,v in r.headers.iteritems():
			dbg("HEADER " + k + ": " + v)

		with open(f["file"], 'wb') as fd:
			for chunk in r.iter_content(chunk_size = 4096):
				f["length"] = f["length"] + len(chunk)
				fd.write(chunk)
				h.update(chunk)

		f["sha256"] = h.hexdigest()

		return f