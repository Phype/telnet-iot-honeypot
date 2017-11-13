import os
import signal

from honeypot.telnet import Telnetd
from util.dbg import dbg

def signal_handler(signal, frame):
	dbg('Ctrl+C')
	srv.stop()

if not os.path.exists("samples"):
	os.makedirs("samples")

signal.signal(signal.SIGINT, signal_handler)

srv = Telnetd(2222)
srv.run()
