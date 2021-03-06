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


def showCurrentVisState(menuClass = None, controlData = None):
	""" Show a screen that represents what sensors are going to be shown, and what visualisation modes they each have. 
	    Allow the user to swap the left and right sensors and change the default visualisation mode for each sensor."""
	
	if 'visConfig' not in menuClass.customData.keys():
		menuClass.customData['visConfig'] = {}
		menuClass.customData['selected'] = None
		menuClass.customData['visIndexLeft'] = 0
		menuClass.customData['visIndexRight'] = 0
		menuClass.customData['visIndexFull'] = 0
		menuClass.customData['selector'] = True
		menuClass.customData['selectorSpeed'] = 0.35
		menuClass.customData['selectorTimer'] = timeit.default_timer()
	
	if controlData:
		# If we get a cancel button, exit the custom function
		if controlData.button == settings.BUTTON_CANCEL:
			menuClass.resetCustomFunction()
			menuClass.resetMenus(showMenu = True)
			return True
	
		# If we get a select button
		if controlData.button == settings.BUTTON_SELECT:
			if menuClass.customData['selected'] == 'left':
				# Turn the sensor off
				if settings.GFX_MODES[menuClass.customData['visIndexLeft']] == settings.GFX_MODE_OFF:
					menuClass.leftVisualisation = menuClass.defaultVisualisation
					menuClass.selectedSensors['left'] = None
				else:
					# Set the vis mode
					menuClass.leftVisualisation = settings.GFX_MODES[menuClass.customData['visIndexLeft']]
				
			if menuClass.customData['selected'] == 'right':
				# Turn the sensor off
				if settings.GFX_MODES[menuClass.customData['visIndexRight']] == settings.GFX_MODE_OFF:
					menuClass.rightVisualisation = menuClass.defaultVisualisation
					menuClass.selectedSensors['right'] = None
				else:
					# Set the vis mode
					menuClass.rightVisualisation = settings.GFX_MODES[menuClass.customData['visIndexRight']]
				
			if menuClass.customData['selected'] == 'full':
				# Turn the sensor off
				if settings.GFX_MODES[menuClass.customData['visIndexFull']] == settings.GFX_MODE_OFF:
					menuClass.fullVisualisation = menuClass.defaultVisualisation
					menuClass.selectedSensors['full'] = None
				else:
					# Set the vis mode
					menuClass.fullVisualisation = settings.GFX_MODES[menuClass.customData['visIndexFull']]
			
			return True
	
		# If we get a left button  select the left window
		if controlData.button == settings.BUTTON_LEFT:
			if (menuClass.selectedSensors['full'] is None):
				menuClass.customData['selected'] = 'left'
			return True
		
		# If we get a right button  select the right window
		if controlData.button == settings.BUTTON_RIGHT:
			if (menuClass.selectedSensors['full'] is None):
				menuClass.customData['selected'] = 'right'
			return True
				
		# If a box is selected and we get an up or down, scroll to next vis mode
		if controlData.button in [settings.BUTTON_UP, settings.BUTTON_DOWN] and (menuClass.customData['selected'] is not None):
			
			# Scroll up through list
			if controlData.button == settings.BUTTON_UP:
				if menuClass.customData['selected'] == 'left':
					# Have we reached end of list?
					if menuClass.customData['visIndexLeft'] < (len(settings.GFX_MODES) - 1):
						menuClass.customData['visIndexLeft'] += 1
					else:
						menuClass.customData['visIndexLeft'] = 0
				if menuClass.customData['selected'] == 'right':
					# Have we reached end of list?
					if menuClass.customData['visIndexRight'] < (len(settings.GFX_MODES) - 1):
						menuClass.customData['visIndexRight'] += 1
					else:
						menuClass.customData['visIndexRight'] = 0
				if menuClass.customData['selected'] == 'full':
					# Have we reached end of list?
					if menuClass.customData['visIndexFull'] < (len(settings.GFX_MODES) - 1):
						menuClass.customData['visIndexFull'] += 1
					else:
						menuClass.customData['visIndexFull'] = 0
						
			# Scroll down through list
			if controlData.button == settings.BUTTON_DOWN:
				if menuClass.customData['selected'] == 'left':
					# Have we reached end of list?
					if menuClass.customData['visIndexLeft'] > 0:
						menuClass.customData['visIndexLeft'] -= 1
					else:
						menuClass.customData['visIndexLeft'] = 0
				if menuClass.customData['selected'] == 'right':
					# Have we reached end of list?
					if menuClass.customData['visIndexRight'] > 0:
						menuClass.customData['visIndexRight'] -= 1
					else:
						menuClass.customData['visIndexRight'] = 0
				if menuClass.customData['selected'] == 'full':
					# Have we reached end of list?
					if menuClass.customData['visIndexFull'] > 0:
						menuClass.customData['visIndexFull'] -= 1
					else:
						menuClass.customData['visIndexFull'] = 0
		return True	
	
	font_big = menuClass.getFont(name = "pixel", style="header", size=16)
	font_small = menuClass.getFont(name = "pixel", style="plain", size=8)
	i = Image.new('1', (menuClass.windowSettings['x_size'], menuClass.windowSettings['y_size']))
	d = ImageDraw.Draw(i)
		
	title = "Configure Screen Layout"
	d.text((0,0), title, font = font_big, fill = "white")
	title_size = font_big.getsize(title)
	icon = Image.open(settings.GFX_ICONS['monitor']['icon'])
	i.paste(icon,(menuClass.windowSettings['x_size'] - settings.GFX_ICONS['monitor']['size'][0],0))
	
	exit_text1 = "U/D:Mode   L/R:Switch   Select:Save   Cancel:Exit"
	#exit_text2 = "Select: Save settings.  Cancel: Return to menu."
	exit_text_size = font_small.getsize(exit_text1)
	#d.text((0,menuClass.windowSettings['y_size'] - exit_text_size[1] - 1), exit_text2, font = font_small, fill = "white")
	d.text((0,menuClass.windowSettings['y_size'] - exit_text_size[1] - 1), exit_text1, font = font_small, fill = "white")
	
	if (timeit.default_timer() - menuClass.customData['selectorTimer']) >= menuClass.customData['selectorSpeed']:
		menuClass.customData['selector'] = not(menuClass.customData['selector'])
		menuClass.customData['selectorTimer'] = timeit.default_timer()
	
	if (menuClass.selectedSensors['full'] is not None) or (menuClass.selectedSensors['left'] is not None) or (menuClass.selectedSensors['right'] is not None):
		# Full screen sensor configured
		if (menuClass.selectedSensors['full'] is not None):
			
			menuClass.customData['selected'] = 'full'
			sensorId = menuClass.selectedSensors['full']
			logger.debug("A fullscreen sensor is selected [%s]" % sensorId)
			
			x_start = 0
			y_start = title_size[1] + 1
			x_end = 200
			y_end = (menuClass.windowSettings['y_size'] - exit_text_size[1]) - 2
			d.rectangle([(x_start, y_start), (x_end,  y_end)], outline="white", fill=0 )
			# Print sensor name
			t = "%s - Fullscreen" % sensorId
			d.text((x_start + 2, y_start + 2), t, font = font_big, fill = "white")
			
			# Paste in bitmap of currently selected visualisation
			if menuClass.fullVisualisation == settings.GFX_MODE_WAVEFORM:
				visText = "Now: Waveform"
			elif menuClass.fullVisualisation == settings.GFX_MODE_SEGMENTS:
				visText = "Now: LED Segment"
			elif menuClass.fullVisualisation == settings.GFX_MODE_CLOCK:
				visText = "Now: Clock"
			elif menuClass.fullVisualisation == settings.GFX_MODE_LINE:
				visText = "Now: Log Graph"
			else:
				visText = "Unknown Mode!"
			sensorId_size = font_big.getsize(sensorId)
			visText_size = font_small.getsize(visText)
			d.text((x_start + 2, y_start + sensorId_size[1] + 2), visText, font = font_small, fill = "white")
			
			nextVis = settings.GFX_MODES[menuClass.customData['visIndexFull']]
			nextVisText = "Next: %s" % nextVis
			d.text((x_start + 2, y_start + sensorId_size[1] + visText_size[1] + 2), nextVisText, font = font_small, fill = "white")
			
			if menuClass.customData['selector']:
				selector = Image.open(settings.GFX_ICONS['selector']['outer'])
			else:
				selector = Image.open(settings.GFX_ICONS['selector']['inner'])
			i.paste(selector, (x_end - settings.GFX_ICONS['selector']['size'][0] - 1, y_start + 1))
			
		else:
			# Left sensor configured
			if (menuClass.selectedSensors['left'] is not None):
				sensorId = menuClass.selectedSensors['left']
				logger.debug("A left sensor is selected [%s]" % sensorId)
				x_start = 0
				y_start = title_size[1] + 1
				x_end = 100
				y_end = (menuClass.windowSettings['y_size'] - exit_text_size[1]) - 2
				d.rectangle([(x_start, y_start), (x_end,  y_end)], outline="white", fill=0 )
				# Print sensor name
				d.text((x_start + 2, y_start + 2), sensorId, font = font_big, fill = "white")
								
				# Paste in bitmap of currently selected visualisation
				if menuClass.leftVisualisation == settings.GFX_MODE_WAVEFORM:
					visText = "Now: Waveform"
				elif menuClass.leftVisualisation == settings.GFX_MODE_SEGMENTS:
					visText = "Now: LED Segment"
				elif menuClass.leftVisualisation == settings.GFX_MODE_CLOCK:
					visText = "Now: Clock"
				elif menuClass.leftVisualisation == settings.GFX_MODE_LINE:
					visText = "Now: Log Graph"
				else:
					visText = "Unknown Mode!"
				sensorId_size = font_big.getsize(sensorId)
				visText_size = font_small.getsize(visText)
				d.text((x_start + 2, y_start + sensorId_size[1] + 2), visText, font = font_small, fill = "white")
				
				nextVis = settings.GFX_MODES[menuClass.customData['visIndexLeft']]
				nextVisText = "Next: %s" % nextVis
				d.text((x_start + 2, y_start + sensorId_size[1] + visText_size[1] + 2), nextVisText, font = font_small, fill = "white")
			else:
				# show blank space
				x_start = 0
				y_start = title_size[1] + 1
				x_end = 100
				y_end = (menuClass.windowSettings['y_size'] - exit_text_size[1]) - 2
				d.rectangle([(x_start, y_start), (x_end,  y_end)], outline="white", fill=0 )
				d.text((x_start + 2, y_start + 2), "Free", font = font_big, fill = "white")
				
			if menuClass.customData['selected'] == 'left':
				if menuClass.customData['selector']:
					selector = Image.open(settings.GFX_ICONS['selector']['outer'])
				else:
					selector = Image.open(settings.GFX_ICONS['selector']['inner'])
				i.paste(selector, (x_end - settings.GFX_ICONS['selector']['size'][0] - 1, y_start + 1))
				
			# Right sensor configured
			if (menuClass.selectedSensors['right'] is not None):
				sensorId = menuClass.selectedSensors['right']
				logger.debug("A right sensor is selected [%s]" % sensorId)
				x_start = 100
				y_start = title_size[1] + 1
				x_end = 200
				y_end = (menuClass.windowSettings['y_size'] - exit_text_size[1]) - 2
				d.rectangle([(x_start, y_start), (x_end,  y_end)], outline="white", fill=0 )
				# Print sensor name
				d.text((x_start + 2, y_start + 2), sensorId, font = font_big, fill = "white")
				
				# Paste in bitmap of currently selected visualisation
				if menuClass.rightVisualisation == settings.GFX_MODE_WAVEFORM:
					visText = "Now: Waveform"
				elif menuClass.rightVisualisation == settings.GFX_MODE_SEGMENTS:
					visText = "Now: LED Segment"
				elif menuClass.rightVisualisation == settings.GFX_MODE_CLOCK:
					visText = "Now: Clock"
				elif menuClass.rightVisualisation == settings.GFX_MODE_LINE:
					visText = "Now: Log Graph"
				else:
					visText = "Unknown Mode!"
				sensorId_size = font_big.getsize(sensorId)
				visText_size = font_small.getsize(visText)
				d.text((x_start + 2, y_start + sensorId_size[1] + 2), visText, font = font_small, fill = "white")
				nextVis = settings.GFX_MODES[menuClass.customData['visIndexRight']]
				nextVisText = "Next: %s" % nextVis
				d.text((x_start + 2, y_start + sensorId_size[1] + visText_size[1] + 2), nextVisText, font = font_small, fill = "white")
			else:
				# show blank space
				x_start = 100
				y_start = title_size[1] + 1
				x_end = 200
				y_end = (menuClass.windowSettings['y_size'] - exit_text_size[1]) - 2
				d.rectangle([(x_start, y_start), (x_end,  y_end)], outline="white", fill=0 )
				d.text((x_start + 2, y_start + 2), "Free", font = font_big, fill = "white")
				
			if menuClass.customData['selected'] == 'right':
				if menuClass.customData['selector']:
					selector = Image.open(settings.GFX_ICONS['selector']['outer'])
				else:
					selector = Image.open(settings.GFX_ICONS['selector']['inner'])
				i.paste(selector, (x_end - settings.GFX_ICONS['selector']['size'][0] - 1, y_start + 1))
	else:
		# Nothing configured yet
		logger.debug("No sensors are selected")
		d.text((2, 26), "No sensors selected!", font = font_big, fill = "white")
	
	menuClass.image = copy.copy(i)
	return True
	
