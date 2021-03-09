from flask import Flask, request, Response, redirect, send_from_directory
from flask_httpauth import HTTPBasicAuth
from flask_socketio import SocketIO

auth = HTTPBasicAuth()

from db import get_db

from clientcontroller import ClientController
from webcontroller import WebController
from authcontroller import AuthController

from util.config import config

import os
import json
import base64
import time
import signal

app  = Flask(__name__)

ctrl     = ClientController()
web      = WebController()
authctrl = AuthController()
socketio = SocketIO(app)

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


SECS_PER_MONTH = 3600 * 24 * 31

@app.after_request
def add_cors(response):
    response.headers["Access-Control-Allow-Origin"]  = "*"
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

	print("--- PUT SESSION ---")
	print(json.dumps(session))

	session = ctrl.put_session(session)
	socketio.emit('session', session)

	return json.dumps(session)

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

### Networks

@app.route("/housekeeping", methods = ["GET"])
def housekeeping():
	ctrl.do_housekeeping()
	return "DONE"

@app.route("/networks", methods = ["GET"])
def get_networks():
	return json.dumps(web.get_networks())

@app.route("/network/<net_id>", methods = ["GET"])
def get_network(net_id):
	return json.dumps(web.get_network(net_id))

@app.route("/network/<net_id>/locations", methods = ["GET"])
def get_network_locations(net_id):
	now = int(time.time())
	loc = web.get_connection_locations(now - SECS_PER_MONTH, now, int(net_id))
	return json.dumps(loc)

@app.route("/network/<net_id>/history", methods = ["GET"])
def get_network_history(net_id):
	
	not_before = request.args.get("not_before")
	not_after  = request.args.get("not_after")
	
	if not_before == None or not_after == None:
		not_after  = int(time.time())
		not_before = not_after - SECS_PER_MONTH
	else:
		not_before = int(not_before)
		not_after  = int(not_after)
		
	d = web.get_network_history(not_before, not_after, int(net_id))
	return json.dumps(d)

@app.route("/network/biggest_history", methods = ["GET"])
def get_network_biggest_history():
	
	not_before = request.args.get("not_before")
	not_after  = request.args.get("not_after")
	
	if not_before == None or not_after == None:
		not_after  = int(time.time())
		not_before = not_after - SECS_PER_MONTH
	else:
		not_before = int(not_before)
		not_after  = int(not_after)
		
	d = web.get_biggest_networks_history(not_before, not_after)
	return json.dumps(d)


### Malwares

@app.route("/malwares", methods = ["GET"])
def get_malwares():
	return json.dumps(web.get_malwares())

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
	allowed_keys = ["ipblock", "user", "password", "ip", "country", "asn_id", "network_id"]
	
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

@app.route("/connection/locations")
def get_connection_locations():
	now   = int(time.time())
	loc   = web.get_connection_locations(now - SECS_PER_MONTH, now)
	return json.dumps(loc)

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
		
### ASN

@app.route("/asn/<asn>")
def get_asn(asn):
	info = web.get_asn(asn)
	if not info:
		return "", 404
	
	return json.dumps(info)

def run():
	signal.signal(15, stop)

	app.run(host=config.get("http_addr"), port=config.get("http_port"),threaded=True)
	#socketio.run(app, host=config.get("http_addr"), port=config.get("http_port"))

def stop():
	print "asdasdasd"

if __name__ == "__main__":
	run()
