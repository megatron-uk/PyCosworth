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
	
	sleep_time = 5
	
	while True:
		logger.debug("Waking")
		
		print("*========================================*")
		print("| PyCosworth Digital Dashboard :every %ss|" % sleep_time)
		print("|----------------------------------------|")
		for sensorId in settings.SENSOR_IDS:
			sensorData = ecudata.getSensorData(sensorId = sensorId)
			sampleData = ecudata.getData(sensorId = sensorId, allData = True)
			
			if (sampleData is not None) and (sensorData is not None):
				print("| %12s: %5.1f %s	[%.4fms]" % (sensorData['classId'], sampleData[0], sensorData['sensorUnit'], sampleData[1]))
		
		print("*----------------------------------------*")
		print("| Sample Count:   %6s                 |" % (ecudata.getCounter()))
		print("*========================================*")
		
		time.sleep(sleep_time)
		