def sensorVisualisation(menuClass = None, controlData = None):
	""" Run visualisation of at least one selected sensor """
		
	if 'displayModes' not in menuClass.windowSettings.keys():
		menuClass.windowSettings['displayModes'] = {}
		for sensor in settings.SENSORS:
			sensorId = sensor['sensorId']	
			menuClass.windowSettings['displayModes'][sensorId] = sensorGraphicsInit(sensor, menuClass.windowSettings)
		menuClass.windowSettings['halfDisplayModes'] = {}
		for sensor in settings.SENSORS:
			sensorId = sensor['sensorId']	
			menuClass.windowSettings['halfDisplayModes'][sensorId] = sensorGraphicsInit(sensor, menuClass.windowSettings, scale_x = 2) # Assume half x resolution
			
	if controlData:
		# If we get a select or cancel button, exit the custom function
		if controlData.button in [ settings.BUTTON_SELECT, settings.BUTTON_CANCEL ]:
			menuClass.resetCustomFunction()
			menuClass.resetMenus(showMenu = True)
			return True
			
	font_big = menuClass.getFont(name = "pixel", style="header", size=16)
	font_small = menuClass.getFont(name = "pixel", style="plain", size=8)
		
	if (menuClass.selectedSensors['full'] is not None):
		
		# Render a fullscreen sensor visualisation
		sensorId = menuClass.selectedSensors['full']
		value = menuClass.ecudata.getData(sensorId)
		if value:
			menuClass.windowSettings['displayModes'][sensorId]['previousValues'].append(value)
		sensorData = menuClass.ecudata.getSensorData(sensorId)
		if menuClass.fullVisualisation == settings.GFX_MODE_WAVEFORM:
			image = gaugeWaveform(ecudata = menuClass.ecudata, sensor = menuClass.windowSettings['displayModes'][sensorId], font = font_big, windowSettings = menuClass.windowSettings, sensorData = sensorData)
		elif menuClass.fullVisualisation == settings.GFX_MODE_SEGMENTS:
			image = gaugeLEDSegments(ecudata = menuClass.ecudata, sensor = menuClass.windowSettings['displayModes'][sensorId], font = font_big, windowSettings = menuClass.windowSettings, sensorData = sensorData)
		elif menuClass.fullVisualisation == settings.GFX_MODE_LINE:
			image = gaugeLine(ecudata = menuClass.ecudata, sensor = menuClass.windowSettings['displayModes'][sensorId], font = font_big, windowSettings = menuClass.windowSettings, sensorData = sensorData)
		elif menuClass.fullVisualisation == settings.GFX_MODE_CLOCK:
			image = gaugeClock(ecudata = menuClass.ecudata, sensor = menuClass.windowSettings['displayModes'][sensorId], font = font_big, windowSettings = menuClass.windowSettings, sensorData = sensorData)
		
		menuClass.image = image.copy()
	elif (menuClass.selectedSensors['left'] is not None) or (menuClass.selectedSensors['right'] is not None):
		
		# New blank image
		i = Image.new('1', (menuClass.windowSettings['x_size'], menuClass.windowSettings['y_size']))
		
		# Store the original x resolution
		old_x = menuClass.windowSettings['x_size']
		menuClass.windowSettings['x_size'] = int(menuClass.windowSettings['x_size'] / 2)
		# Render a left side sensor visualisation
		# paste bitmap at:
		if (menuClass.selectedSensors['left'] is not None):
			x = 0
			y = 0
			# Render a fullscreen sensor visualisation
			sensorId = menuClass.selectedSensors['left']
			value = menuClass.ecudata.getData(sensorId)
			if value:
				menuClass.windowSettings['halfDisplayModes'][sensorId]['previousValues'].append(value)
			sensorData = menuClass.ecudata.getSensorData(sensorId)
			if menuClass.leftVisualisation == settings.GFX_MODE_WAVEFORM:
				image = gaugeWaveform(ecudata = menuClass.ecudata, sensor = menuClass.windowSettings['halfDisplayModes'][sensorId], font = font_big, windowSettings = menuClass.windowSettings, sensorData = sensorData)
			elif menuClass.leftVisualisation == settings.GFX_MODE_SEGMENTS:
				image = gaugeLEDSegments(ecudata = menuClass.ecudata, sensor = menuClass.windowSettings['halfDisplayModes'][sensorId], font = font_big, windowSettings = menuClass.windowSettings, sensorData = sensorData)
			elif menuClass.leftVisualisation == settings.GFX_MODE_LINE:
				image = gaugeLine(ecudata = menuClass.ecudata, sensor = menuClass.windowSettings['halfDisplayModes'][sensorId], font = font_big, windowSettings = menuClass.windowSettings, sensorData = sensorData)
			elif menuClass.leftVisualisation == settings.GFX_MODE_CLOCK:
				image = gaugeClock(ecudata = menuClass.ecudata, sensor = menuClass.windowSettings['halfDisplayModes'][sensorId], font = font_big, windowSettings = menuClass.windowSettings, sensorData = sensorData)
			i.paste(image, (x, y))
	
		if (menuClass.selectedSensors['right'] is not None):
			# Render a right side sensor visualisation
			# paste bitmap at:
			x = menuClass.windowSettings['x_size']
			y = 0
			# Render a fullscreen sensor visualisation
			sensorId = menuClass.selectedSensors['right']
			value = menuClass.ecudata.getData(sensorId)
			if value:
				menuClass.windowSettings['halfDisplayModes'][sensorId]['previousValues'].append(value)
			sensorData = menuClass.ecudata.getSensorData(sensorId)
			if menuClass.rightVisualisation == settings.GFX_MODE_WAVEFORM:
				image = gaugeWaveform(ecudata = menuClass.ecudata, sensor = menuClass.windowSettings['halfDisplayModes'][sensorId], font = font_big, windowSettings = menuClass.windowSettings, sensorData = sensorData)
			elif menuClass.rightVisualisation == settings.GFX_MODE_SEGMENTS:
				image = gaugeLEDSegments(ecudata = menuClass.ecudata, sensor = menuClass.windowSettings['halfDisplayModes'][sensorId], font = font_big, windowSettings = menuClass.windowSettings, sensorData = sensorData)
			elif menuClass.rightVisualisation == settings.GFX_MODE_LINE:
				image = gaugeLine(ecudata = menuClass.ecudata, sensor = menuClass.windowSettings['halfDisplayModes'][sensorId], font = font_big, windowSettings = menuClass.windowSettings, sensorData = sensorData)
			elif menuClass.rightVisualisation == settings.GFX_MODE_CLOCK:
				image = gaugeClock(ecudata = menuClass.ecudata, sensor = menuClass.windowSettings['halfDisplayModes'][sensorId], font = font_big, windowSettings = menuClass.windowSettings, sensorData = sensorData)
			i.paste(image, (x, y))
			
		# Paste the combined image
		menuClass.image = i.copy()
		# Restore full x resolution
		menuClass.windowSettings['x_size'] = old_x
	else:
		i = Image.new('1', (menuClass.windowSettings['x_size'], menuClass.windowSettings['y_size']))
		d = ImageDraw.Draw(i)
			
		title = "ERROR!"
		d.text((0,0), title, font = font_big, fill = "white")
		
		icon = Image.open(settings.GFX_ICONS['sensor']['icon'])
		i.paste(icon,(menuClass.windowSettings['x_size'] - settings.GFX_ICONS['sensor']['size'][0],0))
		
		text = "No sensors selected. Choose one or more."
		d.text((0,30), text, font = font_small, fill = "white")
		
		text = "Press Select to return to menu"
		d.text((0,40), text, font = font_small, fill = "white")
		menuClass.image = copy.copy(i)
		return True

