#!/usr/bin/env python
# -*- coding: utf8 -*-
#
# ControlData - Encode button presses and control messages to pass between
# PyCosworth worker processes.
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
import sys
import os

# Settings file
from libs import settings

# Start a new logger
from libs.newlog import newlog
if getattr(sys, 'frozen', False):
	__file__ = os.path.dirname(sys.executable)
logger = newlog(__file__)

class ControlData():
	""" Control data class """
	
	def __init__(self):
		""" Initialise a new control data class """
		self.created = time.time()
		self.button = None
		self.duration = None
		self.destination = None
		self.setButton()
		self.setDuration()
		self.setDestination()
		self.data = None
		
	def setPayload(self, data = None):
		if data:
			self.data = data
			
	def getPayload(self):
		if self.data:
			return self.data
		else:
			return None
		
	def setButton(self, button = None):
		""" Set the button that was pressed """
		if button:
			self.button = button
			self.setDestination()
	
	def setDuration(self, duration = None):
		""" Set the button duration """
		if duration:
			self.duration = duration
		else:
			self.duration = settings.BUTTON_SHORT
	
	def setDestination(self, destination = None):
		""" Set the destination, based on the button being pressed. """
		if destination:
			self.destination = destination
		else:
			if self.button:
				self.destination = settings.BUTTON_MAP[self.button]['dest']
			else:
				self.destination = settings.BUTTON_DEST_ALL
	
	def isMine(self, my_destination = None):
		""" Is this message for us? """
		if my_destination:
			if (my_destination == self.destination) or (self.destination == settings.BUTTON_DEST_ALL):
				return True
			else:
				return False
		else:
			return False
		
	def show(self):
		""" Print control message contents """
		logger.debug("Control data contents:")
		logger.debug("self.button 		= [%s]" % self.button)
		logger.debug("self.duration 	= [%s]" % self.duration)
		logger.debug("self.destination	= [%s]" % self.destination)
		logger.debug("self.created		= [%s]" % self.created)
		logger.debug("")
		