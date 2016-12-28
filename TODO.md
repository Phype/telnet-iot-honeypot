# Telnet IoT honeypot TODO

## Small

### clean up html/php frontend
### auto update Malware Scan Results from virustotal (done by virustotal_fill_db.py for now)

## Big

### Client/Server Modell

*Idea*
client (the real honeypot) runs as a telnet server (as now) but all conns and urls are just pushed do a db server, downloading and "analyzing" the binaries.

*PRO*
More servers than one possible (to increase the surface to catch connections)

*CONTRA*
I so not have more than one public IP, so multiple honeypots are useless + Multple IP's can be served via Firewall rules
