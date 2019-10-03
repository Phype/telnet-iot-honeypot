#!/bin/bash

if [ -f config.yaml ]; then
	echo -n "config.yaml already exists, delete it? (Y/n): "
	read force
	if [ "$force" = "Y" ] || [ "$force" = "y" ] || [ "$force" = "" ]; then
		rm config.yaml
	else
		echo aborting...
		exit 1
	fi
fi

if [ -f docker-compose.yml ]; then
	echo -n "docker-compose.yml already exists, delete it? (Y/n): "
	read force
	if [ "$force" = "Y" ] || [ "$force" = "y" ] || [ "$force" = "" ]; then
		rm docker-compose.yml
	else
		echo aborting...
		exit 1
	fi
fi

echo -n "DB: Use maria or sqlite? (maria/sqlite): "
read dbbackend
if [ "$dbbackend" != "maria" ] && [ "$dbbackend" != "sqlite" ]; then
	echo "$dbbackend is not valid"
	exit 1
fi

# Honeypot setup
echo " - Writing honeypot config"
user=admin
pass=$(openssl rand -hex 16)
salt=$(openssl rand -hex 16)
echo "backend_user: $user" >> config.yaml
echo "backend_pass: $pass" >> config.yaml
echo "backend_salt: $salt" >> config.yaml
echo "http_addr: \"0.0.0.0\"" >> config.yaml
echo "telnet_addr: \"0.0.0.0\"" >> config.yaml
echo "backend: \"http://backend:5000\"" >> config.yaml
echo "log_samples: True" >> config.yaml
echo "sample_dir: samples" >> config.yaml

# DB setup
if [ "$dbbackend" = "maria" ]; then
	dbpass=$(openssl rand -hex 16)
	sql="mysql+mysqldb://honey:$dbpass@honeydb/honey"
	echo sql: \"$sql\" >> config.yaml
fi

# docker-compose setup
echo " - Writing docker-compose.yml"
cat << EOF >> docker-compose.yml
version: "3.7"
services:
  honeypot:
    depends_on:
      - backend
    image: telnet-iot-honeypot:hot
    restart: always
    entrypoint:
      - python
      - honeypot.py
    ports:
      - "2323:2323"
    volumes:
      - "./samples:/usr/src/app/samples"
  backend:
    build: .
    image: telnet-iot-honeypot:hot
    restart: always
    entrypoint:
      - python
      - backend.py
    ports:
      - "5000:5000"
    volumes:
      - "./samples:/usr/src/app/samples"
EOF

if [ "$dbbackend" = "maria" ]; then
	cat << EOF >> docker-compose.yml
    depends_on:
      - honeydb
  honeydb:
    image: mariadb:latest
    restart: always
    environment:
      MYSQL_RANDOM_ROOT_PASSWORD: "yes"
      MYSQL_DATABASE: honey
      MYSQL_USER: honey
      MYSQL_PASSWORD: $dbpass
EOF
fi

echo -n "Start honeypot using docker-compose now? d = start using daemon flag (Y/n/d): "
read runit
if [ "$runit" = "d" ]; then
	sudo docker-compose up -d
elif [ "$runit" = "Y" ] || [ "$runit" = "y" ] || [ "$runit" = "" ]; then
	sudo docker-compose up
fi

