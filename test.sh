#!/bin/bash

HOST=localhost
PORT=2222
NCPORT=23456
EXIT=0
LOG=/tmp/telnet-iot-honeypot_test.log

function end() {
	kill $HTTPD
	kill $TFTPD
	kill $TELNET
	
	if [[ $EXIT != 0 ]]
	then
		echo ""
		echo "==================="
		echo ""
		echo "SOME TESTS FAILED"
		echo "See $LOG"
		echo ""
		tail -n 10 $LOG
	fi
	exit $EXIT
}

function fail() {
	echo "Test $1 failed"
	EXIT=1
	end
}

function test_conn() {
	r=$(echo "user
	pass
	wget" | nc $HOST $PORT)
	if [[ $r != *"options"* ]]
	then
		fail "test_conn"
	fi
	echo "test_conn OK"
}

function test_down_http() {
	r=$(echo "user
	pass
	wget http://127.0.0.1:8000/main.py" | nc $HOST $PORT)
	sleep 0.5
	r=$(ls samples/*_main.py)
	if [[ "$r" == "" ]]
	then
		fail "test_down_http"
	fi
	
	h1=$(sqlite3 samples.db "SELECT sha256 from samples WHERE name = \"main.py\"")
	h2=$(sha256sum -b main.py)
	
	if [[ "$h2" != *"$h1"* ]]
	then
		echo "Sha256 mismatch"
		echo $h1
		echo $h2
		fail "test_down_http"
	fi
	
	echo "test_down_http OK"
}

function test_down_tftp() {
	r=$(echo "user
	pass
	tftp -r virustotal.py -l lolwtf 127.0.0.1 8001" | nc $HOST $PORT)
	sleep 0.5
	r=$(ls samples/*_virustotal.py)
	if [[ "$r" == "" ]]
	then
		fail "test_down_tftp"
	fi
	
	h1=$(sqlite3 samples.db "SELECT sha256 from samples WHERE name = \"virustotal.py\"")
	h2=$(sha256sum -b virustotal.py)
	
	if [[ "$h2" != *"$h1"* ]]
	then
		echo "Sha256 mismatch"
		echo $h1
		echo $h2
		fail "test_down_tftp"
	fi
	
	echo "test_down_tftp OK"
}

# Reset everything
rm samples/* &>/dev/null
rm samples.db &>/dev/null

python2 main.py &>$LOG &
TELNET=$!

python -m SimpleHTTPServer &>/dev/null &
HTTPD=$!

python minitftp.py &>/dev/null &
TFTPD=$!

sleep 4

test_conn
test_down_http
test_down_tftp

end
