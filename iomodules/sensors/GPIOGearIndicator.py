#!/usr/bin/env python

# Detect gear lever position from a number of sensors attached to Pi
# GPIO pins.
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

class GearIndicatorSensors():
	""" Gear lever position retrieval class """
	
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
			v = self.sensors[sensorId].get(force = force)
			return {  'sensor' : self.sensors[sensorId].data(), 'value' : v, 'rawValue' : v }
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
			history = copy.copy(raw_history)
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
		pass
	
	##########################################
	#
	# The methods listed below should not be called by any external code.
	#
	##########################################
	
	def __init__(self, steps = settings.DEMO_STEPS):
		
		###################################################
		#
		# Class variables and data structures
		#
		###################################################
		
		logger.info("Starting Example sensor module")
		
		# Sensor types
		self.all_sensors = {
			'GEAR'		: { 'classId' : 'GPIOGearIndicator.GEAR', 		'sensorId' : 'GEAR',	'sensorUnit' : '',		'refresh' : 0.2,	'maxValue' : 1, 		'minValue' : 0,	 'description' : 'Shows gear lever position' },
		}
		
		# Available sensors
		self.sensors = {}
		self.demo_steps = steps
		self.__setSensors__()

	def __get__(self, sensorData):
		""" Get a single sensor value.
		This is registered as the getter() callback in the GenericSensor class.	
		"""

		get_start_time = timeit.default_timer()
			
		pin1 = 0
		pin2 = 0
		pin3 = 0
		pin4 = 0
		# If switch 1 and 2 == 1st gear
		# if switch 1 and 4 == 2nd gear
		# if switch 2 == 3rd gear
		# if switch 4 == 4th gear
		# if switch 2 and 3 == 5th gear
		# if switch 3 and 4 == reverse
		
		if pin1 and pin2:
			# 1st gear
			value = "1"
		elif pin1 and pin4:
			# 2nd gear
			value = "2"
		elif pin2:
			# 3rd gear
			value = "3"
		elif pin4:
			# 4th gear
			value = "4"
		elif pin2 and pin3:
			# 5th gear
			value = "5"
		elif pin3 and pin4:
			# Reverse
			value = "R"
		elif (pin1 == 0) and (pin2 == 0) and (pin3 == 0) and (pin4 == 0):
			# Neutral
			value = "N"
		else:
			# Error position
			value = "E"
		
		return value, (timeit.default_timer() - get_start_time)
	
	def __is_connected__(self):
		return True
	
	def __setSensors__(self):
		""" Set up the list of sensors we can use """
		
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