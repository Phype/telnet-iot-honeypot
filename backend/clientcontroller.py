import os
import hashlib
import traceback
import struct
import json
import time
import socket
import urlparse
import random

import additionalinfo
import ipdb.ipdb

from sqlalchemy import desc, func, and_, or_
from decorator import decorator
from functools import wraps
from simpleeval import simple_eval
from argon2 import argon2_hash

from db import get_db, filter_ascii, Sample, Connection, Url, ASN, Tag, User, Network, Malware, IPRange, db_wrapper
from virustotal import Virustotal

from cuckoo import Cuckoo

from util.dbg import dbg
from util.config import config

from difflib import ndiff

ANIMAL_NAMES = ["Boar","Stallion","Yak","Beaver","Salamander","Eagle Owl","Impala","Elephant","Chameleon","Argali","Lemur","Addax","Colt",
				"Whale","Dormouse","Budgerigar","Dugong","Squirrel","Okapi","Burro","Fish","Crocodile","Finch","Bison","Gazelle","Basilisk",
				"Puma","Rooster","Moose","Musk Deer","Thorny Devil","Gopher","Gnu","Panther","Porpoise","Lamb","Parakeet","Marmoset","Coati",
				"Alligator","Elk","Antelope","Kitten","Capybara","Mule","Mouse","Civet","Zebu","Horse","Bald Eagle","Raccoon","Pronghorn",
				"Parrot","Llama","Tapir","Duckbill Platypus","Cow","Ewe","Bighorn","Hedgehog","Crow","Mustang","Panda","Otter","Mare",
				"Goat","Dingo","Hog","Mongoose","Guanaco","Walrus","Springbok","Dog","Kangaroo","Badger","Fawn","Octopus","Buffalo","Doe",
				"Camel","Shrew","Lovebird","Gemsbok","Mink","Lynx","Wolverine","Fox","Gorilla","Silver Fox","Wolf","Ground Hog","Meerkat",
				"Pony","Highland Cow","Mynah Bird","Giraffe","Cougar","Eland","Ferret","Rhinoceros"]

