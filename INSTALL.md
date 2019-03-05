# Installation

For installation instructions, go to section Manual installation.
However, if you just want to get everythig running, there is
also a Vagrantfile. See Section Vagrent for that.

# Vagrant

There is a Vagrantfile in the folder vagrant/ you can use to just make
a basic deployment with honeypot + backend + sqlite running.

Install vagrant and vagrant virtualbox porvider,
then go to vagrant folder and type `vagrant up`.
After a while the box should run a honeypot + backend available
via port-forwarding at `http://localhost:5000/` and `telnet://localhost:2223`.

# Manual installation
confirmed to work with Ubuntu 16.04.2 LTS

Install all requirements:

```
apt-get install -y python-pip libmysqlclient-dev python-mysqldb git sqlite3

git clone https://github.com/Phype/telnet-iot-honeypot.git
cd telnet-iot-honeypot
pip install -r requirements.txt
```

	sudo apt-get install python-setuptools python-werkzeug \
		python-flask python-flask-httpauth python-sqlalchemy \
		python-requests python-decorator python-dnspython \
		python-ipaddress python-simpleeval python-yaml

If you want to use mysql, create a mysql database. Default mysql max key length is 767 bytes,
so it is recommended to use latin1 charset, else the db setup will fail.

```
apt-get install mysql-server mysql-client
sudo mysql_secure_installation

mysql
CREATE DATABASE telhoney CHARACTER SET latin1 COLLATE latin1_swedish_ci;
grant all privileges on telhoney.* to telhoney@localhost identified by "YOUR_PASSWORD";
flush privileges;
```

## Configuration

This software consists of 2 components, a honeypot (client) and a backend (server).
The honeypot will accept incoming telnet connections and may download samples
which an adversary may try to download in the telnet session. When a session is
closed, the honeypot will post all data about the connection to the backend using
a REST-API.

The configuration for both honeypot and backend is in the files
`config.dist.yaml` and `config.yaml`. The `config.dist.yaml` contains the default
config. If you want to change anything, change or create overriding entries in
`config.yaml`. If you need documentation about the configuration,
the file `config.dist.yaml` contains some comments.

The REST-API requires authentification (HTTP Basic Auth).
When the backend is started for the first time,
it will create a "users" table in the database containing an "admin" user.
The admin users password is read from the configuration file.
If this file is empty, it will be created with random credentials.

*TL;DR*: The default config should just work, if you need the credentials for the
admin user, see the file `config.yaml`.

## Running

Create a config:

	bash create_config.sh

Start the backend:

	python backend.py

Now, start the honeypot:

	python honeypot.py

Now, you can test the honeypot

    telnet 127.0.0.1 2223

## HTML Frontend

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

When you got one, put it in your config.yamland enable virustotal integration:

	vt_key: "GET_YOUR_OWN"
    submit_to_vt: true

If you want to import virustotal reports of the collected samples,
run (may have to restart because of db locks). *TODO*: test if this still works

	python virustotal_fill_db.php

