from flask import Flask, request, Response

from db import DB
from clientcontroller import ClientController

from util.config import config

import json
import base64
import time

app  = Flask(__name__)
ctrl = ClientController()
db   = None

app.debug = True

def red(obj, attributes):
	if not obj:
		return None
	res = {}
	for a in attributes:
		if a in obj:
			res[a] = obj[a]
	return res

###
#
# Globals
#
###

@app.after_request
def add_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response

###
#
# Upload API
#
###

@app.route("/conns", methods = ["PUT"])
def put_conn():
	session = request.json
	
	return json.dumps(ctrl.put_session(session))

@app.route("/sample/<sha256>", methods = ["PUT"])
def put_sample_info(sha256):
	sample = request.json
	
	return json.dumps(ctrl.put_sample_info(sample))

@app.route("/file", methods = ["POST"])
def put_sample():
	data   = request.get_data()
	
	return json.dumps(ctrl.put_sample(data))

###
#
# Public API
#
###

def fail(msg = "", code = 400):
	obj = {"ok" : False, "msg" : msg}
	return Response(json.dumps(obj), status=code, mimetype='application/json')

### Samples

@app.route("/samples")
def get_samples():
	try:
		result = []
		for sample in db.get_samples():
			result.append(red(sample, ["sha256", "name", "date", "length", "result"]))
			
		return json.dumps(result)
	finally:
		db.end()

@app.route("/sample/<sha256>")
def get_sample(sha256):
	try:
		sample = db.get_sample(sha256).fetchone()
		sample = red(sample, ["sha256", "name", "date", "length", "result"])
		return json.dumps(sample)
	finally:
		db.end()

@app.route("/samples/search", methods = ["POST"])
def search_sample():
	if not request.json or not "q" in request.json:
		return fail("no query")
	q = request.json["q"]
	try:
		result = []
		for sample in db.search_sample(q):
			result.append(red(sample, ["sha256", "name", "date", "length", "result"]))
			
		return json.dumps(result)
	finally:
		db.end()

@app.route("/samples/statistics")
def get_sample_stats():
	try:
		result = []
		for sample in db.get_sample_stats(int(time.time()) - 6 * 24 * 3600):
			result.append(red(sample, ["sha256", "name", "date", "length", "result", "count", "lastseen"]))
			
		return json.dumps(result)
	finally:
		db.end()
		
### Urls

@app.route("/url/<ref>")
def get_url(ref):
	try:
		ref = base64.b32decode(ref)
		print '"' + ref + '"'
		url = db.get_url(ref).fetchone()
		if url:
			conns_count = db.get_url_conns_count(url["id"]).fetchone()["count"]
			conns = []
			for conn in db.get_url_conns(url["id"]):
				conns.append(red(conn, ["ip", "user", "pass", "date"]))
			
			url = red(url, ["url", "date", "sample"])
			url["ref"]      = urllib.quote(url["url"])
			url["conns"]    = conns
			url["nb_conns"] = conns_count
			return json.dumps(url)
		else:
			return "", 404
	finally:
		db.end()
		
@app.route("/urls/search", methods = ["POST"])
def search_url():
	if not request.json or not "q" in request.json:
		return fail("no query")
	q = request.json["q"]
	try:
		result = []
		for url in db.search_url(q):
			url = red(url, ["url", "date", "sample"])
			url["ref"] = base64.b32encode(url["url"])
			result.append(url)
			
		return json.dumps(result)
	finally:
		db.end()
		
@app.route("/info")
def get_info():
	try:
		obj = {
			"connections" : db.get_conn_count(),
			"samples" : db.get_sample_count(),
			"urls" : db.get_url_count()
		}
		return json.dumps(obj)
	finally:
		db.end()
		
### Hist

def hist_fill(start, end, delta, db_result):
	result = []
	start  = start - start % delta
	end    = end   - end   % delta

	now    = start
	for row in db_result:
		while now + delta < row["hour"]:
			now = now + delta
			result.append(0)
		
		now = row["hour"]
		result.append(row["count"])		
	while now + delta < end:
		now = now + delta
		result.append(0)

	obj = {"start" : start, "end" : end, "delta" : delta, "data" : result}
	return obj

@app.route("/history")
def hist_global():
	try:
		delta  = 3600 * 6
		end    = int(time.time())
		start  = end - delta * 24
		
		start  = start - start % delta
		end    = end   - end   % delta + delta
		
		obj = hist_fill(start, end, delta, db.history_global(start, end, delta))
		return json.dumps(obj)
	finally:
		db.end()
		
@app.route("/history/<sha256>")
def hist_sample(sha256):
	try:
		sample = db.get_sample(sha256).fetchone()
		if not sample:
			return fail("sample not found", 404)
		
		delta  = 3600 * 6
		end    = int(time.time())
		start  = end - delta * 24
		
		start  = start - start % delta
		end    = end   - end   % delta + delta
		
		obj = hist_fill(start, end, delta, db.history_sample(sample["id"], start, end, delta))
		return json.dumps(obj)
	finally:
		db.end()


if __name__ == "__main__":
	app.run()
