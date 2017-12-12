import os
import hashlib
import traceback
import struct

from sqlalchemy import desc, func, and_, or_
from decorator import decorator
from functools import wraps
from simpleeval import simple_eval

from additionalinfo import get_ip_info, get_url_info, get_asn_info
from db import get_db, filter_ascii, Sample, Connection, Url, ASN, Tag
from virustotal import Virustotal

from cuckoo import Cuckoo

from util.dbg import dbg
from util.config import config

@decorator
def db_wrapper(func, *args, **kwargs):
	self = args[0]

	self.db      = get_db()
	self.session = self.db.sess

	try:
		return func(*args, **kwargs)
	finally:
		self.db.end()
		self.db = None
		self.sess = None

class WebController:

	def __init__(self):
		self.db   = None
		self.sess = None
		pass

	@db_wrapper
	def get_connection(self, id):
		connection = self.session.query(Connection).filter(Connection.id == id).first()

		if connection:
			return connection.json(depth=1)
		else:
			return None

	@db_wrapper
	def get_connections(self, filter_obj={}, older_than=None):
		query = self.session.query(Connection).filter_by(**filter_obj)

		if older_than:
			query = query.filter(Connection.date < older_than)

		query = query.order_by(desc(Connection.date))

		connections = query.limit(32).all()
		return map(lambda connection : connection.json(), connections)

	@db_wrapper
	def get_connections_fast(self):
		conns = self.session.query(Connection).all()

		clist = []
		for conn in conns:
			clist.append({
				"id": conn.id,
				"ip": conn.ip,
				"conns_before": map(lambda c: c.id, conn.conns_before),
				"conns_after": map(lambda c: c.id, conn.conns_after)
			})

		return clist

	##

	@db_wrapper
	def get_sample(self, sha256):
		sample = self.session.query(Sample).filter(Sample.sha256 == sha256).first()
		return sample.json(depth=1) if sample else None

	@db_wrapper
	def get_newest_samples(self):
		samples = self.session.query(Sample).order_by(desc(Sample.date)).limit(16).all()
		return map(lambda sample : sample.json(), samples)

	##

	@db_wrapper
	def get_url(self, url):
		url_obj = self.session.query(Url).filter(Url.url == url).first()
		return url_obj.json(depth=1) if url_obj else None

	@db_wrapper
	def get_newest_urls(self):
		urls = self.session.query(Url).order_by(desc(Url.date)).limit(16).all()
		return map(lambda url : url.json(), urls)

	##

	@db_wrapper
	def get_tag(self, name):
		tag = self.session.query(Tag).filter(Tag.name == name).first()
		return tag.json(depth=1) if tag else None

	@db_wrapper
	def get_tags(self):
		tags = self.session.query(Tag).all()
		return map(lambda tag : tag.json(), tags)

	##

	@db_wrapper
	def get_country_stats(self):
		stats = self.session.query(func.count(Connection.country), Connection.country).group_by(Connection.country).all()
		return stats

	##

	@db_wrapper
	def get_asn(self, asn):
		asn_obj = self.session.query(ASN).filter(ASN.asn == asn).first()

		if asn_obj:
			return asn_obj.json(depth=1)
		else:
			return null

# Controls Actions perfomed by Honeypot Clients
class ClientController:

	def __init__(self):
		self.vt   = Virustotal(config["vt_key"])
		self.db   = None
		self.sess = None
		self.cuckoo = Cuckoo(config)

	def get_asn(self, asn):
		asn_obj = self.session.query(ASN).filter(ASN.asn == asn).first()

		if asn_obj:
			return asn_obj.json(depth=1)
		else:
			asn_info = get_asn_info(asn)
			if asn_info:
				asn_obj = ASN(asn=asn, name=asn_info['name'], reg=asn_info['reg'], country=asn_info['country'])
				self.session.add(asn_obj)
				return asn_obj.json(depth=1)

	@db_wrapper
	def put_session(self, session):
		ipinfo  = get_ip_info(session["ip"])
		asn     = None
		block   = None
		country = None

		if ipinfo:
			asn_obj = self.get_asn(ipinfo["asn"])
			asn     = ipinfo["asn"]
			block   = ipinfo["ipblock"]
			country = ipinfo["country"]

		# Calculate "hash"
		connhash = ""
		for line in session["text_in"].split("\n"):
			line     = line.strip()
			linehash = abs(hash(line)) % 0xFFFF
			connhash += struct.pack("!H", linehash)
		connhash = connhash.encode("hex")

		conn = Connection(ip=session["ip"], user=session["user"],
			date=session["date"], password=session["pass"],
			text_combined=session["text_combined"], asn_id=asn, ipblock=block,
			country=country, connhash=connhash)

		self.session.add(conn)
		self.session.flush()

		req_urls = []

		for url in session["urls"]:
			db_url = self.db.get_url(url).fetchone()
			url_id = 0

			if db_url == None:
				url_ip, url_info = get_url_info(url)
				url_asn     = None
				url_country = None

				if url_info:
					asn_obj_url = self.get_asn(url_info["asn"])
					url_asn     = url_info["asn"]
					url_country = url_info["country"]

				url_id = self.db.put_url(url, session["date"], url_ip, url_asn, url_country)
				req_urls.append(url)

			elif db_url["sample"] == None:
				req_urls.append(url)
				url_id = db_url["id"]

			else:
				# Sample exists already
				# TODO: Check url for oldness
				url_id = db_url["id"]

			self.db.link_conn_url(conn.id, url_id)

		# Find previous connections
		assoc_timediff = 120
		previous_conns = (self.session.query(Connection).
				filter(Connection.date > (conn.date - assoc_timediff),
				or_(and_(Connection.user == conn.user, Connection.password == conn.password), 
				Connection.ip == conn.ip),
				Connection.id != conn.id).all())

		for prev in previous_conns:
			conn.conns_before.append(prev)

		# Check connection against all tags
		tags = self.session.query(Tag).all()
		conn = self.session.query(Connection).filter(Connection.id == conn.id).first()
		for tag in tags:
			json_obj = conn.json(depth = 0)
			json_obj["text_combined"] = filter_ascii(json_obj["text_combined"])
			if simple_eval(tag.code, names=json_obj) == True:
				self.db.link_conn_tag(conn.id, tag.id)

		return req_urls

	@db_wrapper
	def put_sample_info(self, f):
		url = f["url"]
		url_id = self.db.get_url(url).fetchone()["id"]

		result = None
		try:
			vtobj  = self.vt.query_hash_sha256(f["sha256"])
			if vtobj:
				result = str(vtobj["positives"]) + "/" + str(vtobj["total"]) + " " + self.vt.get_best_result(vtobj)
		except:
			pass

		sample_id = self.db.put_sample(f["sha256"], f["name"], f["length"], f["date"], f["info"], result)
		self.db.link_url_sample(url_id, sample_id)
		return f

	@db_wrapper
	def put_sample(self, data):
		sha256 = hashlib.sha256(data).hexdigest()
		self.db.put_sample_data(sha256, data)
		if config["cuckoo_enabled"]:
			self.cuckoo.upload(os.path.join(config["sample_dir"], sha256), sha256)
		elif config["submit_to_vt"]:
			self.vt.upload_file(os.path.join(config["sample_dir"], sha256), sha256)
