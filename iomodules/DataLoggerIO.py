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
import os
import re

# Controldata messages
from libs.ControlData import ControlData

# Settings file
from libs import settings

# Start a new logger
from libs.newlog import newlog
logger = newlog(__name__)

def getNextLogfile():
	""" Find the next free logfile name. """
	
	reMatch = '%s[0-9][0-9][0-9]%s' % (settings.LOGGING_FILE_PREFIX, settings.LOGGING_FILE_SUFFIX)
	currentFilenames = [f for f in os.listdir(settings.LOGGING_DIR + "/") if re.match(r'%s' % reMatch, f)]
	
	if len(currentFilenames) == 0:
		nextFilename = settings.LOGGING_FILE_PREFIX + "000" + settings.LOGGING_FILE_SUFFIX
	else:
		currentFilenames.sort()
		# Latest file
		latestFilename = currentFilenames[-1]
		# Latest file number
		latestFilenumber = latestFilename.split("_")[1].split(settings.LOGGING_FILE_SUFFIX)[0]
		# Increment file number
		nextFilenumber = int(latestFilenumber) + 1
		# Construct filename
		nextFilenumberStr = "%03d" % nextFilenumber
		nextFilename = settings.LOGGING_FILE_PREFIX + str(nextFilenumberStr) + settings.LOGGING_FILE_SUFFIX
	return nextFilename

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
	f = False
	sensorIds = []
	previousSampleCount = -1
	while True:
		logger.debug("Waking")
		
		if logging:
			stats['sampleCount'] = ecudata.getCounter()
			
			if stats['sampleCount'] != previousSampleCount:
			
				# Get all sensor ids
				#sensorIds
				
				# get current sample counter
				# write line where all sensors == current sample counter
				t_now = time.time() - t_start
				line = str(stats['sampleCount']) + "," + str(t_now) + ","
				for sensorId in sensorIds:
					d = ecudata.getData(sensorId)
					if d is None:
						line = line + "0,"
					else:
						line = line + str(d) + ","
				f.write(line + "\n")
				# construct a line of text, each sensor value seperated by ","
				
				# check for free disk space
				# check if reaching a set limit of time/space

			previousSampleCount = stats['sampleCount']

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
						filename = getNextLogfile()
						stats['logfile'] = filename
						# open logfile
						try:
							f = open(settings.LOGGING_DIR + "/" + filename, 'w')
							header = "Counter,Time,"
							for sensorId in sensorIds:
								header = header + sensorId + ","
							header = header + "\n"
							f.write(header)
							t_start = time.time()
						except Exception as e:
							logger.error("Unable to open logfile")
							logger.error("%s" % e)
							f = False
			
				# Stop logging
				if cdata.button == settings.BUTTON_LOGGING_STOPPED:
					if logging != False:
						# stop
						logger.info("Stop logging")
						logging = False
						# send message to say stopped
						# close logfile
						if f:
							f.close()
						
		
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
			
		if logging is False:
			time.sleep(settings.LOGGING_SLEEP)
		else:
			time.sleep(0.005)