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
import platform

# low level graphics libs
from PIL import Image
from PIL import ImageOps
from PIL import ImageDraw
from PIL import ImageFont

# PIL
try:
	from PIL import VERSION as PIL_VERSION
except:
	PIL_VERSION = "N/A"

# GPIO
try:
	from RPi.GPIO import VERSION as RPIGPIO_VERSION
except:
	RPIGPIO_VERSION = "N/A"

# OLED driver
try:
	import luma.oled
	LUMA_VERSION = luma.oled.__version__
except:
	LUMA_VERSION = "N/A"

# PySerial
try:
	import serial
	SERIAL_VERSION = serial.__version__
except:
	SERIAL_VERSION = "N/A"

try:
	import sdl2
	SDL2_VERSION = str(sdl2.version_info)
except:
	SDL2_VERSION = "N/A"

try:
	import gpiozero
	GPIOZERO_VERSION = "Yes"
except:
	GPIOZERO_VERSION = "N/A"

try:
	import numpy
	NUMPY_VERSION = numpy.version.version
except:
	NUMPY_VERSION = "N/A"

try:
	import lcdbackpack
	LCDBACKPACK_VERSION = "Yes"
except:
	LCDBACKPACK_VERSION = "N/A"

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
	""" Show all sensors on one or more pages, in a basic text format """
	
	if 'refreshTime' not in menuClass.customData.keys():
		menuClass.customData['refreshTime'] = 0.3
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
			font_big = menuClass.getFont(name = "pixel", style="plain", size=16)
			font_small = menuClass.getFont(name = "pixel", size=8)
			
			t = "Sensors"
			d.text((0,0), t, font = font_big, fill = "white")
			
			sensorIds = menuClass.ecudata.getSensorIds()
			if len(sensorIds) == 0:
				t = "No sensors found"
				d.text((0, 36), t, font = font_big, fill = "white")
			else:
				sensorData = menuClass.ecudata.getSensorData(sensorId = 'RPM')
				sampleData = menuClass.ecudata.getData(sensorId = 'RPM', allData = True)
				if (sensorData is not None) and (sampleData is not None):
					t = "%s: %4.0f%s" % ('RPM', sampleData[0], sensorData['sensorUnit'])
					d.text((0, 18), t, font = font_small, fill = "white")
					
			menuClass.image = copy.copy(i)
			menuClass.customData['timer'] = timeit.default_timer()
		return True

