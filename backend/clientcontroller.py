import hashlib

from db import get_db, Sample, Connection, Url

from util.dbg import dbg

class WebController:
	
	def __init__(self):
		pass
	
	def get_connection(self, id):
		db      = get_db()
		session = db.sess
		
		try:
			connection = session.query(Connection).filter(Connection.id == id).first()
			return connection.json(depth=1) if connection else None
			
		finally:
			db.end()
			
	def get_sample(self, sha256):
		db      = get_db()
		session = db.sess
		
		try:
			sample = session.query(Sample).filter(Sample.sha256 == sha256).first()
			return sample.json(depth=1) if sample else None
			
		finally:
			db.end()
			
	def get_url(self, url):
		db      = get_db()
		session = db.sess
		
		try:
			url_obj = session.query(Url).filter(Url.url == url).first()
			return url_obj.json(depth=1) if url_obj else None
			
		finally:
			db.end()

# Controls Actions perfomed by Honeypot Clients
class ClientController:
	
	def __init__(self):
		pass
		
	def put_session(self, session):
		db = get_db()
		
		try:
			s_id = db.put_conn(session["ip"], session["user"], session["pass"], session["date"])
			req_urls = []
			
			for url in session["urls"]:
				db_url = db.get_url(url).fetchone()
				url_id = 0
				
				if db_url == None:
					url_id = db.put_url(url, session["date"])
					req_urls.append(url)
					
				elif db_url["sample"] == None:
					req_urls.append(url)
					url_id = db_url["id"]
					
				else:
					# Sample exists already
					# TODO: Check url for oldness
					url_id = db_url["id"]
					
				db.link_conn_url(s_id, url_id)
			
			return req_urls
		
		finally:
			db.end()
	
	def put_sample_info(self, f):
		db = get_db()
		
		try:
			url = f["url"]
			url_id = db.get_url(url).fetchone()["id"]
			
			sample_id = db.put_sample(f["sha256"], f["name"], f["length"], f["date"])
			db.link_url_sample(url_id, sample_id)
			return f
	
		finally:
			db.end()
	
	def put_sample(self, data):
		db = get_db()
		
		try:
			sha256 = hashlib.sha256(data).hexdigest()
			db.put_sample_data(sha256, data)
		
		finally:
			db.end()
