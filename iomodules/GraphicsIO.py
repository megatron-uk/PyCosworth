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
			settings.GFX_WINDOWS
			USE_SDL_GRAPHICS = True
			USE_SDL_GRAPHICS_MASTER = True
		else:
			USE_SDL_GRAPHICS = False
			USE_SDL_GRAPHICS_MASTER = False
		################################################
		# Set up sub-windows to emulate the small OLED screens
		################################################
		#USE_SDL_GRAPHICS = True
		for k in settings.GFX_WINDOWS.keys():
			windowSettings = settings.GFX_WINDOWS[k]
			result = sdlInit(windowSettings, settings.GFX_OLED_SIZE[0], settings.GFX_OLED_SIZE[1])
			if result:
				settings.GFX_WINDOWS[k] = result
				USE_SDL_GRAPHICS = True
			else:
				USE_SDL_GRAPHICS = False
	
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
		################################################
		# Set up sub-windows on the small OLED screens
		################################################
		for k in settings.GFX_WINDOWS.keys():
			windowSettings = settings.GFX_WINDOWS[k]
			result =  oledInit(windowSettings, settings.GFX_OLED_SIZE[0], settings.GFX_OLED_SIZE[1])
			if result:
				settings.GFX_WINDOWS[k] = result
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
	
	# This is a list of any connected screens - we'll need to loop 
	# through these each time we want to refresh.
	gfx_window_keys = []
	for w in settings.GFX_WINDOWS.keys():
		windowSettings = settings.GFX_WINDOWS[w]
		if windowSettings['luma_driver'] or windowSettings['sdlWindow']:
			logger.info("Added screen '%s' to list of available SDL/OLED screens" % w)
			gfx_window_keys.append(w)
	
	# Load data about sensors (names etc.) from config file into a local look-up table for EACH window, since 
	# each window MAY be a different size and need a different number of lines/pixels per value/refresh etc.
	
	for w in gfx_window_keys:
		windowSettings = settings.GFX_WINDOWS[w]
		windowSettings['displayModes'] = {}
		for sensor in settings.SENSORS:
			sensorId = sensor['sensorId']
			
			windowSettings['displayModes'][sensorId] = sensorGraphicsInit(sensor, windowSettings)
			
		# Set default modes
		windowSettings['currentMode'] = windowSettings['mode'][0]
		windowSettings['currentSensorId'] = windowSettings['sensorIds'][0]
		
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
	# First on the main scren
	r = "%sx%s" % (settings.GFX_MASTER_SIZE[0], settings.GFX_MASTER_SIZE[1])
	if r in image_assets['boot_logo'].keys():
		if USE_OLED_GRAPHICS_MASTER:
			updateOLEDScreen(pilImage = image_assets['boot_logo'][r], windowSettings = settings.GFX_MASTER_WINDOW)
		if USE_SDL_GRAPHICS:
			updateSDLWindow(pilImage = image_assets['boot_logo'][r], windowSettings = settings.GFX_MASTER_WINDOW)
	# Then on the secondary screen(s)
	for w in gfx_window_keys:
		r = "%sx%s" % (settings.GFX_OLED_SIZE[0], settings.GFX_OLED_SIZE[1])
		if r in image_assets['boot_logo'].keys():
			if USE_OLED_GRAPHICS:
				updateOLEDScreen(pilImage = image_assets['boot_logo'][r], windowSettings = settings.GFX_WINDOWS[w])		
			if USE_SDL_GRAPHICS:
				updateSDLWindow(pilImage = image_assets['boot_logo'][r], windowSettings = settings.GFX_WINDOWS[w])
		
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
			# Secondary screen(s)
			for w in gfx_window_keys:
				r = "%sx%s" % (settings.GFX_OLED_SIZE[0], settings.GFX_OLED_SIZE[1])
				if r in image_assets['wait_sequence'].keys():
					image = image_assets['wait_sequence'][r][f]
					if USE_OLED_GRAPHICS:
						updateOLEDScreen(pilImage = image, windowSettings = settings.GFX_WINDOWS[w])		
					if USE_SDL_GRAPHICS:
						updateSDLWindow(pilImage = image, windowSettings = settings.GFX_WINDOWS[w])
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
	if len(gfx_window_keys)>0:
		selectWindow = gfx_window_keys[selectWindowIdx]
	else:
		selectWindow = None		
		
	if settings.GFX_SLEEP_TIME == 0:
		logger.warn("Graphics frame limiter disabled - frames will be rendered as fast as possible")
		logger.warn("This may result in uneven performance!")

	# Spin up the master window control menu 
	subWindows = {}
	for w in gfx_window_keys:
		subWindows[w] = settings.GFX_WINDOWS[w]
	master = MasterMenu(windowSettings = settings.GFX_MASTER_WINDOW,
		subWindowSettings = subWindows,
		actionQueue = actionQueue,
		ecudata = ecudata, 
		use_sdl = USE_SDL_GRAPHICS, 
		use_oled = USE_OLED_GRAPHICS_MASTER
		)

	logger.info("Entering main graphics loop now...")
	if settings.INFO:
		t0 = timeit.default_timer()
		fps = 0
		fired_windows = 0
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
				# Select a OLED/SDL window to change
				##########################################################
				#if cdata.button and (cdata.button == settings.BUTTON_3) and (cdata.duration == settings.BUTTON_SHORT):
				#	
				#	
				#	if len(gfx_window_keys)>0:
				#		logger.info("Control data received to select next window")
				#		logger.info("Current selected window [%s] index %s" % (selectWindow, selectWindowIdx))
				#		# Select next window
				#		if selectWindow is None:
				#			selectWindow = settings.GFX_WINDOWS.keys()[0]
				#			selectWindowIdx = 0
				#		# Wrap around
				#		elif selectWindowIdx < len(settings.GFX_WINDOWS.keys()) - 1:
				#			selectWindowIdx += 1
				#		else:
				#			selectWindowIdx = 0
				#			
				#		# Select next window
				#		selectWindow = gfx_window_keys[selectWindowIdx]
				#		logger.info("Selected window now [%s] index %s" % (selectWindow, selectWindowIdx))
				#		highlightSelectedWindow(use_oled = USE_OLED_GRAPHICS, use_sdl = USE_SDL_GRAPHICS, windowSettings = settings.GFX_WINDOWS[selectWindow])
				#		time.sleep(1)
				
				##########################################################
				# Change display mode for the currently selected OLED`
				##########################################################
				#if cdata.button and (cdata.button == settings.BUTTON_4) and (cdata.duration == settings.BUTTON_SHORT):
				#	
				#	if len(gfx_window_keys)>0:
				#		logger.info("MODE: Control data received to change display mode")
				#		logger.info("MODE: Current window [%s] has mode [%s] index [%s]" % (selectWindow, settings.GFX_WINDOWS[selectWindow]['currentMode'], settings.GFX_WINDOWS[selectWindow]['currentModeIdx']))
				#		# Select next display mode, handling list of mode wraparound
				#		if settings.GFX_WINDOWS[selectWindow]['currentModeIdx'] < (len(settings.GFX_WINDOWS[selectWindow]['mode']) - 1):
				#			settings.GFX_WINDOWS[selectWindow]['currentModeIdx'] += 1
				#		else:
				#			settings.GFX_WINDOWS[selectWindow]['currentModeIdx'] = 0
				#
				#		settings.GFX_WINDOWS[selectWindow]['currentMode'] = settings.GFX_WINDOWS[selectWindow]['mode'][settings.GFX_WINDOWS[selectWindow]['currentModeIdx']]
				#		logger.info("MODE: Current window [%s] now has mode [%s] index [%s]" % (selectWindow, settings.GFX_WINDOWS[selectWindow]['currentMode'], settings.GFX_WINDOWS[selectWindow]['currentModeIdx']))
		
				##########################################################
				# Change sensor for the currently selected OLED
				##########################################################
				#if cdata.button and (cdata.button == settings.BUTTON_4) and (cdata.duration == settings.BUTTON_LONG):
				#
				#	if len(gfx_window_keys)>0:
				#		logger.info("SENSOR: Control data received to change sensor")
				#		logger.info("SENSOR: Current window [%s] has sensor [%s] index [%s]" % (selectWindow, settings.GFX_WINDOWS[selectWindow]['currentSensorId'], settings.GFX_WINDOWS[selectWindow]['currentSensorIdx']))
				#		# Select next sensor, handling sensor list wraparound
				#		if settings.GFX_WINDOWS[selectWindow]['currentSensorIdx'] < (len(settings.GFX_WINDOWS[selectWindow]['sensorIds']) - 1):
				#			settings.GFX_WINDOWS[selectWindow]['currentSensorIdx'] += 1
				#		else:
				#			settings.GFX_WINDOWS[selectWindow]['currentSensorIdx'] = 0
				#	
				#		settings.GFX_WINDOWS[selectWindow]['currentSensorId'] = settings.GFX_WINDOWS[selectWindow]['sensorIds'][settings.GFX_WINDOWS[selectWindow]['currentSensorIdx']]
				#		highlightSelectedSensor(use_oled = USE_OLED_GRAPHICS, use_sdl = USE_SDL_GRAPHICS, windowSettings = settings.GFX_WINDOWS[selectWindow], sensor = local_sensors[settings.GFX_WINDOWS[selectWindow]['currentSensorId']])
				#		logger.info("SENSOR: Current window [%s] now has sensor [%s] index [%s]" % (selectWindow, settings.GFX_WINDOWS[selectWindow]['currentSensorId'], settings.GFX_WINDOWS[selectWindow]['currentSensorIdx']))
				#		time.sleep(1)
		
		#################################################
		#
		# Update main control window
		#
		#################################################
			
		if USE_SDL_GRAPHICS_MASTER or USE_OLED_GRAPHICS_MASTER:
			if (requiresRefresh(settings.GFX_MASTER_WINDOW)):
				master.buildImage()
				master.update()
				fired_windows += 1
				setRefresh(settings.GFX_MASTER_WINDOW)
		
		##############################################################
		#
		# Update each OLED or SDL gfx sub-window in turn
		#
		##############################################################
				
		for w in gfx_window_keys:
			
			windowSettings = settings.GFX_WINDOWS[w]
			if (requiresRefresh(windowSettings)):
				# What sensor are we processing?
				# TO DO
				
				# What display mode are we in?
				# TO DO
				
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
				
				# Waveform gauge
				if currentMode == settings.GFX_MODE_WAVEFORM:
					image = gaugeWaveform(ecudata = ecudata, 
						sensor = windowSettings['displayModes'][currentSensorId],
						font = font,
						windowSettings = windowSettings,
						sensorData = sensorData, 
						highlight_current = True
					)
				elif currentMode == settings.GFX_MODE_SEGMENTS:
					# LED segment style bargraph gauge
					image = gaugeLEDSegments(ecudata = ecudata, 
						sensor = windowSettings['displayModes'][currentSensorId],
						font = font,
						windowSettings = windowSettings,
						sensorData = sensorData
					)
				elif currentMode == settings.GFX_MODE_CLOCK:
					# Traditional clock type gauge
					image = gaugeClock(ecudata = ecudata,
						sensor = windowSettings['displayModes'][currentSensorId],
						font = font,
						windowSettings = windowSettings,
						sensorData = sensorData
					)
				elif currentMode == settings.GFX_MODE_LINE:
					# Vertical line gauge
					image = gaugeLine(ecudata = ecudata,
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
				logger.debug("Update latency this loop: %6.4fms [%s of %s screens]" % (((t2 - t1) * 1000), fired_windows, len(gfx_window_keys)))
			t = t2 - t0
			if t >= settings.GFX_FRAME_COUNT_TIME:
				logger.debug("Image update speed approximately: %sfps [%s frames / %6.3fs]" % (fired_windows / settings.GFX_FRAME_COUNT_TIME, fired_windows, t))
				fps = 0
				fired_windows = 0
				t0 = timeit.default_timer()
				
		# After updating all of the windows, sleep so that we limit the amount of screen refreshes we do
		time.sleep(settings.GFX_SLEEP_TIME)
