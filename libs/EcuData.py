#!/usr/bin/env python

# EcuData - a class to store sensor data and errors for PyCosworth.
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
import sys
import os

# Settings file
from libs import settings

# Start a new logger
from libs.newlog import newlog
if getattr(sys, 'frozen', False):
	__file__ = os.path.dirname(sys.executable)
logger = newlog(__file__)
class EcuData():
	""" Class representing the current state of sensor data for the ECU """
	
	def __init__(self, 
		ecuDataDict = None,
		ecuSensorDict = None,
		ecuCounter = None, 
		ecuErrors = None, 
		ecuSampleTime = None, 
		ecuMatrixLCDDict = None,
		ecuStatusDict = None):
		""" Initialise the class with the shared data manager dictionary """
		
		self.data = ecuDataDict
		self.sensor = ecuSensorDict
		self.errors = ecuErrors
		self.counter = ecuCounter
		self.timer = ecuSampleTime
		self.status = ecuStatusDict
		
		# Initialise sensor values structure
		for sensor in settings.SENSORS:
			# value, sample time, counter
			self.data[sensor['sensorId']] = (0,0,0)
		
		# Store error codes as they occur
		self.errors_ = []
		
		# Multi line matrix lcd displays can be configured to display
		# different things...
		self.matrix_config = ecuMatrixLCDDict
	
	def setError(self, errortext = None):
		
		self.errors_.append(errortext)
	
	def setData(self, sensorId = None, value = 0, sampletime = 0, counter = 0):
		""" Set the latest value for a sensor """
		
		self.counter.value = counter
		if sensorId in self.data.keys():
			self.data[sensorId] = (value, sampletime, counter)
			
	
	def getData(self, sensorId = None, allData = False):
		
		if sensorId in self.data.keys():
			if len(self.data[sensorId]) > 0:
				logger.debug("Queried %s: value:%s sampletime:%.4f counter:%s [allData:%s]" % (sensorId, self.data[sensorId][0], self.data[sensorId][1], self.data[sensorId][2], allData))
				if self.data[sensorId][0] is not None:
					if allData:
						return self.data[sensorId]
					else:
						v = self.data[sensorId][0]
						return v
				
		# If no data has been recorded, or the value of the data is None, then simply return None as the result, ignoring any sample timer or loop counter
		return None
	
	def getSensorIds(self):
		
		return list(self.sensor.keys())
	
	def getSensorData(self, sensorId = None):
		
		if sensorId in self.sensor.keys():
			return self.sensor[sensorId]
		else:
			return None
	
	def setSensorData(self, sensorData = None):
		
		if sensorData['sensorId'] not in self.sensor.keys():
			logger.info("New sensor type added: %s" % sensorData['classId'])
			self.sensor[sensorData['sensorId']] = sensorData
		else:
			return None
	
	def setStatusData(self, statusData = None):
		
		sourceId = statusData['sourceId']
		self.status[sourceId] = statusData
	
	def setCounter(self, counter):
		""" Set counter """
		
		self.counter.value = int(counter)
	
	def getCounter(self):
		""" Return current sample counter """
		
		return int(self.counter.value)
	
	def get_errors(self):
		""" Return a list of any logged errors """
		logger.debug("There are %s errors stored" % len(self.errors_))
		e = self.errors_
		return e
	
	def set_errors_reset(self):
		""" Reset any stored errors in the current data """
		logger.debug("Resetting any stored error codes")
		self.errors = []
		return True