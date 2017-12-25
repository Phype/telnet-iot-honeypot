import shellgrammar
import sys
import traceback
import requests

ELF_BIN_ARM  = "\x7f\x45\x4c\x46\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x28\x00\x01\x00\x00\x00\xbc\x14\x01\x00\x34\x00\x00\x00\x54\x52\x00\x00\x02\x04\x00\x05\x34\x00\x20\x00\x09\x00\x28\x00\x1b\x00\x1a\x00"

procs = {}
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

def filter_ascii(string):
	string = ''.join(char for char in string if ord(char) < 128 and ord(char) > 32 or char in " ")
	return string

class Env:
    def __init__(self, output=sys.stdout.write):
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

class Proc:
    def __init__(self, name):
        self.register(name)

    def register(self, name):
        procs[name] = self

class StaticProc(Proc):
    def __init__(self, name, output, result=0):
        self.output = output
        self.result = result
        Proc.__init__(self, name)

    def run(self, env, args):
        env.write(self.output)
        return self.result

class FuncProc(Proc):
    def __init__(self, name, func):
        self.func = func
        Proc.__init__(self, name)

    def run(self, env, args):
        env.write(self.func(args))
        return 0

class BusyBox(Proc):
    def __init__(self):
        Proc.__init__(self, "busybox")

    def run(self, env, args):
        name = args[0]
        args = args[1:]
        if name in procs:
            return procs[name].run(env, args)
        else:
            env.write(name + ": applet not found\n")
            return 1

class Wget(Proc):
    def __init__(self):
        Proc.__init__(self, "wget")
    
    def dl(self, env, url, path=None, echo=True):
        host = "hostname.tld"
        ip   = "127.0.0.1"
        date = "2014-12-24 04:13:37"
        if echo:
            env.write("--"+date+"--  " + url + "\n")
            env.write("Resolving "+host+" ("+host+")... "+ip+"\n")
            env.write("Connecting to  "+host+" ("+host+")|"+ip+"|:80...")

        hdr = { "User-Agent" : "Wget/1.15 (linux-gnu)" }
        r = requests.get(url, stream=True, timeout=5.0, headers=hdr)

        if path == None:
            path = url.split("/")[-1].strip()
        if path == "":
            path = "index.html"

        if echo:
            env.write(" connected\nHTTP request sent, awaiting response... 200 OK\n")
            env.write("Length: unspecified [text/html]\n")
            env.write("Saving to: '"+path+"'\n\n")
            env.write("     0K .......... 7,18M=0,001s\n\n")
            env.write(date+" (7,18 MB/s) - '"+path+"' saved [11213]\n")

        data = ""
        for chunk in r.iter_content(chunk_size = 4096):
            data = data + chunk

        info = ""
        for his in r.history:
            info = info + "HTTP " + str(his.status_code) + "\n"
            for k,v in his.headers.iteritems():
                info = info + k + ": " + v + "\n"
                info = info + "\n"

        info = info + "HTTP " + str(r.status_code) + "\n"
        for k,v in r.headers.iteritems():
            info = info + k + ": " + v + "\n"

        env.writeFile(path, data)
        env.action("download", {
            "url":  url,
            "path": path,
            "info": info
        })

    def run(self, env, args):
        if len(args) == 0:
            env.write("""wget: missing URL
Usage: wget [OPTION]... [URL]...

Try `wget --help' for more options.\n""")
            return 1
        else:
            echo = True
            for arg in args:
                if arg == "-O":
                    echo = False
            for url in args:
                if url.startswith("http"):
                    self.dl(env, url, echo=echo)
            return 0

class Cat(Proc):
    def __init__(self):
        Proc.__init__(self, "cat")
    
    def run(self, env, args):
        fname = args[0]
        string = env.readFile(fname)
        if string != None:
            env.write(string)
            return 0
        else:
            env.write("cat: " + fname + ": No such file or directory\n")
            return 1

class Shell(Proc):
    def __init__(self):
        Proc.__init__(self, "sh")

    def run(self, env, args):
        if len(args) == 0:
            # env.write("Busybox built-in shell (ash)\n")
            return 0
        
        if args[0][0] == ">":
            name = "true"
        else:
            name = args[0]
            args = args[1:]

        # $path = /bin/
        if name.startswith("/bin/"):
            name = name[5:]

        if name in procs:
            try:
                return procs[name].run(env, args)
            except:
                traceback.print_exc()
                env.write("Segmention fault\n")
                return 1
        else:
            env.write(name + ": command not found\n")
            return 1