def showSysInfo(menuClass = None, controlData = None):
	""" Shows a screen with constantly updating system performance information """
	
	if 'refreshTime' not in menuClass.customData.keys():
		menuClass.customData['refreshTime'] = 1.0
		menuClass.customData['timer'] = timeit.default_timer()
		menuClass.customData['page'] = 1
	
	# We accept control data
	if controlData:
		# If we get a select or cancel button, exit the custom function
		if controlData.button in [ settings.BUTTON_SELECT, settings.BUTTON_CANCEL ]:
			menuClass.resetCustomFunction()
			menuClass.resetMenus(showMenu = True)
			return True
		
		# Turn to page 2
		if controlData.button == settings.BUTTON_RIGHT:
			if menuClass.customData['page'] == 1:
				menuClass.customData['page'] = 2
				return True
				
			if menuClass.customData['page'] == 2:
				menuClass.customData['page'] = 3
				return True
				
		# Turn to page 1
		if controlData.button == settings.BUTTON_LEFT:
			if menuClass.customData['page'] == 2:
				menuClass.customData['page'] = 1
				return True
				
			if menuClass.customData['page'] == 3:
				menuClass.customData['page'] = 2
				return True
	else:
		if (timeit.default_timer() - menuClass.customData['timer']) >= menuClass.customData['refreshTime']:
			
			i = Image.new('1', (menuClass.windowSettings['x_size'], menuClass.windowSettings['y_size']))
			d = ImageDraw.Draw(i)
			font_big = menuClass.getFont(name = "pixel", style="plain", size=16)
			font_small = menuClass.getFont(name = "pixel", size=8)
			
			########################################################################
			
			if menuClass.customData['page'] == 1:
				# Page 1
				# Performance information
				cpu_percent = psutil.cpu_percent(interval=None, percpu=False)
				load_average = os.getloadavg()
				cpu_speeds = []
				cpu_cores = psutil.cpu_count()
				try:
					f = open('/proc/cpuinfo', 'r')
					cpuinfo = f.readlines()
					f.close()
					for l in cpuinfo:
						if 'MHz' in l:
							cpu_mhz = l.split(':')[1].split('.')[0].strip() 
							cpu_speeds.append(int(cpu_mhz))
				except:
					pass
				
				t = "Processor"
				d.text((0,0), t, font = font_big, fill = "white")
				
				# Current CPU %
				t = "CPU: %s%%" % cpu_percent
				d.text((0,18), t, font = font_big, fill = "white")
				
				# Load average
				t = "Load: %s" % load_average[0] 
				d.text((120,18), t, font = font_big, fill = "white")
				
				# CPU speed and cores
				t_avg = int(sum(cpu_speeds) / cpu_cores)
				t = "Cores: %s" % cpu_cores
				d.text((0,36), t, font = font_big, fill = "white")
				t = "%sMHz" % t_avg
				d.text((120,36), t, font = font_big, fill = "white")
			
			########################################################################
			
			elif menuClass.customData['page'] == 2:
				# Page 2
				# Memory information
				t = "Memory"
				d.text((0,0), t, font = font_big, fill = "white")
			
				# Memory
				vm = psutil.virtual_memory()
				t_total = int(vm.total / (1024 * 1024))
				t_avail = int(vm.available / (1024 * 1024))
				t = "Total: %sMB" % t_total
				d.text((0,18), t, font = font_big, fill = "white")
				
				# Warning if less than 100MB available
				if t_avail <= 100:
					t = "Avail: %sMB !Warning!" % t_avail
				else:
					t = "Avail: %sMB" % t_avail
				d.text((0,36), t, font = font_big, fill = "white")
			
			########################################################################
			
			elif menuClass.customData['page'] == 3:
				# Page 3
				# Versions of software
				t = "Software Version"
				d.text((0,0), t, font = font_big, fill = "white")
				
				# Python version
				t = "Python - %s" % platform.python_version()
				d.text((0,18), t, font = font_small, fill = "white")
				
				# psutil
				t = "psutil - %s" % str(psutil.version_info)
				d.text((120,18), t, font = font_small, fill = "white")
				
				# Imaging library
				t = "PIL - %s" % PIL_VERSION
				d.text((0,26), t, font = font_small, fill = "white")
				
				# RPI.GPIO
				t = "RPi.GPIO - %s" % RPIGPIO_VERSION
				d.text((120,26), t, font = font_small, fill = "white")
				
				# OLED driver
				t = "Luma.OLED - %s" % LUMA_VERSION
				d.text((0,34), t, font = font_small, fill = "white")
				
				# gpiozero
				t = "GPIOZero - %s" % GPIOZERO_VERSION
				d.text((120,34), t, font = font_small, fill = "white")
				
				# Pyserial
				t = "PySerial - %s" % SERIAL_VERSION
				d.text((0,42), t, font = font_small, fill = "white")
				
				# Numpy
				t = "Numpy - %s" % NUMPY_VERSION
				d.text((120,42), t, font = font_small, fill = "white")
				
				# PySDL2
				t = "PySDL2 - %s" % SDL2_VERSION
				d.text((0,50), t, font = font_small, fill = "white")
				
				# lcdbackpack
				t = "LCDBackPack - %s" % LCDBACKPACK_VERSION
				d.text((120,50), t, font = font_small, fill = "white")
			
			# Page number
			t = "%s/3" % menuClass.customData['page']
			d.text((menuClass.windowSettings['x_size'] - 30, 48), t, font = font_big, fill = "white")
			
			menuClass.image = copy.copy(i)
			menuClass.customData['timer'] = timeit.default_timer()
		return True

def showRestartConfirmation(menuClass = None, controlData = None):
	pass

def showShutdownConfirmation(menuClass = None, controlData = None):
	pass