def sensorSelectFull(menuClass = None, controlData = None):
	""" Selects a sensor to display full width in the main window """
	
	menuClass.selectedSensors['left'] = None
	menuClass.selectedSensors['right'] = None
	
	if controlData:
		# If we get a select or cancel button, exit the custom function
		if controlData.button in [ settings.BUTTON_SELECT, settings.BUTTON_CANCEL ]:
			menuClass.resetCustomFunction()
			menuClass.resetMenus(showMenu = True)
			# Activate visualisation
			return sensorVisualisation

	font_big = menuClass.getFont(name = "pixel", style="header", size=16)
	font_small = menuClass.getFont(name = "pixel", style="plain", size=8)
	i = Image.new('1', (menuClass.windowSettings['x_size'], menuClass.windowSettings['y_size']))
	d = ImageDraw.Draw(i)
		
	title = "Sensor Config"
	d.text((0,0), title, font = font_big, fill = "white")
	
	icon = Image.open(settings.GFX_ICONS['sensor']['icon'])
	i.paste(icon,(menuClass.windowSettings['x_size'] - settings.GFX_ICONS['sensor']['size'][0],0))
	
	menuIndex = menuClass.customData['selectedItem'][0]
	subMenuIndex = menuClass.customData['selectedItem'][1]
	items = copy.copy(menuClass.menu[menuIndex]['items'])
	items.reverse()
	sensorId = items[subMenuIndex]['itemName']
	menuClass.selectedSensors['full'] = sensorId

	text = "%s is set for FULL width" % sensorId
	d.text((0,30), text, font = font_small, fill = "white")
	
	text = "Press Select to return to menu"
	d.text((0,40), text, font = font_small, fill = "white")
	menuClass.image = copy.copy(i)
	return True

