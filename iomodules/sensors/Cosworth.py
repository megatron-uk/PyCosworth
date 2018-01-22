#!/usr/bin/env python

# Cosworth - retrieve engine sensor data from Cosworth ECU with Pectel serial datastream.
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

# Python serial library
import serial

# Generic sensor class
from iomodules.sensors.GenericSensor import GenericSensor

# Settings file
from libs import settings

# Start a new logger
from libs.newlog import newlog
logger = newlog(__name__)

class CosworthSensors():
	""" Cosworth sensor retrieval class """
	
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
	
	def sensor(self, sensorId):
		""" Retrieve the latest value for a sensor """
		
		# Is it a valid sensor 
		if sensorId in self.sensors.keys():
			# Has the refresh timer expired
			raw_v = self.sensors[sensorId].get(self.sensors[sensorId])
			v = self.__translate__(sensorId, raw_v)
			return {  'sensor' : self.sensors[sensorId].data(), 'value' : v }
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
			
		logger.info("Starting Cosworth ECU sensor module")
			
		#self.pressureType = "psi"
		#self.pressureType = "mmHg"
		self.pressureType = "mbar"
			
		# List of supported and selected ecu
		self.supportedECU = ["L8 Pectel", "P8"]
		self.ecuType = False
		
		# Comms parameters
		self.comms = {
			'device' : settings.COSWORTH_ECU_USB,
			'baud' : "1952",
			'bits' : 8,
			'parity' : "N",
			'stopbits' : 1,
		}
		self.serial = False
		
		# Sensor types
		self.all_sensors = {
			'RPM' 		: { 'classId' : 'Cosworth.RPM', 		'sensorId' : 'RPM', 		'sensorUnit' : 'rpm', 		'refresh' : 0.1, 	'controlCodes' : [0x80, 0x81], 	'supportedECU' : ['L8 Pectel', 'P8'],	'description' : 'Engine speed' },
			'MAP' 		: { 'classId' : 'Cosworth.MAP', 		'sensorId' : 'MAP',	 	'sensorUnit' : 'mbar', 		'refresh' : 0.2, 	'controlCodes' : [0x82], 		'supportedECU' : ['L8 Pectel', 'P8'],	'description' : 'Inlet manifold pressure in milibars' },
			'IAT'			: { 'classId' : 'Cosworth.IAT', 		'sensorId' : 'IAT',		'sensorUnit' : 'deg C.',		'refresh' : 0.5,	'controlCodes' : [0x83],		'supportedECU' : ['L8 Pectel', 'P8'], 	'description' : 'Inlet manifold air temperature in degrees Celsius' },
			'ECT'		: { 'classId' : 'Cosworth.ECT', 		'sensorId' : 'ECT',		'sensorUnit' : 'deg C.',		'refresh' : 0.5,	'controlCodes' : [0x84],		'supportedECU' : ['L8 Pectel', 'P8'], 	'description' : 'Engine coolant temperature in degrees Celsius' },
			'TPS'		: { 'classId' : 'Cosworth.TPS', 		'sensorId' : 'TPS',		'sensorUnit' : 'deg',		'refresh' : 0.1,	'controlCodes' : [0x85],		'supportedECU' : ['L8 Pectel', 'P8'], 	'description' : 'Open angle of throttle plate in degrees ' },
			'IGNADV'		: { 'classId' : 'Cosworth.IGNADV', 	'sensorId' : 'IGNADV',	'sensorUnit' : 'deg BTDC',	'refresh' : 0.2,	'controlCodes' : [0x86],		'supportedECU' : ['L8 Pectel', 'P8'], 	'description' : 'Ignition timing in degrees before top dead centre' },
			'INJDUR'		: { 'classId' : 'Cosworth.INJDUR', 	'sensorId' : 'INJDUR',	'sensorUnit' : 'ms',			'refresh' : 0.1,	'controlCodes' : [0x87, 0x88],	'supportedECU' : ['L8 Pectel', 'P8'], 	'description' : 'Injector pulse width duration in milliseconds' },
			'BAT'		: { 'classId' : 'Cosworth.BAT', 		'sensorId' : 'BAT',		'sensorUnit' : 'v',			'refresh' : 0.5,	'controlCodes' : [0x89],		'supportedECU' : ['L8 Pectel', 'P8'], 	'description' : 'Battery or supply circuit voltage' },
			'AMAL'		: { 'classId' : 'Cosworth.AMAL', 		'sensorId' : 'AMAL',	'sensorUnit' : '% duty',		'refresh' : 0.2,	'controlCodes' : [0x90],		'supportedECU' : ['L8 Pectel', 'P8'], 	'description' : 'Duty cycle of boost control valve' },
		}
		
		# Available sensors for this ecu type
		self.sensors = {}
		
		if ecuType not in self.supportedECU:
			logger.fatal("Attempted initalisation of an unsupported ECU type %s" % ecuType)
			logger.fatal("Supported types are:")
			for ecu in self.supported_ecu:
				logger.fatal(ecu)	
			return None
		else:
			if ecuType:
				self.ecu = ecuType
			if pressureType:
				self.pressureType = pressureType
			self.__connectECU__()
			if self.serial is False:
				return None
			else:
				self.__setSensors__()

	def __get__(self, sensorData):
		""" Get a single sensor value.
		This is registered as the getter() callback in the GenericSensor class.	
		"""

		if self.serial:
			raw_value = None
			get_start_time = timeit.default_timer()

			if len(sensorData['controlCodes']) == 1:
				self.serial.write(bytes[sensorData['controlCodes'][0]])
				raw_value = self.serial.read(1)
				
			elif len(sensorData['controlCodes']) == 2:
				self.serial.write(bytes[sensorData['controlCodes'][0]])
				raw_value_1 = self.serial.read(1)
				self.serial.write(bytes[sensorData['controlCodes'][1]])
				raw_value_2 = self.serial.read(1)
				raw_value = (raw_value_1 << 8) + raw_value_2
				
			else:
				logger.error("Unsupported number of control codes for sensor %s" % sensorData['sensorId'])
				return None, None
		else:
			logger.error("Serial port is not open")
			return None, None
		
		return raw_value, (timeit.default_timer() - get_start_time)

	def __translate__(self, sensorId, rawValue):
		""" Translate a raw value from a Cosworth sensor into a real-world number """
		
		if sensorId == 'RPM':
			value = int(30000000 / rawValue)
		elif sensorId == 'INJDUR':
			value = int((rawValue * 4) / 1000)
		elif sensorId == 'MAP':
			if self.pressureType == "mmHg":
				# mmHg
				value = rawValue * 6.4161 + 45.63
			elif self.pressureType == "mbar":
				# millibar
				value = (rawValue * 6.4161 + 45.63) *  0.75006156130264
			elif self.pressureType == "psi":
				# PSI
				value = (rawValue * 6.4161 + 45.63) * 51.714924102396
			else:
				logger.warn("Unsupported pressure type %s" % self.pressureType)
				return rawValue
		elif sensorId == "TPS":
			if rawValue < 0x30:
				value = (rawValue * 0.1848) - 1.41
			if rawValue >= 0x30:
				value = (rawValue * 0.7058) - 90
		elif sensorId == "BAT":
			value = rawValue * 0.0628
		else:
			logger.warn("No translation found for sensor %s" % sensorId)
			return rawValue
			
		return value

	def __setSensors__(self):
		""" Set up the list of sensors we can use, based on the selected ECU type """
		
		for sensorId in self.all_sensors.keys():
			# Is this sensor valid for the current ECU?
			if self.ecuType  in self.all_sensors[sensorId]['supportedECU']:
				# Add a new instance of a generic sensor
				newSensor = GenericSensor(sensorData = self.all_sensors[sensorId], getter = self.__get__)
				# Set the refresh timer
				newSensor.refreshTimer(self.all_sensors[sensorId]['refresh'])
				# Start timer
				newSensor.resetTimer()
				self.sensors[sensorId] = newSensor
				
	
	def __connectECU__(self):
		""" Connect to the ECU """
		if self.ecuType:
			try:
				self.serial = serial.Serial(
					port = self.comms['device'],
					baudrate=self.comms['baud'], 
					bytesize=self.comms['databits'], 
					parity=self.comms['parity'], 
					stopbits=self.comms['stopbits'], 
					xonxoff=0, 
					rtscts=0, 
					dsrdtr=0, 
					timeout=self.comms_timeout
				)
			except Exception as e:
				self.serial = False
				logger.fatal("Unable to open requested serial port for Cosworth ECU module")
				logger.fatal("%s" % e)
	
	def __disconnectECU__(self):
		""" Disconnect from ECU """
		try:
			self.serial.close()
			logger.info("Closed serial port for Cosworth ECU module")
			self.serial = False
		except Exception as e:
			logger.warn("Unable to close serial port for Cosworth ECU module")
			logger.warn("%s" % e)
	
	def __reconnectECU__(self):
		""" Close and reconnect """
		
		self.__disconnectECU__()
		self.__connectECU__()