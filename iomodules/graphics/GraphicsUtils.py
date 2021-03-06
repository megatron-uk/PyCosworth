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
		'font'		: ImageFont.truetype(settings.GFX_FONTS['sans']['plain']['font'], 16),
		'font_small': ImageFont.truetype(settings.GFX_FONTS['sans']['plain']['font'], 8),
	}
	return d

def gaugeWaveform(ecudata, sensor, font, windowSettings, sensorData, highlight_current = False):
	""" Render a waveform type image """
	
	sensorId = sensor['sensor']['sensorId']
	sensorValueString = "%.f" % (sensor['previousValues'][-1])
	t1 = timeit.default_timer()
	
	# Have we created an image for this sensor before?
	if "image" in sensor['waveform'].keys():
		image = copy.copy(sensor['waveform']['image'])
		draw = ImageDraw.Draw(image)
		font = sensor['waveform']['font']
		font_small = sensor['waveform']['font_small']
	else:
		sensor['waveform']['image'] = None
		sensor['waveform']['font'] = None
		sensor['waveform']['font_small'] = None
		blank = blankImage(windowSettings)
		image = blank['image']
		font = ImageFont.truetype(settings.GFX_FONTS["pixel"]["header"]['font'], size = 16)
		font_small = ImageFont.truetype(settings.GFX_FONTS['pixel']['plain']['font'], size = 8)
		draw = ImageDraw.Draw(image)

		# If the scale is from <0 to >0 then plot where 0 is on the Y axis
		if sensor['waveform']['zeroline'] is not None:
			zx = windowSettings['x_size']
			zy = sensor['waveform']['zeroline']
			draw.line([(0, zy), (zx, zy)], fill="white")
		else:
			zx = False
			zy = False
		
		# Draw the maximum value of the Y axis
		max_x = windowSettings['x_size'] - (font.getsize(str(sensor['sensor']['maxValue']))[0])
		max_y = 0
		
		# Draw the minimum value
		min_x = windowSettings['x_size'] - (font.getsize(str(sensor['sensor']['minValue']))[0])
		min_y = windowSettings['y_size'] - (font.getsize(str(sensor['sensor']['minValue']))[1])
		
		#############################################
		#
		# Draw any text elements
		#
		#############################################
		# Zero line
		if zx:
			draw.text((zx - 6, zy - 8), "0", fill="white", font = font_small)
		# Max value
		draw.text((max_x, max_y), str(sensor['sensor']["maxValue"]), fill="white", font = font_small)
		# Min value
		if zy:
			if zy > (windowSettings['y_size'] -  (font.getsize(str(sensor['sensor']['minValue']))[1])):
				pass
			else:
				draw.text((min_x, min_y), str(sensor['sensor']["minValue"]), fill="white", font = font_small)
		# Add sensor name to top left
		draw.text((0, 0), sensorId, fill="white", font = font)
	
		# Save a copy of the image for next time around
		sensor['waveform']['image'] = copy.copy(image)
		sensor['waveform']['font'] = font
		sensor['waveform']['font_small'] = font_small
		
	###############################################
	#
	# Draw a waveform-like display with most current value on the right
	# and all previous values scrolling to the left
	#
	###############################################
	last_pos = (0,0)
	for x in range(0, windowSettings['x_size']):
		v = sensor['previousValues'][x]
		# Cope with sensors who have a min value < 0
		v = abs(sensor['sensor']['minValue']) + v
		# Calculate how many lines/height
		lines = int(v / sensor['waveform']['valuePerLine'])
		# Y-position is screen size minus number of lines
		y = windowSettings['y_size'] - lines
		# For the first data point we can't connect it to a previous point
		if x == 0:
			# Draw a point
			draw.point([x, y], fill="white")
		else:
			# Connect to previous data point
			draw.line([(x, y), (last_pos[0], last_pos[1])], width=2, fill="white")
		# Update last data position co-ords
		last_pos = (x, y)	
	
	#############################################
	#
	# Draw a dashed horizontal line representing current sensor value
	#
	#############################################
	if highlight_current:
		v = sensor['previousValues'][-1]
		# Cope with sensors who have a min value < 0
		v = abs(sensor['sensor']['minValue']) + v
		# Calculate how many lines/height
		lines = int(v / sensor['waveform']['valuePerLine'])
		# Y-position is screen size minus number of lines
		x = windowSettings['x_size']
		y = windowSettings['y_size'] - lines
		line_length = 2
		for xpos in range(0, windowSettings['x_size'], 4):
			if (xpos <= (windowSettings['x_size'] - line_length)):
				draw.line([(xpos, y), (xpos + line_length, y)], width=1, fill="white")
	
	# Add raw sensor value at bottom left
	draw.text((4, windowSettings['y_size'] - 12), sensorValueString, fill="white", font = font)
	
	t2 = (timeit.default_timer() - t1) * 1000
	frame_time = "%.2fms" % t2
	logger.debug("gaugeWaveform Draw time: %s" % frame_time)
	
	return image

