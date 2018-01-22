#!/usr/bin/env python
# -*- coding: utf8 -*-

# MatrixIO - print sensor data to a Matrix Orbital compatible character LCD.
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
import timeit
import sys
import os

# Settings file
from libs import settings

# Import the lcd driver
from lcdbackpack import LcdBackpack

# ECU data storage structure
from libs.EcuData import EcuData

# Start a new logger
from libs.newlog import newlog
logger = newlog(__name__)

def lcdWriteNumeric(lcd = None, ecudata = None, sensorId = None, previousId = False, row = 1, peak = False):
	""" Write a numeric sensor value """
	lcd.set_cursor_position(1, row)
	lcd.write("                ")
	lcd.set_cursor_position(1, row)
	lcd.write("%3s %s%s" % (sensorId, int(ecudata.data[sensorId]), ecudata.sensor[sensorId]['sensorUnit']))
	return None

def lcdWriteBarGraph(lcd = None, ecudata = None, sensorId = None, previousId = False, row = 1, peak = False, peak_segments = 0):
	""" Display a bar graph of the sensor value """
	
	# How many columns do we have to play with?
	max_cols = settings.MATRIX_COLS - (len(sensorId) + 1)
	max_value = ecudata.sensor[sensorId]['maxValue']
	segment_value = (max_value * 1.0) / max_cols
	total_segments = int(ecudata.data[sensorId] / segment_value)
	
	if previousId:
		lcd.set_cursor_position(1, row)
		lcd.write("%3s" % (sensorId))
		# Same sensor as previous
		old_segments = int(ecudata.data_previous[sensorId] / segment_value)
		if old_segments != total_segments:
			# Seek to start position
			lcd.set_cursor_position(settings.MATRIX_DATA_START_COL, row)
			
			# Write new bar graph
			lcd._write_command([0xC0, settings.MATRIX_FONT_BANK])
			for n in range(0, total_segments - 1):
				lcd.write(chr(settings.MATRIX_FONT_BOX_FILLED))
			lcd.write(chr(settings.MATRIX_FONT_RIGHT_ANGLE))
			for n in range(total_segments, max_cols - 1):
				lcd.write(" ")
		else:
			# No update
			pass
		
		if peak:
			if (peak_segments > total_segments) and (peak_segments > 1):
				# Write new bar graph
				lcd.set_cursor_position(settings.MATRIX_DATA_START_COL + peak_segments - 1, row)
				lcd._write_command([0xC0, settings.MATRIX_FONT_BANK])
				lcd.write(chr(settings.MATRIX_FONT_PEAK))
				return None
			else:
				return (True, total_segments)
	else:
		# A new sensor, clear row
		lcd.set_cursor_position(1, row)
		lcd.write("%3s" % (sensorId))
		lcd.set_cursor_position(settings.MATRIX_DATA_START_COL, row)
		
		# Write new bar graph
		lcd._write_command([0xC0, settings.MATRIX_FONT_BANK])
		for n in range(0, total_segments - 1):
			lcd.write(chr(settings.MATRIX_FONT_BOX_FILLED))
		lcd.write(chr(settings.MATRIX_FONT_RIGHT_ANGLE))
		for n in range(total_segments, max_cols - 1):
			lcd.write(" ")
		return None

def lcdFadeIn(lcd):
	r = range(0,settings.MATRIX_BACKLIGHT_MAX_BRIGHTNESS)
	for i in r:
		lcd.set_brightness(i)
		time.sleep(0.01)

def lcdFadeOut(lcd):
	r = range(0,settings.MATRIX_BACKLIGHT_MAX_BRIGHTNESS)
	r = reversed(r)
	for i in r:
		lcd.set_brightness(i)
		time.sleep(0.01)
	lcd.clear()

def lcdCreateCustomChars(lcd):
	""" Create a nice set of sloping block characters, useable in a bar chart, for example. """
	
	# Create a custom bank of characters
	lcd._write_command([0x58]) 
	
	# outline bars in custom font bank #1
	# Create a custom bank of characters
	lcd._write_command([0x58])
	
	# Solid box, like '[]'
	lcd._write_command([0xC1, settings.MATRIX_FONT_BANK, settings.MATRIX_FONT_BOX_FILLED, 0x1F,0x1F,0x1F,0x1F,0x1F,0x1F,0x1F,0x1F])
	
	# An empty box, like '[]'
	lcd._write_command([0xC1, settings.MATRIX_FONT_BANK, settings.MATRIX_FONT_BOX_OUTLINE, 0x1F,0x11,0x11,0x11,0x11,0x11,0x11,0x1F])
	
	# Half box, angled right, like a '>'
	lcd._write_command([0xC1, settings.MATRIX_FONT_BANK, settings.MATRIX_FONT_RIGHT_ANGLE, 0x18,0x1c,0x1e,0x1f,0x1f,0x1e,0x1c,0x18])
	
	# Peak value symbol, like an 'I'
	lcd._write_command([0xC1, settings.MATRIX_FONT_BANK, settings.MATRIX_FONT_PEAK, 0x1F,0x0E,0x04,0x04,0x04,0x04,0x0E,0x1F])
	
	lcd._write_command([0xC0, settings.MATRIX_FONT_BANK])

	######################################
	#
	# To use the custom font bank entries, first
	# select the bank:
	# lcd._write_command([0xC0, 1])
	# 
	# You can then print each custom font as so:
	# lcd._ser.write(chr(settings.MATRIX_FONT_PEAK))	

