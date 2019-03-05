import yaml
import random
import string

def rand():
	chars = string.ascii_uppercase + string.digits
	return ''.join(random.SystemRandom().choice(chars) for _ in range(32))

class Config:
	def __init__(self):
		self.distconfig = self.loadyaml("config.dist.yaml")
		try:
			self.userconfig = self.loadyaml("config.yaml")
		except:
			print "Warning: Cannot load config.yaml"
			self.userconfig = {}

	def loadyaml(self, filename):
		with open(filename, "rb") as fp:
			string = fp.read()
			return yaml.load(string)
		
	def loadUserConfig(self, filename):
		try:
			self.userconfig = self.loadyaml(filename)
		except:
			print "Warning: Cannot load " + str(filename)
	
	def get(self, key, optional=False, default=None):
		if key in self.userconfig:
			return self.userconfig[key]
		elif key in self.distconfig:
			return self.distconfig[key]
		elif not(optional):
			raise Exception("Option \""+ key +"\" not found in config")
		else:
			return default

config = Config()