class Echo(Proc):
    def __init__(self):
        Proc.__init__(self, "echo")

    def run(self, env, args):
        opts = ""
        if args[0][0] == "-":
            opts = args[0][1:]
            args = args[1:]

        string = " ".join(args)
        if "e" in opts:
            string = string.decode('string_escape')

        env.write(string)

        if not("n" in opts):
            env.write("\n")

        return 0

class Rm(Proc):
    def __init__(self):
        Proc.__init__(self, "rm")

    def run(self, env, args):
        if args[0] in env.files:
            env.deleteFile(args[0])
            return 0
        else:
            env.write("rm: cannot remove '" + args[0] + "': No such file or directory\n")
            return 1

class Ls(Proc):
    def __init__(self):
        Proc.__init__(self, "ls")

    def run(self, env, args):
        for f in env.files:
            env.write(f + "\n")
        return 0

class Dd(Proc):
    def __init__(self):
        Proc.__init__(self, "dd")

    def run(self, env, args):
        infile  = None
        outfile = None
        count   = None
        bs      = 512
        for a in args:
            if a.startswith("if="):
                infile = a[3:]
            if a.startswith("of="):
                outfile = a[3:]
            if a.startswith("count="):
                count = int(a[6:])
            if a.startswith("bs="):
                bs = int(a[3:])
        
        if infile != None:
            data = env.readFile(infile)
            if count != None:
                data = data[0:(count*bs)]
            if outfile:
                env.deleteFile(infile)
                env.writeFile(infile, data)
            else:
                env.write(data)

        env.write("""0+0 records in
0+0 records out
0 bytes copied, 0 s, 0,0 kB/s\n""")
        return 0

class Cp(Proc):
    def __init__(self):
        Proc.__init__(self, "cp")

    def run(self, env, args):
        infile  = args[0]
        outfile = args[1]
        
        data = env.readFile(infile)
        if data != None:
            env.writeFile(outfile, data)
            return 0
        else:
            env.write("cp: cannot stat '" + infile + "': No such file or directory\n")
            return 1

shell = Shell()

BusyBox()
Wget()
Cat()
Echo()
Rm()
Ls()
Dd()
Cp()
StaticProc("cd", "")
StaticProc("true", "")
StaticProc("chmod", "")
StaticProc("uname", "Linux hostname 3.13.0-23-generic #12-Wub SMP Tue Mon 3 12:43:04 UTC 2014 x86 GNU/Linux\n")
StaticProc(">", "")
StaticProc(":", "")
StaticProc("ps",
"""  PID TTY          TIME CMD
 6467 pts/0    00:00:00 sh
12013 pts/0    00:00:00 ps\n""")

###

class Command:
    def __init__(self, args):
        self.args          = args
        self.redirect_from   = None
        self.redirect_to     = None
        self.redirect_append = False

    def run(self, env):
        if self.redirect_to != None:
            print "Redirect to: " + self.redirect_to + " , append=" + str(self.redirect_append)
            if not(self.redirect_append):
                env.deleteFile(self.redirect_to)
            env = RedirEnv(env, self.redirect_to)
        return shell.run(env, self.args)

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
        if isinstance(elements[1], shellgrammar.TreeNode):
            l = []    
        else:
            l = [ elements[1] ]
        for e in elements[2].elements:
            if not(isinstance(e.elements[1], shellgrammar.TreeNode)):
                l.append(e.elements[1])
                
        cmd = Command(l)
                
        # redirects
        for r in elements[4]:
            print r
        
            if r[0] == ">":
                cmd.redirect_to = r[1]
                cmd.redirect_append = False
            if r[0] == ">>":
                cmd.redirect_to = r[1]
                cmd.redirect_append = True
            if r[0] == "<":
                cmd.redirect_from = r[2]
        
        return cmd 

    def make_cmdop(self, input, start, end, elements):
        if isinstance(elements[2], shellgrammar.TreeNode):
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

def parse(string):
    return shellgrammar.parse(filter_ascii(string).strip(), actions=Actions())

if __name__ == "__main__":
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
        tree = parse(line)
        tree.run(env)
        sys.stdout.flush()

