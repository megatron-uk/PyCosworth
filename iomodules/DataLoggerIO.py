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
	
	if os.path.exists(settings.LOGGING_DIR):
		logger.info("Log directory [%s] already exists" % settings.LOGGING_DIR)
		pass
	else:
		logger.info("Log directory [%s] is missing, creating..." % settings.LOGGING_DIR)
		os.mkdir(settings.LOGGING_DIR, mode=0o775)
		logger.info("Done")
	
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

def DataLoggerIO(ecudata, dataQueue, controlQueue):
	""" Logs ecu data to disk """
	
	myButtonId = settings.BUTTON_DEST_DATALOGGER
	
	logger.info("DataLoggerIO process now running")
	
	logging = False
	heartbeat_timer = timeit.default_timer()
	stats = {
		'status' 	: False,
		'description' : "Logger stopped."
	}
	f = False
	sensorIds = []
	previousSampleCount = -1
	while True:
		logger.debug("Waking")
		
		if logging:
			stats['sampleCount'] = ecudata.getCounter()
			
			if stats['sampleCount'] != previousSampleCount:
			
				# Write counter sample number and time from start of log file
				t_now = time.time() - t_start
				line = "%s,%.3f," % (stats['sampleCount'], t_now)
				
				# Write a line containing the value of every sensor
				for sensorId in sensorIds:
					d = ecudata.getData(sensorId)
					if d is None:
						line = line + "0,"
					else:
						line = line + str(d) + ","
				f.write(line + "\n")
				
				# check for free disk space
				# check if reaching a set limit of time/space
				
			previousSampleCount = stats['sampleCount']
			
		# Listen for control messages
		if controlQueue.empty() == False:
			cdata = controlQueue.get()
			if cdata.isMine(myButtonId):
				logger.info("Got a control message")
												
				# toggle logging
				if cdata.button == settings.BUTTON_LOGGING_TOGGLE:
					if logging is True:
						# stop
						logger.info("Stop logging")
						logging = False
						stats = {
							'status' : False,
							'description' : "Logger stopped."
						}
						# send message to say stopped
						# close logfile
						if f:
							f.close()
					elif logging is False:
						# start
						logger.info("Start logging")
						stats = {
							'status' : True,
							'description' : "Logger started."
						}
						logging = True
						sensorIds = ecudata.getSensorIds()
						sensorIds.sort()
						# send message to say started
						# find name of next logfile
						filename = getNextLogfile()
						stats['logFile'] = filename
						# open logfile
						try:
							t_start = time.time()
							f = open(settings.LOGGING_DIR + "/" + filename, 'w')
							header = "Counter,Time,"
							for sensorId in sensorIds:
								header = header + sensorId + ","
							header = header + "\n"
							f.write(header)
						except Exception as e:
							logger.error("Unable to open logfile")
							logger.error("%s" % e)
							f = False
		
		# Send heartbeat message indicating logging status
		if (timeit.default_timer() - heartbeat_timer) >= settings.LOGGING_HEARTBEAT_TIMER:
			logger.debug("Sending heartbeat - logging:%s" % logging)
			cdata = ControlData()
			cdata.button = settings.BUTTON_LOGGING_STATUS
			cdata.destination = settings.BUTTON_DEST_GRAPHICSIO
			stats['status'] = logging
			if logging and f:
				f_stat = os.stat(settings.LOGGING_DIR + "/" + filename)
				stats['fileSize'] = f_stat.st_size / 1024 / 1024
			cdata.setPayload(data = stats)
			dataQueue.put(cdata)
			# Reset timer
			heartbeat_timer = timeit.default_timer()
			
		if logging is False:
			time.sleep(settings.LOGGING_SLEEP)
		else:
			time.sleep(settings.LOGGING_ACTIVE_SLEEP)