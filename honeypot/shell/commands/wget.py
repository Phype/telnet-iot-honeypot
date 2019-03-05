
import requests
import traceback
import datetime
import urlparse

from util.config import config

from base     import Proc

class Wget(Proc):

	def dl(self, env, url, path=None, echo=True):
		u = urlparse.urlparse(url)
		
		host  = u.hostname
		ip    = "127.0.0.1"
		port  = u.port if u.port else 80
		date  = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		
		if echo:
		    env.write("--"+date+"--  " + url + "\n")
		    env.write("Resolving " + host + " (" + host + ")... " + ip + "\n")
		    env.write("Connecting to  " + host + " (" + host + ")|" + ip + "|:" + str(port) + "...")
		    
		if path == None:
			path = url.split("/")[-1].strip()
		if path == "":
			path = "index.html"

		if config.get("fake_dl", optional=True, default=False):
			data = str(hash(url))
			info = ""
		else:
			hdr = { "User-Agent" : "Wget/1.15 (linux-gnu)" }
			r   = None
			try:
				r = requests.get(url, stream=True, timeout=5.0, headers=hdr)
				if echo:
					env.write(" connected\n")
					env.write("HTTP request sent, awaiting response... 200 OK\n")
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
			except requests.ConnectTimeout as e:
				data = None
				info = "Download failed"
				if echo:
					env.write(" failed: Connection timed out.\n")
					env.write("Giving up.\n\n")
			except requests.ConnectionError as e:
				data = None
				info = "Download failed"
				if echo:
					env.write(" failed: Connection refused.\n")
					env.write("Giving up.\n\n")
			except requests.ReadTimeout as e:
				data = None
				info = "Download failed"
				if echo:
					env.write(" failed: Read timeout.\n")
					env.write("Giving up.\n\n")
			except Exception as e:
				data = None
				info = "Download failed"
				if echo:
					env.write(" failed: " + str(e.message) + ".\n")
					env.write("Giving up.\n\n")
				

		if data:
			env.writeFile(path, data)
		
		env.action("download", {
		    "url":  url,
		    "path": path,
		    "info": info,
		    "data": data
		})

	def run(self, env, args):
		if len(args) == 0:
		    env.write("""BusyBox v1.22.1 (Ubuntu 1:1.22.0-19ubuntu2) multi-call binary.

Usage: wget [-c|--continue] [-s|--spider] [-q|--quiet] [-O|--output-document FILE]
	[--header 'header: value'] [-Y|--proxy on/off] [-P DIR]
	[-U|--user-agent AGENT] URL...

Retrieve files via HTTP or FTP

	-s	Spider mode - only check file existence
	-c	Continue retrieval of aborted transfer
	-q	Quiet
	-P DIR	Save to DIR (default .)
	-O FILE	Save to FILE ('-' for stdout)
	-U STR	Use STR for User-Agent header
	-Y	Use proxy ('on' or 'off')

""")
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

Proc.register("wget", Wget())
