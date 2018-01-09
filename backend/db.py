import time
import json
import sqlalchemy

from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, Text

from sqlalchemy.sql import select, join, insert, text
from sqlalchemy.orm import relationship, sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from sqlalchemy.ext.declarative import declarative_base

from util.config import config

is_sqlite = "sqlite://" in config.get("sql")

print("Creating/Connecting to DB")

def now():
	return int(time.time())

def filter_ascii(string):
	string = ''.join(char for char in string if ord(char) < 128 and ord(char) > 32 or char in "\r\n ")
	return string

Base = declarative_base()

# n to m relation connection <-> url
conns_urls = Table('conns_urls', Base.metadata,
	Column('id_conn', None, ForeignKey('conns.id'), primary_key=True),
	Column('id_url', None, ForeignKey('urls.id'), primary_key=True),
)

# n to m relation connection <-> tag
conns_tags = Table('conns_tags', Base.metadata,
	Column('id_conn', None, ForeignKey('conns.id'), primary_key=True),
	Column('id_tag', None, ForeignKey('tags.id'), primary_key=True),
)

# n to m relationship connection <-> connection (associates)
conns_conns = Table('conns_assocs', Base.metadata,
	Column('id_first', None, ForeignKey('conns.id'), primary_key=True),
	Column('id_last',  None, ForeignKey('conns.id'), primary_key=True),
)

class User(Base):
	__tablename__ = 'users'

	id       = Column('id', Integer, primary_key=True)
	username = Column('username', String(32), unique=True)
	password = Column('password', String(64))

	connections = relationship("Connection", back_populates="backend_user")

	def json(self, depth=0):
		return {
			"username": self.username
		}
		
class Network(Base):
	__tablename__ = 'network'
	
	id = Column('id', Integer, primary_key=True)

	samples     = relationship("Sample",     back_populates="network")
	urls        = relationship("Url",        back_populates="network")
	connections = relationship("Connection", back_populates="network")

class ASN(Base):
	__tablename__ = 'asn'
	
	asn = Column('asn', Integer, primary_key=True)
	name = Column('name', String(64))
	reg = Column('reg', String(32))
	country = Column('country', String(3))
	
	urls = relationship("Url", back_populates="asn")
	connections = relationship("Connection", back_populates="asn")
	
	def json(self, depth=0):
		return {
			"asn": self.asn,
			"name": self.name,
			"reg": self.reg,
			"country": self.country,
			
			"urls": map(lambda url : url.url if depth == 0
			   else url.json(depth - 1), self.urls),
			
			"connections": None if depth == 0 else map(lambda connection :
                connection.json(depth - 1), self.connections)
		}

class Sample(Base):
	__tablename__ = 'samples'
	
	id = Column('id', Integer, primary_key=True)
	sha256 = Column('sha256', String(64), unique=True)
	date = Column('date', Integer)
	name = Column('name', String(32))
	file = Column('file', String(512))
	length = Column('length', Integer)
	result = Column('result', String(32))
	info = Column('info', Text())
	
	urls = relationship("Url", back_populates="sample")
	
	network_id  = Column('network', None, ForeignKey('network.id'))
	network     = relationship("Network", back_populates="samples")
	
	def json(self, depth=0):
		return {
			"sha256": self.sha256,
			"date": self.date,
			"name": self.name,
			"length": self.length,
			"result": self.result,
			"info": self.info,
			"urls": len(self.urls) if depth == 0 else map(lambda url :
                url.json(depth - 1), self.urls)
		}
	
