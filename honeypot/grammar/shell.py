import shellgrammar
import sys
import traceback

procs = {}

ELF_BIN_ARM  = "\x7f\x45\x4c\x46\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x28\x00\x01\x00\x00\x00\xbc\x14\x01\x00\x34\x00\x00\x00\x54\x52\x00\x00\x02\x04\x00\x05\x34\x00\x20\x00\x09\x00\x28\x00\x1b\x00\x1a\x00"

class Env:
    def __init__(self, output=sys.stdout.write):
        self.files  = {}
        self.output = output

    def write(self, string):
        self.output(string)

    def deleteFile(self, path):
        if path in self.files:
            del self.files[path]

    def writeFile(self, path, string):
        if path in self.files:
            self.files[path] += string
        else:
            self.files[path] = string

    def readFile(self, path):
        if path in self.files:
            return self.files[path]
        else:
            return None

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
    
    def run(self, env, args):
        if len(args) == 0:
            env.write("""wget: missing URL
Usage: wget [OPTION]... [URL]...

Try `wget --help' for more options.\n""")
            return 1
        else:
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
        elif fname == "/proc/mounts":
            env.write("""/dev/root /rom squashfs ro,relatime 0 0
proc /proc proc rw,nosuid,nodev,noexec,noatime 0 0
sysfs /sys sysfs rw,nosuid,nodev,noexec,noatime 0 0
tmpfs /tmp tmpfs rw,nosuid,nodev,noatime 0 0
/dev/mtdblock10 /overlay jffs2 rw,noatime 0 0
overlayfs:/overlay / overlay rw,noatime,lowerdir=/,upperdir=/overlay/upper,workdir=/overlay/work 0 0
tmpfs /dev tmpfs rw,nosuid,relatime,size=512k,mode=755 0 0
devpts /dev/pts devpts rw,nosuid,noexec,relatime,mode=600 0 0
debugfs /sys/kernel/debug debugfs rw,noatime 0 0\n""")
            return 0
        elif fname == "/bin/echo" or fname == "/bin/busybox":
            env.write(ELF_BIN_ARM)
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

        name = args[0]
        args = args[1:]

        # $path = /bin/
        if name.startswith("/bin/"):
            name = name[5:]

        # Emultae redir
        write_to  = None
        read_from = None
        i = len(args) - 1
        while i >= 0:
            if args[i] == ">":
                write_to = args[i+1]
                args = args[0:i]
            elif args[i].startswith(">"):
                write_to = args[i][1:]
                args = args[0:i]
            elif args[i] == "<":
                read_from = args[i+1]
                args = args[0:i]
            elif args[i].startswith("<"):
                read_from = args[i][1:]
                args = args[0:i]
            i -= 1

        if write_to != None:
            env.deleteFile(write_to)
            env = RedirEnv(env, write_to)

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

class Rm(Proc):
    def __init__(self):
        Proc.__init__(self, "rm")

    def run(self, env, args):
        env.deleteFile(args[0])

class Ls(Proc):
    def __init__(self):
        Proc.__init__(self, "ls")

    def run(self, env, args):
        for f in env.files:
            env.write(f + "\n")

shell = Shell()

BusyBox()
Wget()
Cat()
Echo()
Rm()
Ls()
StaticProc("cp", "")
StaticProc("cd", "")
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
        self.args = args

    def run(self, env):
        shell.run(env, self.args)

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
        l = [ elements[1] ]
        for e in elements[2].elements:
            l.append(e.elements[1])
        return Command(l)

    def make_cmdop(self, input, start, end, elements):
        return CommandList(elements[1].text, elements[0], elements[2])

    def make_cmdbrace(self, input, start, end, elements):
        return elements[3]

    def make_cmdlist(self, input, start, end, elements):
        if elements[1]:
            # Pipes not supported
            pass
        return elements[0]

def parse(string):
    return shellgrammar.parse(string, actions=Actions())

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
        tree = shellgrammar.parse(line, actions=Actions())
        tree.run(env)
        sys.stdout.flush()