def sensorSelectLeft(menuClass = None, controlData = None):
	""" Select the left hand sensor to display in the main window """
	
	menuClass.selectedSensors['full'] = None
	
	if controlData:
		# If we get a select or cancel button, exit the custom function
		if controlData.button in [ settings.BUTTON_SELECT, settings.BUTTON_CANCEL ]:
			menuClass.resetCustomFunction()
			menuClass.resetMenus(showMenu = True)
			# Activate visualisation
			return sensorVisualisation
	
	font_big = menuClass.getFont(name = "pixel", style="header", size=16)
	font_small = menuClass.getFont(name = "pixel", style="plain", size=8)
	i = Image.new('1', (menuClass.windowSettings['x_size'], menuClass.windowSettings['y_size']))
	d = ImageDraw.Draw(i)
		
	title = "Sensor Config"
	d.text((0,0), title, font = font_big, fill = "white")
	icon = Image.open(settings.GFX_ICONS['sensor']['icon'])
	i.paste(icon,(menuClass.windowSettings['x_size'] - settings.GFX_ICONS['sensor']['size'][0],0))		
			
	menuIndex = menuClass.customData['selectedItem'][0]
	subMenuIndex = menuClass.customData['selectedItem'][1]
	items = copy.copy(menuClass.menu[menuIndex]['items'])
	items.reverse()
	sensorId = items[subMenuIndex]['itemName']
	menuClass.selectedSensors['left'] = sensorId

	text = "%s is selected as LEFT" % sensorId
	d.text((0,30), text, font = font_small, fill = "white")
	
	text = "Press Select to return to menu"
	d.text((0,40), text, font = font_small, fill = "white")
	menuClass.image = copy.copy(i)
	return True
	
