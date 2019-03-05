from base import Proc

class Shell(Proc):
    
    def run(self, env, args):
        from honeypot.shell.shell import run
        
        if len(args) == 0:
            env.write("Busybox built-in shell (ash)\n")
            return 0
        
        fname = args[0]
        contents = env.readFile(fname)
        
        if contents == None:
            env.write("sh: 0: Can't open " + fname)
            return 1
        else:
            shell = Proc.get("exec")
            for line in contents.split("\n"):
                line = line.strip()
                line = line.split("#")[0]
                run(line, env)
            return 0

Proc.register("sh", Shell())
