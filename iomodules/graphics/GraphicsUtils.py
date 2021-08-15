#!/usr/bin/env python
# -*- coding: utf8 -*-
#
# GraphicsUtils - Helper utils and methods for GraphicsIO.py
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

# Settings file
from libs import settings

# Start a new logger
from libs.newlog import newlog
logger = newlog(__name__)

def requiresRefresh(windowSettings):
	""" Has the timer for a window expired? """
	
	if 'timer' in windowSettings.keys():
		if (timeit.default_timer() - windowSettings['timer']) >= windowSettings['screen_refreshTime']:
			return True
		else:
			return False
	else:
		setRefresh(windowSettings)
		return False
	
def setRefresh(windowSettings):
	""" Start a new timer """
	
	windowSettings['timer'] = timeit.default_timer()
	
def getStartPosForCentredText(x_size, font, message):
	""" Return the start position for a string to be centred, given the resolution of the window """
	
	text_size = font.getsize(message)
	start_x_pos = int((x_size - text_size[0]) / 2)
	return start_x_pos
	
def updateSDLWindow(pilImage, windowSettings):
	""" Take pilImage (of some bit-depth), convert to a SDL surface and update the SDL window """

	# SDL works better with an RGB image
	pilImage = pilImage.convert('RGB')
	
	# Turn the PIL.Image object into a numpy array
	numpyimage = numpy.array(pilImage)
	
	# Add missing alpha channel rotate 90', and flip upside down to match screen
	numpyimage = numpy.dstack((numpyimage, numpy.zeros((windowSettings['y_size'], windowSettings['x_size']))))
	numpyimage = numpy.rot90(numpyimage)
	numpyimage = numpy.flipud(numpyimage)
	
	# Copy the adjusted PIL.Image into the SDL pixel array
	numpy.copyto(dst=windowSettings['sdlWindowArray'], src=numpyimage, casting='unsafe')
	
	# Save a copy of this screen
	windowSettings['sdl_framebuffer'] = copy.copy(numpyimage)
	
	# Refresh window
	sdl2.SDL_UpdateWindowSurface(windowSettings['sdlWindowContents'])

def updateOLEDScreen(pilImage, windowSettings):
	""" Update an OLED screen """
	
	# Save a copy of the this screen
	windowSettings['luma_framebuffer'] = pilImage
	# Render image
	windowSettings['luma_driver'].display(pilImage)

def blankImage(windowSettings):
	# Image is 1bit black and white
	d = {
		'image'		: Image.new('1', (windowSettings['x_size'], windowSettings['y_size'])),
		'font'		: ImageFont.truetype(settings.GFX_FONTS['lcd']['plain']['font'], 16),
		'font_small': ImageFont.truetype(settings.GFX_FONTS['sans']['plain']['font'], 8),
	}
	return d

def addLogStatus(pilImage, windowSettings):
	""" Adds a 'we are logging' status display to any current screen """
	
	draw = ImageDraw.Draw(pilImage)
	
	font = ImageFont.truetype(settings.GFX_FONTS["pixel"]["header"]['font'], size = 10)
	
	statusString = "Logging"
	text_size = font.getsize(statusString)
	
	draw.text((windowSettings['x_size'] - text_size[0], windowSettings['y_size'] - text_size[1]), statusString, fill="white", font = font)
	
	return pilImage

def gaugeNumeric(ecudata, sensor, font, windowSettings, sensorData):
	""" Simple numeric display, with the sensor name in one corner """
	
	sensorValueString = "%.f" % (sensor['previousValues'][-1])

	t1 = timeit.default_timer()

	# Have we created an image for this sensor before?
	if "image" in sensor['numeric'].keys():
		image = copy.copy(sensor['numeric']['image'])
		draw = ImageDraw.Draw(image)
		font = sensor['numeric']['font']
		font_big = sensor['numeric']['font_big']
		font_small = sensor['numeric']['font_small']
	else:
		image = Image.new('1', (windowSettings['x_size'], windowSettings['y_size']))
		draw = ImageDraw.Draw(image)
		font = ImageFont.truetype(settings.GFX_FONTS["pixel"]["header"]['font'], size = 16)
		font_big = ImageFont.truetype(settings.GFX_FONTS["sans"]["bolditalic"]['font'], size = 42)
		font_small = ImageFont.truetype(settings.GFX_FONTS['pixel']['plain']['font'], size = 8)
		x = 1
		
		# Add sensor name to top left
		draw.text((0, 0), sensor['sensor']['sensorId'], fill="white", font = font)
		
		# Save a copy of the image for next time around
		sensor['numeric']['image'] = copy.copy(image)
		sensor['numeric']['font'] = font
		sensor['numeric']['font_big'] = font_big
		sensor['numeric']['font_small'] = font_small
		
	if sensorData:
		# Add raw sensor value at middle left
		text_size = font_small.getsize(sensorData['sensorUnit'])
		text_big_size = font_big.getsize(sensorValueString)
		# Raw value
		draw.text((windowSettings['x_size'] - text_size[0] - text_big_size[0], text_size[1] + 2), sensorValueString, fill="white", font = font_big)
		# Units
		draw.text((windowSettings['x_size'] - text_size[0], text_size[1] + 2), sensorData['sensorUnit'], fill="white", font = font_small)
		
	t2 = timeit.default_timer() - t1
	logger.debug("gaugeNumeric Draw time: %0.4fms" % (t2 * 1000))
	
	return image

