import hashlib
import traceback

from sqlalchemy import desc, func
from decorator import decorator
from functools import wraps

from additionalinfo import get_ip_info, get_url_info
from db import get_db, Sample, Connection, Url
from virustotal import Virustotal

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
		date = connection.date
		ts   = 120
		
		if connection:
			
			# Find associates == connections with same user/pass in the same timespan
			# TODO: add filter by same honeypot, this requires honeypot accounts somehow
			# TODO: maybe do this when creating the connection, may by adding event handlers
			associates = (self.session.query(Connection).
				filter(Connection.date > (connection.date-ts),
				Connection.date < (connection.date+ts),
				Connection.user == connection.user,
				Connection.password == connection.password,
				Connection.id != connection.id).all())
			
			json = connection.json(depth=1)
			json['associates'] = map(lambda connection : connection.json(), associates)
			
			return json
		else:
			return None
			
	@db_wrapper
	def get_connections(self, filter_obj={}, older_than=None):
		query = self.session.query(Connection).filter_by(**filter_obj)
		
		if older_than:
			query = query.filter(Connection.date < older_than)
			
		query = query.order_by(desc(Connection.date))
		
		connections = query.limit(16).all()
		return map(lambda connection : connection.json(), connections)
	
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
	def get_country_stats(self):
		stats = self.session.query(func.count(Connection.country), Connection.country).group_by(Connection.country).all()
		return stats

# Controls Actions perfomed by Honeypot Clients
class ClientController:
	
	def __init__(self):
		self.vt = Virustotal(config["vt_key"])
		
	@db_wrapper
	def put_session(self, session):
		ipinfo  = get_ip_info(session["ip"])
		asn     = None
		block   = None
		country = None
		
		if ipinfo:
			asn     = ipinfo["asn"]
			block   = ipinfo["ipblock"]
			country = ipinfo["country"]
		
		s_id = self.db.put_conn(session["ip"], session["user"], session["pass"], session["date"], session["text_combined"], asn, block, country)
		req_urls = []
		
		for url in session["urls"]:
			db_url = self.db.get_url(url).fetchone()
			url_id = 0
			
			if db_url == None:
				url_ip, url_info = get_url_info(url)
				url_asn     = None
				url_country = None
				
				if url_info:
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
				
			self.db.link_conn_url(s_id, url_id)
		
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