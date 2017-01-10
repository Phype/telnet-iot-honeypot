import time
import sqlalchemy

import virustotal

from config import config
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy.sql import select, join, insert, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool

def now():
	return int(time.time())

metadata = MetaData()
samples = Table('samples', metadata,
	Column('id', Integer, primary_key=True),
	Column('sha256', String(64, collation="latin1_swedish_ci"), unique=True),
	Column('date', Integer),
	Column('name', String(32)),
	Column('file', String(512)),
	Column('length', Integer),
	Column('result', String(32)),
)

conns = Table('conns', metadata,
	Column('id', Integer, primary_key=True),
	Column('ip', String(16)),
	Column('date', Integer),
	Column('user', String(16)),
	Column('pass', String(16)),
)

urls = Table('urls', metadata,
	Column('id', Integer, primary_key=True),
	Column('url', String(256, collation="latin1_swedish_ci"), unique=True),
	Column('date', Integer),
	Column('sample', None, ForeignKey('samples.id')),
)

conns_urls = Table('conns_urls', metadata,
	Column('id_conn', None, ForeignKey('conns.id'), primary_key=True),
	Column('id_url', None, ForeignKey('urls.id'), primary_key=True),
)

class DB:
	eng = sqlalchemy.create_engine(config["sql"], poolclass=QueuePool, pool_size=config["max_db_conn"], max_overflow=config["max_db_conn"])
	metadata.create_all(eng)
	sess = None
	
	def __init__(self):
		self.sample_dir    = config["sample_dir"]
		self.limit_samples = 32
		self.limit_urls    = 32
		self.limit_conns   = 32

	def close(self):
		pass

	def conn(self):
		if not self.sess:
			self.sess = scoped_session(sessionmaker(bind=self.eng))
		return self.sess

	def end(self):
		if self.sess:
			try:
				self.sess.commit()
			except:
				pass
			self.sess.remove()
		self.sess = None

	# INPUT
	
	def put_sample_data(self, sha256, data):
		file = self.sample_dir + "/" + sha256
		fp = open(file, "wb")
		fp.write(data)
		fp.close()
		
		self.conn().execute(samples.update().where(samples.c.sha256 == sha256).values(file=file))
			
	def put_sample_result(self, sha256, result):
		self.conn().execute(samples.update().where(samples.c.sha256 == sha256).values(result=result))

	def put_url(self, url, date = now()):
		ex_url = self.conn().execute(urls.select().where(urls.c.url == url)).fetchone()
		if ex_url:
			return ex_url["id"]
		else:
			return self.conn().execute(urls.insert().values(url=url, date=date, sample=None)).inserted_primary_key[0]

	def put_conn(self, ip, user, password, date = now()):
		return self.conn().execute(conns.insert().values((None, ip, date, user, password))).inserted_primary_key[0]

	def put_sample(self, sha256, name, length, date):
		ex_sample = self.get_sample(sha256).fetchone()
		if ex_sample:
			return ex_sample["id"]
		else:
			return self.conn().execute(samples.insert().values(sha256=sha256, date=date, name=name, length=length, result=None)).inserted_primary_key[0]

	def link_conn_url(self, id_conn, id_url):
		self.conn().execute(conns_urls.insert().values(id_conn=id_conn, id_url=id_url))

	def link_url_sample(self, id_url, id_sample):
		self.conn().execute(urls.update().where(urls.c.id == id_url).values(sample=id_sample))

	# OUTPUT
	
	def get_conn_count(self):
		q = """
		SELECT COUNT(id) as count FROM conns
		"""
		return self.conn().execute(text(q)).fetchone()["count"]
	
	def get_sample_count(self):
		q = """
		SELECT COUNT(id) as count FROM samples
		"""
		return self.conn().execute(text(q)).fetchone()["count"]
	
	def get_url_count(self):
		q = """
		SELECT COUNT(id) as count FROM urls
		"""
		return self.conn().execute(text(q)).fetchone()["count"]

	def search_sample(self, q):
		q = "%" + q + "%"
		return self.conn().execute(samples.select().where(samples.c.name.like(q) | samples.c.result.like(q)).limit(self.limit_samples))

	def search_url(self, q):
		search = "%" + q + "%"
		q = """
		SELECT urls.url as url, urls.date as date, samples.sha256 as sample
		FROM urls
		LEFT JOIN samples on samples.id = urls.sample
		WHERE urls.url LIKE :search
		LIMIT :limit
		"""		
		return self.conn().execute(text(q), {"search": search, "limit": self.limit_urls})
	
	def get_url(self, url):
		q = """
		SELECT urls.url as url, urls.date as date, samples.sha256 as sample, urls.id as id
		FROM urls
		LEFT JOIN samples on samples.id = urls.sample
		WHERE urls.url = :search
		"""		
		return self.conn().execute(text(q), {"search": url})
		
	def get_url_conns(self, id_url):
		q = """
		SELECT conns.ip as ip, conns.user as user, conns.pass as pass, conns.date as date
		FROM conns_urls
		LEFT JOIN conns on conns.id = conns_urls.id_conn
		WHERE conns_urls.id_url = :id_url
		ORDER BY conns.date DESC
		LIMIT :limit
		"""		
		return self.conn().execute(text(q), {"id_url": id_url, "limit" : self.limit_samples})
	
	def get_url_conns_count(self, id_url):
		q = """
		SELECT COUNT(conns_urls.id_conn) as count
		FROM conns_urls
		WHERE conns_urls.id_url = :id_url
		"""		
		return self.conn().execute(text(q), {"id_url": id_url})

	def get_sample_stats(self, date_from = 0):
		date_from = 0
		limit     = self.limit_samples
		q = """
		select
			samples.name as name, samples.sha256 as sha256,
			COUNT(samples.id) as count, MAX(conns.date) as lastseen,
			samples.length as length, samples.result as result
		from conns_urls
		INNER JOIN conns on conns_urls.id_conn = conns.id
		INNER JOIN urls on conns_urls.id_url = urls.id
		INNER JOIN samples on urls.sample = samples.id
		WHERE conns.date > :from
		GROUP BY samples.id
		ORDER BY count DESC
		LIMIT :limit"""
		return self.conn().execute(text(q), {"from": date_from, "limit": self.limit_samples})

	def history_global(self, fromdate, todate, delta=3600):
		q = """
		SELECT COUNT(conns.id) as count, :delta * (conns.date DIV :delta) as hour
		FROM conns
		WHERE conns.date >= :from
		AND conns.date <= :to
		GROUP BY hour
		"""
		return self.conn().execute(text(q), {"from": fromdate, "to": todate, "delta": delta})
	
	def history_sample(self, id_sample, fromdate, todate, delta=3600):
		q = """
		SELECT COUNT(conns.id) as count, :delta * (conns.date DIV :delta) as hour
		FROM conns
		INNER JOIN conns_urls on conns_urls.id_conn = conns.id
		INNER JOIN urls on conns_urls.id_url = urls.id
		WHERE urls.sample = :id_sample
		AND conns.date >= :from
		AND conns.date <= :to
		GROUP BY hour
		ORDER BY hour ASC
		"""
		return self.conn().execute(text(q), {"from": fromdate, "to": todate, "delta": delta, "id_sample" : id_sample})

	def get_samples(self):
		return self.conn().execute(samples.select().limit(self.limit_samples))
	
	def get_sample(self, sha256):
		return self.conn().execute(samples.select().where(samples.c.sha256 == sha256))
