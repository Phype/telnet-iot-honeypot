import requests
import json

from dbg import dbg
from config import config
from backend.auth import do_hmac

class Client:
	user    = config["user"]
	secret  = config["secret"]
	url     = config["backend"]

	next_id = 0

	def put(self, data, retry=True):
		r = requests.put(self.url + "/conns", json=data, timeout=20.0)
		
		if r.status_code == 200:
			return r.json()
		elif retry:
			msg = r.raw.read()
			dbg("Backend upload failed, retrying (" + str(msg) + ")")
			return self.put(data, False)
		else:
			msg = r.raw.read()
			raise IOError(msg)

	def upload(self, sha256, filename, retry=True):
		fp = open(filename, "rb")
		data = fp.read()
		fp.close()
		
		r = requests.put(self.url + "/sample/" + sha256, data=data, timeout=20.0)
		
		if r.status_code == 200:
			return
		elif retry:
			msg = r.raw.read()
			dbg("Backend upload failed, retrying (" + str(msg) + ")")
			return self.upload(sha256, filename, False)
		else:
			msg = r.raw.read()
			raise IOError(msg)

