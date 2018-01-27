#!/usr/bin/env python
# -*- coding: utf8 -*-
# DataLoggerIO - Logs ecu data to disk.
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

# Controldata messages
from libs.ControlData import ControlData

# Settings file
from libs import settings

# Start a new logger
from libs.newlog import newlog
logger = newlog(__name__)

def DataLoggerIO(ecudata, controlQueue, actionQueue):
	""" Logs ecu data to disk """
	
	myButtonId = settings.BUTTON_DEST_DATALOGGER
	
	logger.info("DataLoggerIO process now running")
	
	logging = False
	heartbeat_timer = timeit.default_timer()
	stats = {
		'status' 	: False,
		'logfile'	: "",
		'sampleCount' : 0,
	}
	sensorIds = []
	while True:
		logger.debug("Waking")
		
		if logging:
			stats['sampleCount'] = ecudata.getCounter()
		# Get all sensor ids
		# get current sample counter
		# write line where all sensors == current sample counter
		# construct a line of text, each sensor value seperated by ","
		
		# check for free disk space
		# check if reaching a set limit of time/space
		
		# Listen for control messages
		if controlQueue.empty() == False:
			cdata = controlQueue.get()
			if cdata.isMine(myButtonId):
				logger.info("Got a control message")
				cdata.show()
					
				# Start logging
				if cdata.button == settings.BUTTON_LOGGING_RUNNING:
					if logging != True:
						# start
						logger.info("Start logging")
						stats = {}
						logging = True
						sensorIds = ecudata.getSensorIds()
						sensorIds.sort()
						# send message to say started
						# find name of next logfile
						# open logfile
			
				# Stop logging
				if cdata.button == settings.BUTTON_LOGGING_STOPPED:
					if logging != False:
						# stop
						logger.info("Stop logging")
						logging = False
						# send message to say stopped
						# close logfile
						
		
		# Send heartbeat message indicating logging status
		if (timeit.default_timer() - heartbeat_timer) >= settings.LOGGING_HEARTBEAT_TIMER:
			logger.debug("Sending heartbeat - logging:%s" % logging)
			cdata = ControlData()
			cdata.button = settings.BUTTON_LOGGING_STATUS
			cdata.destination = settings.BUTTON_DEST_ALL
			stats['status'] = logging
			cdata.setPayload(data = stats)
			actionQueue.put(cdata)
			# Reset timer
			heartbeat_timer = timeit.default_timer()
			
		if logging:
			time.sleep(settings.LOGGING_ACTIVE_SLEEP)
		else:
			time.sleep(settings.LOGGING_SLEEP)