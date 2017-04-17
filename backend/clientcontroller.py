import hashlib

from sqlalchemy import desc, func
from decorator import decorator
from functools import wraps

from additionalinfo import get_ip_info, get_url_info
from db import get_db, Sample, Connection, Url
from util.dbg import dbg

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
		return connection.json(depth=1) if connection else None
			
	@db_wrapper
	def get_newest_connections(self):
		connections = self.session.query(Connection).order_by(desc(Connection.date)).limit(16).all()
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
		pass
		
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
		print(f)
		
		url = f["url"]
		url_id = self.db.get_url(url).fetchone()["id"]
		
		sample_id = self.db.put_sample(f["sha256"], f["name"], f["length"], f["date"], f["info"])
		self.db.link_url_sample(url_id, sample_id)
		return f
	
	@db_wrapper
	def put_sample(self, data):
		sha256 = hashlib.sha256(data).hexdigest()
		self.db.put_sample_data(sha256, data)