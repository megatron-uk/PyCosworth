#!/usr/bin/env python

# AEM - retrieve sensor data from AEM X-series wideband air-fuel meter serial datastream.
# Copyright (C) 2021  John Snowdon
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
import copy

# Python serial library
import serial

# Generic sensor class
from iomodules.sensors.GenericSensor import GenericSensor

# Settings file
from libs import settings

# Start a new logger
from libs.newlog import newlog
logger = newlog(__name__)

class AEMSensors():
	""" AEM sensor retrieval class """
	
	#############################################
	#
	# Public methods
	#
	#############################################
	
	def available(self):
		""" Return the list of available sensors """
	
		return self.sensors.keys()
	
	def data(self, sensorId):
		""" Return sensor dictionary for a sensor id """
		
		# Is it a valid sensor 
		if sensorId in self.sensors.keys():
			return self.sensors[sensorId].data()
		else:
			# Not a valid sensor
			logger.warn("Unsupported sensor type: %s" % sensorId)
			return None
	
	def sensor(self, sensorId, force = False):
		""" Retrieve the latest value for a sensor """
		
		# Is it a valid sensor 
		if sensorId in self.sensors.keys():
			# Has the refresh timer expired
			raw_v = self.sensors[sensorId].get(force = force)
			if raw_v:
				v = self.__translate__(sensorId, raw_v)
			else:
				v = raw_v
			return {  'sensor' : self.sensors[sensorId].data(), 'value' : v, 'rawValue' : raw_v}
		else:
			# Not a valid sensor
			logger.warn("Unsupported sensor type: %s" % sensorId)
			return None
	
	def history(self, sensorId):
		""" Return historic sample data for a sensor """
		
		# Is it a valid sensor 
		if sensorId in self.sensors.keys():
			history = []
			raw_history = self.sensors[sensorId].history()
			for raw_v in raw_history:
				v = self.__translate__(sensorId, raw_v)
				history.append(v)
			return history
		else:
			# Not a valid sensor
			logger.warn("Unsupported sensor type: %s" % sensorId)
			return None
		
	def performance(self, sensorId):
		""" Return sample-time statistics for a sensor: latest, min, max and average time to get a reading """
		
		# Is it a valid sensor 
		if sensorId in self.sensors.keys():
			history = []
			return self.sensors[sensorId].performance()
		else:
			# Not a valid sensor
			logger.warn("Unsupported sensor type: %s" % sensorId)
			return None
		
	def close(self):
		""" Disconnect the sensor and clean up any resources """
		logger.info("Closing sensor module")
		self.__disconnectECU__()
	
	##########################################
	#
	# The methods listed below should not be called directly by any external code.
	#
	##########################################
		
	def __init__(self, ecuType = None, pressureType = None):
			
		###################################################
		#
		# Class variables and data structures
		#
		###################################################
			
		logger.info("Starting AEM Wideband AFR sensor module")
			
		
		# Comms parameters
		self.comms = {
			'device' : settings.AEM_USB,
			'baud' : "9600",
			'bits' : 8,
			'parity' : "N",
			'stopbits' : 1,
		}
		self.comms_timeout = 0.1
		self.serial = False
		
		# Sensor types
		self.all_sensors = {
			'AFR': { 
				'classId' : 'AEM.AFR',
				'sensorId' : 'AFR',
				'sensorUnit' : 'afr',
				'refresh' : 0.1,
				'description' : 'AFR reading from AEM Wideband O2 sensor'
			},
		}
		
		# Available sensors for this ecu type
		self.sensors = {}
		self.connected = False
		
		# Open a connection
		self.__setSensors__()
		self.__connectECU__()
		if self.serial is False:
			return None

	def __get__(self, sensorData):
		""" Get a single sensor value.
		This is registered as the getter() callback in the GenericSensor class.	
		"""

		if self.connected:
			raw_value = None
			get_start_time = timeit.default_timer()

			try:
				raw_value = self.serial.readline()

			except Exception as e:
				#logger.error("Error communicating with serial port!")
				#logger.error(e)
				return None, None
		else:
			logger.debug("Serial port is not open")
			return None, None
		
		return raw_value, (timeit.default_timer() - get_start_time)

	def __translate__(self, sensorId, rawValue):
		""" Translate a raw value from a AEM sensor into a real-world number """
		
		if sensorId == 'AFR':
			try:
				value = rawValue.strip('\n')
				value = float(value)
			except:
				value = rawValue
			
		return value

	def __setSensors__(self):
		""" Set up the list of sensors we can use, based on the selected ECU type """
		
		sensorIds = list(self.all_sensors.keys())
		sensorIds.sort()
		for sensorId in sensorIds:
			logger.debug("Adding sensor [%s]" % self.all_sensors[sensorId]['classId'])
			# Add a new instance of a generic sensor
			newSensor = GenericSensor(sensorData = self.all_sensors[sensorId], getter = self.__get__)
			# Set the refresh timer
			newSensor.refreshTimer(self.all_sensors[sensorId]['refresh'])
			# Start timer
			newSensor.resetTimer()
			self.sensors[sensorId] = newSensor
				
	
	def __is_connected__(self):
		
		return self.connected
	
	def __connectECU__(self):
		""" Connect to the ECU """
		try:
			logger.info("Bringing up serial interface [%s baud=%s,databits=%s,parity=%s,stopbits=%s]" % (self.comms['device'], self.comms['baud'], self.comms['bits'], self.comms['parity'], self.comms['stopbits']))
			self.serial = serial.Serial(
				port = self.comms['device'],
				baudrate=self.comms['baud'], 
				bytesize=self.comms['bits'], 
				parity=self.comms['parity'], 
				stopbits=self.comms['stopbits'], 
				xonxoff=0, 
				rtscts=0, 
				dsrdtr=0, 
				timeout=self.comms_timeout
			)
			logger.info("Serial interface up")
			self.connected = True
		except Exception as e:
			self.connected = False
			self.serial = False
			logger.fatal("Unable to open requested serial port for AEM Wideband module")
			logger.fatal("%s" % e)
			logger.fatal("")
			logger.fatal("Is the USB to serial adaptor plugged in?")
			logger.fatal("Is the device name correct?")
			logger.fatal("Is the Wideband AFR module powered on?")
	
	def __disconnectECU__(self):
		""" Disconnect from AEM module """
		try:
			self.serial.close()
			logger.info("Closed serial port for AEM Wideband module")
			self.serial = False
		except Exception as e:
			logger.warn("Unable to close serial port for AEM Wideband module")
			logger.warn("%s" % e)
	
	def __reconnectECU__(self):
		""" Close and reconnect """
		
		self.__disconnectECU__()
		self.__connectECU__()
