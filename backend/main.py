from flask import Flask, request
from db import DB

from config import config
from auth import do_hmac
import json

app = Flask(__name__)
db  = DB()

app.debug = True

def red(obj, attributes):
	res = {}
	for a in attributes:
		if a in obj:
			res[a] = obj[a]
	return res

# Auth class

class Auth:
	next_id = 5;
	secret  = config["secret"];

	def do_auth(self, req):
		if req == None:
			return self.bad("no content")
		if not "auth" in req:
			return self.bad("no auth")
		if not "data" in req:
			return self.bad("no data")
		if not "id" in req["auth"]:
			return self.bad("no auth.id")
		if not "hash" in req["auth"]:
			return self.bad("no auth.hash")
		if not "user" in req["auth"]:
			return self.bad("no auth.user")
		
		i = req["auth"]["id"]
		h = req["auth"]["hash"]
		d = req["data"]
		
		if i != self.next_id:
			return self.bad("wrong id")

		my_h = do_hmac(self.secret + str(self.next_id), d)
		if h != my_h:
			print "Hash mismatch " + h + " != " + my_h
			return self.bad("wrong hash")
		
		return self.good()
		
	def bad(self, msg = None):
		self.next_id = self.next_id + 1
		return {"ok" : False, "next" : self.next_id, "msg" : msg}

	def good(self, msg = None):
		self.next_id = self.next_id + 1
		return {"ok" : True, "next" : self.next_id, "msg" : msg}

auth = Auth()

@app.route("/samples")
def get_samples():
	try:
		result = []
		for sample in db.get_samples():
			result.append(red(sample, ["sha256", "name", "date", "length", "result"]))
			
		return json.dumps(result)
	finally:
		db.end()

@app.route("/conns", methods = ["PUT"])
def put_sample():
	try:
		res = auth.do_auth(request.json)
		if not res["ok"]:
			return json.dumps(res)
		
		conn = json.loads(request.json["data"])
		id_conn = db.put_conn(conn["ip"], conn["user"], conn["pass"], conn["date"])

		for url in conn["urls"]:
			id_url = db.put_url(url["url"], conn["date"])
			db.link_conn_url(id_conn, id_url)
			if url["sample"]:
				sample = url["sample"]
				id_sample = db.put_sample(sample["sha256"], sample["name"], None, sample["length"], conn["date"])
				db.link_url_sample(id_url, id_sample)
		return json.dumps(res)
	finally:
		db.end()

if __name__ == "__main__":
	app.run()
