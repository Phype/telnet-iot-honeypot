# INSTALL

Installation instructions for this branch are not available.
Server is a python flask app, while the client runs on its own, connecting to the Server app.

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

