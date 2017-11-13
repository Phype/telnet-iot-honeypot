# INSTALL

Installation instructions for this branch are not available.
Server is a python flask app, while the client runs on its own, connecting to the Server app.

```
apt install python-pip libmysqlclient-dev python-mysqldb git
apt-get install mysql-server mysql-client -y
sudo mysql_secure_installation

git clone https://github.com/Phype/telnet-iot-honeypot.git

create database telhoney;
grant all privileges on telhoney.* to telhoney@localhost identified by "YOUR_PASSWORD";
flush privileges;

pip install setuptools flask sqlalchemy requests decorator dnspython ipaddress
```

## FrontEnd

```
sudo apt-get install apache2
cd telnet-iot-honeypot
mv html /var/www
sudo chown www-data:www-data /var/www -R
```

## Virustotal integration

Please get yout own virustotal key,
since mine only allows for 4 API Req/min.

For how to do this, see https://www.virustotal.com/de/faq/#virustotal-api

When you got one, replace the Key in virustotal.py

	self.api_key    = "YOUR_KEY_HERE"

If you want to import virustotal reports of the collected samples,
run (may have to restart because of db locks)

	python virustotal_fill_db.php

## Run

	python main.py