def gaugeLEDSegments(ecudata, sensor, font, windowSettings, sensorData):
	""" Render the 80's style LED segment bar-graph image """
	
	sensorValueString = "%.f" % (sensor['previousValues'][-1])
	t1 = timeit.default_timer()
	
	# Definitions for heights of 'LED' segments
	led_height = sensor['segment']['segmentHeights']
	
	# Have we created an image for this sensor before?
	if "image" in sensor['segment'].keys():
		image = copy.copy(sensor['segment']['image'])
		draw = ImageDraw.Draw(image)
		font = sensor['segment']['font']
		font_small = sensor['segment']['font_small']
	else:
		# Image is 1bit black and white
		image = Image.new('1', (windowSettings['x_size'], windowSettings['y_size']))
		draw = ImageDraw.Draw(image)
		font = ImageFont.truetype(settings.GFX_FONTS["pixel"]["header"]['font'], size = 16)
		font_small = ImageFont.truetype(settings.GFX_FONTS['pixel']['plain']['font'], size = 8)
		x = 1
		
		# Add sensor name to top left
		draw.text((0, 0), sensor['sensor']['sensorId'], fill="white", font = font)
		
		# Draw all the empty LED segments
		for led_h in led_height:
			y = (windowSettings['y_size'] -  led_h) 
			draw.rectangle([(x, windowSettings['y_size'] - 1), (x + sensor['segment']['segmentWidth'], y)], outline="white", fill=0)
			x += sensor['segment']['segmentWidth'] + 2
				
		# Save a copy of the image for next time around
		sensor['segment']['image'] = copy.copy(image)
		sensor['segment']['font'] = font
		sensor['segment']['font_small'] = font_small
		
	# Overwrite any of the empty LED segments will 
	# filled ones as necessary.
	v = sensor['previousValues'][-1]
	v = abs(sensor['sensor']['minValue']) + v
	segments = int(v / sensor['segment']['segmentValue'])
	# Have we exceeded the number of segments shown?
	if segments > sensor['segment']['segments']:
		segments = sensor['segment']['segments']
	x = 1
	for s in range(0, segments):
		#print("s:%s, v:%s, segments:%s" %(s, v, segments))
		if s > len(led_height):
			height = led_height[-1]
		else:
			height = led_height[s]
		y = (windowSettings['y_size'] - height)
		draw.rectangle([(x, windowSettings['y_size'] - 1), (x + sensor['segment']['segmentWidth'], y)], outline="white", fill=1)
		x += sensor['segment']['segmentWidth'] + 2
			
	# Add raw sensor value at middle left
	text_size = font.getsize(sensorValueString)
	draw.text((0, text_size[1] + 2), sensorValueString, fill="white", font = font)
	draw.text((text_size[0] + 2, text_size[1]), sensorData['sensorUnit'], fill="white", font = font_small)
	
	t2 = timeit.default_timer() - t1
	logger.debug("gaugeLED Draw time: %0.4fms" % (t2 * 1000))
	
	return image