def MatrixIO(ecudata, datamanager):
	""" Matrix IO - print sensor data to a matrix orbital compatible character mode LCD """
	
	proc_name = multiprocessing.current_process().name
	connected = False
	lcd = False
	
	##############################################################
	#
	# This is all LCD driver initialisation stuff, shouldn't need
	# to change anything below here once it works...
	#
	##############################################################
	logger.info("Initialising LCD driver")
	try:
		lcd = LcdBackpack(serial_device = settings.MATRIX_SERIAL_PORT, baud_rate = settings.MATRIX_BAUD)
		lcd.connect()
		lcd.display_off()
		lcd.set_lcd_size(columns = settings.MATRIX_COLS, rows = settings.MATRIX_ROWS)
		lcd.set_underline_cursor(underline_cursor = False)
		lcd.clear()
		lcd.set_contrast(settings.MATRIX_FONT_MAX_CONTRAST)
		lcd.set_brightness(settings.MATRIX_BACKLIGHT_MAX_BRIGHTNESS)
		lcd.set_backlight_rgb(settings.MATRIX_BACKLIGHT_RGB[0], settings.MATRIX_BACKLIGHT_RGB[1], settings.MATRIX_BACKLIGHT_RGB[2])
		lcd.display_on()
		# Record as connected, so we dont try to reconnect next time round
		connected = True
		
		# Create custom font banks
		lcdCreateCustomChars(lcd)
		
		# Fade out the intro splash
		lcd.write("PyCosworth")
		lcd.set_cursor_position(1, 2)
		lcd.write("LCD Driver!")
		time.sleep(0.5)
		lcdFadeOut(lcd)
		
		# Sleep to show the splash mesage
		logger.info("LCD serial port initialiased")
		time.sleep(1)
		lcd.clear()
		
		# Fade in a sensors loading message
		lcd.write("Sensors loading...")
		lcd.set_cursor_position(1,2)
		lcd.write("...please wait")
		lcdFadeIn(lcd)
		time.sleep(0.5)
		lcdFadeOut(lcd)
		
		# Clear screen before loading sensor data
		lcd.clear()
		time.sleep(0.5)
		lcd.set_brightness(255)
		
	except Exception as e:
		# We couldnt connect
		logger.error("LCD character display not available")
		logger.error("%s" % e)
		logger.critical("This process will now exit")
		exit(1)
	
	# Make a local copy of the matrix configuration data
	local_matrix_config = {}
	for k in ecudata.matrix_config.keys():
		local_matrix_config[k] = ecudata.matrix_config[k]
		local_matrix_config[k]['row_cycleTimer'] = 0
		local_matrix_config[k]['value_refreshTimer'] = 0
		local_matrix_config[k]['peak'] = False
		local_matrix_config[k]['peak_counter'] = settings.MATRIX_PEAK_COUNT
		local_matrix_config[k]['peak_segments'] = 0
	i = 0
	previousId = False
	while True:
		logger.debug("Waking [connected = %s]" % (connected))
		if connected:
			
			i += 1
			
			if i == 1000:
				logger.info("Still running [%s]" % proc_name)
				i = 0
			
			matrix_rows = local_matrix_config.keys()
			for row in matrix_rows:				
				
				# Only process this row if we have any sensors defined for it
				if len(local_matrix_config[row]['sensorIds']) > 0:
					##################################################
					# Check if configuration for this line has changed
					# TO DO
					
					############################################################################
					# row = line of LCD
					# sensorId = 'RPM', or 'TPS' or similar
					# current_sensorIdx = int; index to the list of sensor names we are showing this time round
					# next_sensorIdx = int; index to the list of sensor names we show next time round
					
					############################################################################
					# Is the row configured to cycle through sensors?
					if local_matrix_config[row]['setting'] == settings.MATRIX_SETTING_CYCLE:
						
						current_sensorIdx = local_matrix_config[row]['next_sensorIdx']
						next_sensorIdx = current_sensorIdx
						
						# Start a timer to cycle this row to the next
						if local_matrix_config[row]['row_cycleTimer'] == 0:
							local_matrix_config[row]['row_cycleTimer'] = timeit.default_timer()
						
						# Start a timer to refresh the data on this row
						if local_matrix_config[row]['value_refreshTimer'] == 0:
							local_matrix_config[row]['value_refreshTimer'] = timeit.default_timer()
						
						# Loop to next sensor, unless we've reached end of sensor list
						if (current_sensorIdx < len(local_matrix_config[row]['sensorIds'])):
							sensorId = local_matrix_config[row]['sensorIds'][current_sensorIdx]
						else:
							sensorId = local_matrix_config[row]['sensorIds'][0]
						
						# Check if timer for this row has expired
						#if timeit.default_timer() - local_matrix_config[k]['timer'] >= settings.MATRIX_ROW_TIME:
						if (timeit.default_timer() - local_matrix_config[row]['row_cycleTimer']) >= local_matrix_config[row]['row_cycleTime']:
							
							# set up the pointer for the next cycle
							if current_sensorIdx == len(local_matrix_config[row]['sensorIds']):
								# loop back to start
								next_sensorIdx = 0
							else:
								# move to next sensor id in list
								next_sensorIdx = current_sensorIdx + 1
						
							# Set next sensor index
							local_matrix_config[row]['next_sensorIdx'] = next_sensorIdx
							
							# restart timer
							local_matrix_config[row]['row_cycleTimer'] = timeit.default_timer()
						
						# If timer exceeded, refresh data on this row
						t = timeit.default_timer() - local_matrix_config[row]['value_refreshTimer']
						if (t >= settings.MATRIX_CONFIG[row]['value_refreshTime']):
	
							# Display sensor information
							previousId = True if current_sensorIdx == next_sensorIdx else False
							if settings.MATRIX_MODE_BAR in local_matrix_config[row]['mode']:
								lcdWriteBarGraph(lcd = lcd,
									ecudata = ecudata,
									sensorId = sensorId,
									previousId = previousId,
									row = row,
									peak = False)
							else:
								lcdWriteNumeric(lcd = lcd,
									ecudata = ecudata,
									sensorId = sensorId,
									previousId = previousId,
									row = row,
									peak = False)
								
							# restart timer
							local_matrix_config[row]['value_refreshTimer'] = timeit.default_timer()
						else:
							pass
					
					############################################################################
					# Is the row configured to hold a static sensor?
					if local_matrix_config[row]['setting'] == settings.MATRIX_SETTING_FIXED:
						
						# Start a timer to refresh the data on this row
						if local_matrix_config[row]['value_refreshTimer'] == 0:
							local_matrix_config[row]['value_refreshTimer'] = timeit.default_timer()
						
						# If timer exceeded, refresh the data shown
						t = timeit.default_timer() - local_matrix_config[row]['value_refreshTimer']
						if (t >= settings.MATRIX_CONFIG[row]['value_refreshTime']):
							
							sensorId = local_matrix_config[row]['sensorIds'][0]
							logger.debug("Row %s is in FIXED mode for sensor %s" % (row, sensorId))
							# Display sensor information
							if settings.MATRIX_MODE_PEAK in local_matrix_config[row]['mode']:
								peak = True
							else:
								peak = False
							if settings.MATRIX_MODE_BAR in local_matrix_config[row]['mode']:
								peak_data = lcdWriteBarGraph(lcd = lcd,
									ecudata = ecudata,
									sensorId = sensorId,
									previousId = previousId,
									row = row,
									peak = peak,
									peak_segments = local_matrix_config[row]['peak_segments'])
							else:
								peak_data = lcdWriteNumeric(lcd = lcd,
									ecudata = ecudata,
									sensorId = sensorId,
									previousId = previousId,
									row = row,
									peak = peak)
								
							# Is there a new peak?
							if peak_data:
								# Reset peak timer and set new peak value
								local_matrix_config[row]['peak'] = True
								local_matrix_config[row]['peak_segments'] = peak_data[1]
								local_matrix_config[row]['peak_counter'] = settings.MATRIX_PEAK_COUNT
							else:
								# Decrement peak timer
								if local_matrix_config[row]['peak_counter'] > 0:
									local_matrix_config[row]['peak_counter'] -= 1
								else:
									# Peak timer expired, reset
									local_matrix_config[row]['peak'] = False
									local_matrix_config[row]['peak_segments'] = 0
									local_matrix_config[row]['peak_counter'] = 0
															 
							local_matrix_config[row]['value_refreshTimer'] = timeit.default_timer()
							previousId = True
						else:
							pass
					
					############################################################################
					# Is the row configured to show additional data from above or below?
					if local_matrix_config[row]['setting'] in [settings.MATRIX_SETTING_FOR_ABOVE, settings.MATRIX_SETTING_FOR_BELOW]:
						if local_matrix_config[row]['setting'] == settings.MATRIX_SETTING_FOR_ABOVE:
							parent_row = row - 1
							
						if local_matrix_config[row]['setting'] == settings.MATRIX_SETTING_FOR_BELOW:
							parent_row = row + 1
							
						logger.debug("Row %s is in additional info mode for row %s" % (row, parent_row))
					
					# Is the row configured to show peak values?
				
			# Normal LCD refresh wait timer
			time.sleep(settings.MATRIX_REFRESH)