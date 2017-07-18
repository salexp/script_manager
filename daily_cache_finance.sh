#!/bin/bash
cd /home/stuart/script_manager
/usr/bin/python /home/stuart/script_manager/script_manager.py cache_finance
/usr/bin/python /home/stuart/script_manager/script_manager.py -s intraday cache_finance