class Connection(Base):
	__tablename__ = 'conns'
	
	id = Column('id', Integer, primary_key=True)
	ip = Column('ip', String(16))
	date = Column('date', Integer)
	user = Column('user', String(16))
	password = Column('pass', String(16))
	connhash = Column('connhash', String(256))

	stream = Column('text_combined', Text())

	asn_id = Column('asn', None, ForeignKey('asn.asn'))
	asn = relationship("ASN", back_populates="connections")

	backend_user_id = Column('backend_user_id', None, ForeignKey('users.id'))
	backend_user = relationship("User", back_populates="connections")

	ipblock = Column('ipblock', String(32))
	country = Column('country', String(3))
	
	urls    = relationship("Url", secondary=conns_urls, back_populates="connections")
	tags    = relationship("Tag", secondary=conns_tags, back_populates="connections")
	
	network_id  = Column('network', None, ForeignKey('network.id'))
	network     = relationship("Network", back_populates="connections")
	
	conns_before = relationship("Connection", secondary=conns_conns,
			back_populates="conns_after", 
            primaryjoin=(conns_conns.c.id_last==id),
            secondaryjoin=(conns_conns.c.id_first==id))
	conns_after  = relationship("Connection", secondary=conns_conns,
			back_populates="conns_before", 
            primaryjoin=(conns_conns.c.id_first==id),
            secondaryjoin=(conns_conns.c.id_last==id))
	
	def json(self, depth=0):
		return {
			"id": self.id,
			"ip": self.ip,
			"date": self.date,
			"user": self.user,
			"password": self.password,
			"connhash": self.connhash,
			"stream": None if depth == 0 else json.loads(self.stream),
			
			"asn": None if self.asn == None else self.asn.json(0),
			
			"ipblock": self.ipblock,
			"country": self.country,

			"conns_before": map(lambda conn : conn.id if depth == 0
				else conn.json(depth - 1), self.conns_before),
			"conns_after": map(lambda conn : conn.id if depth == 0
				else conn.json(depth - 1), self.conns_after),

			"backend_user": self.backend_user.username,
			
			"urls": len(self.urls) if depth == 0 else map(lambda url :
			   url.json(depth - 1), self.urls),

			"tags": len(self.tags) if depth == 0 else map(lambda tag :
			   tag.json(depth - 1), self.tags),
		}
	
class Url(Base):
	__tablename__ = 'urls'
	
	id   = Column('id', Integer, primary_key=True)
	url  = Column('url', String(256), unique=True)
	date = Column('date', Integer)
	
	sample_id = Column('sample', None, ForeignKey('samples.id'))
	sample    = relationship("Sample", back_populates="urls")
	
	network_id  = Column('network', None, ForeignKey('network.id'))
	network     = relationship("Network", back_populates="urls")
	
	connections = relationship("Connection", secondary=conns_urls, back_populates="urls")
	
	asn_id = Column('asn', None, ForeignKey('asn.asn'))
	asn = relationship("ASN", back_populates="urls")
	
	ip  = Column('ip', String(32))
	country = Column('country', String(3))
	
	def json(self, depth=0):
		return {
			"url": self.url,
			"date": self.date,
			"sample": None if self.sample == None else 
				(self.sample.sha256 if depth == 0
					else self.sample.json(depth - 1)),
				
			"connections": len(self.connections) if depth == 0 else map(lambda connection :
					  connection.json(depth - 1), self.connections),
			
			"asn": None if self.asn == None else 
				(self.asn.asn if depth == 0
					else self.asn.json(depth - 1)),
				
			"ip": self.ip,
			"country": self.country,
		}

class Tag(Base):
	__tablename__ = 'tags'
	
	id   = Column('id', Integer, primary_key=True)
	name = Column('name', String(32), unique=True)
	code = Column('code', String(256))

	connections = relationship("Connection", secondary=conns_tags, back_populates="tags")
	
	def json(self, depth=0):
		return {
			"name": self.name,
			"code": self.code,
				
			"connections": None if depth == 0 else map(lambda connection :
                connection.json(depth - 1), self.connections)
		}
	
	
samples = Sample.__table__ 
conns   = Connection.__table__
urls    = Url.__table__
tags    = Tag.__table__

eng = None

if is_sqlite:
	eng = sqlalchemy.create_engine(config.get("sql"),
								poolclass=QueuePool,
								pool_size=1,
								max_overflow=1,
								connect_args={'check_same_thread': False})
else:
	eng = sqlalchemy.create_engine(config.get("sql"),
								poolclass=QueuePool,
								pool_size=config.get("max_db_conn"),
								max_overflow=config.get("max_db_conn"))

Base.metadata.create_all(eng)

def get_db():
	return DB(scoped_session(sessionmaker(bind=eng)))

