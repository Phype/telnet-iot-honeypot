# INSTALL

Installation instructions for this branch are not available.
Server is a python flask app, while the client runs on its own, connecting to the Server app.

```
apt-get install python-pip libmysqlclient-dev python-mysqldb git
apt-get install mysql-server mysql-client
pip install setuptools flask sqlalchemy requests decorator dnspython ipaddress
sudo mysql_secure_installation

git clone https://github.com/Phype/telnet-iot-honeypot.git

# Create a mysql database
# default mysql max key length is 767 bytes, so it is recommended to use latin1 charset
# else the db setup will fail
CREATE DATABASE telhoney CHARACTER SET latin1 COLLATE latin1_swedish_ci;
grant all privileges on telhoney.* to telhoney@localhost identified by "YOUR_PASSWORD";
flush privileges;
```

## Frontend

You can use the frontend by just opening the file html/index.html in your browser.
If you want to make the frontend publically available, deploy the html/ folder to you webserver,
or install one:

```
sudo apt-get install apache2
cd telnet-iot-honeypot
cp -R html /var/www
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

Start the honeypotl like so:

	python honeypot.py
	
If you have set `use_local_db = false` in your config, start the backend:

	python backend.py