# Controls Actions perfomed by Honeypot Clients
class ClientController:

	def __init__(self):
		self.session  = None
		if config.get("submit_to_vt"):
			self.vt = Virustotal(config.get("vt_key", optional=True))
		else:
			self.vt = None
		self.cuckoo   = Cuckoo(config)
		
		self.do_ip_to_asn_resolution = False
		self.ip2asn = config.get("ip_to_asn_resolution", optional=True, default=True)
		if self.ip2asn == "offline":
			self.do_ip_to_asn_resolution = True
			self.fill_db_ipranges()
		if self.ip2asn == "online":
			self.do_ip_to_asn_resolution = True

	@db_wrapper
	def _get_asn(self, asn_id):
		asn_obj = self.session.query(ASN).filter(ASN.asn == asn_id).first()
		
		if asn_obj:
			return asn_obj
		else:
			asn_info = additionalinfo.get_asn_info(asn_id)
			if asn_info:
				asn_obj = ASN(asn=asn_id, name=asn_info['name'], reg=asn_info['reg'], country=asn_info['country'])
				self.session.add(asn_obj)
				return asn_obj
			
		return None

	def calc_connhash_similiarity(self, h1, h2):
		l = min(len(h1), len(h2))
		r = 0
		for i in range(0, l):
			r += int(h1[i] != h2[i])

		if l == 0: return 0
		return float(r)/float(l)

	def calc_connhash(self, stream):
		output = ""
		for event in stream:
			if event["in"]:
				line  = event["data"]
				line  = line.strip()
				parts = line.split(" ")
				for part in parts:
					part_hash = chr(hash(part) % 0xFF)
					output += part_hash

		# Max db len is 256, half because of hex encoding
		return output[:120]

	@db_wrapper
	def fill_db_ipranges(self):		
		if self.session.query(IPRange.ip_min).count() != 0:
			return
		
		print "Filling IPRange Tables"
		
		asntable = ipdb.ipdb.get_asn()
		progress = 0
		
		for row in ipdb.ipdb.get_geo_iter():
			progress += 1
			if progress % 1000 == 0:
				self.session.commit()
				self.session.flush()
				print str(100.0 * float(row[0]) / 4294967296.0) + "% / " + str(100.0 * progress / 3315466) + "%" 
			
			ip = IPRange(ip_min = int(row[0]), ip_max=int(row[1]))
			
			ip.country   = row[2]
			ip.region    = row[4]
			ip.city      = row[5]
			ip.zipcode   = row[8]
			ip.timezone  = row[9]
			ip.latitude  = float(row[6])
			ip.longitude = float(row[7])
			
			asn_data = asntable.find_int(ip.ip_min)
			
			if asn_data:
				asn_id = int(asn_data[3])
				asn_db = self.session.query(ASN).filter(ASN.asn == asn_id).first()
				
				if asn_db == None:
					asn_db = ASN(asn = asn_id, name = asn_data[4], country=ip.country)
					self.session.add(asn_db)
				
				ip.asn = asn_db
				
				# Dont add session if we cannot find an asn for it
				self.session.add(ip)
		
		print "IPranges loaded"
		
	@db_wrapper
	def get_ip_range_offline(self, ip):
		ip_int = ipdb.ipdb.ipstr2int(ip)
		
		range = self.session.query(IPRange).filter(and_(IPRange.ip_min <= ip_int, 
			ip_int <= IPRange.ip_max)).first()
		
		return range

	def get_ip_range_online(self, ip):
		
		addinfo = additionalinfo.get_ip_info(ip)
		
		if addinfo:
		
			# TODO: Ugly hack
			range = type('',(object,),{})()
			
			range.country   = addinfo["country"]
			range.city      = "Unknown"
			range.latitude  = 0
			range.longitude = 0
			range.asn_id    = int(addinfo["asn"])
			range.asn       = self._get_asn(range.asn_id)
			range.cidr      = addinfo["ipblock"]
			
			return range
		
		else:
			
			return None

	def get_ip_range(self, ip):
		if self.ip2asn == "online":
			return self.get_ip_range_online(ip)
		else:
			return self.get_ip_range_offline(ip)
		
	def get_url_info(self, url):
		parsed = urlparse.urlparse(url)
		host   = parsed.netloc.split(':')[0]
		
		if host[0].isdigit():
			ip = host
		else:
			try:
				ip = socket.gethostbyname(host)
			except:
				return None
			
		range  = self.get_ip_range(ip)
		return ip, range
	
	@db_wrapper
	def do_housekeeping(self):
		
		for malware in self.session.query(Malware).all():
			malware.name = random.choice(ANIMAL_NAMES)
		
		# rebuild nb_firstconns
		if False:
			
			net_cache = {}
			
			for conn in self.session.query(Connection).all():
				if len(conn.conns_before) == 0:
					if conn.network_id in net_cache:
						net_cache[conn.network_id] += 1
					else:
						net_cache[conn.network_id] = 1
			
			for network in self.session.query(Network).all():
				if network.id in net_cache:
					network.nb_firstconns = net_cache[network.id]
				else:
					network.nb_firstconns = 0
					
				print "Net " + str(network.id) + ": " + str(network.nb_firstconns)
	
	@db_wrapper
	def put_session(self, session):
		
		connhash = self.calc_connhash(session["stream"]).encode("hex")
		
		backend_user = self.session.query(User).filter(
			User.username == session["backend_username"]).first()
		
		conn = Connection(ip=session["ip"], user=session["user"],
			date=session["date"], password=session["pass"],
			stream=json.dumps(session["stream"]),
			connhash=connhash, backend_user_id=backend_user.id)
		
		conn.user     = filter_ascii(conn.user)
		conn.password = filter_ascii(conn.password)
		
		if self.do_ip_to_asn_resolution:
			range = self.get_ip_range(conn.ip)
			if range:
				conn.country = range.country
				conn.city    = range.city
				conn.lat     = range.latitude
				conn.lon     = range.longitude
				conn.asn     = range.asn
		
		self.session.add(conn)
		self.session.flush() # to get id
		
		network_id = None
		
		samples = []
		urls    = []
		for sample_json in session["samples"]:
			# Ignore junk - may clean up the db a bit
			if sample_json["length"] < 2000:
				continue

			sample, url = self.create_url_sample(sample_json)
			
			if sample:
				if network_id == None and sample.network_id != None:
					network_id = sample.network_id
				samples.append(sample)
				
			if url:
				if network_id == None and url.network_id != None:
					network_id = url.network_id
				conn.urls.append(url)
				urls.append(url)

		# Find previous connections
		# A connection is associated when:
		#  - same honeypot/user
		#  - connection happened as long as 120s before
		#  - same client ip OR same username/password combo
		assoc_timediff        = 120
		assoc_timediff_sameip = 3600
		
		previous_conns = (self.session.query(Connection).
				filter(
				or_(
					and_(
						Connection.date > (conn.date - assoc_timediff),
						Connection.user == conn.user,
						Connection.password == conn.password
					),
					and_(
						Connection.date > (conn.date - assoc_timediff_sameip),
						Connection.ip == conn.ip
					)
				),
				Connection.backend_user_id == conn.backend_user_id,
				Connection.id != conn.id).all())

		for prev in previous_conns:
			if network_id == None and prev.network_id != None:
				network_id = prev.network_id
			conn.conns_before.append(prev)

		# Check connection against all tags
		tags = self.session.query(Tag).all()
		for tag in tags:
			json_obj = conn.json(depth = 0)
			json_obj["text_combined"] = filter_ascii(json_obj["text_combined"])
			if simple_eval(tag.code, names=json_obj) == True:
				self.db.link_conn_tag(conn.id, tag.id)

		# Only create new networks for connections with urls or associtaed conns,
		# to prevent the creation of thousands of networks
		# NOTE: only conns with network == NULL will get their network updated
		#       later so whe should only create a network where we cannot easily
		#       change it later
		if (len(conn.urls) > 0 or len(previous_conns) > 0) and network_id == None:
			network_id = self.create_network().id
		
		# Update network on self
		conn.network_id = network_id
		
		# Update network on all added Urls
		for url in urls:
			if url.network_id == None:
				url.network_id = network_id
				
		# Update network on all added Samples
		for sample in samples:
			if sample.network_id == None:
				sample.network_id = network_id
		
		# Update network on all previous connections withut one
		if network_id != None:
			for prev in previous_conns:
				if prev.network_id == None:
					prev.network_id = network_id
					
					# Update number of first conns on network
					if len(prev.conns_before) == 0:
						conn.network.nb_firstconns += 1
		
		self.session.flush()

		# Check for Malware type
		# 	only if our network exists AND has no malware associated
		if conn.network != None and conn.network.malware == None:
			# Find connections with similar connhash
			similar_conns = (self.session.query(Connection)
				.filter(func.length(Connection.connhash) == len(connhash))
				.all())

			min_sim  = 2
			min_conn = None
			for similar in similar_conns:
				if similar.network_id != None:
					c1  = connhash.decode("hex")
					c2  = similar.connhash.decode("hex")
					sim = self.calc_connhash_similiarity(c1, c2)
					if sim < min_sim and similar.network.malware != None:
						min_sim  = sim
						min_conn = similar

			# 0.9: 90% or more words in session are equal
			#	think this is probably the same kind of malware
			#	doesn't need to be the same botnet though!
			if min_sim < 0.9:
				conn.network.malware = min_conn.network.malware
			else:
				conn.network.malware = Malware()
				conn.network.malware.name = random.choice(ANIMAL_NAMES)
				
				self.session.add(conn.network.malware)
				self.session.flush()
		
		# Update network number of first connections
		if len(previous_conns) == 0 and conn.network_id != None:
			conn.network.nb_firstconns += 1

		return conn.json(depth=1)
		
	@db_wrapper
	def create_network(self):
		net = Network()
		self.session.add(net)
		self.session.flush()
		return net

	def create_url_sample(self, f):
		url = self.session.query(Url).filter(Url.url==f["url"]).first()
		if url == None:
			url_ip      = None
			url_asn     = None
			url_country = None
			
			if self.do_ip_to_asn_resolution:
				url_ip, url_range = self.get_url_info(f["url"])
				if url_range:
					url_asn     = url_range.asn_id
					url_country = url_range.country
			
			url = Url(url=f["url"], date=f["date"], ip=url_ip, asn_id=url_asn, country=url_country)
			self.session.add(url)
		
		if f["sha256"] != None:
			sample = self.session.query(Sample).filter(Sample.sha256 == f["sha256"]).first()
			if sample == None:
				result = None
				try:
					if self.vt != None:
						vtobj  = self.vt.query_hash_sha256(f["sha256"])
						if vtobj:
							result = str(vtobj["positives"]) + "/" + str(vtobj["total"]) + " " + self.vt.get_best_result(vtobj)
				except:
					pass

				sample = Sample(sha256=f["sha256"], name=f["name"], length=f["length"],
					date=f["date"], info=f["info"], result=result)
				self.session.add(sample)
		
			if sample.network_id != None and url.network_id == None:
				url.network_id = sample.network_id
		
			if sample.network_id == None and url.network_id != None:
				sample.network_id = url.network_id
		else:
			sample = None
		
		url.sample = sample
		
		return sample, url

	@db_wrapper
	def put_sample(self, data):
		sha256 = hashlib.sha256(data).hexdigest()
		self.db.put_sample_data(sha256, data)
		if config.get("cuckoo_enabled"):
			self.cuckoo.upload(os.path.join(config.get("sample_dir"), sha256), sha256)
		elif config.get("submit_to_vt"):
			self.vt.upload_file(os.path.join(config.get("sample_dir"), sha256), sha256)

	@db_wrapper
	def update_vt_result(self, sample_sha):
		sample = self.session.query(Sample).filter(Sample.sha256 == sample_sha).first()
		if sample:
			vtobj = self.vt.query_hash_sha256(sample_sha)
			if vtobj:
				sample.result = str(vtobj["positives"]) + "/" + str(vtobj["total"]) + " " + self.vt.get_best_result(vtobj)
				return sample.json(depth=1)
		return None

