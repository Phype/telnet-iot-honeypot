import struct
import socket
import traceback
import re
import sys
import random
import signal

from dbg import dbg
from sampledb import Sampledb

# Gonna catch em all
ELF_BIN_ARM  = "\x7f\x45\x4c\x46\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x28\x00\x01\x00\x00\x00\xbc\x14\x01\x00\x34\x00\x00\x00\x54\x52\x00\x00\x02\x04\x00\x05\x34\x00\x20\x00\x09\x00\x28\x00\x1b\x00\x1a\x00"
ELF_BIN_X86  = "\x7f\x45\x4c\x46\x02\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x3e\x00\x01\x00\x00\x00\x8b\x18\x40\x00\x00\x00\x00\x00\x40\x00\x00\x00\x00\x00\x00\x00\x40\x73\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
ELF_BIN_MIPS = "\x7f\x45\x4c\x46\x01\x02\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x08\x00\x00\x00\x01\x00\x40\x38\x30\x00\x00\x00\x34\x00\x00\x00\x00\x74\x00\x10\x05\x00\x34\x00\x20\x00\x08\x00\x00\x00\x00\x00\x00"
ELF_BIN_M68K = "\x7f\x45\x4c\x46\x01\x02\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x04\x00\x00\x00\x01\x80\x00\x03\x46\x00\x00\x00\x34\x00\x00\x04\x64\x00\x00\x00\x00\x00\x34\x00\x20\x00\x03\x00\x28\x00\x05\x00\x04"
ELF_BIN_MPSL = "\x7f\x45\x4c\x46\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x08\x00\x01\x00\x00\x00\xe4\x04\x40\x00\x34\x00\x00\x00\xd8\x06\x00\x00\x07\x10\x00\x00\x34\x00\x20\x00\x03\x00\x28\x00\x07\x00\x06\x00"
ELF_BIN_PPC  = "\x7f\x45\x4c\x46\x01\x02\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x14\x00\x00\x00\x01\x10\x00\x03\xc8\x00\x00\x00\x34\x00\x00\x05\xa4\x00\x00\x00\x00\x00\x34\x00\x20\x00\x02\x00\x28\x00\x04\x00\x03"
ELF_BIN_SH4  = "\x7f\x45\x4c\x46\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x2a\x00\x01\x00\x00\x00\x04\x03\x40\x00\x34\x00\x00\x00\xf4\x04\x00\x00\x18\x00\x00\x00\x34\x00\x20\x00\x02\x00\x28\x00\x04\x00\x03\x00"
ELF_BIN_SPC  = "\x7f\x45\x4c\x46\x01\x02\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x02\x00\x00\x00\x01\x00\x01\x03\x68\x00\x00\x00\x34\x00\x00\x04\x40\x00\x00\x00\x00\x00\x34\x00\x20\x00\x03\x00\x28\x00\x05\x00\x04"

ELF_BINS = [ELF_BIN_ARM, ELF_BIN_X86, ELF_BIN_MIPS, ELF_BIN_M68K, ELF_BIN_MPSL, ELF_BIN_PPC, ELF_BIN_SH4, ELF_BIN_SPC]

class Telnetd:
	cmds   = {}
	cmds[240] = "SE   - subnegoation end"
	cmds[241] = "NOP  - no operation"
	cmds[242] = "DM   - data mark"
	cmds[243] = "BRK  - break"
	cmds[244] = "IP   - interrupt process"
	cmds[245] = "AO   - abort output"
	cmds[246] = "AYT  - are you there"
	cmds[247] = "EC   - erase char"
	cmds[248] = "EL   - erase line"
	cmds[249] = "GA   - go ahead"
	cmds[250] = "SB   - subnegotiation"
	cmds[251] = "WILL - positive return"
	cmds[252] = "WONT - negative return"
	cmds[253] = "DO   - set option"
	cmds[254] = "DONT - unset option"
	cmds[255] = "IAC  - interpret as command"

	SE   = 240
	NOP  = 241
	DM   = 242
	BRK  = 243
	IP   = 244
	AO   = 245
	AYT  = 246
	EC   = 247
	EL   = 248
	GA   = 249
	SB   = 250
	WILL = 251
	WONT = 252
	DO   = 253
	DONT = 254
	IAC  = 255

	# Options
	NAWS = 31

	def __init__(self, port):
		self.host    = "0.0.0.0"
		self.port    = port
		self.sock    = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.do_run  = True
		self.samples = Sampledb()
		self.samples.enable_vt()

	def run(self):
		self.sock.bind((self.host, self.port))
		self.sock.listen(10)
		dbg("Socket open on port " + str(self.port))
		while self.do_run:
			try:
				self.handle()
			except:
				traceback.print_exc()
			# ONLY HANDLE ONE CLIENT
			# self.stop()
		self.sock.close()
		dbg("Socket Closed")

	def handle(self):
		try:
			conn, addr = self.sock.accept()
			dbg("Client connected at " + str(addr))

			sess = TelnetSess(self, conn, addr)
			sess.loop()
		except EOFError:
			pass
		except:
			traceback.print_exc()

		conn.close()
		dbg("Client connection closed")

	def stop(self):
		self.do_run = False
		self.samples.stop()

