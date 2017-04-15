import requests
import requests.exceptions

import json

from util.dbg import dbg
from util.config import config

class Client:
	user    = config.get("user")
	url     = config.get("backend")

	next_id = 0
	def put_session(self, session, retry=True):
		
		try:
			r = requests.put(self.url + "/conns", json=session, timeout=20.0)
		except requests.exceptions.RequestException:
			dbg("Cannot connect to backend")
			return []
		
		if r.status_code == 200:
			return r.json()
		elif retry:
			msg = r.raw.read()
			dbg("Backend upload failed, retrying (" + str(msg) + ")")
			return self.put_session(session, False)
		else:
			msg = r.raw.read()
			raise IOError(msg)
		
	def put_sample_info(self, f, retry=True):
		try:
			sha256 = f["sha256"]
			r = requests.put(self.url + "/sample/" + sha256, json=f, timeout=20.0)
		except requests.exceptions.RequestException:
			dbg("Cannot connect to backend")
			return
		
		if r.status_code == 200:
			return r.json()
		elif retry:
			msg = r.raw.read()
			dbg("Backend upload failed, retrying (" + str(msg) + ")")
			return self.put_sample_info(f, False)
		else:
			msg = r.raw.read()
			raise IOError(msg)

	def put_sample(self, data, retry=True):
		
		try:
			r = requests.post(self.url + "/file", data=data, timeout=20.0)
		except requests.exceptions.RequestException:
			dbg("Cannot connect to backend")
			return
		
		if r.status_code == 200:
			return
		elif retry:
			msg = r.raw.read()
			dbg("Backend upload failed, retrying (" + str(msg) + ")")
			return self.put_sample(sha256, filename, False)
		else:
			msg = r.raw.read()
			raise IOError(msg)

