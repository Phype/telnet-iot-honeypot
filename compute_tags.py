from backend.db import filter_ascii, get_db, Sample, Connection, Url, ASN, Tag
from backend.additionalinfo import get_ip_info, get_url_info, get_asn_info
from simpleeval import simple_eval

db   = get_db()
sess = db.sess

tags = sess.query(Tag).all()
for tag in tags:
	count = 0
	print "Processing tag " + tag.name
	print "  " + tag.code

	conns = sess.query(Connection).all()
	for conn in conns:
		json_obj = conn.json()
		json_obj["text_combined"] = filter_ascii(json_obj["text_combined"])
		if simple_eval(tag.code, names=json_obj) == True:
			count += 1
			db.link_conn_tag(conn.id, tag.id)

	print "  Tag hit " + str(count) + " times"

db.end()

