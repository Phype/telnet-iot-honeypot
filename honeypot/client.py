import requests
import requests.exceptions
import requests.auth

import json

from util.dbg import dbg
from util.config import config

class Client:

	def __init__(self):
		self.user     = config.get("backend_user")
		self.password = config.get("backend_pass")
		self.url      = config.get("backend")
		self.auth     = requests.auth.HTTPBasicAuth(self.user, self.password)

		self.test_login()
	
	def test_login(self):
		try:
			r = requests.get(self.url + "/connections", auth=self.auth, timeout=20.0)
		except:
			raise IOError("Cannot connect to backend")
		try:
			r = requests.get(self.url + "/login", auth=self.auth, timeout=20.0)
			if r.status_code != 200:
				raise IOError()
		except:
			raise IOError("Backend authentification test failed, check config.json")

	def put_session(self, session, retry=True):
		
		try:
			r = requests.put(self.url + "/conns", auth=self.auth, json=session, timeout=20.0)
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

	def put_sample(self, data, retry=True):
		
		try:
			r = requests.post(self.url + "/file", auth=self.auth, data=data, timeout=20.0)
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