def gaugeLine(ecudata, sensor, font, windowSettings, sensorData):
	""" Render a vertical line chart, single pixel width """
	
	sensorValueString = "%.f" % (sensor['previousValues'][-1])
	t1 = timeit.default_timer()
	# Have we created an image for this sensor before?
	if "image" in sensor['line'].keys():
		image = copy.copy(sensor['line']['image'])
		draw = ImageDraw.Draw(image)
		font = sensor['line']['font']
		font_small = sensor['line']['font_small']
	else:
		# Image is 1bit black and white
		image = Image.new('1', (windowSettings['x_size'], windowSettings['y_size']))
		draw = ImageDraw.Draw(image)
		font = ImageFont.truetype(settings.GFX_FONTS["pixel"]["header"]['font'], size = 16)
		font_small = ImageFont.truetype(settings.GFX_FONTS['pixel']['plain']['font'], size = 8)


		# Add sensor name to top left
		draw.text((0, 0), sensor['sensor']['sensorId'], fill="white", font = font)

		# Save a copy of the image for next time around
		sensor['line']['image'] = copy.copy(image)
		sensor['line']['font'] = font
		sensor['line']['font_small'] = font_small

	v = sensor['previousValues'][-1]
	# Cope with sensors who have a min value < 0
	v = abs(sensor['sensor']['minValue']) + v
	# Calculate how many lines to draw
	num_lines = int(v / sensor['line']['lineValue'])

	# Draw the outline of the chart
	for peak_pos in range(0, windowSettings['x_size']):
		x = peak_pos
		y =  windowSettings['y_size'] - sensor['line']['lineHeights'][x]
		draw.point((x, y), fill="white")
	draw.line([(0, windowSettings['y_size']), (windowSettings['x_size'], windowSettings['y_size'])], fill = "white")

	for x_pos in range(0, num_lines):
		# X-position is the line number
		x = x_pos
		# Y-position is screen size minus number of lines
		y = sensor['line']['lineHeights'][x_pos]
		# Draw a line representing the height of this sensor value
		draw.line([(x, windowSettings['y_size']), (x, windowSettings['y_size'] - y)], fill = "white") 
		
	# Add raw sensor value at middle left
	text_size = font.getsize(sensorValueString)
	draw.text((0, text_size[1] + 2), sensorValueString, fill="white", font = font)
	draw.text((text_size[0] + 2, text_size[1]), sensorData['sensorUnit'], fill="white", font = font_small)
	
	t2 = timeit.default_timer() - t1
	logger.debug("gaugeLine Draw time: %0.4fms" % (t2 * 1000))
	return image

def gaugeClock(ecudata, sensor, font, windowSettings, sensorData):
	""" Render an analogue clock style image """
	
	sensorValueString = "%4.f" % (sensor['previousValues'][-1])
	t1 = timeit.default_timer()
	
	# Have we created an image for this sensor before?
	if "image" in sensor['clock'].keys():
		image = copy.copy(sensor['clock']['image'])
		draw = ImageDraw.Draw(image)
		font = sensor['clock']['font']
		font_small = sensor['clock']['font_small']
	else:
		# Image is 1bit black and white
		image = Image.new('1', (windowSettings['x_size'], windowSettings['y_size']))
		draw = ImageDraw.Draw(image)
		font = ImageFont.truetype(settings.GFX_FONTS["pixel"]["header"]['font'], size = 16)
		font_small = ImageFont.truetype(settings.GFX_FONTS['pixel']['plain']['font'], size = 8)

		# Draw the arc and outline of the gauge
		draw.chord([(0, 8), (windowSettings['x_size'], windowSettings['y_size'] * 2)], 180, 360, outline = "white", fill = 0)
		
		# The point around which the needle rotates
		x1 = int((windowSettings['x_size'] / 2) - 6)
		y1 = windowSettings['y_size'] - 5
		x2 = int(x1 + 10)
		y2 = windowSettings['y_size'] + 5
		draw.ellipse([(x1, y1), (x2, y2)], outline = "white", fill = 0)
		
		sensor['clock']['needleOrigin'] = int(windowSettings['x_size'] / 2)
		
		# Add sensor name to top left
		draw.text((0, 0), sensor['sensor']['sensorId'], fill="white", font = font)
		
		# Save a copy of the image for next time around
		sensor['clock']['image'] = copy.copy(image)
		sensor['clock']['font'] = font
		sensor['clock']['font_small'] = font_small
		
	# Draw the needle
	x1 = sensor['clock']['needleOrigin']
	y1 = windowSettings['y_size']
	v = sensor['previousValues'][-1]
	v = abs(sensor['sensor']['minValue']) + v
	degrees = int(v / sensor['clock']['degreeValue'])
	armlength = windowSettings['y_size'] - 8
	d = 180 + degrees
	x2 = int(math.cos(math.radians(d)) * armlength)
	y2 = int(math.sin(math.radians(d)) * armlength)
	logger.debug("Pointer data: v:%s | d:%s | x1/y1: %s,%s | x2/y2: %s,%s" % (v, d, x1, y1, x2, y2))
	draw.line([(x1, y1), (x1 + x2, y1 + y2)], width = 2, fill = "white")
	
	# Current value
	# Add raw sensor value at middle left
	draw.text((windowSettings['x_size'] - ((len(sensorValueString) * 12) - 12), 0), sensorValueString, fill="white", font = font)

	t2 = timeit.default_timer() - t1
	logger.debug("gaugeClock Draw time: %0.4fms" % (t2 * 1000))
	
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

