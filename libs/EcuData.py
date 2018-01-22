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
		ecuPrevDataDict = None,
		ecuCounter = None, 
		ecuErrors = None, 
		ecuSampleTime = None, 
		ecuMatrixLCDDict = None):
		""" Initialise the class with the shared data manager dictionary """
		self.data = ecuDataDict
		self.data_previous = ecuPrevDataDict
		self.errors = ecuErrors
		self.counter = ecuCounter
		self.timer = ecuSampleTime
		
		# Initialise sensor values structure
		for sensor in settings.SENSORS:
			self.data[sensor['sensorId']] = 0
		
		for sensor in settings.SENSORS:
			self.data_previous[sensor['sensorId']] = 0
		
		# Store error codes as they occur
		self.errors_ = []
		
		# Multi line matrix lcd displays can be configured to display
		# different things...
		self.matrix_config = ecuMatrixLCDDict
	
		self.sensor = {}
	
	def set_sensor(self, sensor = None):
		sensorId = sensor['sensorId']
		self.sensor[sensorId] = sensor
	
	def get_timer(self):
		""" Return the time taken to process the last set of ECU values, in ms. """
		t = self.timer.value * 1000
		return t
	
	def get_counter(self):
		""" Return current sample counter """
		c = int(self.counter.value)
		return c
	
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