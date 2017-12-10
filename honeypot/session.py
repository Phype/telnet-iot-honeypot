
import re
import random
import time

from util.dbg import dbg

from sampledb_client import Sampledb
from sampledb_client import get_sample_db

# Gonna catch em all
ELF_BIN_ARM  = "\x7f\x45\x4c\x46\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x28\x00\x01\x00\x00\x00\xbc\x14\x01\x00\x34\x00\x00\x00\x54\x52\x00\x00\x02\x04\x00\x05\x34\x00\x20\x00\x09\x00\x28\x00\x1b\x00\x1a\x00"
ELF_BIN_X86  = "\x7f\x45\x4c\x46\x02\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x3e\x00\x01\x00\x00\x00\x8b\x18\x40\x00\x00\x00\x00\x00\x40\x00\x00\x00\x00\x00\x00\x00\x40\x73\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
ELF_BIN_MIPS = "\x7f\x45\x4c\x46\x01\x02\x01\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x08\x00\x00\x00\x01\x00\x40\x38\x30\x00\x00\x00\x34\x00\x00\x00\x00\x74\x00\x10\x05\x00\x34\x00\x20\x00\x08\x00\x00\x00\x00\x00\x00"
ELF_BIN_M68K = "\x7f\x45\x4c\x46\x01\x02\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x04\x00\x00\x00\x01\x80\x00\x03\x46\x00\x00\x00\x34\x00\x00\x04\x64\x00\x00\x00\x00\x00\x34\x00\x20\x00\x03\x00\x28\x00\x05\x00\x04"
ELF_BIN_MPSL = "\x7f\x45\x4c\x46\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x08\x00\x01\x00\x00\x00\xe4\x04\x40\x00\x34\x00\x00\x00\xd8\x06\x00\x00\x07\x10\x00\x00\x34\x00\x20\x00\x03\x00\x28\x00\x07\x00\x06\x00"
ELF_BIN_PPC  = "\x7f\x45\x4c\x46\x01\x02\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x14\x00\x00\x00\x01\x10\x00\x03\xc8\x00\x00\x00\x34\x00\x00\x05\xa4\x00\x00\x00\x00\x00\x34\x00\x20\x00\x02\x00\x28\x00\x04\x00\x03"
ELF_BIN_SH4  = "\x7f\x45\x4c\x46\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x2a\x00\x01\x00\x00\x00\x04\x03\x40\x00\x34\x00\x00\x00\xf4\x04\x00\x00\x18\x00\x00\x00\x34\x00\x20\x00\x02\x00\x28\x00\x04\x00\x03\x00"
ELF_BIN_SPC  = "\x7f\x45\x4c\x46\x01\x02\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x02\x00\x00\x00\x01\x00\x01\x03\x68\x00\x00\x00\x34\x00\x00\x04\x40\x00\x00\x00\x00\x00\x34\x00\x20\x00\x03\x00\x28\x00\x05\x00\x04"

sh_regex      = re.compile("(.* )*sh\\s*(;|$)")
nc_regex      = re.compile(".*nc\\s*(;|$)")
wget_regex    = re.compile(".*wget\\s*(;|$)")
dd_regex      = re.compile(".*dd bs=52 count=1 if=.s.*")
cat_regex     = re.compile(".*cat .s.*cp /bin/echo .s.*")
mount_regex   = re.compile(".*cat /proc/mounts.*")
elfcat_regex  = re.compile(".*cat (/bin/echo|/bin/busybox).*")
token_regex   = re.compile(".*/bin/busybox ([^;&<>]+).*")
downl_regex   = re.compile(".*wget (?:-[a-zA-Z] )?(http[^ ;><&]*).*")
tftp_regex    = re.compile(".*tftp ([^;&<>]+).*")
nc_dl_regex   = re.compile(".*nc ([^;&<>]+).*")
ftp_dl_regex  = re.compile(".*ftpget ([^;&<>]+).*")
echo_regex    = re.compile(".*echo -n?e '([^;&<>]+)'.*")

ELF_BINS = [ELF_BIN_ARM, ELF_BIN_X86, ELF_BIN_MIPS, ELF_BIN_MPSL]
			
