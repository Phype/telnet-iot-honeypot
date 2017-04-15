import socket
import struct
import ipaddress
import random

import bitarray # apt install python-bitarray
import hexdump # pip install hexdump

AF_PACKET = 17
AF_INET   = 2
ETH_P_ALL = 0x0300

IPPROTO_UDP  = 17
IPPROTO_TCP  = 6
IPPROTO_ICMP = 1
IPPROTO_RAW  = 255

ICMP_ECHOREPLY		= 0		# Echo Reply
ICMP_DEST_UNREACH	= 3		# Destination Unreachable
ICMP_SOURCE_QUENCH	= 4		# Source Quench
ICMP_REDIRECT		= 5		# Redirect (change route)
ICMP_ECHO			= 8		# Echo Request
ICMP_TIME_EXCEEDED	= 11	# Time Exceeded
ICMP_PARAMETERPROB	= 12	# Parameter Problem	
ICMP_TIMESTAMP		= 13	# Timestamp Request
ICMP_TIMESTAMPREPLY	= 14	# Timestamp Reply
ICMP_INFO_REQUEST	= 15	# Information Request
ICMP_INFO_REPLY		= 16	# Information Reply
ICMP_ADDRESS		= 17	# Address Mask Request

struct_ip4 = struct.Struct("!BBHHHBBHII")
def parse_ip4(pack):
	arr = struct_ip4.unpack(pack[:20])
	hdr = {
		"version"  : arr[0] >> 4,       # should be 4 ...
		"ihl"      : arr[0] & 0xF,
		"tos"      : arr[1],
		"tot_len"  : arr[2],
		"id"       : arr[3],
		"frag_off" : arr[4],
		"ttl"      : arr[5],
		"protcol"  : arr[6],
		"check"    : arr[7],
		"saddr"    : ipaddress.IPv4Address(arr[8]),
		"daddr"    : ipaddress.IPv4Address(arr[9])
	}
	hdr_len = hdr["ihl"] * 4
	return hdr, pack[hdr_len:]

def pack_ip4(hdr, data):
	tot_len = 20 + len(data)
	arr = (
		0x45, # version + ihl
		0, # tos
		tot_len,
		hdr["id"],
		0, # frag_off
		hdr["ttl"],
		hdr["protocol"],
		0, # CRC32
		int(hdr["saddr"]),
		int(hdr["daddr"])
	)
	pack = struct_ip4.pack(*arr) + data
	
	# TODO: compute CRC32
	return pack

struct_tcp = struct.Struct("!HHIIHHHH")
def parse_tcp(pack):
	arr = struct_tcp.unpack(pack[:20])
	hdr = {
		"source"   : arr[0],
		"dest"     : arr[1],
		"seq"      : arr[2],
		"ack_seq"  : arr[3],
		"flags"    : parse_tcp_flags(arr[4]),
		"window"   : arr[5],
		"check"    : arr[6],
		"urg_ptr"  : arr[7],
	}
	return hdr, pack[20:]

def parse_tcp_flags(flags):
	arr = bitarray.bitarray(endian='little')
	arr.frombytes(chr(flags & 0xFF))
	flags = {
		"fin" : arr[0],
		"syn" : arr[1],
		"rst" : arr[2],
		"psh" : arr[3],
		"ack" : arr[4],
		"urg" : arr[5],
		"ece" : arr[6],
		"cwr" : arr[7],
	}
	return flags

def pack_tcp_flags(flags_list):
	flags = {
		"fin" : False,
		"syn" : False,
		"rst" : False,
		"psh" : False,
		"ack" : False,
		"urg" : False,
		"ece" : False,
		"cwr" : False,
	}
	for f in flags_list:
		if f in flags:
			flags[f] = True
	arr = bitarray.bitarray(endian='little')
	arr.extend([
		flags["fin"],
		flags["syn"],
		flags["rst"],
		flags["psh"],
		flags["ack"],
		flags["urg"],
		flags["ece"],
		flags["cwr"]
	])
	
	# Hdr length: 0x5 * 4 = 20 bytes
	return 0x5000 | ord(arr.tobytes()[0])
	

def pack_tcp(hdr, data):
	arr = (
		hdr["source"],
		hdr["dest"],
		hdr["seq"],
		hdr["ack_seq"],
		pack_tcp_flags(hdr["flags"]),
		0, # window
		0, # check
		0  # urg_ptr
	)
	pack = struct_tcp.pack(*arr) + data
	
	# TODO: compute CRC32
	return pack

struct_tcp_stub = struct.Struct("!HHI")
def parse_tcp_stub(pack):
	arr = struct_tcp_stub.unpack(pack[:8])
	hdr = {
		"source"   : arr[0],
		"dest"     : arr[1],
		"seq"      : arr[2]
	}
	return hdr, pack[8:]

struct_udp = struct.Struct("!HHHH")
def parse_udp(pack):
	arr = struct_udp.unpack(pack[:8])
	hdr = {
		"source" : arr[0],
		"dest"   : arr[1],
		"len"    : arr[2],
		"check"  : arr[3],
	}
	return hdr, pack[8:]

struct_icmp = struct.Struct("!BBH")
def parse_icmp(pack):
	arr = struct_icmp.unpack(pack[:4])
	hdr = {
		"type"     : arr[0],
		"code"     : arr[1],
		"checksum" : arr[2]
	}
	return hdr, pack[8:]


