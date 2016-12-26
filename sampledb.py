import datetime
import requests
import hashlib
import sqlite3
import os
import time
import re
import Queue
import threading

from dbg import dbg
from virustotal import Virustotal

# DB SCHEME QUERY ALL
# select conns.ip, conns.date, conns.user, conns.pass, urls.url, samples.sha256, samples.name from conns_urls INNER JOIN conns on conns_urls.id_conn = conns.id INNER JOIN urls on conns_urls.id_url = urls.id INNER JOIN samples on urls.sample = samples.id;

class Sampledb:
	def __init__(self):
		self.vt         = Virustotal()
		self.vt_on      = False
		self.vt_queue   = Queue.Queue()
		self.vt_worker  = None

		self.dir   = "samples/"
		self.sql   = sqlite3.connect("samples.db")
		self.setup_db()

		self.url_recheck = 3600 * 24 # 1 day
		self.sh_re = re.compile(".*\\.sh$")
		self.dl_re = re.compile(".*wget (?:-[a-zA-Z] )?(http[^ ;><&]*).*")

	def enable_vt(self):
		self.vt_on      = True
		self.vt_worker = threading.Thread(target=self.vt_work)
		# self.vt_worker.deamon = True
		self.vt_worker.start()

	def setup_db(self):
		self.sql.execute("CREATE TABLE IF NOT EXISTS samples    (id INTEGER PRIMARY KEY AUTOINCREMENT, sha256 TEXT UNIQUE, date INTEGER, name TEXT, file TEXT, result TEXT)")
		self.sql.execute("CREATE TABLE IF NOT EXISTS urls       (id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT UNIQUE, date INTEGER, sample INTEGER)")
		self.sql.execute("CREATE TABLE IF NOT EXISTS conns      (id INTEGER PRIMARY KEY AUTOINCREMENT, ip TEXT, date INTEGER, user TEXT, pass TEXT)")
		self.sql.execute("CREATE TABLE IF NOT EXISTS conns_urls (id_conn INTEGER, id_url INTEGER)")

	def db_add_url(self, url, date):
		c = self.sql.cursor()
		c.execute("INSERT INTO urls VALUES (NULL,?,?,NULL)", (url, date))
		id_url = c.lastrowid
		self.sql.commit()
		return id_url

	def db_link_url_conn(self, id_url, id_conn):
		self.sql.execute("INSERT INTO conns_urls VALUES (?,?)", (id_conn, id_url))
		self.sql.commit()

	def db_add_sample(self, sha256, date, name, filename, id_url, length):
		c = self.sql.cursor()
		c.execute("INSERT INTO samples VALUES (NULL,?,?,?,?,?)", (sha256, date, name, filename, length))
		id_sample = c.lastrowid
		self.db_url_set_sample(id_sample, id_url)
		self.sql.commit()
		return id_sample

	def db_url_set_sample(self, id_sample, id_url):
		self.sql.execute("UPDATE urls SET sample = ? WHERE id = ?", (id_sample, id_url))
		self.sql.commit()

	def db_get_url(self, url):
		url = self.sql.execute("SELECT * FROM urls WHERE url = ?", (url,))
		url = url.fetchone()
		return url

	def db_get_sample(self, sha256):
		url = self.sql.execute("SELECT * FROM samples WHERE sha256 = ?", (sha256,))
		url = url.fetchone()
		return url

	def put_conn(self, ip, user, password, date=None):
		if date == None:
			date = int(time.time())
		c = self.sql.cursor()
		c.execute("INSERT INTO conns VALUES (NULL,?,?,?,?)", (ip, date, user, password))
		id_conn = c.lastrowid
		self.sql.commit()
		return id_conn

	def put_url(self, url, id_conn):
		dbg("New Url " + url)

		db_url = self.db_get_url(url)
		if db_url:
			id_url = db_url[0]

			ts  = db_url[2]
			now = int(time.time())
			if (now - ts > self.url_recheck):
				dbg("Re-Checking Url")
				self.sql.execute("UPDATE urls SET date = ? WHERE id = ?", (now, id_url))
				self.sql.commit()
			else:
				dbg("Url already known")
				self.db_link_url_conn(id_url, id_conn)
				return
		else:
			id_url = self.db_add_url(url, int(time.time()))
	
		self.db_link_url_conn(id_url, id_conn)

		f = self.download(url
		if f["len"] < 5000 or self.sh_re.match(f["name"]):
			with open(f["file"], "rb") as fd:
				for line in fd:
					m = self.dl_re.match(line)
					if m:
						dbg("Found link in File. Downloading ...")
						self.put_url(m.group(1), id_conn)

		sample = self.db_get_sample(f["sha256"])
		if sample:
			self.db_url_set_sample(sample[0], id_url)
			dbg("Hash already known")
			os.remove(f["file"])
			return
		
		self.db_add_sample(f["sha256"], f["date"], f["name"], f["file"], id_url, f["len"])

		if self.vt_on:
			dbg("ANALYZE")
			self.vt_analyze(f)

	def vt_analyze(self, f):
		self.vt_queue.put(f)

	def vt_work(self):
		dbg("Virustotal uploader started")
		while True:
			f    = self.vt_queue.get()
			if f == "!STOP!":
				self.vt_queue.task_done()
				dbg("Stopping worker")
				return
			scan = self.vt.query_hash_sha256(f["sha256"])
			if scan:
				pass
			else:
				self.vt.upload_file(f["file"], f["name"])
			self.vt_queue.task_done()

	def stop(self):
		if self.vt_on:
			dbg("Waiting for virustotal queue to be empty")
			self.vt_queue.put("!STOP!")
			self.vt_queue.join()
		
	def download(self, url):
		url = url.strip()
		dbg("Downloading " + url)
		hdr = { "User-Agent" : "Wget/1.15 (linux-gnu)" }
		r   = requests.get(url, stream=True, timeout=5.0)
		f   = {}
		h   = hashlib.sha256()

		f["name"] = url.split("/")[-1].strip()
		f["date"] = int(time.time())
		f["len"]  = 0
		if len(f["name"]) < 1:
			f["name"] = "index.html"

		f["file"] = self.dir + str(f["date"]) + "_" + f["name"]

		for his in r.history:
			dbg("HTTP Response " + str(his.status_code))
			for k,v in his.headers.iteritems():
				dbg("HEADER " + k + ": " + v)

		dbg("HTTP Response " + str(r.status_code))
		for k,v in r.headers.iteritems():
			dbg("HEADER " + k + ": " + v)

		with open(f["file"], 'wb') as fd:
			for chunk in r.iter_content(chunk_size = 4096):
				f["len"] = f["len"] + len(chunk)
				fd.write(chunk)
				h.update(chunk)

		f["sha256"] = h.hexdigest()
		dbg("Downlod finished. length: " + str(f["len"]) + " sha256: " + f["sha256"])

		return f


#sdb = Sampledb()

#id = sdb.put_conn("0.0.0.0", "", "")
#sdb.put_url("http://blog.fefe.de", id)
#sdb.put_url("https://blog.fefe.de", id)
#sdb.stop()
