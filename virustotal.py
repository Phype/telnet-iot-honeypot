import requests
import time
import db
import Queue

from config import config


class QuotaExceededError(Exception):		
	def __str__(self):
		return "QuotaExceededError: Virustotal API Quota Exceeded"

class Virustotal:
	def __init__(self, key, database):
		self.api_key    = key
		self.db         = database
		self.url        = "https://www.virustotal.com/vtapi/v2/"
		self.user_agent = "Telnet Honeybot Backend"
		self.engines    = ["DrWeb", "Kaspersky", "ESET-NOD32"]
		
		self.queue      = Queue.Queue()
		self.timeout    = 0

	def req(self, method, url, files=None, params=None, headers=None):
		print "VT " + url
		r = None
		if method == "GET":
			r = requests.get(url, files=files, params=params, headers=headers)
		elif method == "POST":
			r = requests.post(url, files=files, params=params, headers=headers)
		else:
			raise ValueError("Unknown Method: " + str(method))

		if r.status_code == 204:
			raise QuotaExceededError()
		else:
			return r

	def upload_file(self, f, fname):
		fp      = open(f, 'rb')
		params  = {'apikey': self.api_key}
		files   = {'file': (fname, fp)}
		headers = { "User-Agent" : self.user_agent }
		res     = self.req("POST", self.url + 'file/scan', files=files, params=params, headers=headers)
		json    = res.json()
		fp.close()
		
		if json["response_code"] == 1:
			return json
		else:
			return None

	def query_hash_sha256(self, h):
		params  = { 'apikey': self.api_key, 'resource': h }
		headers = { "User-Agent" : self.user_agent }
		res     = self.req("GET", self.url + "file/report", params=params, headers=headers)

		json = res.json()

		if json["response_code"] == 1:
			return json
		else:
			return None

	def put_comment(self, obj, msg):
		res = None
		params  = { 'apikey': self.api_key, 'resource': obj, "comment": msg }
		headers = { "User-Agent" : self.user_agent }
		res     = self.req("GET", self.url + "comments/put", params=params, headers=headers)
		json    = res.json()

		if json["response_code"] == 1:
			return json
		else:
			return None

	### High-level

	def get_result(self, r):
		if r["scans"]:
			for e in self.engines:
				if r["scans"][e] and r["scans"][e]["detected"]:
					return r["scans"][e]["result"]
			for e,x in r["scans"].iteritems():
				if x["detected"]:
					return x["result"]
			return None
		else:
			return None

	def process_sample(self, sha256):		
		r = self.query_hash_sha256(sha256)
		if r != None:
			r = self.get_result(r)
			if r == None:
				r = "No Detection"
			self.db.put_sample_result(sha256, r)
			return
		
		sample = self.db.get_sample(sha256).fetchone()
		r = self.upload_file(sample["file"], sample["name"])
		if r == None:
			raise IOError("vt upload failed")
		else:
			self.put_queue(sha256, 60 * 4)

	def put_queue(self, sha256, wait=0):
		now = int(time.time())
		e   = (sha256, now + wait)
		print "VT put " + sha256
		self.queue.put(e)
		
		while self.timeout < now:
			try:
				e = self.queue.get(e, False)
				self.queue.task_done()
				print "VT get " + str(e)
				if e != None and e[1] < now + 1:
					print "VT: process " + e[0]
					try:
						self.process_sample(e[0])
					except QuotaExceededError:
						self.put_queue(sha256)
						print "VT: quota exceeded"
						self.timeout = now + 61
			except Queue.Empty:
				break
		else:
			print "VT: waiting or timeout: " + str(self.timeout)