class DB:
	
	def __init__(self, sess):
		self.sample_dir    = config.get("sample_dir")
		self.limit_samples = 32
		self.limit_urls    = 32
		self.limit_conns   = 32
		self.sess          = sess

	def end(self):
		try:
			self.sess.commit()
		finally:
			self.sess.remove()

	# INPUT
	
	def put_sample_data(self, sha256, data):
		file = self.sample_dir + "/" + sha256
		fp = open(file, "wb")
		fp.write(data)
		fp.close()
		
		self.sess.execute(samples.update().where(samples.c.sha256 == sha256).values(file=file))
			
	def put_sample_result(self, sha256, result):
		self.sess.execute(samples.update().where(samples.c.sha256 == sha256).values(result=result))

	def put_url(self, url, date, url_ip, url_asn, url_country):
		ex_url = self.sess.execute(urls.select().where(urls.c.url == url)).fetchone()
		if ex_url:
			return ex_url["id"]
		else:
			return self.sess.execute(urls.insert().values(url=url, date=date, sample=None, ip=url_ip, asn=url_asn, country=url_country)).inserted_primary_key[0]

	def put_conn(self, ip, user, password, date, text_combined, asn, block, country, connhash):
		return self.sess.execute(conns.insert().values((None, ip, date, user, password, text_combined, asn, block, country))).inserted_primary_key[0]

	def put_sample(self, sha256, name, length, date, info, result):
		ex_sample = self.get_sample(sha256).fetchone()
		if ex_sample:
			return ex_sample["id"]
		else:
			return self.sess.execute(samples.insert().values(sha256=sha256, date=date, name=name, length=length, result=result, info=info)).inserted_primary_key[0]

	def link_conn_url(self, id_conn, id_url):
		self.sess.execute(conns_urls.insert().values(id_conn=id_conn, id_url=id_url))

	def link_url_sample(self, id_url, id_sample):
		self.sess.execute(urls.update().where(urls.c.id == id_url).values(sample=id_sample))

	def link_conn_tag(self, id_conn, id_tag):
		self.sess.execute(conns_tags.insert().values(id_conn=id_conn, id_tag=id_tag))

	# OUTPUT
	
	def get_conn_count(self):
		q = """
		SELECT COUNT(id) as count FROM conns
		"""
		return self.sess.execute(text(q)).fetchone()["count"]
	
	def get_sample_count(self):
		q = """
		SELECT COUNT(id) as count FROM samples
		"""
		return self.sess.execute(text(q)).fetchone()["count"]
	
	def get_url_count(self):
		q = """
		SELECT COUNT(id) as count FROM urls
		"""
		return self.sess.execute(text(q)).fetchone()["count"]

	def search_sample(self, q):
		q = "%" + q + "%"
		return self.sess.execute(samples.select().where(samples.c.name.like(q) | samples.c.result.like(q)).limit(self.limit_samples))

	def search_url(self, q):
		search = "%" + q + "%"
		q = """
		SELECT urls.url as url, urls.date as date, samples.sha256 as sample
		FROM urls
		LEFT JOIN samples on samples.id = urls.sample
		WHERE urls.url LIKE :search
		LIMIT :limit
		"""		
		return self.sess.execute(text(q), {"search": search, "limit": self.limit_urls})
	
	def get_url(self, url):
		q = """
		SELECT urls.url as url, urls.date as date, samples.sha256 as sample, urls.id as id
		FROM urls
		LEFT JOIN samples on samples.id = urls.sample
		WHERE urls.url = :search
		"""		
		return self.sess.execute(text(q), {"search": url})
		
	def get_url_conns(self, id_url):
		q = """
		SELECT conns.ip as ip, conns.user as user, conns.pass as password, conns.date as date
		FROM conns_urls
		LEFT JOIN conns on conns.id = conns_urls.id_conn
		WHERE conns_urls.id_url = :id_url
		ORDER BY conns.date DESC
		LIMIT :limit
		"""		
		return self.sess.execute(text(q), {"id_url": id_url, "limit" : self.limit_samples})
	
	def get_url_conns_count(self, id_url):
		q = """
		SELECT COUNT(conns_urls.id_conn) as count
		FROM conns_urls
		WHERE conns_urls.id_url = :id_url
		"""		
		return self.sess.execute(text(q), {"id_url": id_url})

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
		return self.sess.execute(text(q), {"from": date_from, "limit": self.limit_samples})

	def history_global(self, fromdate, todate, delta=3600):
		q = """
		SELECT COUNT(conns.id) as count, :delta * cast((conns.date / :delta) as INTEGER) as hour
		FROM conns
		WHERE conns.date >= :from
		AND conns.date <= :to
		GROUP BY hour
		"""
		return self.sess.execute(text(q), {"from": fromdate, "to": todate, "delta": delta})
	
	def history_sample(self, id_sample, fromdate, todate, delta=3600):
		q = """
		SELECT COUNT(conns.id) as count, :delta * cast((conns.date / :delta) as INTEGER) as hour
		FROM conns
		INNER JOIN conns_urls on conns_urls.id_conn = conns.id
		INNER JOIN urls on conns_urls.id_url = urls.id
		WHERE urls.sample = :id_sample
		AND conns.date >= :from
		AND conns.date <= :to
		GROUP BY hour
		ORDER BY hour ASC
		"""
		return self.sess.execute(text(q), {"from": fromdate, "to": todate, "delta": delta, "id_sample" : id_sample})

	def get_samples(self):
		return self.sess.execute(samples.select().limit(self.limit_samples))
	
	def get_sample(self, sha256):
		return self.sess.execute(samples.select().where(samples.c.sha256 == sha256))
	
print("DB Setup done")
