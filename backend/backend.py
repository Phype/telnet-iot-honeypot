from flask import Flask, request, Response

from db import get_db
from clientcontroller import ClientController, WebController

from util.config import config

import json
import base64
import time

app  = Flask(__name__)
ctrl = ClientController()
web  = WebController()

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

@app.route("/sample/<sha256>")
def get_sample(sha256):
	sample = web.get_sample(sha256)
	if sample:
		return json.dumps(sample)
	else:
		return "", 404
	
@app.route("/sample/newest")
def get_newest_samples():
	samples = web.get_newest_samples()
	return json.dumps(samples)
		
### Urls

@app.route("/url/<ref_enc>", methods = ["GET"])
def get_url(ref_enc):
	ref = base64.b64decode(ref_enc)
	print("\"" + ref_enc + "\" decodes to \"" + ref + "\"")
	
	url = web.get_url(ref)
	if url:
		return json.dumps(url)
	else:
		return "", 404
	
@app.route("/url/newest")
def get_newest_urls():
	urls = web.get_newest_urls()
	return json.dumps(urls)
		
### connections

@app.route("/connection/<id>")
def get_connection(id):
	conn = web.get_connection(id)
	if conn:
		return json.dumps(conn)
	else:
		return "", 404
	
@app.route("/connections")
def get_connections():
	obj          = {}
	allowed_keys = ["ipblock", "user", "password", "ip", "country", "asn"]
	
	for k,v in request.args.iteritems():
		if k in allowed_keys:
			obj[k] = v
	
	conn = web.get_connections(obj, request.args.get("older_than", None))
	if conn:
		return json.dumps(conn)
	else:
		return "", 404
	
@app.route("/connection/statistics/per_country")
def get_country_stats():
	stats = web.get_country_stats()
	return json.dumps(stats)

@app.route("/connection/by_country/<country>")
def get_country_connections(country):
	older_than = request.args.get('older_than', None)
	stats = web.get_country_connections(country, older_than)
	return json.dumps(stats)

@app.route("/connection/by_ip/<ip>")
def get_ip_connections(ip):
	older_than = request.args.get('older_than', None)
	stats = web.get_ip_connections(ip, older_than)
	return json.dumps(stats)
	
@app.route("/connection/newest")
def get_newest_connections():
	connections = web.get_newest_connections()
	return json.dumps(connections)

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
		db = get_db()
		
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
