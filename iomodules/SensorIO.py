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

def SensorIO(dataQueue, controlQueue):
	""" Serial IO """
		
	proc_name = multiprocessing.current_process().name
	myButtonId = settings.BUTTON_DEST_SENSORIO
		
	# Initialise connection
	logger.info("Initialising Sensor IO [id:%d]" % myButtonId)
	
	# Now we begin a continuous sample loop
	counter = 0
	
	IS_ECU_ERROR = False
	IS_AEM_ERROR = False
	
	# Load any cosworth sensor types here
	if settings.USE_COSWORTH:
		logger.info("Trying Cosworth ECU sensors...")
		cosworth = CosworthSensors(ecuType = settings.COSWORTH_ECU_TYPE, pressureType = "mbar")
		if cosworth.__is_connected__():
			cosworth_sensors = cosworth.available()
		else:
			logger.warn("Unable to initialise Cosworth ECU comms")
			cosworth_sensors = []
			IS_ECU_ERROR = True
	else:
		cosworth = None
		cosworth_sensors = []
	
	# Load any aem sensor types here
	if settings.USE_AEM:
		logger.info("Trying AEM Wideband AFR sensors...")
		aem = AEMSensors()
		if aem.__is_connected__():
			aem_sensors = aem.available()
		else:
			logger.warn("Unable to initialise AEM Wideband AFR comms")
			aem_sensors = []
			IS_AEM_ERROR = True
	else:
		aem = None
		aem_sensors = []
	
	# Load any demo sensor types here
	if settings.USE_SENSOR_DEMO:
		logger.info("Trying Demo sensors...")
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
			dataQueue.put((settings.TYPE_DATA, sensorData, 0, 0))
			
	heartbeat_timer = timeit.default_timer()
	timerData = {
		'last' : 0,
	}
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
				
				if cdata.button == settings.STATUS_SHUTDOWN:
					logger.critical("Shutting down")
					sys.exit(0)
				
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
						logger.debug("Confirming Demo mode disabled status")
						cdata = ControlData()
						cdata.button = settings.STATUS_DEMO_DISABLED
						cdata.destination = settings.BUTTON_DEST_GRAPHICSIO
						cdata.setPayload(data = {'status' : True, 'description' : "Demo mode has been disabled."})
						dataQueue.put((settings.TYPE_STATUS, cdata, counter, None))
					elif SENSOR_DEMO is False:
						logger.info("Enable demo mode")
						SENSOR_DEMO = True
						demo = DemoSensors()
						demo_sensors = demo.available()
						status = {
							'sourceId' : myButtonId,
							'demoMode' : True
						}
						logger.debug("Confirming Demo mode enabled status")
						cdata = ControlData()
						cdata.button = settings.STATUS_DEMO_ENABLED
						cdata.destination = settings.BUTTON_DEST_GRAPHICSIO
						cdata.setPayload(data = {'status' : True, 'description' : "Demo mode is enabled."})
						dataQueue.put((settings.TYPE_STATUS, cdata, counter, None))

						
				# Reset Cosworth ecu comms
				if (cdata.button == settings.BUTTON_RESET_ECU):
					if (settings.USE_COSWORTH):
						logger.info("Resetting Cosworth ECU serial connection")
						cosworth.__reconnectECU__()
						time.sleep(2)
						if cosworth.__is_connected__():
							cosworth_sensors = cosworth.available()
							IS_ECU_ERROR = False
						else:
							logger.warn("Unable to initialise Cosworth ECU comms")
							cosworth_sensors = []
							IS_ECU_ERROR = True
						
					# Reset AEM comms
					if (settings.USE_AEM):
						logger.info("Resetting AEM serial connection")
						aem.__reconnectECU__()
						time.sleep(2)
						if aem.__is_connected__():
							aem_sensors = aem.available()
							IS_AEM_ERROR = False
						else:
							logger.warn("Unable to initialise AEM comms")
							aem_sensors = []
							IS_AEM_ERROR = True
		
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
					dataQueue.put((settings.TYPE_DATA, sensorData, counter, timerData['last']))
					data_added = True
		
		# Send heartbeat message indicating ECU error status
		if (timeit.default_timer() - heartbeat_timer) >= settings.SENSOR_ERROR_HEARTBEAT_TIMER:
			if settings.USE_COSWORTH:
				if IS_ECU_ERROR:
					logger.debug("Sending Cosworth ECU error status")
					cdata = ControlData()
					cdata.button = settings.STATUS_ECU_ERROR
					cdata.destination = settings.BUTTON_DEST_GRAPHICSIO
					cdata.setPayload(data = {'status' : True, 'description' : "Cosworth ECU connection error."})
					dataQueue.put((settings.TYPE_STATUS, cdata, counter, timerData['last']))
				else:
					logger.debug("Sending Cosworth ECU okay status")
					cdata = ControlData()
					cdata.button = settings.STATUS_ECU_OK
					cdata.destination = settings.BUTTON_DEST_GRAPHICSIO
					cdata.setPayload(data = {'status' : False, 'description' : "Cosworth ECU connected okay."})
					dataQueue.put((settings.TYPE_STATUS, cdata, counter, timerData['last']))
			
			# Send heartbeat message indicating AEM error status
			if settings.USE_AEM:
				if IS_AEM_ERROR:
					logger.debug("Sending AEM AFR error status")
					cdata = ControlData()
					cdata.button = settings.STATUS_AEM_ERROR
					cdata.destination = settings.BUTTON_DEST_GRAPHICSIO
					cdata.setPayload(data = {'status' : True, 'description' : "AEM Wideband AFR connection error."})
					dataQueue.put((settings.TYPE_STATUS, cdata, counter, timerData['last']))
				else:
					logger.debug("Sending AEM AFR okay status")
					cdata = ControlData()
					cdata.button = settings.STATUS_AEM_OK
					cdata.destination = settings.BUTTON_DEST_GRAPHICSIO
					cdata.setPayload(data = {'status' : False, 'description' : "AEM Wideband AFR connected okay."})
					dataQueue.put((settings.TYPE_STATUS, cdata, counter, timerData['last']))
				
			heartbeat_timer = timeit.default_timer()
		
		# Sleep at the end of each round so that we don't
		# consume too many processor cycles. May need to experiment
		# with this value for different platforms.
		time.sleep(settings.SENSOR_SLEEP_TIME)
		
		if data_added:
			counter += 1
