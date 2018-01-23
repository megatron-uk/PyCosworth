#!/usr/bin/env python
# -*- coding: utf8 -*-
#
# MenuFunctions - helper functions called by options in the main menu class
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
import psutil

# low level graphics libs
from PIL import Image
from PIL import ImageOps
from PIL import ImageDraw
from PIL import ImageFont

# Our local graphics utils
from iomodules.graphics.GraphicsUtils import *

# button press library
from libs.ControlData import ControlData

# Settings file
from libs import settings

# Start a new logger
from libs.newlog import newlog
logger = newlog(__name__)

##############################################################
#
# All functions are called from within the MasterMenu
# class.
#
# All functions take the same parameters:
# - menuClass : a reference to the parent MasterMenu instance (i.e. 'self')
#


def doNothing(menuClass = None, controlData = None):
	""" Do nothing, other than disable this function the next time
	processControlData is called. """
	
	menuClass.resetCustomFunction()
	return True
	

def sensorSelectFull(menuClass = None, controlData = None):
	pass

def sensorSelectLeft(menuClass = None, controlData = None):
	pass

def sensorSelectRight(menuClass = None, controlData = None):
	pass

def showLoggingState(menuClass = None, controlData = None):
	pass

def startLogging(menuClass = None, controlData = None):
	pass

def stopLogging(menuClass = None, controlData = None):
	pass

def toggleDemo(menuClass = None, controlData = None):
	""" Toggle demo mode on/off and then remove ourselves from 
	the custom function list so we don't run next time around. """
	
	cdata = ControlData()
	cdata.setButton(settings.BUTTON_TOGGLE_DEMO)
	menuClass.actionQueue.put(cdata)
	menuClass.resetCustomFunction()
	menuClass.resetMenus(showMenu = True)
	return True

def restartSensorIO(menuClass = None, controlData = None):
	pass

def showSensorComms(menuClass = None, controlData = None):
	pass

def showSensorText(menuClass = None, controlData = None):
	pass

def showSysInfo(menuClass = None, controlData = None):
	""" Shows a screen with constantly updating system performance information """
	
	if 'refreshTime' not in menuClass.customData.keys():
		menuClass.customData['refreshTime'] = 1.0
		menuClass.customData['timer'] = timeit.default_timer()
	
	# We accept control data
	if controlData:
		# If we get a select or cancel button, exit the custom function
		if controlData.button in [ settings.BUTTON_SELECT, settings.BUTTON_CANCEL ]:
			menuClass.resetCustomFunction()
			menuClass.resetMenus(showMenu = True)
			return True
			
	else:
		if (timeit.default_timer() - menuClass.customData['timer']) >= menuClass.customData['refreshTime']:
			
			i = Image.new('1', (menuClass.windowSettings['x_size'], menuClass.windowSettings['y_size']))
			d = ImageDraw.Draw(i)
			font_big = menuClass.getFont(size=18)
			font_small = menuClass.getFont(size=8)
			
			cpu_percent = psutil.cpu_percent(interval=None, percpu=False)
			load_average = os.getloadavg()
			
			cpu_speeds = []
			try:
				f = open('/proc/cpuinfo', 'r')
				cpuinfo = f.readlines()
				f.close()
				for l in cpuinfo:
					if 'MHz' in l:
						cpu_mhz = l.split(':')[1].split('.')[0].strip() 
						cpu_speeds.append(cpu_mhz)
			except:
				pass
	
			# Current CPU %
			d.text((0,0), str(cpu_percent) + "%", font = font_big, fill = "white")
	
			# Load average
			d.text((0,18), str(load_average) + "%", font = font_big, fill = "white")
			
			menuClass.image = copy.copy(i)
			menuClass.customData['timer'] = timeit.default_timer()
		return True

def showRestartConfirmation(menuClass = None, controlData = None):
	pass

def showShutdownConfirmation(menuClass = None, controlData = None):
	pass