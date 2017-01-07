import hashlib
import array

# RFC 2104 HMAC

def do_hmac(key, data):
	return do_hash(do_xor(key, 0x5C) + do_hash(do_xor(key, 0x36) + data))

def do_xor(data, d):
	data = array.array('B', data)
	res  = array.array('B', " " * len(data))
	for i in range(len(data)):
		res[i] = data[i] ^ d
	return str(res)

def do_hash(data):
	h = hashlib.sha256()
	h.update(data)
	return h.hexdigest()
