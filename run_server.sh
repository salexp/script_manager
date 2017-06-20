#!/bin/bash
pid=$(pgrep -f server_main.py)

if [ "$pid" != "" ]
then
	pkill -f server_main.py
fi

cd /home/stuart/script_manager
/usr/bin/python /home/stuart/script_manager/server_main.py -ip 0.0.0.0 -p 80 > /dev/null 2>&1  &
