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
			
		logger.info("Starting Cosworth ECU sensor module")
			
		logger.info("ECU type configured as [%s]" % ecuType)
		logger.info("Pressure values reported in [%s]" % pressureType)
		
		# List of supported pressure measurement types
		self.supportedPressureType = ["mmhg", "mbar", "psi"]
		self.pressureType = False
			
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
		self.comms_timeout = 0.1
		self.serial = False
		
		# Sensor types
		self.all_sensors = {
			'RPM': { 
				'classId' : 'Cosworth.RPM',
				'sensorId' : 'RPM',
				'sensorUnit' : 'rpm',
				'refresh' : 0.1,
				'controlCodes' : [0x80, 0x81],
				'supportedECU' : ['L8 Pectel', 'P8'],
				'description' : 'Engine speed from crank sensor'
			},
			'MAP' : { 
				'classId' : 'Cosworth.MAP',
				'sensorId' : 'MAP',	
				'sensorUnit' : 'mbar',
				'refresh' : 0.2,
				'controlCodes' : [0x82],
				'supportedECU' : ['L8 Pectel', 'P8'],
				'description' : 'Inlet manifold pressure in millibars' 
			},
			'IAT': { 
				'classId' : 'Cosworth.IAT',
				'sensorId' : 'IAT',
				'sensorUnit' : 'deg C.',
				'refresh' : 0.5,
				'controlCodes' : [0x83],
				'supportedECU' : ['L8 Pectel', 'P8'],
				'description' : 'Inlet manifold air temperature in degrees Celsius' 
			},
			'ECT': { 
				'classId' : 'Cosworth.ECT',
				'sensorId' : 'ECT',
				'sensorUnit' : 'deg C.',
				'refresh' : 0.5,
				'controlCodes' : [0x84],
				'supportedECU' : ['L8 Pectel', 'P8'],
				'description' : 'Engine coolant temperature in degrees Celsius' 
			},
			'TPS': { 
				'classId' : 'Cosworth.TPS',
				'sensorId' : 'TPS',
				'sensorUnit' : 'deg',
				'refresh' : 0.1,
				'controlCodes' : [0x85],
				'supportedECU' : ['L8 Pectel', 'P8'], 
				'description' : 'Throttle body opening in degrees' 
			},
			'IGNADV': { 
				'classId' : 'Cosworth.IGNADV', 
				'sensorId' : 'IGNADV',
				'sensorUnit' : 'deg',
				'refresh' : 0.2,
				'controlCodes' : [0x86],
				'supportedECU' : ['L8 Pectel', 'P8'],
				'description' : 'Ignition timing, degrees before top dead centre' 
			},
			'INJDUR': { 
				'classId' : 'Cosworth.INJDUR', 
				'sensorId' : 'INJDUR',
				'sensorUnit' : 'ms',
				'refresh' : 0.1,
				'controlCodes' : [0x87, 0x88],
				'supportedECU' : ['L8 Pectel', 'P8'],
				'description' : 'Injector pulse width duration, milliseconds' 
			},
			'BAT': { 
				'classId' : 'Cosworth.BAT',
				'sensorId' : 'BAT',
				'sensorUnit' : 'v',
				'refresh' : 0.5,
				'controlCodes' : [0x89],
				'supportedECU' : ['L8 Pectel', 'P8'],
				'description' : 'Battery or supply circuit voltage' 
			},
			'AMAL': { 
				'classId' : 'Cosworth.AMAL', 
				'sensorId' : 'AMAL',
				'sensorUnit' : '% duty',
				'refresh' : 0.2,
				'controlCodes' : [0x90],
				'supportedECU' : ['L8 Pectel', 'P8'],
				'description' : 'Boost control valve duty cycle' 
			},
			'CO': { 
				'classId' : 'Cosworth.CO',
				'sensorId' : 'CO',
				'sensorUnit' : '% trim',
				'refresh' : 1,
				'controlCodes' : [0x8a],
				'supportedECU' : ['L8 Pectel', 'P8'],
				'description' : 'Base fuel delivery trim pot'
			},
		}
		
		# Available sensors for this ecu type
		self.sensors = {}
		self.connected = False
		
		if ecuType not in self.supportedECU:
			logger.fatal("Attempted initalisation of an unsupported ECU type [%s]" % ecuType)
			logger.fatal("Supported types are:")
			for ecu in self.supportedECU:
				logger.fatal("'%s'" % ecu)	
			logger.fatal("Either set the correct ECU type in the settings file, or pass it manually to this class")
			self.connected = False
			return None
			
		if pressureType not in self.supportedPressureType:
			logger.fatal("Invalid pressure type paramter [%s]" % pressureType)
			logger.fatal("Supported types are:")
			for ptype in self.supportedPressureType:
				logger.fatal("'%s'" % ptype)
			logger.fatal("Either set the correct pressure type in the settings file, or pass it manually to this class")
			self.connected = False
			return None
		
		self.ecuType = ecuType
		self.pressureType = pressureType
		self.all_sensors['MAP']['sensorUnit'] = self.pressureType
		
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

			if len(sensorData['controlCodes']) == 1:
				self.serial.write(bytes([sensorData['controlCodes'][0]]))
				raw_value = self.serial.read(1)[0]
				
			elif len(sensorData['controlCodes']) == 2:
				[sensorData['controlCodes'][0]]
				self.serial.write(bytes([sensorData['controlCodes'][0]]))
				raw_value_1 = self.serial.read(1)[0]
				self.serial.write(bytes([sensorData['controlCodes'][1]]))
				raw_value_2 = self.serial.read(1)[0]
				raw_value = (raw_value_1 << 8) + raw_value_2
				
			else:
				logger.error("Unsupported number of control codes for sensor %s" % sensorData['sensorId'])
				return None, None
		else:
			logger.debug("Serial port is not open")
			return None, None
		
		return raw_value, (timeit.default_timer() - get_start_time)

	def __translate__(self, sensorId, rawValue):
		""" Translate a raw value from a Cosworth sensor into a real-world number """
		
		if sensorId == 'RPM':
			if rawValue == 0:
				value = 0
			else:
				# FIAT value
				#value = int(30000000 / rawValue)
				# Pectel/Ford value
				value = int(1875000 / rawValue)
		elif sensorId == 'INJDUR':
			if rawValue == 0:
				value = 0
			else:
				# This is the FIAT calculation
				value = int((rawValue * 4) / 1000)
		elif sensorId == 'MAP':
			if self.pressureType == "mmHg":
				# mmHg
				# This is the FIAT calculation
				value = rawValue * 6.4161 + 45.63
			elif self.pressureType == "mbar":
				# millibar
				# Transpose the FIAT calculation into mbar
				value = (rawValue * 6.4161 + 45.63) * 0.75006156130264
			elif self.pressureType == "psi":
				# PSI
				# Transpose the FIAT calculation into pounds per square inch
				value = (rawValue * 6.4161 + 45.63) * 51.714924102396
			else:
				logger.warn("Unsupported pressure type [%s]" % self.pressureType)
				value = 0
		elif sensorId == "TPS":
			if rawValue == 0:
				value = 0
			elif rawValue < 0x30:
				# This is the FIAT calculation
				value = (rawValue * 0.1848) - 1.41
			elif rawValue >= 0x30:
				# This is the FIAT calculation
				value = (rawValue * 0.7058) - 90
		elif sensorId == "BAT":
			if rawValue == 0:
				value = 0
			else:
				# This is the FIAT calculation
				value = rawValue * 0.0628
		elif sensorId == "IGNADV":
			if rawValue == 0:
				value = 0
			else:
				# This is the FIAT calculation
				value = rawValue / 4
		elif sensorId in ['IAT', 'ECT']:
			value = rawValue
		else:
			logger.warn("No translation found for sensor [%s]" % sensorId)
			value = 0
			
		return value

	def __setSensors__(self):
		""" Set up the list of sensors we can use, based on the selected ECU type """
		
		sensorIds = list(self.all_sensors.keys())
		sensorIds.sort()
		for sensorId in sensorIds:
			# Is this sensor valid for the current ECU?
			# Some ECU variants have a different subset of sensors that they
			# support, for example, the P8 supports full information from
			# lambda sensors, whereas the L8 does not.
			if self.ecuType  in self.all_sensors[sensorId]['supportedECU']:
				logger.debug("Adding sensor [%s]" % self.all_sensors[sensorId]['classId'])
				# Add a new instance of a generic sensor
				newSensor = GenericSensor(sensorData = self.all_sensors[sensorId], getter = self.__get__)
				# Set the refresh timer
				newSensor.refreshTimer(self.all_sensors[sensorId]['refresh'])
				# Start timer
				newSensor.resetTimer()
				self.sensors[sensorId] = newSensor
			else:
				logger.warn("Sensor type [%s] is unsupported for ecu [%s]" % (self.all_sensors[sensorId]['classId'], self.ecuType))
				
	
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
			logger.fatal("Unable to open requested serial port for Cosworth ECU module")
			logger.fatal("%s" % e)
			logger.fatal("")
			logger.fatal("Is the USB to serial adaptor plugged in?")
			logger.fatal("Is the device name correct?")
			logger.fatal("Is the ECU powered on?")
	
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