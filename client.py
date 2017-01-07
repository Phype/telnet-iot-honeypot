import requests
import json

from config import config
from backend.auth import do_hmac

class Client:
	user    = config["user"]
	secret  = config["secret"]
	url     = config["backend"]

	next_id = 0

	def put(self, data, retry=True):
		jsondata = json.dumps(data)
		postdata = {
			"auth" : {
				"user" : 0,
				"hash" : do_hmac(self.secret + str(self.next_id), jsondata),
				"id"   : self.next_id
			},
			"data" : jsondata
		}
		print str(postdata)
		r = requests.put(self.url + "/conns", json=postdata, timeout=20.0)
		r = r.json()
		self.next_id = r["next"]
		if r["ok"]:
			return r
		elif r["msg"] == "wrong id" and retry:
			return self.put(data, False)
		else:
			raise IOError(r["msg"])

