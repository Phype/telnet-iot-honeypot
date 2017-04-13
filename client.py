import requests
import requests.exceptions

import json

from dbg import dbg
from config import config

class Client:
	user    = config["user"]
	url     = config["backend"]

	next_id = 0

	def put_session(self, data, retry=True):
		# TODO: Debug purpose only
		return data["urls"]
		
		try:
			r = requests.put(self.url + "/conns", json=data, timeout=20.0)
		except requests.exceptions.RequestException:
			dbg("Cannot connect to backend")
			return []
		
		if r.status_code == 200:
			return r.json()
		elif retry:
			msg = r.raw.read()
			dbg("Backend upload failed, retrying (" + str(msg) + ")")
			return self.put(data, False)
		else:
			msg = r.raw.read()
			raise IOError(msg)

	def put_sample(self, sha256, filename, retry=True):
		fp = open(filename, "rb")
		data = fp.read()
		fp.close()
		
		try:
			r = requests.put(self.url + "/sample/" + sha256, data=data, timeout=20.0)
		except requests.exceptions.RequestException:
			dbg("Cannot connect to backend")
			return
		
		if r.status_code == 200:
			return
		elif retry:
			msg = r.raw.read()
			dbg("Backend upload failed, retrying (" + str(msg) + ")")
			return self.upload(sha256, filename, False)
		else:
			msg = r.raw.read()
			raise IOError(msg)

