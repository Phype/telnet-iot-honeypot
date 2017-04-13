from db import DB
from dbg import dbg

# Controls Actions perfomed by Honeypot Clients
class ClientController:
	
	def __init__(self):
		self.db = DB()
		
	def put_session(self, session):
		s_id = self.db.put_conn(session["ip"], session["user"], session["pass"], session["date"])
		req_urls = []
		
		for url in session["urls"]:
			db_url = self.db.get_url(url).fetchone()
			url_id = 0
			
			if db_url == None:
				url_id = self.db.put_url(url, session["date"])
				req_urls.append(url)
				
			elif db_url["sample"] == None:
				req_urls.append(url)
				url_id = db_url["id"]
				
			else:
				# Sample exists already
				# TODO: Check url for oldness
				pass
				
			self.db.link_conn_url(s_id, url_id)
		
		return req_urls
	
	def put_sample_info(self, f):
		url = f["url"]
		url_id = self.db.get_url(url).fetchone()["id"]
		
		sample_id = self.db.put_sample(f["sha256"], f["name"], f["length"], f["date"])
		self.db.link_url_sample(url_id, sample_id)
		return f
	
	def put_sample(self, sha256, filename):
		fp = open(filename, "rb")
		data = fp.read()
		fp.close()
		
		self.db.put_sample_data(sha256, data)
