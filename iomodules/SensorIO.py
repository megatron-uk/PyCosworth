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
from iomodules.sensors.AEM import AEMSensors
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
	myButtonId = settings.BUTTON_DEST_SENSORIO
		
	# Initialise connection
	logger.info("Initialising Sensor IO")
	
	# Now we begin a continuous sample loop
	counter = 0
	
	# Load any additional sensor types here
	if settings.USE_COSWORTH:
		cosworth = CosworthSensors(ecuType = settings.COSWORTH_ECU_TYPE, pressureType = "mbar")
		cosworth_sensors = cosworth.available()
	else:
		cosworth = None
		cosworth_sensors = []
	
	if settings.USE_AEM:
		aem = AEMSensors()
		aem_sensors = aem.available()
	else:
		aem = None
		aem_sensors = []
	
	if settings.USE_SENSOR_DEMO:
		SENSOR_DEMO = True
		demo = DemoSensors()
		demo_sensors = demo.available()
	else:
		SENSOR_DEMO = False
		demo = None
		demo_sensors = []
	
	####################################################
	#
	# This loop runs forever, or until the process is
	# signalled to exit
	#
	####################################################
	logger.info("Sensor retrieval starting")
	
	for sensor in settings.SENSORS:
		sensorId = sensor['sensorId']
		sensorData = False			
		if sensorId in cosworth_sensors:
			sensorData = cosworth.sensor(sensorId, force = True)
			timerData = cosworth.performance(sensorId)
		if sensorId in aem_sensors:
			sensorData = aem.sensor(sensorId, force = True)
			timerData = aem.performance(sensorId)
		if SENSOR_DEMO:
			if (sensorData is False) and (sensorId in demo_sensors):
				sensorData = demo.sensor(sensorId, force = True)
				timerData = demo.performance(sensorId)
		if sensorData:
			receiveQueue.put((settings.TYPE_DATA, sensorData, 0, 0))
			
	while True:
		data_added = False
		####################################################
		#
		# Listen for control messages
		#
		####################################################
		if controlQueue.empty() == False:
			cdata = controlQueue.get()
			if cdata.isMine(myButtonId):
				logger.debug("Got a control message")
				cdata.show()
				# We only do one thing:
				# short press - turn on/off demo mode
				
				# Toggle demo mode
				if (cdata.button == settings.BUTTON_TOGGLE_DEMO):
					if SENSOR_DEMO:
						logger.info("Disable demo mode")
						SENSOR_DEMO = False
						demo = False
						demo_sensors = []
						status = {
							'sourceId' : myButtonId,
							'demoMode' : True
						}
						receiveQueue.put((settings.TYPE_STATUS, status, counter, None))
					elif SENSOR_DEMO is False:
						logger.info("Enable demo mode")
						SENSOR_DEMO = True
						demo = DemoSensors()
						demo_sensors = demo.available()
						status = {
							'sourceId' : myButtonId,
							'demoMode' : True
						}
						receiveQueue.put((settings.TYPE_STATUS, status, counter, None))

						
				# Reset Cosworth ecu comms
				if (settings.USE_COSWORTH) and (cdata.button == settings.BUTTON_RESET_COSWORTH_ECU):
					logger.info("Resetting Cosworth ECU serial connection")
					cosworth.__reconnectECU__()
					cosworth_sensors = cosworth.available()
		
		####################################################
		#
		# Standard loop - do a read of sensors defined in
		# the settings file.
		#
		####################################################
		for sensor in settings.SENSORS:
			
			sensorId = sensor['sensorId']
			sensorData = False
			
			# is demo mode disabled?
			if SENSOR_DEMO is False:
				# Is this a cosworth sensor?
				if sensorId in cosworth_sensors:
					sensorData = cosworth.sensor(sensorId)
					timerData = cosworth.performance(sensorId)
					
				# Is this a cosworth sensor?
				if sensorId in aem_sensors:
					sensorData = aem.sensor(sensorId)
					timerData = aem.performance(sensorId)
			else:
				# Otherwise read from the demo sensors, if demo mode is active
				if (sensorData is False) and (sensorId in demo_sensors):
					sensorData = demo.sensor(sensorId)
					timerData = demo.performance(sensorId)
			
			# Did we get any data for this sensor?
			if sensorData:
				if sensorData['value'] is not None:
					logger.debug("Received %s: value:%s counter:%s" % (sensorData['sensor']['sensorId'], sensorData['value'], counter))
					receiveQueue.put((settings.TYPE_DATA, sensorData, counter, timerData['last']))
					data_added = True
				
		# Sleep at the end of each round so that we don't
		# consume too many processor cycles. May need to experiment
		# with this value for different platforms.
		time.sleep(settings.SENSOR_SLEEP_TIME)
		
		if data_added:
			counter += 1