def sensorSelectRight(menuClass = None, controlData = None):
	""" Selects the right hand sensor to display in the main window """

	menuClass.selectedSensors['full'] = None
	
	if controlData:
		# If we get a select or cancel button, exit the custom function
		if controlData.button in [ settings.BUTTON_SELECT, settings.BUTTON_CANCEL ]:
			menuClass.resetCustomFunction()
			menuClass.resetMenus(showMenu = True)
			# Activate visualisation on exit
			return sensorVisualisation
			
	font_big = menuClass.getFont(name = "pixel", style="header", size=16)
	font_small = menuClass.getFont(name = "pixel", style="plain", size=8)
	i = Image.new('1', (menuClass.windowSettings['x_size'], menuClass.windowSettings['y_size']))
	d = ImageDraw.Draw(i)
		
	title = "Sensor Config"
	d.text((0,0), title, font = font_big, fill = "white")
	icon = Image.open(settings.GFX_ICONS['sensor']['icon'])
	i.paste(icon,(menuClass.windowSettings['x_size'] - settings.GFX_ICONS['sensor']['size'][0],0))		
			
	menuIndex = menuClass.customData['selectedItem'][0]
	subMenuIndex = menuClass.customData['selectedItem'][1]
	items = copy.copy(menuClass.menu[menuIndex]['items'])
	items.reverse()
	sensorId = items[subMenuIndex]['itemName']
	menuClass.selectedSensors['right'] = sensorId

	text = "%s is now selected as RIGHT" % sensorId
	d.text((0,30), text, font = font_small, fill = "white")
	
	text = "Press Select to return to menu"
	d.text((0,40), text, font = font_small, fill = "white")
	menuClass.image = copy.copy(i)
	return True
	