class Netstack:
	def __init__(self):
		self.sock      = socket.socket(AF_PACKET, socket.SOCK_DGRAM, ETH_P_ALL)
		self.sock_send = socket.socket(AF_INET,   socket.SOCK_RAW,   IPPROTO_RAW)
		self.tcp_table = {}
		self.udp_table = {}
		
	def send(self, pack):
		self.sock_send.sendto(pack, ("192.168.2.1", 0))
	
	def recv(self):
		pack = self.sock.recv(2000)
		# hexdump.hexdump(pack)
		self.handle_ip4(pack)
		
	def register_tcp(self, port, handler):
		if port in self.tcp_table:
			raise IOError("Port is in use")
		self.tcp_table[port] = handler
		
	def register_udp(self, port, handler):
		if port in self.udp_table:
			raise IOError("Port is in use")
		self.udp_table[port] = handler
		
	###
		
	def handle_ip4(self, packet):
		hdr, data = parse_ip4(packet)
		
		if hdr["protcol"] == IPPROTO_ICMP:
			self.handle_icmp(hdr, data)
		if hdr["protcol"] == IPPROTO_TCP:
			self.handle_tcp(hdr, data)
		if hdr["protcol"] == IPPROTO_UDP:
			self.handle_udp(hdr, data)
	
	def handle_icmp(self, ip, packet):
		icmp, data = parse_icmp(packet)
		
		if icmp["type"] == ICMP_TIME_EXCEEDED:
			ip_org,  data_org = parse_ip4(data)
			
			if ip_org["protcol"] == IPPROTO_TCP:
				tcp_org, data_org = parse_tcp_stub(data_org)
				port = tcp_org["source"]
				if port in self.tcp_table:
					self.tcp_table[port].handle_icmp(ip, icmp, ip_org, tcp_org)
				
			if ip_org["protcol"] == IPPROTO_UDP:
				udp_org, data_org = parse_udp(data_org)
				port = udp_org["source"]
				if port in self.udp_table:
					self.udp_table[port].handle_icmp(ip, icmp, ip_org, udp_org)
		
		pass
	
	def handle_tcp(self, ip, packet):
		tcp, data = parse_tcp(packet)
		port = tcp["dest"]
		
		if port in self.tcp_table:
			self.tcp_table[port].handle_tcp(ip, tcp, data)
	
	def handle_udp(self, ip, packet):
		udp, data = parse_udp(packet)
		port = udp["dest"]
		
		if port in self.udp_table:
			self.udp_table[port].handle_udp(ip, udp, data)
	
class Tracer:
	def __init__(self, net):
		self.net  = net
		self.port = random.randint(16000, 32000)
		
		self.net.register_tcp(self.port, self)
		self.net.register_udp(self.port, self)
		
		self.ip = ipaddress.IPv4Address(u"192.168.2.192")
		
		print("New Tracer on Port " + str(self.port))
		
	def tcp_bare(self):
		ip_hdr = {
			"id"       : 0,
			"ttl"      : 255,
			"protocol" : IPPROTO_TCP,
			"saddr"    : self.ip,
			"daddr"    : self.ip
		}
		tcp_hdr = {
			"source"   : self.port,
			"dest"     : 0,
			"seq"      : 0,
			"ack_seq"  : 0,
			"flags"    : []
		}
		return ip_hdr, tcp_hdr
	
	def tcp_syn_ping(self, dst_ip, dst_port):
		ip, tcp = self.tcp_bare()
		ip["daddr"]  = dst_ip
		tcp["dest"]  = dst_port
		tcp["flags"] = ["syn"]
		return ip, tcp
	
	def trace(self, dst_ip, dst_port):
		ip, tcp = self.tcp_syn_ping(dst_ip, dst_port)

		for ttl in range(1,16):
			ip["ttl"]  = ttl
			ip["id"]   = 1000 * random.randint(1, 9) + ttl
			tcp["seq"] = 1000 * random.randint(1, 9) + ttl
			
			pack = pack_ip4(ip, pack_tcp(tcp, ""))
			self.net.send(pack)

	###
		
	def handle_icmp(self, ip, icmp, ip_org, tcp_or_udp_org):
		print "From " + str(ip["saddr"]) + ": ICMP   \t TTL: " + str(ip_org["id"] % 1000)
		
	def handle_udp(self, ip, udp, data):
		pass
	
	def handle_tcp(self, ip, tcp, data):
		if tcp["flags"]["syn"] and tcp["flags"]["ack"]:
			print "From " + str(ip["saddr"]) + ": SYN ACK \t TTL: " + str(tcp["ack_seq"] % 1000)
		elif tcp["flags"]["ack"]:
			print "From " + str(ip["saddr"]) + ": ACK     \t TTL: " + str(tcp["ack_seq"] % 1000)
		elif tcp["flags"]["rst"]:
			print "From " + str(ip["saddr"]) + ": RST     \t TTL: " + str(tcp["ack_seq"] % 1000)
		else:
			print "From " + str(ip["saddr"]) + ": WTF"
			print ip
			print tcp

n = Netstack()
t = Tracer(n)

t.trace(ipaddress.IPv4Address(u"79.220.252.230"), 443)

while True:
	n.recv()
