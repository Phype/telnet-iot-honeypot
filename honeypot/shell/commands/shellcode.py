
from base     import Proc

class Shellcode():

	def run(self, data):
		dbg("Parsing stub downloader (" + str(len(data)) + " bytes)")

		socks  = []
		tuples = []
		pos    = 0
		while True:
			pos = data.find("\x02\x00", pos)
			if pos == -1: break
			
			sockaddr = data[pos:pos+8]
			sockaddr = struct.unpack(">HHBBBB", sockaddr)
			
			ip   = str(sockaddr[2]) + "." + str(sockaddr[3]) + "." + str(sockaddr[4]) + "." + str(sockaddr[5])
			port = sockaddr[1]		
			tuples.append((ip, port))
			pos += 8

		for addr in tuples:
			try:
				s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				s.settimeout(15)
				s.setblocking(0)
				s.connect_ex(addr)
				socks.append(s)
				dbg("Trying tcp://" + addr[0] + ":" + str(addr[1]))
			except:
				pass
		
		goodsocket = None
		data       = None
		url        = None
		while len(socks) > 0:
			read, a, b = select.select(socks, [], [], 15)
			if len(read) == 0: break
			for s in read:
				if s.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR) == 0:
					try:
						s.setblocking(1)
						data = s.recv(1024)
						goodsocket = s
						peer = s.getpeername()
						url  = "tcp://" + peer[0] + ":" + str(peer[1])
						dbg("Connected to " + url)
						break
					except:
						s.close()
						socks.remove(s)
				else:
					s.close()
					socks.remove(s)
			if goodsocket != None:
				break

		for s in socks:
			if s != goodsocket:
				s.close()
		
		if goodsocket == None:
			dbg("Could not connect to any addresses in binary.")
			return

		while True:
			r = goodsocket.recv(1024)
			if r != "":
				data += r
			else:
				break
		
		goodsocket.close()
		self.record.add_file(data, url=url)
