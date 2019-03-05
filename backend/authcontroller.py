import os
import hashlib
import traceback
import struct
import json
import time

import additionalinfo
import ipdb.ipdb

from sqlalchemy import desc, func, and_, or_
from decorator import decorator
from functools import wraps
from simpleeval import simple_eval
from argon2 import argon2_hash

from db import get_db, filter_ascii, Sample, Connection, Url, ASN, Tag, User, Network, Malware, IPRange, db_wrapper
from virustotal import Virustotal

from cuckoo import Cuckoo

from util.dbg import dbg
from util.config import config

from difflib import ndiff

class AuthController:

	def __init__(self):
		self.session = None
		self.salt    = config.get("backend_salt")
		self.checkInitializeDB()

	def pwhash(self, username, password):
		return argon2_hash(str(password), self.salt + str(username), buflen=32).encode("hex")

	@db_wrapper
	def checkInitializeDB(self):
		user = self.session.query(User).filter(User.id == 1).first()
		if user == None:
			admin_name = config.get("backend_user")
			admin_pass = config.get("backend_pass")

			print 'Creating admin user "' + admin_name + '" see config for password'
			self.addUser(admin_name, admin_pass, 1)

	@db_wrapper
	def getUser(self, username):
		user = self.session.query(User).filter(User.username == username).first()
		return user.json(depth=1) if user else None

	@db_wrapper
	def addUser(self, username, password, id=None):
		user = User(username=username, password=self.pwhash(username, password))
		if id != None:
			user.id = id
		self.session.add(user)
		return user.json()

	@db_wrapper
	def checkAdmin(self, user):
		user = self.session.query(User).filter(User.username == user).first()
		if user == None:
			return False
		return user.id == 1

	@db_wrapper
	def checkLogin(self, username, password):
		user = self.session.query(User).filter(User.username == username).first()
		if user == None:
			return False
		if self.pwhash(username, password) == user.password:
			return True
		else:
			return False