def highlightSelectedSensor(use_oled = False, use_sdl = False, windowSettings = None, sensor = None):
	""" Show the name of the sensor in a window when we change to a different one """
	
	i = Image.new('1', (windowSettings['x_size'], windowSettings['y_res']))
	draw = ImageDraw.Draw(i)
	font = ImageFont.truetype(settings.GFX_FONTS['sans']['plain']['font'], 16)

	sensorString = "%s" % sensor['sensorId']
	messageString = "Selected"

	# Print sensor name, centered
	x = getStartPosForCentredText(windowSettings['x_size'], font, sensorString)
	draw.text((x,2), sensorString, fill="white", font=font)
	
	# Print second string, centered
	x = getStartPosForCentredText(windowSettings['x_size'], font, messageString)
	draw.text((x,15), messageString, fill="white", font=font)
	
	# Render image to output device - OLED screen or SDL window
	if use_oled:
		# Update the OLED screen
		updateOLEDScreen(pilImage = i, windowSettings = windowSettings)
	
	if use_sdl:
		# Update the SDL window
		updateSDLWindow(pilImage = i, windowSettings = windowSettings)

def highlightSelectedWindow(use_oled = False, use_sdl = False, windowSettings = None):
	""" Given a window identifier, show a momentary, full-screen 'Selected' message,
	whilst also blanking all other windows. """
	
	i = Image.new('1', (windowSettings['x_size'], windowSettings['y_size']))
	draw = ImageDraw.Draw(i)
	font = ImageFont.truetype(settings.GFX_FONTS['sans']['plain']['font'], 16)
	
	messageString1 = "Gauge"
	messageString2 = "Selected"
	
	# Print first string, centered
	x = getStartPosForCentredText(windowSettings['x_size'], font, messageString1)
	draw.text((x,2), messageString1, fill="white", font=font)
	
	# Print second string, centered
	x = getStartPosForCentredText(windowSettings['x_size'], font, messageString2)
	draw.text((x,15), messageString2, fill="white", font=font)
	
	# Render image to output device - OLED screen or SDL window
	if use_oled:
		# Update the OLED screen
		updateOLEDScreen(pilImage = i, windowSettings = windowSettings)
	
	if use_sdl:
		# Update the SDL window
		updateSDLWindow(pilImage = i, windowSettings = windowSettings)
		
	# Momentarily blank all other windows
	for w in settings.GFX_WINDOWS.keys():
		if w != windowSettings['windowName']:
			i = Image.new('1', (settings.GFX_WINDOWS[w]['x_size'], settings.GFX_WINDOWS[w]['y_size']))
			draw = ImageDraw.Draw(i)
			draw.rectangle([(0,0), (settings.GFX_WINDOWS[w]['x_size'], settings.GFX_WINDOWS[w]['y_size'])], fill = 0)
			# Render image to output device - OLED screen or SDL window
			if use_oled:
				# Update the OLED screen
				updateOLEDScreen(pilImage = i, windowSettings = settings.GFX_WINDOWS[w])
			
			if use_sdl:
				# Update the SDL window
				updateSDLWindow(pilImage = i, windowSettings = settings.GFX_WINDOWS[w])