def showLoggingState(menuClass = None, controlData = None):
	
	if 'loggerData' not in menuClass.customData.keys():
		menuClass.customData['loggerData'] = {}
		menuClass.customData['lastUpdate'] = time.time()
		menuClass.customData['tick'] = False
		menuClass.customData['tickSpeed'] = 0.5
		menuClass.customData['tickTimer'] = timeit.default_timer()
	
	if controlData:
		# If we get a select or cancel button, exit the custom function
		if controlData.button in [ settings.BUTTON_SELECT, settings.BUTTON_CANCEL ]:
			menuClass.resetCustomFunction()
			menuClass.resetMenus(showMenu = True)
			return True
	
	# if we got a datalogger status message, update our locally held data
	if controlData:
		if controlData.button == settings.BUTTON_LOGGING_STATUS:
			menuClass.customData['lastUpdate'] = time.time()
			menuClass.customData['loggerData'] = controlData.getPayload()
	
	font_big = menuClass.getFont(name = "pixel", style="header", size=16)
	font_small = menuClass.getFont(name = "pixel", style="plain", size=8)
	
	log_keys = menuClass.customData['loggerData'].keys()
	if 'status' in log_keys:
		if menuClass.customData['loggerData']['status'] == True:
			recording = True
			t1 = "Status: Recording"
		else:
			recording = False
			t1 = "Status: Not running"
	else:
		recording = False
		t1 = "Status: N/A"
		
	# Number of samples in log
	if 'sampleCount' in log_keys:
		t2 = "Samples: %s" % menuClass.customData['loggerData']['sampleCount']
	else:
		t2 = "Samples: N/A"
		
	# Name of logfile
	if 'logFile' in log_keys:
		t3 = "File name: %s" % menuClass.customData['loggerData']['logFile']
	else:
		t3 = "File name: N/A"
		
	# Size of logfile
	if 'fileSize' in log_keys:
		t4 = "File size: %.2f MBytes" % menuClass.customData['loggerData']['fileSize']
	else:
		t4 = "File size: N/A"
		
	# Available disk space
	try:
		logdir = os.getcwd() + "/" + settings.LOGGING_DIR
		disk_use = psutil.disk_usage(logdir)
		avail_mbytes = int(disk_use.free / 1024 / 1024)
		t5 = "Disk space: %s MBytes" % avail_mbytes
	except Exception as e:
		logger.error("Unable to calculate disk space")
		logger.error("%s" % e)
		t5 = "WARNING: Unable to calculate disk space!"
	
	####### Cache this
	if (timeit.default_timer() - menuClass.customData['tickTimer']) >= menuClass.customData['tickSpeed']:
		menuClass.customData['tick'] = not(menuClass.customData['tick'])
		menuClass.customData['tickTimer'] = timeit.default_timer()
	
	if recording:
		k = "showLoggingState|recording:True,tick:%s" % menuClass.customData['tick']
	else:
		k = "showLoggingState|recording:False"
	if k in menuClass.bitmapCache.keys():
		i = menuClass.bitmapCache[key].copy()
		d = ImageDraw.Draw(i)	
	else:
		i = Image.new('1', (menuClass.windowSettings['x_size'], menuClass.windowSettings['y_size']))
		d = ImageDraw.Draw(i)	
		title = "Data Logging"
		d.text((0,0), title, font = font_big, fill = "white")
		if recording:
			if menuClass.customData['tick']:
				icon = Image.open(settings.GFX_ICONS['stopwatch']['icon'])
				i.paste(icon,(menuClass.windowSettings['x_size'] - settings.GFX_ICONS['stopwatch']['size'][0],0))
			else:
				icon = Image.open(settings.GFX_ICONS['stopwatch']['alt'])
				i.paste(icon,(menuClass.windowSettings['x_size'] - settings.GFX_ICONS['stopwatch']['size'][0],0))
		else:
			icon = Image.open(settings.GFX_ICONS['stopwatch']['icon'])
			i.paste(icon,(menuClass.windowSettings['x_size'] - settings.GFX_ICONS['stopwatch']['size'][0],0))
	####### end cache
	
	
	d.text((0,20), t1, font = font_small, fill = "white")
	d.text((0,28), t2, font = font_small, fill = "white")
	d.text((0,36), t3, font = font_small, fill = "white")
	d.text((0,44), t4, font = font_small, fill = "white")
	d.text((0,52), t5, font = font_small, fill = "white")
	menuClass.image = copy.copy(i)
	return True

def startLogging(menuClass = None, controlData = None):
	
	if 'messageStatus' not in menuClass.customData.keys():
		menuClass.customData['messageStatus'] = "unsent"
	
	# We accept control data
	if controlData:
		# If we get a select or cancel button, exit the custom function
		if controlData.button in [ settings.BUTTON_SELECT, settings.BUTTON_CANCEL ]:
			menuClass.resetCustomFunction()
			menuClass.resetMenus(showMenu = True)
			return True
	
	font_big = menuClass.getFont(name = "pixel", style="header", size=16)
	font_small = menuClass.getFont(name = "pixel", style="plain", size=8)
	i = Image.new('1', (menuClass.windowSettings['x_size'], menuClass.windowSettings['y_size']))
	d = ImageDraw.Draw(i)
	
	title = "Data Logging"
	d.text((0,0), title, font = font_big, fill = "white")
	
	icon = Image.open(settings.GFX_ICONS['stopwatch']['icon'])
	i.paste(icon,(menuClass.windowSettings['x_size'] - settings.GFX_ICONS['stopwatch']['size'][0],0))
	
	text = "Datalogger is now starting"
	d.text((0,30), text, font = font_small, fill = "white")
	
	text = "Press Select to return to menu"
	d.text((0,40), text, font = font_small, fill = "white")
	menuClass.image = copy.copy(i)
	
	if menuClass.customData['messageStatus'] != "sent":
		cdata = ControlData()
		cdata.setButton(settings.BUTTON_LOGGING_RUNNING)	
		menuClass.actionQueue.put(cdata)
		menuClass.customData['messageStatus'] = "sent"
	return True