def buildImageAssets(use_oled_master = False, use_sdl_master = False):
	""" Pre-build any essential images; boot logo, splash screens, warnings, etc. """

	logger.info("Building image assets")

	# Load a font
	try:
		font = ImageFont.truetype(settings.GFX_FONTS['sans']['plain']['font'], 10)	
	except:
		font = ImageFont.load_default()

	assets = {}
	assets['boot_logo'] = {}
	
	# Boot logo - part 1 - master window
	# Load the Cosworth logo from disk
	sub_res = "%sx%s" % (settings.GFX_OLED_SIZE[0], settings.GFX_OLED_SIZE[1])
	logo_small = Image.open(settings.GFX_ASSETS_DIR + settings.GFX_BOOT_LOGO)
	i = Image.new('1', (settings.GFX_OLED_SIZE[0], settings.GFX_OLED_SIZE[1]))
	pasted = Image.new('1', (settings.GFX_OLED_SIZE[0], settings.GFX_OLED_SIZE[1]))
	pasted.paste(i,(4,8))
	assets['boot_logo'][sub_res] = pasted
	res_list = [(settings.GFX_OLED_SIZE[0], settings.GFX_OLED_SIZE[1])]
	
	# Boot logo - part 1 - master window
	# Load the Cosworth logo from disk
	if use_oled_master or use_sdl_master:
		master_res = "%sx%s" % (settings.GFX_MASTER_SIZE[0], settings.GFX_MASTER_SIZE[1])
		logo_big = Image.open(settings.GFX_ASSETS_DIR + settings.GFX_BOOT_LOGO_BIG)
		i = Image.new('1', (settings.GFX_MASTER_SIZE[0], settings.GFX_MASTER_SIZE[1]))
		pasted = Image.new('1', (settings.GFX_MASTER_SIZE[0], settings.GFX_MASTER_SIZE[1]))
		pasted.paste(i,(0,8))
		assets['boot_logo'][master_res] = pasted
		res_list.append((settings.GFX_MASTER_SIZE[0], settings.GFX_MASTER_SIZE[1]))
	
	###########################################################
	
	# Build the small animation sequence for waiting....
	assets['wait_sequence'] = {}
	
	for res in res_list:
		r = "%sx%s" % (res[0], res[1])
		assets['wait_sequence'][r] = []
	
		if res[0] == settings.GFX_OLED_SIZE[0]:
			logo = logo_small
		else:
			logo = logo_big
	
		i = Image.new('1', (res[0], res[1]))
		i.paste(logo,(4,8))
		draw = ImageDraw.Draw(i)
		draw.text((4, res[1] - 11), "Initialising |", fill="white", font = font)
		assets['wait_sequence'][r].append(i)
		
		i = Image.new('1', (res[0], res[1]))
		draw = ImageDraw.Draw(i)
		i.paste(logo,(4,8))
		draw.text((4, res[1] - 11), "Initialising /", fill="white", font = font)
		assets['wait_sequence'][r].append(i)
		
		i = Image.new('1', (res[0], res[1]))
		draw = ImageDraw.Draw(i)
		i.paste(logo,(4,8))
		draw.text((4, res[1] - 11), "Initialising -", fill="white", font = font)
		assets['wait_sequence'][r].append(i)
		
		i = Image.new('1', (res[0], res[1]))
		draw = ImageDraw.Draw(i)
		i.paste(logo,(4,8))
		draw.text((4, res[1] - 11), "Initialising \\", fill="white", font = font)
		assets['wait_sequence'][r].append(i)
		
		i = Image.new('1', ( res[0], res[1]))
		draw = ImageDraw.Draw(i)
		i.paste(logo,(4,8))
		draw.text((4, res[1] - 11), 'Initialising |', fill="white", font = font)
		assets['wait_sequence'][r].append(i)
		
		i = Image.new('1', ( res[0], res[1]))
		draw = ImageDraw.Draw(i)
		i.paste(logo,(4,8))
		draw.text((4, res[1] - 11), "Please wait .....", fill="white", font = font)
		assets['wait_sequence'][r].append(i)
	
	return assets

def sensorInitNumeric(sensor, windowSettings, scale_x):
	""" Derive params for a basic numeric gauge """
	
	data = {}
	
	return data

def sensorGraphicsInit(sensor = None, windowSettings = None, scale_x = 1):
	""" Get the default params for a sensor (height, width, line weight, number of bars per pixel, etc)
	, given a particular window """
	
	sensorParams = {}
	
	# Parameters for the various visualisations
	sensorParams['sensor'] = sensor
	sensorParams['numeric'] = sensorInitNumeric(sensor, windowSettings, scale_x)
	
	###################################################################
	# Create a local deque to hold historical sensor values
	###################################################################
	sensorParams['previousValues'] = deque(maxlen = int(windowSettings['x_size'] / scale_x))
	x_size = int(windowSettings['x_size'] / scale_x)
	for n in range(0, x_size):
		sensorParams['previousValues'].append(0)
				
	return sensorParams
	