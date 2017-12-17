import json

config = None

class Config:
	def __init__(self):
		fp   = open("config.json", "rb")
		data = fp.read()
		fp.close()
		self.table = json.loads(data)

	def get(self, key):
		if key in self.table:
			return self.table[key]
		else:
			raise Exception("Option \""+ key +"\" not found in config")

config = Config()