class Session:
	def __init__(self, output, remote_addr):
		dbg("New Session")
		self.output      = output
		self.remote_addr = remote_addr
		self.samples     = get_sample_db()
		
		# Data gathered
		self.urls          = []
		self.date          = int(time.time())
		self.text_in       = ""
		self.text_out      = ""
		self.text_combined = ""
		self.user          = None
		self.password      = None

	def login(self, user, password):
		dbg("Session login: user=" + user + " password=" + password)
		self.user        = user
		self.password    = password

	def end(self):
		dbg("Session End")
		
		print(self.text_combined)
		print("URLS GATHARED: " + repr(self.urls))
		
		# Do not report non-login connections
		if self.user != None:
			self.samples.put_session(self)
	
	def getopt(self, args, switches=[]):
		res   = {}
		opts  = args.split(" ")
		i     = 0
		p     = 0
		named = None
		while i < len(opts):
			opt = opts[i]
			if opt[0] == '-':
				if not opt in switches:
					named = opt
				res[named] = True
			elif named != None:
				res[named] = opt
				named = None
			else:
				res[p] = opt
				p = p + 1
			i = i + 1
		return res

	def send_string(self, text):
		self.text_combined = self.text_combined + text
		self.text_out      = self.text_out + text
		self.output(text)

	def shell(self, l):
		self.text_combined = self.text_combined + " # " + l + "\n"
		self.text_in       = self.text_in + l + "\n"

		for cmd in l.split(";"):
			self.shell_sub(cmd)

	def shell_sub(self, l):
		matched = False
		
		if mount_regex.match(l):
			self.send_string("/dev/root /rom squashfs ro,relatime 0 0\r\nproc /proc proc rw,nosuid,nodev,noexec,noatime 0 0\r\nsysfs /sys sysfs rw,nosuid,nodev,noexec,noatime 0 0\r\ntmpfs /tmp tmpfs rw,nosuid,nodev,noatime 0 0\r\n/dev/mtdblock10 /overlay jffs2 rw,noatime 0 0\r\noverlayfs:/overlay / overlay rw,noatime,lowerdir=/,upperdir=/overlay/upper,workdir=/overlay/work 0 0\r\ntmpfs /dev tmpfs rw,nosuid,relatime,size=512k,mode=755 0 0\r\ndevpts /dev/pts devpts rw,nosuid,noexec,relatime,mode=600 0 0\r\ndebugfs /sys/kernel/debug debugfs rw,noatime 0 0\r\n")
			matched = True

		if nc_regex.match(l):
			self.send_string("BusyBox v1.24.2 () multi-call binary.\r\n\r\nUsage: nc [IPADDR PORT]\r\n\r\nOpen a pipe to IP:PORT\r\n")
			matched = True

		if sh_regex.match(l):
			self.send_string("\r\n\r\nBusyBox v1.24.2 () built-in shell (ash)\r\n\r\n")
			matched = True

		if wget_regex.match(l):
			self.send_string("wget: missing URL\r\nUsage: wget [OPTION]... [URL]...\r\n\r\nTry `wget --help' for more options.\r\n")
			matched = True

		if dd_regex.match(l) or elfcat_regex.match(l):
			# Select random binary header, so we get multiple samples
			bin = ELF_BINS[random.randint(0, len(ELF_BINS) - 1)]
			self.send_string(bin)
			self.send_string("41+0 records in\r\n1+0 records out\r\n")
			matched = True

		if cat_regex.match(l):
			self.send_string("cat: can't open '.s': No such file or directory\r\n")
			matched = True

		m = echo_regex.match(l)
		if m:
			bla = m.group(1).decode('string_escape')
			self.send_string(bla + "\r\n")
			matched = True

		m = downl_regex.match(l)
		if m:
			url = m.group(1)
			dbg("DOWNLOAD URL " + url)
			self.urls.append(url)
			matched = True
			
		m = tftp_regex.match(l)
		if m:
			opts = self.getopt(m.group(1), ["-g", "-p"])
			ip   = opts[0]
			port = opts[1] if 1 in opts else 69
			f    = opts["-r"]
			url = "tftp://" + str(ip) + ":" + str(port) + "/" + str(f)
			self.urls.append(url)
			matched = True
		
		m = nc_dl_regex.match(l)
		if m:
			opts = self.getopt(m.group(1), ["-l", "-ll"])
			ip   = opts[0]
			port = opts[1]
			self.urls.append("nc://" + ip + ":" + port)
			matched = True
		
		m = ftp_dl_regex.match(l)
		if m:
			opts = self.getopt(m.group(1), ["-c", "-v"])
			ip   = opts[0]
			port = opts["-p"] if "-p" in opts else "21"
			f    = opts[1]
			self.urls.append("ftp://" + ip + ":" + port + "/" + f)
			matched = True

		m = token_regex.match(l)
		if m and not(matched):
			token = m.group(1)
			self.send_string(token + ": applet not found\r\n")

