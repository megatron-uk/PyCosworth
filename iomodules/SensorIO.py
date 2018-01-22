#!/usr/bin/env python

# SensorIO - retrieve engine sensor data from various sources: OBDII, Cosworth Pectel datastream, etc/
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
import sys
import os

# Sensor back end libraries
from iomodules.sensors.Cosworth import CosworthSensors
from iomodules.sensors.Demo import DemoSensors

# Settings file
from libs import settings
from libs.ControlData import ControlData

# Start a new logger
from libs.newlog import newlog
logger = newlog(__name__)

def SensorIO(transmitQueue, receiveQueue, controlQueue):
	""" Serial IO """
		
	proc_name = multiprocessing.current_process().name
	myButtonId = settings.BUTTON_DEST_SERIALIO
		
	# Initialise connection
	logger.info("Initialising Sensor IO")
	
	# Now we begin a continuous sample loop
	counter = 0
	
	
	# Load any additional sensor types here
	if settings.USE_COSWORTH:
		cosworth = CosworthSensors(ecuType = settings.COSWORTH_ECU_TYPE, pressureType = "mbar")
	else:
		cosworth = None
		
	if settings.USE_SENSOR_DEMO:
		SENSOR_DEMO = True
		demo = DemoSensors()
	else:
		SENSOR_DEMO = False
		demo = None
	
	####################################################
	#
	# This loop runs forever, or until the process is
	# signalled to exit
	#
	####################################################
	while True:
		
		####################################################
		#
		# Listen for control messages
		#
		####################################################
		if controlQueue.empty() == False:
			cdata = controlQueue.get()
			if cdata.isMine(myButtonId):
				logger.info("Got a control message")
				cdata.show()
				# We only do one thing:
				# short press - turn on/off demo mode
				
				# Toggle demo mode
				if (cdata.button) and (cdata.duration == settings.BUTTON_SHORT):
					if SENSOR_DEMO:
						demo = False
					else:
						demo = DemoSensors()			
		
		####################################################
		#
		# Standard loop - do a read of sensors defined in
		# the settings file.
		#
		####################################################
		for sensor in settings.SENSORS:
			
			sensorId = sensor['sensorId']
			valueData = False
			
			if cosworth:
				if sensorId in cosworth.available():
					valueData = cosworth.sensor(sensorId)
					sampleData = cosworth.performance(sensorId)
			else:
				valueData = False
				
			if valueData is False and demo:
				if sensorId in demo.available():
					valueData = demo.sensor(sensorId)
					sampleData = demo.performance(sensorId)
				else:
					logger.warn("No sensor modules available that match that sensor %s" % sensorId)
			
			if valueData:
				receiveQueue.put((settings.TYPE_DATA, sensor['sensorId'], valueData['value'], counter, sampleData['last']))
		
		# Sleep at the end of each round so that we don't
		# consume too many processor cycles. May need to experiment
		# with this value for different platforms.
		time.sleep(settings.SERIAL_SLEEP_TIME)