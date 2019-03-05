#!/bin/bash

if [ -f config.yaml ]; then
	echo "config.yaml already exists, aborting"
	exit
fi

user=admin
pass=$(openssl rand -hex 16)
salt=$(openssl rand -hex 16)

echo "backend_user: $user" >> config.yaml
echo "backend_pass: $pass" >> config.yaml
echo "backend_salt: $salt" >> config.yaml

