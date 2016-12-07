import requests
import os.path
import hashlib
import time

from dbg import dbg

class Virustotal:
	def __init__(self):
		self.url        = "https://www.virustotal.com/vtapi/v2/"
		self.api_key    = "f1275b1a6f444aaf3cccb3d557748f4f2eb9e5f21ee8b410965b98d7b01f73ee"
		self.user_agent = "Telnet Honeybot aka Embylinux (telnet://nack.duckdns.org:23)"

	def req(self, method, url, files=None, params=None, headers=None, retries=3):
		r = None
		if method == "GET":
			r = requests.get(url, files=files, params=params, headers=headers)
		elif method == "POST":
			r = requests.post(url, files=files, params=params, headers=headers)
		else:
			raise ValueError("Unknown Method: " + str(method))

		if r.status_code == 204:
			if retries > 0:
				dbg("API Quota exceeded. Retrying in 61 seconds.")
				time.sleep(61)
				return self.req(method, url, files, params, headers, retries - 1)
			else:
				dbg("API Quota exceeded. Giving up.")
				return None
		else:
			return r

	def upload_file(self, f, fname):
		dbg("Uploading file " + f)
		fp      = open(f, 'rb')
		params  = {'apikey': self.api_key}
		files   = {'file': (fname, fp)}
		headers = { "User-Agent" : self.user_agent }
		res     = self.req("POST", self.url + 'file/scan', files=files, params=params, headers=headers)
		json    = res.json()
		fp.close()
		if json["response_code"] == 1:
			dbg("Uploading finished. See " + str(json["permalink"]))
			return json
		else:
			return None

	def query_hash_sha256(self, h):
		dbg("Query Hash " + h)
		params  = { 'apikey': self.api_key, 'resource': h }
		headers = { "User-Agent" : self.user_agent }
		res     = self.req("GET", self.url + "file/report", params=params, headers=headers)

		if str(res.status_code) == 204:
			dbg("API quota exceeded. Waiting 61 seconds")
			time.sleep(61)

		json    = res.json()

		if json["response_code"] == 1:
			dbg("File already scanned. See " + str(json["permalink"]))
			return json
		else:
			return None

	def put_comment(self, obj, msg):
		res = None
		try:
			dbg("Commenting on " + obj)
			params  = { 'apikey': self.api_key, 'resource': obj, "comment": msg }
			headers = { "User-Agent" : self.user_agent }
			res     = self.req("GET", self.url + "comments/put", params=params, headers=headers)
			json    = res.json()

			if json["response_code"] == 1:
				return json
			else:
				return None
		except:
			dbg("Request failed")
			if res:
				dbg("Result:\n" + res.text)
			return None

def sha256_file(f):
	BUFSIZE = 4096
	fp = open(f, "rb")
	h  = hashlib.sha256()
	while True:
		buf = fp.read(BUFSIZE)
		if (len(buf) > 0):
			h.update(buf)
		else:
			break
	fp.close()
	return h.hexdigest()

#vt = Virustotal()
#vt.put_comment("4d0aba73fcd8e8ea22560d8ed1e1c0c21b080e1fa1a24c57d3935307989d3717", "test123 Mybot")

