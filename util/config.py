import json

config = None

fp   = open("config.json", "rb")
data = fp.read()
fp.close()

config = json.loads(data)
