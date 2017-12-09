# INSTALL

Install all requirements:

```
apt-get install python-pip libmysqlclient-dev python-mysqldb git
pip install setuptools flask sqlalchemy requests decorator dnspython ipaddress simpleeval

git clone https://github.com/Phype/telnet-iot-honeypot.git
```

If you watn to use mysql, create a mysql database. Default mysql max key length is 767 bytes,
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

The honeypot can run in two modes: local db and backend operated db (default in config.json).
If you want to use the frontend seen in the screenshots, you have to use the backend operated db mode.
The mode is set in the `config.json` file using the option `use_local_db`.

In local db mode, the honeypot will put all information into the database itself,
however since no backend server is running no frontend will be available.
If you have set `"use_local_db": true` and decide you want to use the backend,
just set `"use_local_db": false` (re-)start both backend and honeypot and the data
should now be available in the frontend.

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

You can also post the data to the test-backend running at http://phype.pythonanywhere.com/.
To do set the following options in `config.json`:

```
        "use_local_db": false,
        "backend": "https://phype.pythonanywhere.com/",
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

Start the honeypot like so:

	python honeypot.py
	
If you have set `use_local_db = false` in your config, start the backend:

	python backend.py

Now you can test the honeypot

    telnet 127.0.0.1 2222

