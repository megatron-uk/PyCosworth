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
import time
import timeit 
from collections import deque

# Settings file
from libs import settings

# Start a new logger
from libs.newlog import newlog
logger = newlog(__name__)

class GenericSensor():
	""" Generic sensor class """
			
	def __init__(self, sensorData = None, getter = None):
		""" Store all sensor-specific data """
		self.sensorData = {}
		self.refreshTime = 1
		self.timer = None
		self.getter = None
		
		self.history_get_times = deque(maxlen = settings.SENSOR_MAX_HISTORY)
		self.history_raw_values = deque(maxlen = settings.SENSOR_MAX_HISTORY)
		self.getter = getter
		self.sensorData = sensorData
	
	def data(self):
		""" Return the dictionary defining the sensor """
		
		return self.sensorData
	
	def refreshTimer(self, interval = 1):
		""" Set the refresh interval of this sensor """
		
		self.refreshTime = interval
	
	def resetTimer(self):
		""" Set an initial timer """
		
		self.timer = timeit.default_timer()
	
	def refresh(self):
		""" Should the sensor be refreshed? """
		
		if (timeit.default_timer() - self.timer) >= self.refreshTime:
			return True
		else:
			return False
		
	def get(self, force = False):
		""" Get a new data value - if required - and return it """
		
		if force or self.refresh():
			raw_value, get_time = self.getter(self.sensorData)
			self.history_raw_values.append(raw_value)
			self.history_get_times.append(get_time)
			return self.value()
		else:
			return self.value()
		
	def value(self):
		""" Return current value """
		
		return self.history_raw_values[-1]
	
	def history(self):
		
		return list(self.history_raw_values)
		
	def performance(self):
		""" Return performance of sample times """
		
		time_min = min(self.history_get_times) * 1000
		time_max = max(self.history_get_times) * 1000
		time_avg = (sum(self.history_get_times) / len(self.history_get_times))  * 1000
		
		return { 'last' : (self.history_get_times[-1]  * 1000), 'min' : time_min, 'max' : time_max, 'average' : time_avg}