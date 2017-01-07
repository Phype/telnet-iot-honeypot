import time
import sqlalchemy

from config import config
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy.sql import select, join, insert
from sqlalchemy.orm import sessionmaker, scoped_session

def now():
	return int(time.time())

metadata = MetaData()
samples = Table('samples', metadata,
	Column('id', Integer, primary_key=True),
	Column('sha256', String(32), unique=True),
	Column('date', Integer),
	Column('name', String(32)),
	Column('file', String(32)),
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
	Column('url', String(256), unique=True),
	Column('date', Integer),
	Column('sample', None, ForeignKey('samples.id')),
)

conns_urls = Table('conns_urls', metadata,
	Column('id_conn', None, ForeignKey('conns.id'), primary_key=True),
	Column('id_url', None, ForeignKey('urls.id'), primary_key=True),
)

class DB:
	eng = sqlalchemy.create_engine(config["sql"])
	metadata.create_all(eng)
	conn = scoped_session(sessionmaker(bind=eng))

	def close(self):
		self.conn.close()

	# INPUT
			
	def put_url(self, url, date = now()):
		ex_url = self.conn.execute(urls.select().where(urls.c.url == url)).fetchone()
		if ex_url:
			return ex_url["id"]
		else:
			return self.conn.execute(urls.insert().values(url=url, date=date, sample=None)).inserted_primary_key[0]

	def put_conn(self, ip, user, password, date = now()):
		return self.conn.execute(conns.insert().values((None, ip, date, user, password))).inserted_primary_key[0]
		
	def put_sample(self, sha256, name, file, length, date = now()):
		ex_sample = self.conn.execute(samples.select().where(samples.c.sha256 == sha256)).fetchone()
		if ex_sample:
			return ex_sample["id"]
		else:
			return self.conn.execute(samples.insert().values(sha256=sha256, date=date, name=name, file=file, length=length, result=None)).inserted_primary_key[0]
		
	def link_conn_url(self, id_conn, id_url):
		self.conn.execute(conns_urls.insert().values(id_conn=id_conn, id_url=id_url))
		
	def link_url_sample(self, id_url, id_sample):
		self.conn.execute(urls.update().where(urls.c.id == id_url).values(sample=id_sample))

	# OUTPUT
	
	def get_samples(self):
		return self.conn.execute(samples.select())
