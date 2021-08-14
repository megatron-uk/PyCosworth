#!/usr/bin/env python
# -*- coding: utf8 -*-
#
# GraphicsIO - output graphics to OLED screens or SDL windows on your desktop
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
import math
import time
import timeit 
import numpy
import sys
import os
import copy
import traceback
from collections import deque

# Graphics libs
import sdl2
import sdl2.ext
from PIL import Image
from PIL import ImageOps
from PIL import ImageDraw
from PIL import ImageFont

# SDL and OLED initialisation utils and helpers
from iomodules.graphics.SDLInit import sdlInit
from iomodules.graphics.OLEDInit import oledInit
from iomodules.graphics.GraphicsUtils import *

# Settings file
from libs import settings

# Control data
from libs.ControlData import ControlData
from libs.MasterMenu import MasterMenu

# Start a new logger
from libs.newlog import newlog
logger = newlog(__name__)

###########################################################################################

def GraphicsIO(ecudata, controlQueue, actionQueue):
	""" GraphicsIO - output sensor data to graphics options: OLED screens or SDL windows on your desktop """
	
	# Our process name
	proc_name = multiprocessing.current_process().name
	myButtonId = settings.BUTTON_DEST_GRAPHICSIO
	
	logger.info("GraphicsIO process now running")
	
	# Counter to wake up the display loop
	i = 0
	button = False
	
	########################################################################
	#
	# This next chunk is all just SDL/desktop graphics initialisation
	#
	########################################################################
	USE_SDL_GRAPHICS = False
	USE_SDL_GRAPHICS_MASTER = False
	if settings.USE_SDL_GRAPHICS:
		################################################
		# Set up the main control window to mirror the big OLED screen
		################################################
		windowSettings = settings.GFX_MASTER_WINDOW
		result = sdlInit(windowSettings, settings.GFX_MASTER_SIZE[0], settings.GFX_MASTER_SIZE[1])
		if result:
			USE_SDL_GRAPHICS = True
			USE_SDL_GRAPHICS_MASTER = True
		else:
			USE_SDL_GRAPHICS = False
			USE_SDL_GRAPHICS_MASTER = False
		################################################
		# Set up sub-windows to emulate the small OLED screens
		################################################
		#USE_SDL_GRAPHICS = True
		#for k in settings.GFX_WINDOWS.keys():
		#	windowSettings = settings.GFX_WINDOWS[k]
		#	result = sdlInit(windowSettings, settings.GFX_OLED_SIZE[0], settings.GFX_OLED_SIZE[1])
		#	if result:
		#		settings.GFX_WINDOWS[k] = result
		#		USE_SDL_GRAPHICS = True
		#	else:
		#		USE_SDL_GRAPHICS = False
	
	#######################################################
	#
	# Initialise any I2C OLED devices
	#
	#######################################################
	USE_OLED_GRAPHICS = False
	USE_OLED_GRAPHICS_MASTER = False
	if settings.USE_OLED_GRAPHICS:
		################################################
		# Set up a the master windows on the main OLED screen
		################################################
		result = oledInit(settings.GFX_MASTER_WINDOW, settings.GFX_MASTER_SIZE[0], settings.GFX_MASTER_SIZE[1])
		if result:
			settings.GFX_MASTER_WINDOW = result
			USE_OLED_GRAPHICS_MASTER = True
			USE_OLED_GRAPHICS = True
	
	# Summary of available devices
	logger.info("SDL graphics: %s" % USE_SDL_GRAPHICS)
	logger.info("SDL graphics: %s (master)" % USE_SDL_GRAPHICS_MASTER)
	logger.info("OLED graphics: %s" % USE_OLED_GRAPHICS)
	logger.info("OLED graphics: %s (master)" % USE_OLED_GRAPHICS_MASTER)
	
	if (USE_SDL_GRAPHICS is False) and (USE_SDL_GRAPHICS_MASTER is False) and (USE_OLED_GRAPHICS is False) and (USE_OLED_GRAPHICS_MASTER is False):
		logger.fatal("There are NO display devices available")
		logger.fatal("This process will now exit - we cannot display anything!")
		exit(1)
			
	# Pre-load any image assets
	image_assets = buildImageAssets(USE_OLED_GRAPHICS_MASTER, USE_SDL_GRAPHICS_MASTER)

	#####################################################################################
	#
	# This next section shows a splash logo and a few loading screens in turn, 
	# just so that we delay sensor output until the serial port has started to
	# gather data.
	#
	#####################################################################################
	
	# Show the splash logo
	r = "%sx%s" % (settings.GFX_MASTER_SIZE[0], settings.GFX_MASTER_SIZE[1])
	if r in image_assets['boot_logo'].keys():
		if USE_OLED_GRAPHICS_MASTER:
			updateOLEDScreen(pilImage = image_assets['boot_logo'][r], windowSettings = settings.GFX_MASTER_WINDOW)
		if USE_SDL_GRAPHICS:
			updateSDLWindow(pilImage = image_assets['boot_logo'][r], windowSettings = settings.GFX_MASTER_WINDOW)
		
	# Show a 'please wait' loading sequence - just so that the serial port can 
	# start collecting data
	r = "%sx%s" % (settings.GFX_MASTER_SIZE[0], settings.GFX_MASTER_SIZE[1])
	res_list = list(image_assets['wait_sequence'].keys())	
	frame_count = len(res_list[0])
	frames = range(0, frame_count -1)
	for f in frames:
		if r in image_assets['wait_sequence'].keys():
			# Main screen
			r = "%sx%s" % (settings.GFX_MASTER_SIZE[0], settings.GFX_MASTER_SIZE[1])
			image = image_assets['wait_sequence'][r][f]
			if USE_OLED_GRAPHICS_MASTER:
				updateOLEDScreen(pilImage = image, windowSettings = settings.GFX_MASTER_WINDOW)		
			if USE_SDL_GRAPHICS:
				updateSDLWindow(pilImage = image, windowSettings = settings.GFX_MASTER_WINDOW)
			time.sleep(0.5)
	
	# Load a font
	try:
		font = ImageFont.truetype(settings.GFX_ASSETS_DIR + settings.GFX_FONT, 8)	
	except:
		font = ImageFont.load_default()
	
	####################################################################################
	#
	# Now begin the main display loop
	#
	####################################################################################
		
	# Default selected window
	selectWindowIdx = 0
	selectWindow = None		
		
	if settings.GFX_SLEEP_TIME == 0:
		logger.warn("Graphics frame limiter disabled - frames will be rendered as fast as possible")
		logger.warn("This may result in uneven performance!")

	# Spin up the master window control menu 
	subWindows = {}
	master = MasterMenu(windowSettings = settings.GFX_MASTER_WINDOW,
		subWindowSettings = subWindows,
		actionQueue = actionQueue,
		ecudata = ecudata, 
		use_sdl = USE_SDL_GRAPHICS, 
		use_oled = USE_OLED_GRAPHICS_MASTER
	)

	# Set display mode defaults
	settings.GFX_MASTER_WINDOW['displayModes'] = {}
	for sensor in settings.SENSORS:
		sensorId = sensor['sensorId']
		logger.info("Adjusting %s sensor defaults for the current %dx%d output device" % (sensorId, settings.GFX_MASTER_WINDOW['x_size'],settings.GFX_MASTER_WINDOW['y_size']))
		
		settings.GFX_MASTER_WINDOW['displayModes'][sensorId] = sensorGraphicsInit(sensor, settings.GFX_MASTER_WINDOW)

	logger.info("Entering main graphics loop now...")
	if settings.INFO:
		t0 = timeit.default_timer()
		fps = 0
		fired_windows = 0
		
	# Slide out intro screen....
	slideBitmapVertical(
		bitmap = image.copy(),
		x_start = 0, 
		y_start = 0, 
		y_end = settings.GFX_MASTER_WINDOW['y_size'], 
		direction = "down", 
		steps = 30,
		sleep = 0.025,
		windowSettings = settings.GFX_MASTER_WINDOW,
		USE_SDL_GRAPHICS = USE_SDL_GRAPHICS,
		USE_OLED_GRAPHICS = USE_OLED_GRAPHICS
	)
	
	
	
	while True:
		
		# Set a timer for this loop
		if settings.INFO:
			t1 = timeit.default_timer()
		
		####################################################
		#
		# Listen for control messages
		#
		####################################################
		if controlQueue.empty() == False:
			cdata = controlQueue.get()
			if cdata.isMine(myButtonId):
				logger.debug("Got a control message")
				cdata.show()
				
				master.processControlData(cdata)

				##########################################################
				# Change sensor for the window
				##########################################################
				if cdata.button and (cdata.button == settings.BUTTON_SENSOR_NEXT):
				
					logger.info("SENSOR: Control data received to change sensor")
					logger.info("SENSOR: Current window has sensor [%s] index [%s]" % (settings.GFX_MASTER_WINDOW['currentSensorId'], settings.GFX_MASTER_WINDOW['currentSensorIdx']))
					# Select next sensor, handling sensor list wraparound
					if settings.GFX_MASTER_WINDOW['currentSensorIdx'] < (len(settings.GFX_MASTER_WINDOW['sensorIds']) - 1):
						settings.GFX_MASTER_WINDOW['currentSensorIdx'] += 1
					else:
						settings.GFX_MASTER_WINDOW['currentSensorIdx'] = 0
				
					settings.GFX_MASTER_WINDOW['currentSensorId'] = settings.GFX_MASTER_WINDOW['sensorIds'][settings.GFX_MASTER_WINDOW['currentSensorIdx']]
					logger.info("SENSOR: Current window now has sensor [%s] index [%s]" % (settings.GFX_MASTER_WINDOW['currentSensorId'], settings.GFX_MASTER_WINDOW['currentSensorIdx']))
					
					# Slide the current sensor screen out
					slideBitmapVertical(
						bitmap = image.copy(),
						x_start = 0, 
						y_start = 0, 
						y_end = settings.GFX_MASTER_WINDOW['y_size'], 
						direction = "down", 
						steps = 10,
						sleep = 0.025,
						windowSettings = settings.GFX_MASTER_WINDOW,
						USE_SDL_GRAPHICS = USE_SDL_GRAPHICS,
						USE_OLED_GRAPHICS = USE_OLED_GRAPHICS
					)					
				
		##############################################################
		#
		# Update each OLED or SDL gfx sub-window in turn
		#
		##############################################################
				
		windowSettings = settings.GFX_MASTER_WINDOW
		windowSettings['currentSensorId'] = settings.GFX_MASTER_WINDOW['sensorIds'][settings.GFX_MASTER_WINDOW['currentSensorIdx']]
		if (requiresRefresh(windowSettings)):
			# Generate the latest image of sensor data for this gfx window (be it SDL or OLED)
			currentSensorId = windowSettings['currentSensorId']
			currentMode = windowSettings['currentMode']
			
			# Add latest sensor value to list of previous values
			# As the list is a fixed size, this also pushes the oldest
			# value off the back of the list.
			value = ecudata.getData(currentSensorId)
			if value:
				windowSettings['displayModes'][currentSensorId]['previousValues'].append(value)
			sensorData = ecudata.getSensorData(currentSensorId)
			
			# Simple numeric gauge
			if currentMode == settings.GFX_MODE_NUMERIC:
				# Simple numeric display
				image = gaugeNumeric(ecudata = ecudata,
					sensor = windowSettings['displayModes'][currentSensorId],
					font = font,
					windowSettings = windowSettings,
					sensorData = sensorData
				)
			else:
				pass
			
			if USE_OLED_GRAPHICS:
				# Update the OLED screen
				updateOLEDScreen(pilImage = image, windowSettings = windowSettings)
			
			if USE_SDL_GRAPHICS:
				# Update the SDL window
				updateSDLWindow(pilImage = image, windowSettings = windowSettings)
				
			# Reset the timer for this window
			setRefresh(windowSettings)
			
			fired_windows += 1
		
		# Timers to work out average latency for updating all windows
		# as well as a rough approximation of frames generated per second
		if settings.INFO:
			fps += 1
			t2 = timeit.default_timer()
			if settings.DEBUG:
				logger.debug("Update latency this loop: %6.4fms" % ((t2 - t1) * 1000))
			t = t2 - t0
			if t >= settings.GFX_FRAME_COUNT_TIME:
				logger.debug("Image update speed approximately: %sfps [%s frames / %6.3fs]" % (fired_windows / settings.GFX_FRAME_COUNT_TIME, fired_windows, t))
				fps = 0
				fired_windows = 0
				t0 = timeit.default_timer()
				
		# After updating all of the windows, sleep so that we limit the amount of screen refreshes we do
		time.sleep(settings.GFX_SLEEP_TIME)
		
		# At the end of the loop the variable 'image' always contains the content of the screen from the last update
		# ...
	
