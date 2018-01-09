import sys
import traceback

from grammar       import parse, TreeNode
from commands.base import Proc

def filter_ascii(string):
	string = ''.join(char for char in string if ord(char) < 128 and ord(char) > 32 or char in " ")
	return string

###

ELF_BIN_ARM  = "\x7f\x45\x4c\x46\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x28\x00\x01\x00\x00\x00\xbc\x14\x01\x00\x34\x00\x00\x00\x54\x52\x00\x00\x02\x04\x00\x05\x34\x00\x20\x00\x09\x00\x28\x00\x1b\x00\x1a\x00"

globalfiles = {
    "/proc/mounts": """/dev/root /rom squashfs ro,relatime 0 0
proc /proc proc rw,nosuid,nodev,noexec,noatime 0 0
sysfs /sys sysfs rw,nosuid,nodev,noexec,noatime 0 0
tmpfs /tmp tmpfs rw,nosuid,nodev,noatime 0 0
/dev/mtdblock10 /overlay jffs2 rw,noatime 0 0
overlayfs:/overlay / overlay rw,noatime,lowerdir=/,upperdir=/overlay/upper,workdir=/overlay/work 0 0
tmpfs /dev tmpfs rw,nosuid,relatime,size=512k,mode=755 0 0
devpts /dev/pts devpts rw,nosuid,noexec,relatime,mode=600 0 0
debugfs /sys/kernel/debug debugfs rw,noatime 0 0\n""",
    "/proc/cpuinfo": """processor       : 0
model name      : ARMv6-compatible processor rev 7 (v6l)
BogoMIPS        : 697.95
Features        : half thumb fastmult vfp edsp java tls 
CPU implementer : 0x41
CPU architecture: 7
CPU variant     : 0x0
CPU part        : 0xb76
CPU revision    : 7

Hardware        : BCM2835
Revision        : 000e
Serial          : 0000000000000000\n""",
    "/bin/echo": ELF_BIN_ARM,
    "/bin/busybox": ELF_BIN_ARM
}

def instantwrite(msg):
	sys.stdout.write(msg)
	sys.stdout.flush()

class Env:
	def __init__(self, output=instantwrite):
		self.files   = {}
		self.deleted = []
		self.events  = {}
		self.output  = output

	def write(self, string):
		self.output(string)

	def deleteFile(self, path):
		if path in self.files:
		    self.deleted.append((path, self.files[path]))
		    del self.files[path]

	def writeFile(self, path, string):
		if path in self.files:
		    self.files[path] += string
		else:
		    self.files[path] = string

	def readFile(self, path):
		if path in self.files:
		    return self.files[path]
		elif path in globalfiles:
		    return globalfiles[path]
		else:
		    return None

	def listen(self, event, handler):
		self.events[event] = handler

	def action(self, event, data):
		if event in self.events:
		    self.events[event](data)
		else:
		    print("WARNING: Event '" + event + "' not registered")

class RedirEnv:
	def __init__(self, baseenv, redir):
		self.baseenv = baseenv
		self.redir   = redir

	def write(self, string):
		self.baseenv.writeFile(self.redir, string)

	def deleteFile(self, path):
		self.baseenv.deleteFile(path)

	def writeFile(self, path, string):
		self.baseenv.writeFile(path, string)

	def readFile(self, path):
		self.baseenv.readFile(path)

	def listen(self, event, handler):
		self.baseenv.listen(event, handler)

	def action(self, event, data):
		self.baseenv.action(event, data)

class Command:
    def __init__(self, args):
        self.args          = args
        self.redirect_from   = None
        self.redirect_to     = None
        self.redirect_append = False
        self.shell           = Proc.get("sh")

    def run(self, env):
        if self.redirect_to != None:
            if not(self.redirect_append):
                env.deleteFile(self.redirect_to)
            env = RedirEnv(env, self.redirect_to)
        return self.shell.run(env, self.args)

    def __str__(self):
        return " ".join(self.args)

class CommandList:

    def __init__(self, mode, cmd1, cmd2):
        self.mode = mode
        self.cmd1 = cmd1
        self.cmd2 = cmd2

    def run(self, env):
        ret = self.cmd1.run(env)
        if (self.mode == "&&"):
            if (ret == 0):
                return self.cmd2.run(env)
            else:
                return ret
        if (self.mode == "||"):
            if (ret != 0):
                return self.cmd2.run(env)
            else:
                return ret
        if (self.mode == ";" or self.mode == "|"):
            return self.cmd2.run(env)

    def __str__(self):
        return "(" + str(self.cmd1) + self.mode + str(self.cmd2) + ")"

class Actions(object):
    def make_arg_noquot(self, input, start, end, elements):
	    return input[start:end]

    def make_arg_quot(self, input, start, end, elements):
        return elements[1].text

    def make_basecmd(self, input, start, end, elements):
        if isinstance(elements[1], TreeNode):
            l = []    
        else:
            l = [ elements[1] ]
        for e in elements[2].elements:
            if not(isinstance(e.elements[1], TreeNode)):
                l.append(e.elements[1])
                
        cmd = Command(l)
                
        # redirects
        for r in elements[4]:
            if r[0] == ">":
                cmd.redirect_to = r[1]
                cmd.redirect_append = False
            if r[0] == ">>":
                cmd.redirect_to = r[1]
                cmd.redirect_append = True
            if r[0] == "<":
                cmd.redirect_from = r[1]
        
        return cmd 

    def make_cmdop(self, input, start, end, elements):
        if isinstance(elements[2], TreeNode):
            return elements[0]
        else:
            return CommandList(elements[1].text, elements[0], elements[2])

    def make_cmdbrace(self, input, start, end, elements):
        return elements[3]

    def make_cmdlist(self, input, start, end, elements):
        if elements[1]:
            # Pipes not supported
            pass
        return elements[0]
        
    def make_redirect(self, input, start, end, elements):
        op  = elements[3].text
        arg = elements[7]
        return (op, arg)
        
    def make_redirects(self, input, start, end, elements):
        return elements

def run(string, env):
    return parse(filter_ascii(string).strip(), actions=Actions()).run(env)

def test_shell():
    env = Env()
    while True:
        sys.stdout.write(" # ")
        sys.stdout.flush()
        line = sys.stdin.readline()
        sys.stdout.write(line)
        if line == "":
            break
        if line == "\n":
            continue
        line = line[:-1] 
        tree = run(line, env)
        sys.stdout.flush()

