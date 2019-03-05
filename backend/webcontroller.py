import os
import hashlib
import traceback
import struct
import json
import time
import math

import additionalinfo
import ipdb.ipdb

from sqlalchemy import desc, func, and_, or_, not_
from functools import wraps
from simpleeval import simple_eval
from argon2 import argon2_hash

from db import get_db, filter_ascii, Sample, Connection, Url, ASN, Tag, User, Network, Malware, IPRange, db_wrapper, conns_conns
from virustotal import Virustotal

from cuckoo import Cuckoo

from util.dbg import dbg
from util.config import config

from difflib import ndiff

class WebController:

	def __init__(self):
		self.session  = None

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
	def get_networks(self):
		networks = self.session.query(Network).all()
		ret      = []
		for network in networks:
			if len(network.samples) > 0 and network.nb_firstconns >= 10:
				n   = network.json(depth = 0)
				# ips = set()
				# for connection in network.connections:
				# 	ips.add(connection.ip)
				# n["ips"] = list(ips)
				ret.append(n)
		return ret
	
	@db_wrapper
	def get_network(self, net_id):
		network  = self.session.query(Network).filter(Network.id == net_id).first()
		ret      = network.json()
		
		honeypots              = {}
		initialconnections     = filter(lambda connection: len(connection.conns_before) == 0, network.connections)
		ret["connectiontimes"] = map(lambda connection: connection.date, initialconnections)
		
		has_infected = set([])
		for connection in network.connections:
			if connection.backend_user.username in honeypots:
				honeypots[connection.backend_user.username] += 1
			else:
				honeypots[connection.backend_user.username] = 1

			for connection_before in connection.conns_before:
				if connection.ip != connection_before.ip:
					has_infected.add(("i:" + connection.ip, "i:" + connection_before.ip))

			for url in connection.urls:
				has_infected.add(("u:" + url.url, "i:" + connection.ip))		
				
				if url.sample:
					has_infected.add(("s:" + url.sample.sha256, "u:" + url.url))

		ret["has_infected"] = list(has_infected)
		ret["honeypots"]    = honeypots
		
		return ret
	
	@db_wrapper
	def get_network_history(self, not_before, not_after, network_id):
		granularity = float(3600 * 24) # 1 day
		timespan    = float(not_after - not_before)
		
		if timespan < 3600 * 24 * 2:
			granularity = float(3600) * 2
		
		conns = self.session.query(Connection.date)
		conns = conns.filter(Connection.network_id == network_id)
		conns = conns.filter(and_(not_before < Connection.date, Connection.date < not_after))
		
		# Filter out subsequent connections
		conns = conns.outerjoin(conns_conns, Connection.id == conns_conns.c.id_last)
		conns = conns.filter(conns_conns.c.id_last == None)
		
		ret = [0] * int(math.ceil(timespan / granularity))
		
		for i in range(len(ret)):
			ret[i] = [ not_before + i * granularity, 0 ]
		
		for date in conns.all():
			i = int((date[0] - not_before) / granularity)
			ret[i][1] += 1
			
		return ret
	
	@db_wrapper
	def get_biggest_networks_history(self, not_before, not_after):
		
		MAX_NETWORKS = 4
		
		n = self.session.query(Connection.network_id, func.count(Connection.network_id))
		n = n.filter(and_(not_before < Connection.date, Connection.date < not_after))
		
		# Filter out subsequent connections
		n = n.outerjoin(conns_conns, Connection.id == conns_conns.c.id_last)
		n = n.filter(conns_conns.c.id_last == None)
		
		n = n.group_by(Connection.network_id)
		n = n.order_by(func.count(Connection.network_id).desc())
		
		data = n.all()
		
		nb_networks = min(MAX_NETWORKS, len(data))
		
		r = [0] * nb_networks
		
		i = 0
		for net in data[:nb_networks]:
			
			network = self.session.query(Network).filter(Network.id == net[0]).first()
			
			if (network != None):
				r[i] = { "network": network.json(), "data": self.get_network_history(not_before, not_after, network.id) }
				i   += 1
		
		return r
	
	@db_wrapper
	def get_connection_locations(self, not_before, not_after, network_id = None):
		conns = self.session.query(Connection.lat, Connection.lon)
		
		conns = conns.filter(and_(not_before < Connection.date, Connection.date < not_after))
		
		if network_id:
			conns = conns.filter(Connection.network_id == network_id)
			
		conns = conns.all()
		
		return conns

	##
	
	@db_wrapper
	def get_malwares(self):
		malwares = self.session.query(Malware).all()
		return map(lambda m: m.json(), malwares)

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
			return None

	##
	
	@db_wrapper
	def connhash_tree_lines(self, lines, mincount):
		length     = 1 + lines * 4
		othercount = 0
		
		ret   = {}
		dbres = self.session.query(func.count(Connection.id),
			func.substr(Connection.connhash, 0, length).label("c"),
			Connection.stream, Connection.id).group_by("c").all()

		for c in dbres:
			count    = c[0]
			connhash = c[1]
			if count > mincount:
				ev_in = filter(lambda ev : ev["in"], json.loads(c[2]))

				if len(ev_in) >= lines:
					ret[connhash] = {
						"count": c[0],
						"connhash": connhash,
						"text": ev_in[lines-1]["data"],
						"childs": [],
						"sample_id": c[3]
					}
			else:
				othercount += count

		return ret

	@db_wrapper
	def connhash_tree(self, layers):
		tree  = self.connhash_tree_lines(1, 10)
		layer = tree

		for lines in range(2,layers+1):
			length = (lines-1) * 4
			new_layer = self.connhash_tree_lines(lines, 0)
			for connhash in new_layer:
				connhash_old = connhash[:length]
				if connhash_old in layer:
					parent = layer[connhash_old]
					parent["childs"].append(new_layer[connhash])
			layer = new_layer

		return tree
				
			