def stopLogging(menuClass = None, controlData = None):
	
	if 'messageStatus' not in menuClass.customData.keys():
		menuClass.customData['messageStatus'] = "unsent"
	
	# We accept control data
	if controlData:
		# If we get a select or cancel button, exit the custom function
		if controlData.button in [ settings.BUTTON_SELECT, settings.BUTTON_CANCEL ]:
			menuClass.resetCustomFunction()
			menuClass.resetMenus(showMenu = True)
			return True
	
	font_big = menuClass.getFont(name = "pixel", style="header", size=16)
	font_small = menuClass.getFont(name = "pixel", style="plain", size=8)
	i = Image.new('1', (menuClass.windowSettings['x_size'], menuClass.windowSettings['y_size']))
	d = ImageDraw.Draw(i)
	
	title = "Data Logging"
	d.text((0,0), title, font = font_big, fill = "white")
	
	icon = Image.open(settings.GFX_ICONS['stopwatch']['icon'])
	i.paste(icon,(menuClass.windowSettings['x_size'] - settings.GFX_ICONS['stopwatch']['size'][0],0))
	
	text = "Datalogger is stopping"
	d.text((0,30), text, font = font_small, fill = "white")
	
	text = "Press Select to return to menu"
	d.text((0,40), text, font = font_small, fill = "white")
	menuClass.image = copy.copy(i)
	
	if menuClass.customData['messageStatus'] != "sent":
		cdata = ControlData()
		cdata.setButton(settings.BUTTON_LOGGING_STOPPED)
		menuClass.actionQueue.put(cdata)
		menuClass.customData['messageStatus'] = "sent"
	return True

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
		menuClass.customData['page'] = 1
		menuClass.customData['sensorColumns'] = 2
		if menuClass.customData['sensorColumns'] > 1:
			menuClass.customData['sensorColumnOffsets'] = int(menuClass.windowSettings['x_size'] / menuClass.customData['sensorColumns'])
		else:
			menuClass.customData['sensorColumnOffsets'] = 0
		
	font_big = menuClass.getFont(name = "pixel", style="header", size=16)
	font_small = menuClass.getFont(name = "pixel", style="plain", size=8)
	title = "Sensors"
	
	# How many sensors can we fit on a page?
	sensorIds = menuClass.ecudata.getSensorIds()
	sensorIds.sort()
	if len(sensorIds) > 0:
		title_size = font_big.getsize(title)
		sensor_size = font_small.getsize("Example")
		available_y_size = menuClass.windowSettings['y_size'] - (title_size[1] + 1)
		menuClass.customData['sensorsPerPage'] = int((available_y_size / (sensor_size[1] + 1)) * menuClass.customData['sensorColumns'])
		pages, remaining = divmod(len(sensorIds), menuClass.customData['sensorsPerPage'])
		real_pages = int(pages + int(bool(remaining)))
		menuClass.customData['pages'] = real_pages
		menuClass.customData['sensorPerColumn'] = int(menuClass.customData['sensorsPerPage'] / menuClass.customData['sensorColumns'])
	else:
		menuClass.customData['sensorsPerPage'] = 0
		menuClass.customData['sensorPerColumn'] = 0
		menuClass.customData['pages'] = 1
		
	# We accept control data
	if controlData:
		# If we get a select or cancel button, exit the custom function
		if controlData.button in [ settings.BUTTON_SELECT, settings.BUTTON_CANCEL ]:
			menuClass.resetCustomFunction()
			menuClass.resetMenus(showMenu = True)
			return True
			
		# Turn to next page
		if controlData.button == settings.BUTTON_RIGHT:
			if menuClass.customData['page'] < menuClass.customData['pages']:
				menuClass.customData['page'] += 1
				return True
				
		# Turn to previous page
		if controlData.button == settings.BUTTON_LEFT:
			if menuClass.customData['page'] > 1:
				menuClass.customData['page'] -= 1
				return True

	else:
		if (timeit.default_timer() - menuClass.customData['timer']) >= menuClass.customData['refreshTime']:
						
			i = Image.new('1', (menuClass.windowSettings['x_size'], menuClass.windowSettings['y_size']))
			icon = Image.open(settings.GFX_ICONS['sensor']['icon'])
			i.paste(icon,(menuClass.windowSettings['x_size'] - settings.GFX_ICONS['sensor']['size'][0],0))
			d = ImageDraw.Draw(i)
			d.text((0,0), title, font = font_big, fill = "white")
			
			if len(sensorIds) == 0:
				t = "No sensors found"
				d.text((0, 36), t, font = font_big, fill = "white")
			else:
				# which sensors
				sensor_start = (menuClass.customData['page'] - 1) * menuClass.customData['sensorsPerPage']
				sensor_end = sensor_start + menuClass.customData['sensorsPerPage']
				prev_col = 0
				idx = 0
				inner_idx = 0
				for sensorId in sensorIds[sensor_start:sensor_end]:
					# Column
					col = int(idx / menuClass.customData['sensorPerColumn'])
					
					# Reset y pos if we moved to the next column
					if prev_col != col:
						inner_idx = 0
						prev_col = col
					x_pos = col * menuClass.customData['sensorColumnOffsets']
					y_pos = (title_size[1]) + (sensor_size[1] * inner_idx)
				
					sensorData = menuClass.ecudata.getSensorData(sensorId = sensorId)
					sampleData = menuClass.ecudata.getData(sensorId = sensorId, allData = True)
					if (sensorData is not None) and (sampleData is not None):
						t = "%s: %4.1f%s" % (sensorId, sampleData[0], sensorData['sensorUnit'])
						d.text((x_pos, y_pos), t, font = font_small, fill = "white")
					else:
						t = "%s: No Data" % sensorId
						d.text((x_pos, y_pos), t, font = font_small, fill = "white")
					idx += 1
					inner_idx += 1
				
			# Page number
			t = "%s/%s" % (menuClass.customData['page'], menuClass.customData['pages'])
			d.text((menuClass.windowSettings['x_size'] - 30, 48), t, font = font_big, fill = "white")
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
			icon = Image.open(settings.GFX_ICONS['microchip']['icon'])
			i.paste(icon,(menuClass.windowSettings['x_size'] - settings.GFX_ICONS['microchip']['size'][0],0))
		
			#font_big = menuClass.getFont(name = "pixel", style="plain", size=16)
			#font_small = menuClass.getFont(name = "pixel", size=8)
			font_big = menuClass.getFont(name = "pixel", style="header", size=16)
			font_small = menuClass.getFont(name = "pixel", style="plain", size=8)
			
			########################################################################
			
			if menuClass.customData['page'] == 1:
				# Page 1
				# Performance information
				cpu_percent = psutil.cpu_percent(interval=None, percpu=False)
				load_average = os.getloadavg()
				cpu_speeds = []
				cpu_cores = psutil.cpu_count()
				cpu_model = "Unknown CPU"
				try:
					f = open('/proc/cpuinfo', 'r')
					cpuinfo = f.readlines()
					f.close()
					for l in cpuinfo:
						if 'model name' in l:
							cpu_model = l.split(':')[1].strip()
						if 'MHz' in l:
							cpu_mhz = l.split(':')[1].split('.')[0].strip() 
							cpu_speeds.append(int(cpu_mhz))
				except:
					pass
				
				t = "Processor"
				d.text((0,0), t, font = font_big, fill = "white")
				
				# CPU model
				t = "%s" % cpu_model
				d.text((0,18), t, font = font_small, fill = "white")
				
				# Current CPU %
				t = "CPU Use: %s%%" % cpu_percent
				d.text((0,30), t, font = font_small, fill = "white")
				
				# Load average
				t = "Current Load: %s" % load_average[0] 
				d.text((80,30), t, font = font_small, fill = "white")
				
				# CPU speed and cores
				t_avg = int(sum(cpu_speeds) / cpu_cores)
				t = "Cores: %s" % cpu_cores
				d.text((0,42), t, font = font_small, fill = "white")
				t = "Current Speed: %sMHz" % t_avg
				d.text((80,42), t, font = font_small, fill = "white")
			
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
				d.text((0,18), t, font = font_small, fill = "white")
				
				# Warning if less than 100MB available
				if t_avail <= 100:
					t = "Avail: %sMB !Warning!" % t_avail
				else:
					t = "Avail: %sMB" % t_avail
				d.text((0,30), t, font = font_small, fill = "white")
			
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
				d.text((110,18), t, font = font_small, fill = "white")
				
				# Imaging library
				t = "PIL - %s" % PIL_VERSION
				d.text((0,26), t, font = font_small, fill = "white")
				
				# RPI.GPIO
				t = "RPi.GPIO - %s" % RPIGPIO_VERSION
				d.text((110,26), t, font = font_small, fill = "white")
				
				# OLED driver
				t = "Luma.OLED - %s" % LUMA_VERSION
				d.text((0,34), t, font = font_small, fill = "white")
				
				# gpiozero
				t = "GPIOZero - %s" % GPIOZERO_VERSION
				d.text((110,34), t, font = font_small, fill = "white")
				
				# Pyserial
				t = "PySerial - %s" % SERIAL_VERSION
				d.text((0,42), t, font = font_small, fill = "white")
				
				# Numpy
				t = "Numpy - %s" % NUMPY_VERSION
				d.text((110,42), t, font = font_small, fill = "white")
				
				# PySDL2
				t = "PySDL2 - %s" % SDL2_VERSION
				d.text((0,50), t, font = font_small, fill = "white")
				
				# lcdbackpack
				t = "LCDBackPack - %s" % LCDBACKPACK_VERSION
				d.text((110,50), t, font = font_small, fill = "white")
			
			# Page number
			t = "%s/3" % menuClass.customData['page']
			d.text((menuClass.windowSettings['x_size'] - 30, 50), t, font = font_big, fill = "white")
			
			menuClass.image = copy.copy(i)
			menuClass.customData['timer'] = timeit.default_timer()
		return True

def showRestartConfirmation(menuClass = None, controlData = None):
	pass

def showShutdownConfirmation(menuClass = None, controlData = None):
	pass
