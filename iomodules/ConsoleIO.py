#!/usr/bin/env python
# -*- coding: utf8 -*-
# ConsoleIO - print sensor data to the screen as used in PyConsole.
# Copyright (C) 2018  John Snowdon
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Standard libraries
import multiprocessing
import time
import timeit 

# Settings file
from libs import settings

# Start a new logger
from libs.newlog import newlog
logger = newlog(__name__)

def ConsoleIO(ecudata, controlQueue):
	""" Console IO - a poor mans digital dashboard! 
	Seriously, all we are doing here is printing out the 
	sensor values :) """
	
	while True:
		logger.debug("Waking")
		
		print("*========================================*")
		print("| PyCosworth Digital Dashboard :)        |")
		print("|----------------------------------------|")
		print("| RPM: %4srpm |  Boost: %4smbar        |" % (ecudata.data['RPM'], ecudata.data['MAP']))
		print("| ECT: %4s°c  |  TPS:    %3s%%           |" % (ecudata.data['ECT'], ecudata.data['TPS']))
		print("| ACT: %4s°c  |  CO:     %3s            |" % (ecudata.data['ACT'], ecudata.data['CO']))
		print("| 12v: %4sv   |                         |" % (ecudata.data['BAT']))
		print("*----------------------------------------*")
		
		errors = ecudata.get_errors()
		print("| Errors: %s errors recorded              |" % len(errors))
		if len(errors) > 0:
			for e in errors:
				print("| Error: %10s             |" % e)
		
		print("*----------------------------------------*")
		print("| Sample Count:   %6s                 |" % (ecudata.get_counter()))
		print("| Last Sample : %4fms               |" % (ecudata.get_timer()))
		print("*========================================*")

		time.sleep(2)
		#print("\033[H\033[J")
		