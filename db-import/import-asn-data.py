from backend.db import get_db, Sample, Connection, Url, ASN
from backend.additionalinfo import get_ip_info, get_url_info, get_asn_info

db   = get_db()
sess = db.sess

asn_cache = {}

urls = sess.query(Url).all()
for url in urls:
	if url.asn_id and not url.asn and not url.asn_id in asn_cache:
		asn_info = get_asn_info(url.asn_id)
		
		if asn_info:
			asn_obj = ASN(asn=url.asn_id, name=asn_info['name'], reg=asn_info['reg'], country=asn_info['country'])
			sess.add(asn_obj)
			print "Adding ASN " + str(url.asn_id) + " " + asn_info['name']
		
		asn_cache[url.asn_id] = True
		

conns = sess.query(Connection).all()
for conn in conns:
	if conn.asn_id and not conn.asn and not conn.asn_id in asn_cache:
		asn_info = get_asn_info(conn.asn_id)
		
		if asn_info:
			asn_obj = ASN(asn=conn.asn_id, name=asn_info['name'], reg=asn_info['reg'], country=asn_info['country'])
			sess.add(asn_obj)
			print "Adding ASN " + str(conn.asn_id) + " " + asn_info['name']
		
		asn_cache[conn.asn_id] = True

db.end()
