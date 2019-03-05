
import csv
import ipaddress
import struct
import os

def ipstr2int(ip):
	ip = unicode(ip)
	ip = ipaddress.IPv4Address(ip).packed
	ip = struct.unpack("!I", ip)[0]
	return ip

class Entry:
	def __init__(self, start, end, value):
		self.start = int(start)
		self.end   = int(end)
		self.value = value

class IPTable:
	def __init__(self, fname):
		self.tzlist = []
		iplocfile = os.path.join(os.path.dirname(__file__), fname)
		with open(iplocfile, "rb") as ipcsv:
			reader = csv.reader(ipcsv, delimiter=',', quotechar='"')
			for row in reader:
				e = Entry(row[0], row[1], row)
				self.tzlist.append(e)

	def find_i(self, ip, start, end):
		if end - start < 100:
			for i in range(start, end):
				obj = self.tzlist[i]
				if obj.start <= ip and ip <= obj.end:
					return obj.value
			return None
		else:
			mid = start + (end - start) / 2
			val = self.tzlist[mid].start
			if ip < val:   return self.find_i(ip, start, mid)
			elif ip > val: return self.find_i(ip, mid, end)
			else:          return self.tzlist[mid].value
		
	def __iter__(self):
		return self.tzlist.__iter__()
	
	def find_int(self, ip):
		return self.find_i(ip, 0, len(self.tzlist) - 1)

	def find(self, ip):
		return self.find_i(ipstr2int(ip), 0, len(self.tzlist) - 1)

def get_geo():
	return IPTable("IP2LOCATION-LITE-DB11.CSV")

def get_asn():
	return IPTable("IP2LOCATION-LITE-ASN.CSV")

def get_geo_iter():
	iplocfile = os.path.join(os.path.dirname(__file__), "IP2LOCATION-LITE-DB11.CSV")
	fp = open(iplocfile, "rb")
	return csv.reader(fp, delimiter=',', quotechar='"')

class IPDB:
	def __init__(self):
		self.geo = get_geo()
		self.asn = get_asn()
		
	def find(self, ip):
		geo = self.geo.find(ip)
		asn = self.asn.find(ip)
		
		if geo != None and asn != None:
			r = {}
			r["asn"]      = int(asn[3])
			r["ipblock"]  = asn[2]
			r["country"]  = geo[2]
			r["region"]   = geo[4]
			r["city"]     = geo[5]
			r["zip"]      = geo[8]
			r["lon"]      = float(geo[7])
			r["lat"]      = float(geo[6])
			r["timezone"] = geo[9]
			return r
		else:
			return None

if __name__ == "__main__":
	db = IPDB()
	print db.find("217.81.94.77")


