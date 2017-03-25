# INSTALL

## Python packages

	struct socket traceback re sys random signal datetime
	os.path requests hashlib sqlite3 os time Queue threading

On ubuntu: (i think)

	apt install python-requests

## Virustotal integration

Please get yout own virustotal key,
since mine only allows for 4 API Req/min.

For how to do this, see https://www.virustotal.com/de/faq/#virustotal-api

When you got one, replace the Key in virustotal.py

	self.api_key    = "YOUR_KEY_HERE"
	
If you want to import virustotal reports of the collected samples,
run (may have to restart because of db locks)

	python virustotal_fill_db.py

## Html Frontend

 - Copy the html/ folder on a php-enabled webserver	
 - Create db.php with content (replace PATH TO SAMPLES.DB whereever your samples.db was created)

	<?PHP
	$sql = new SQLite3("PATH TO SAMPLES.DB");
	?>

 - Run the honeypot, the samples.db file should be created
 
## Run

	python main.py