def sensorInitWaveform(sensor, windowSettings, scale_x):
	""" Derive the parameters for a waveform display """
	
	data = {}
	
	###################################################################
	# Set up defaults for waveform display
	###################################################################
	
	# The value of each Y pixel on the waveform
	data['valuePerLine'] = ((sensor['maxValue'] - sensor['minValue']) * 1.0) / windowSettings['y_size']
	
	if sensor['minValue'] < 0:
		# If the scale is below zero, where is zero on the Y axis?
		data['zeroline'] = windowSettings['y_size'] - int(abs(sensor['minValue']) / data['valuePerLine'])
		data['baseline'] = windowSettings['y_size']
	elif sensor['minValue'] > 0:
		# No zero line if the Y axis starts at a positive number
		data['zeroline'] = None
		data['baseline'] = windowSettings['y_size']
	else:
		# Otherwise zero is at the very bottom of the screen, so dont show it
		data['zeroline'] = None
		data['baseline'] = None
	data['maxline'] = 0

	return data

def sensorInitSegment(sensor, windowSettings, scale_x):
	""" Derive params for a LED segment display """
	
	data = {}
	
	###################################################################
	# Set up defaults for LED segment display
	###################################################################
	if int(windowSettings['x_size'] / scale_x) >= 256:
		segments = settings.GFX_LED_SEGMENT_NUMBER_MASTER
	else:
		segments = settings.GFX_LED_SEGMENT_NUMBER
	data['segments'] = segments
	data['segmentValue'] = ((sensor['maxValue'] - sensor['minValue']) * 1.0) / segments
	graph_range = numpy.logspace(numpy.log10(6), numpy.log10(windowSettings['y_size']), num=segments)
	led_height = []
	for v in graph_range:
		led_height.append(int(v))
	data['segmentHeights'] = led_height
	data['segmentWidth'] = int((windowSettings['x_size'] * scale_x) / segments) - 2
	
	return data

def sensorInitClock(sensor, windowSettings, scale_x):
	""" Derive params for an analogue gauge/clock """
	
	data = {}
	
	###################################################################
	# Set up defaults for analogue clock display
	###################################################################
	degrees = 180
	data['degreeValue'] =  ((sensor['maxValue'] - sensor['minValue']) * 1.0) / degrees	
	
	return data

def sensorInitLine(sensor, windowSettings, scale_x):
	""" Derive params for a line gauge """
	
	data = {}
	
	###################################################################
	# Set up defaults for line gauge display
	###################################################################
	
	graph_range = numpy.logspace(numpy.log10(6), numpy.log10(windowSettings['y_size']), num=(int(windowSettings['x_size'] / scale_x)))
	line_height = []
	for v in graph_range:
		line_height.append(int(v))
	lines = int(windowSettings['x_size'] / scale_x)
	data['lineHeights'] = line_height
	data['lineValue'] = ((sensor['maxValue'] - sensor['minValue']) * 1.0) / lines
	
	return data

def sensorGraphicsInit(sensor = None, windowSettings = None, scale_x = 1):
	""" Get the default params for a sensor (height, width, line weight, number of bars per pixel, etc)
	, given a particular window """
	
	sensorParams = {}
	
	# Parameters for the various visualisations
	sensorParams['sensor'] = sensor
	sensorParams['waveform'] = sensorInitWaveform(sensor, windowSettings, scale_x)
	sensorParams['segment'] = sensorInitSegment(sensor, windowSettings, scale_x)
	sensorParams['clock'] = sensorInitClock(sensor, windowSettings, scale_x)
	sensorParams['line'] = sensorInitLine(sensor, windowSettings, scale_x)
	
	###################################################################
	# Create a local deque to hold historical sensor values
	###################################################################
	sensorParams['previousValues'] = deque(maxlen = int(windowSettings['x_size'] / scale_x))
	x_size = int(windowSettings['x_size'] / scale_x)
	for n in range(0, x_size):
		sensorParams['previousValues'].append(0)
				
	print(sensorParams)
	return sensorParams
	