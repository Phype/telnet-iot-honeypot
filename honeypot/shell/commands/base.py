import sys
import traceback

from binary import run_binary

class Proc:
    procs = {}

    @staticmethod
    def register(name, obj):
        Proc.procs[name] = obj

    @staticmethod
    def get(name):
        if name in Proc.procs:
            return Proc.procs[name]
        else:
            return None

class StaticProc(Proc):
    def __init__(self, output, result=0):
        self.output = output
        self.result = result

    def run(self, env, args):
        env.write(self.output)
        return self.result

class FuncProc(Proc):
    def __init__(self, func):
        self.func = func

    def run(self, env, args):
        env.write(self.func(args))
        return 0

# Basic Procs

class Exec(Proc):

    def run(self, env, args):
        if len(args) == 0:
            return 0
        
        if args[0][0] == ">":
            name = "true"
        elif args[0].startswith("./"):
            fname = args[0][2:]
            fdata = env.readFile(fname)
            
            if fdata == None:
                env.write("sh: 1: ./" + fname + ": not found\n")
                return 1
            else:
                run_binary(fdata, fname, args[1:], env)
                return 0
        else:
            name = args[0]
            args = args[1:]

        # $path = /bin/
        if name.startswith("/bin/"):
            name = name[5:]

        if Proc.get(name):
            try:
                return Proc.get(name).run(env, args)
            except:
                traceback.print_exc()
                env.write("Segmention fault\n")
                return 1
        else:
            env.write(name + ": command not found\n")
            return 1

class BusyBox(Proc):

    def run(self, env, args):
        
        if len(args) == 0:
            env.write("""BusyBox v1.27.2 (Ubuntu 1:1.27.2-2ubuntu3) multi-call binary.
BusyBox is copyrighted by many authors between 1998-2015.
Licensed under GPLv2. See source distribution for detailed
copyright notices.

Usage: busybox [function [arguments]...]

Currently defined functions:
    """ + " ".join(Proc.procs.keys()) + "\n\n")
            return 0

        name = args[0]
        args = args[1:]
        if Proc.get(name):
            return Proc.get(name).run(env, args)
        else:
            env.write(name + ": applet not found\n")
            return 1

class Cat(Proc):
    
    def run(self, env, args):
        fname = args[0]
        string = env.readFile(fname)
        if string != None:
            env.write(string)
            return 0
        else:
            env.write("cat: " + fname + ": No such file or directory\n")
            return 1

class Echo(Proc):

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

    def run(self, env, args):
        if args[0] in env.listfiles():
            env.deleteFile(args[0])
            return 0
        else:
            env.write("rm: cannot remove '" + args[0] + "': No such file or directory\n")
            return 1

class Ls(Proc):

    def run(self, env, args):
        for f in env.listfiles().keys():
            env.write(f + "\n")
        return 0

class Dd(Proc):

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

Proc.register("cp",      Cp())
Proc.register("ls",      Ls())
Proc.register("cat",     Cat())
Proc.register("dd",      Dd())
Proc.register("rm",      Rm())
Proc.register("echo",    Echo())
Proc.register("busybox", BusyBox())
Proc.register("exec",    Exec())

Proc.register("cd",      StaticProc(""))
Proc.register("true",    StaticProc(""))
Proc.register("chmod",   StaticProc(""))
Proc.register("uname",   StaticProc(""))
Proc.register(":",       StaticProc(""))
Proc.register("ps",      StaticProc(
"""  PID TTY          TIME CMD
 6467 pts/0    00:00:00 sh
12013 pts/0    00:00:00 ps\n"""))

# Other files

from wget  import Wget
from shell import Shell

# tftp disabled
#from tftp import Tftp


