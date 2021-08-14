#!/usr/bin/env python
# -*- coding: utf8 -*-
#
# masterWindow - class and state machine representing the master display screen
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
import sys
import os
import copy
import traceback
from collections import deque

# Graphics libs
from PIL import Image
from PIL import ImageOps
from PIL import ImageDraw
from PIL import ImageFont

from iomodules.GraphicsIO import updateSDLWindow, updateOLEDScreen, blankImage

# Settings file
from libs import settings

# Menu settings
from libs.MenuFunctions import *

# Control data
from libs.ControlData import ControlData

# Start a new logger
from libs.newlog import newlog
logger = newlog(__name__)

class MasterMenu():
	""" A class which encapsulates the main master window and/or the control buttons """
	
	def __init__(self, 
		windowSettings = None,
		subWindowSettings = [],
		actionQueue = None,
		ecudata = None, 
		use_sdl = False, 
		use_oled = False
		):
		""" Instaniate the class """
		
		# A queue to pass messages back up the main process
		self.actionQueue = actionQueue
		
		# A list of any sub windows
		self.subWindowSettings = subWindowSettings
		
		# Ecu/sensor data class
		self.ecudata = ecudata
		
		# Load window settings for the master screen
		if windowSettings:
			self.windowSettings = windowSettings
		else:
			self.windowSettings = settings.GFX_MASTER_WINDOW
						
		# Selected sensors
		self.selectedSensors = {
			'left' : None,
			'full' : None,
			'right' : None,
			'custom' : None,
		}
		
		self.defaultVisualisation = settings.GFX_MODES[0]
		self.leftVisualisation = self.defaultVisualisation
		self.rightVisualisation = self.defaultVisualisation
		self.fullVisualisation = self.defaultVisualisation
		
		# The custom function and its associated data which run
		# run every time the mastermenu class has 'buildimage' called
		# and we are *not* in a menu.
		self.customFunction = None
		self.customData = None
		
	def processControlData(self, controlData):
		""" Respond to button presses and other control data. """
				
		# Start/stop logging
		if controlData.button == settings.BUTTON_LOGGING:
			# Start logger if not running
			
			# Stop logger is already running
			pass
				
		# View next sensor
		if controlData.button == settings.BUTTON_SENSOR_NEXT:
			# Change to next sensor
			pass
	
	def update(self):
		""" Redraw the screen with the current bitmap stored in self.image """
		
		pass