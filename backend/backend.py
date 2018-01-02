from flask import Flask, request, Response, redirect, send_from_directory
from flask_httpauth import HTTPBasicAuth
auth = HTTPBasicAuth()

from db import get_db
from clientcontroller import ClientController, WebController, AuthController

from util.config import config

import os
import json
import base64
import time

app  = Flask(__name__)

ctrl     = ClientController()
web      = WebController()
authctrl = AuthController()

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
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE"
    response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-type"
    return response

@auth.verify_password
def verify_password(username, password):
	return authctrl.checkLogin(username, password)

###
#
# Index
#
###

@app.route('/')
def send_index():
	return redirect('/html/index.html')

@app.route('/html/<path:filename>')
def serve_static(filename):
	root_dir = os.getcwd()
	return send_from_directory(os.path.join(root_dir, 'html'), filename)

###
#
# Admin API
#
###

@app.route("/user/<username>", methods = ["PUT"])
@auth.login_required
def add_user(username):
	if authctrl.checkAdmin(auth.username()):
		user = request.json
		if user["username"] != username:
			return "username mismatch in url/data", 500
		return json.dumps(authctrl.addUser(user["username"], user["password"]))
	else:
		return "Authorization required", 401

###
#
# Upload API
#
###

@app.route("/login")
@auth.login_required
def test_login():
	return "LOGIN OK"

@app.route("/conns", methods = ["PUT"])
@auth.login_required
def put_conn():
	session = request.json
	session["backend_username"] = auth.username()	
	return json.dumps(ctrl.put_session(session))

@app.route("/sample/<sha256>", methods = ["PUT"])
@auth.login_required
def put_sample_info(sha256):
	sample = request.json
	
	return json.dumps(ctrl.put_sample_info(sample))

@app.route("/sample/<sha256>/update", methods = ["GET"])
@auth.login_required
def update_sample(sha256):
	return json.dumps(ctrl.update_vt_result(sha256))

@app.route("/file", methods = ["POST"])
@auth.login_required
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
	allowed_keys = ["ipblock", "user", "password", "ip", "country", "asn_id"]
	
	for k,v in request.args.iteritems():
		if k in allowed_keys:
			obj[k] = v
	
	conn = web.get_connections(obj, request.args.get("older_than", None))
	if conn:
		return json.dumps(conn)
	else:
		return "", 404

@app.route("/connections_fast")
def get_connections_fast():
	conn = web.get_connections_fast()
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

### Tags

@app.route("/tag/<name>")
def get_tag(name):
	tag = web.get_tag(name)
	if tag:
		return json.dumps(tag)
	else:
		return "", 404

@app.route("/tags")
def get_tags():
	tags = web.get_tags()
	return json.dumps(tags)

### Hist

@app.route("/connhashtree/<layers>")
def connhash_tree(layers):
	return json.dumps(web.connhash_tree(int(layers)))

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
		
### ASN

@app.route("/asn/<asn>")
def get_asn(asn):
	info = web.get_asn(asn)
	if not info:
		return "", 404
	
	return json.dumps(info)

if __name__ == "__main__":
	app.run()