class TelnetSess:

	def __init__(self, serv, sock, remote):
		self.serv    = serv
		self.sock    = sock
		self.timeout = 100.0
		self.text    = ""
		self.db_id   = 0
		self.remote  = remote

	def shell(self, l):
		sh_regex    = re.compile(".*sh\\s*(;|$)")
		nc_regex    = re.compile(".*nc\\s*(;|$)")
		wget_regex  = re.compile(".*wget\\s*(;|$)")
		dd_regex    = re.compile(".*dd bs=52 count=1 if=.s.*")
		cat_regex   = re.compile(".*cat .s.*cp /bin/echo .s.*")
		mount_regex = re.compile(".*cat /proc/mounts.*")
		elfcat_regex= re.compile(".*cat /bin/echo.*")
		token_regex = re.compile(".*/bin/busybox ([A-Z]+).*")
		downl_regex = re.compile(".*wget (?:-[a-zA-Z] )?(http[^ ;><&]*).*")
		tftp_regex  = re.compile(".*tftp ([^;&<>]+).*")

		if mount_regex.match(l):
			self.send_string("/dev/root /rom squashfs ro,relatime 0 0\r\nproc /proc proc rw,nosuid,nodev,noexec,noatime 0 0\r\nsysfs /sys sysfs rw,nosuid,nodev,noexec,noatime 0 0\r\ntmpfs /tmp tmpfs rw,nosuid,nodev,noatime 0 0\r\n/dev/mtdblock10 /overlay jffs2 rw,noatime 0 0\r\noverlayfs:/overlay / overlay rw,noatime,lowerdir=/,upperdir=/overlay/upper,workdir=/overlay/work 0 0\r\ntmpfs /dev tmpfs rw,nosuid,relatime,size=512k,mode=755 0 0\r\ndevpts /dev/pts devpts rw,nosuid,noexec,relatime,mode=600 0 0\r\ndebugfs /sys/kernel/debug debugfs rw,noatime 0 0\r\n")

		if nc_regex.match(l):
			self.send_string("BusyBox v1.24.2 () multi-call binary.\r\n\r\nUsage: nc [IPADDR PORT]\r\n\r\nOpen a pipe to IP:PORT\r\n")

		if sh_regex.match(l):
			self.send_string("\r\n\r\nBusyBox v1.24.2 () built-in shell (ash)\r\n\r\n")

		if wget_regex.match(l):
			self.send_string("Usage: wget [options] <URL>\r\nOptions:\r\n")

		if dd_regex.match(l) or elfcat_regex.match(l):
			# Select random binary header, so we get multiple samples
			bin = ELF_BINS[random.randint(0, len(ELF_BINS) - 1)]
			self.send_string(bin)
			self.send_string("41+0 records in\r\n1+0 records out")

		if cat_regex.match(l):
			self.send_string("cat: can't open '.s': No such file or directory")

		m = token_regex.match(l)
		if m:
			token = m.group(1)
			self.send_string(token + ": applet not found\r\n")

		m = downl_regex.match(l)
		if m:
			url = m.group(1)
			dbg("DOWNLOAD URL " + url)
			self.serv.samples.put_url(url, self.db_id)
			
		m = tftp_regex.match(l)
		if m:
			remote = []
			file   = None
			opts   = m.group(1).split(" ")
			i      = 0
			while i < len(opts):
				opt = opts[i]
				if opt[0] == '-':
					if opt == "-r":
						i = i + 1
						file = opts[i]
					if opt == "-l" or opt == "-b":
						i = i + 1
				else:
					remote.append(opt)
				i = i + 1
			url = "tftp://" + ":".join(remote) + "/" + str(file)
			dbg("DOWNLOAD URL " + url)
			self.serv.samples.put_url(url, self.db_id)

	def loop(self):
		dbg("New Session")
		dbg("Setting timeout to " + str(self.timeout) + " seconds")
		self.sock.settimeout(self.timeout)

		self.test_opt(1)

		#self.test_naws()
		#if self.test_opt(1, True):
		#	self.send_string("123\r\n")
		#	sefl.recv_string()
		#	self.test_opt(1, False)

		self.send_string("Hello. Hint: Try any username/password\r\n\r\nLogin: ")
		u = self.recv_line()
		self.send_string("Password: ")
		p = self.recv_line()

		self.db_id = self.serv.samples.put_conn(self.remote[0], u, p)
		self.send_string("\r\nWelcome to EmbyLinux 3.13.0-24-generic\r\n")

		dbg("USER " + u)
		dbg("PASS " + p)

		while True:
			self.send_string(" # ")
			l = self.recv_line()
			dbg(" # " + l)
			self.text = self.text + " # " + l + "\r\n"
			
			try:
				self.shell(l)
			except:
				traceback.print_exc()
				self.send_string("sh: error\r\n")

	def test_naws(self):
		dbg("TEST NAWS")
		if self.test_opt(Telnetd.NAWS):
			self.need(Telnetd.IAC)
			self.need(Telnetd.SB)
			self.need(Telnetd.NAWS)
			
			w = self.recv_short()
			h = self.recv_short()

			self.need(Telnetd.IAC)
			self.need(Telnetd.SE)

			dbg("TEST NAWS OK " + str(w) + "x" + str(h))
		elif byte == Telnetd.WONT:
			dgb("TEST NAWS FAILED")
		else:
			raise ValueError()

	def test_linemode(self):
		dbg("TEST LINEMODE")
		if self.test_opt(34):
			self.need(Telnetd.IAC)
			self.need(Telnetd.SE)

	def test_opt(self, opt, do=True):
		dbg("TEST " + str(opt))

		self.send(Telnetd.IAC)
		if do:
			self.send(Telnetd.DO)
		else:
			self.send(Telnetd.DONT)
		self.send(opt)

		#self.need(Telnetd.IAC)
		#byte = self.recv()
		#opt  = self.recv()
		#if byte == Telnetd.WILL:
		#	dbg("TEST OPT " + str(opt) + " TRUE")
		#	return True
		#elif byte == Telnetd.WONT:
		#	dbg("TEST OPT " + str(opt) + " FALSE")
		#	return False
		#else:
		#	raise ValueError()
	
	def send(self, byte):
		if byte in Telnetd.cmds:
			dbg("SEND " + str(Telnetd.cmds[byte]))
		else:
			dbg("SEND " + str(byte))
		self.sock.send(chr(byte))
	
	def send_string(self, msg):
		self.sock.send(msg)
		#dbg("SEND STRING LEN" + str(len(msg)))

	def recv(self):
		byte = self.sock.recv(1)
		if len(byte) == 0:
			raise EOFError
		byte = ord(byte)
		if byte in Telnetd.cmds:
			dbg("RECV " + str(Telnetd.cmds[byte]))
		else:
			pass
			#dbg("RECV " + str(byte))
		return byte

	def recv_line(self):
		line = ""
		while True:
			byte = self.recv()
			if byte == Telnetd.IAC:
				byte = self.recv()
				self.process_cmd(byte)
			elif byte == ord("\r"):
				pass
			elif byte == ord("\n"):
				break
			else:
				line = line + chr(byte)
		#dbg("RECV STRING " + line)
		return line

	def recv_short(self):
		bytes = self.sock.recv(2)
		short = struct.unpack("!H", bytes)[0]
		dbg("RECV SHORT " + str(short))
		return short

	def need(self, byte_need):
		byte = ord(self.sock.recv(1))
		if byte in Telnetd.cmds:
			dbg("RECV " + str(Telnetd.cmds[byte]))
		else:
			dbg("RECV " + str(byte))
		if byte != byte_need:
			dbg("BAD  " + "PROTOCOL ERROR. EXIT.")
			raise ValueError()
		return byte

	def process_cmd(self, cmd):
		if cmd == Telnetd.DO:
			byte = self.recv()
			self.send(Telnetd.IAC)
			self.send(Telnetd.WONT)
			self.send(byte)
		if cmd == Telnetd.WILL or cmd == Telnetd.WONT:
			byte = self.recv()

def signal_handler(signal, frame):
	dbg('Ctrl+C')
	srv.stop()

signal.signal(signal.SIGINT, signal_handler)

srv = Telnetd(2222)
srv.run()