def slideBitmapVertical(bitmap = None, x_start = 0, y_start = 0, y_end = 0, steps = 0, direction = "up", sleep = 0.1, windowSettings = None, USE_SDL_GRAPHICS = False, USE_OLED_GRAPHICS = False):
	""" Slide in a bitmap vertically - either from top or bottom of screen """
	
	y_pos = y_start
	y_increment = int(bitmap.size[1]/steps)
	image = None
	
	if direction == "up":
		# Slide a bitmap from bottom to top
		logger.debug("Vertically sliding image up from y:%s to y:%s in x%s %spx steps" % (y_start, y_end, steps, y_increment))
		for i in range(0, steps + 1):
			image = Image.new('1', (settings.GFX_MASTER_WINDOW['x_size'], settings.GFX_MASTER_WINDOW['y_size']))
			logger.debug("Pasting bitmap at x:%s,y:%s" % (x_start, y_pos))
			image.paste(bitmap,(x_start, y_pos))
			if USE_OLED_GRAPHICS:
				updateOLEDScreen(pilImage = image, windowSettings = windowSettings)
			if USE_SDL_GRAPHICS:
				updateSDLWindow(pilImage = image, windowSettings = windowSettings)
			time.sleep(sleep)
			y_pos -= y_increment
	else:
		logger.debug("Vertically sliding image up from y:%s to y:%s - %s steps" % (y_start, y_end, steps))
		l = list(range(0, steps + 1))
		l.reverse()
		for i in l: 
			image = Image.new('1', (settings.GFX_MASTER_WINDOW['x_size'], settings.GFX_MASTER_WINDOW['y_size']))
			logger.debug("Pasting bitmap at x:%s,y:%s" % (x_start, y_pos))
			image.paste(bitmap,(x_start, y_pos))
			if USE_OLED_GRAPHICS:
				updateOLEDScreen(pilImage = image, windowSettings = windowSettings)
			if USE_SDL_GRAPHICS:
				updateSDLWindow(pilImage = image, windowSettings = windowSettings)
			time.sleep(sleep)
			y_pos += y_increment
		# Slide a bitmap from top to bottom
