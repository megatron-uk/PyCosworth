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

class DemoSensors():
	""" Demo sensor retrieval class """
	
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
			v = self.sensors[sensorId].get(self.sensors[sensorId])
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
		
		logger.info("Starting Demo engine sensor module")
		
		# Sensor types
		self.all_sensors = {
			'RPM' 		: { 'classId' : 'Demo.RPM', 		'sensorId' : 'RPM', 		'sensorUnit' : 'rpm', 		'refresh' : 0.1, 	'maxValue' : 7500, 	'minValue' : 0,	'demo_data' : [], 'demo_idx' : 0, 'description' : 'DEMO engine speed' },
			'MAP' 		: { 'classId' : 'Demo.MAP', 		'sensorId' : 'MAP',	 	'sensorUnit' : 'mbar', 		'refresh' : 0.2, 	'maxValue' : 2850, 	'minValue' : -200,	'demo_data' : [], 'demo_idx' : 0, 'description' : 'DEMO Inlet manifold pressure' },
			'IAT'			: { 'classId' : 'Demo.IAT', 		'sensorId' : 'IAT',		'sensorUnit' : 'deg C.',		'refresh' : 0.5,	'maxValue' : 60, 		'minValue' : 0,	'demo_data' : [], 'demo_idx' : 0, 'description' : 'DEMO Inlet manifold air temperature in degrees Celsius' },
			'ECT'		: { 'classId' : 'Demo.ECT', 		'sensorId' : 'ECT',		'sensorUnit' : 'deg C.',		'refresh' : 0.5,	'maxValue' : 120, 		'minValue' : 0,	'demo_data' : [], 'demo_idx' : 0, 'description' : 'DEMO Engine coolant temperature in degrees Celsius' },
			'TPS'		: { 'classId' : 'Demo.TPS', 		'sensorId' : 'TPS',		'sensorUnit' : 'deg',		'refresh' : 0.1,	'maxValue' : 90, 		'minValue' : -2,	'demo_data' : [], 'demo_idx' : 0, 'description' : 'DEMO Open angle of throttle plate in degrees ' },
			'IGNADV'		: { 'classId' : 'Demo.IGNADV', 	'sensorId' : 'IGNADV',	'sensorUnit' : 'deg BTDC',	'refresh' : 0.2,	'maxValue' : 40, 		'minValue' : 0,	'demo_data' : [], 'demo_idx' : 0, 'description' : 'DEMO Ignition timing in degrees before top dead centre' },
			'INJDUR'		: { 'classId' : 'Demo.INJDUR', 	'sensorId' : 'INJDUR',	'sensorUnit' : 'ms',			'refresh' : 0.1,	'maxValue' : 5, 		'minValue' : 0,	'demo_data' : [], 'demo_idx' : 0, 'description' : 'DEMO Injector pulse width duration in milliseconds' },
			'BAT'		: { 'classId' : 'Demo.BAT', 		'sensorId' : 'BAT',		'sensorUnit' : 'v',			'refresh' : 0.5,	'maxValue' : 16, 		'minValue' : 0,	'demo_data' : [], 'demo_idx' : 0, 'description' : 'DEMO Battery or supply circuit voltage' },
			'AMAL'		: { 'classId' : 'Demo.AMAL', 		'sensorId' : 'AMAL',	'sensorUnit' : '% duty',		'refresh' : 0.2,	'maxValue' : 100, 		'minValue' : 0,	'demo_data' : [], 'demo_idx' : 0, 'description' : 'DEMO Duty cycle of boost control valve' },
		}
		
		# Available sensors
		self.sensors = {}
		self.demo_steps = steps
		self.__setSensors__()

	def __get__(self, sensorData):
		""" Get a single sensor value.
		This is registered as the getter() callback in the GenericSensor class.	
		"""

		sensorId = sensorData['sensorId']
		value = None
		get_start_time = timeit.default_timer()
		idx = self.all_sensors[sensorId]['demo_idx']
		value = self.all_sensors[sensorId]['demo_data'][idx]
		
		if self.all_sensors[sensorId]['demo_idx'] < (len (self.all_sensors[sensorId]['demo_data']) - 1):
			self.all_sensors[sensorId]['demo_idx'] += 1
		else:
			self.all_sensors[sensorId]['demo_idx'] = 0
		
		return value, (timeit.default_timer() - get_start_time)
		
	def __setSensors__(self):
		""" Set up the list of sensors we can use """
		
		for sensorId in self.all_sensors.keys():
			# Generate the sequence of demo data
			demo_step_size = (self.all_sensors[sensorId]['maxValue'] * 1.0) / self.demo_steps
			d_value = self.all_sensors[sensorId]['minValue']
			for d in range(0, self.demo_steps):
				self.all_sensors[sensorId]['demo_data'].append(d_value)
				d_value += demo_step_size
			for d in range(0, self.demo_steps):
				d_value = d_value - demo_step_size
				self.all_sensors[sensorId]['demo_data'].append(d_value)
	
			# Add a new instance of a generic sensor
			newSensor = GenericSensor(sensorData = self.all_sensors[sensorId], getter = self.__get__)
			# Set the refresh timer
			newSensor.refreshTimer(self.all_sensors[sensorId]['refresh'])
			# Start timer
			newSensor.resetTimer()
			self.sensors[sensorId] = newSensor