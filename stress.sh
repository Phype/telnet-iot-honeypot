#!/bin/bash

FILE=/tmp/jshgslkgsfdjklhsdklflgj

while [ true ]
do
	echo user >$FILE
	echo pass >>$FILE
	echo system >>$FILE
	echo "wget http://127.0.0.1/kjsdfhjksdfhk_$((RANDOM))" >>$FILE

	nc 127.0.0.1 2222 <$FILE

	sleep 10
	echo sdfjldf
done
