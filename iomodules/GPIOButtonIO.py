#!/usr/bin/env python
# -*- coding: utf8 -*-
#
# GPIO - listen for button presses coming from Raspberry Pio GPIO pins
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
import traceback

# Settings file
from libs import settings
from libs.ControlData import ControlData

# Start a new logger
from libs.newlog import newlog
logger = newlog(__name__)

def GPIOButtonIO(actionQueue, stdin):
	""" GPIO - listen for button presses on the Raspberry Pi GPIO pins """
	
	proc_name = multiprocessing.current_process().name
	logger.info("GPIO input process now running")
	
	######################################################
	# First try importing the library - this will fail on a non-Pi
	######################################################
	try:
		import RPi.GPIO as GPIO
		logger.info("GPIO library available")
		USE_GPIO = True
	except Exception as e:
		logger.warn("GPIO library not available! - Are we running on a Pi and have you installed RPi.GPIO?")
		logger.debug("%s" % traceback.print_exc())
		USE_GPIO = False
		
	######################################################
	# Try setting up the GPIO configuration
	######################################################
	if USE_GPIO:
		try:
			GPIO.setmode(GPIO.BOARD)
			logger.info("GPIO features initialised")
		except Exception as e:
			logger.error("Unable to initialise GPIO features!")
			logger.error("%s" % e)
			logger.debug("%s" % traceback.print_exc())
			USE_GPIO = False
		
	######################################################
	# Try initialising STDIN for keyboard input
	######################################################
	try:
		sys.stdin = os.fdopen(stdin)
		logger.info("Opened STDIN for keyboard input")
		USE_STDIN = True
	except:
		logger.error("Unable to open STDIN for keyboard input!")
		logger.error("%s" % e)
		logger.debug("%s" % traceback.print_exc())
		############################################################
		# If GPIO support is also unavailable, then exit, as
		# we have no way of capturing input
		############################################################
		if USE_GPIO == False:
			logger.fatal("This process will now exit - We have NO methods to capture input")
			exit(1)

	######################################################
	# The main loop where we scan for button or key presses
	######################################################
	i = 0
	button = False
	while True:
		logger.debug("Waking")		
		i += 1
			
		if i == 1000:
			logger.debug("Still running [%s]" % proc_name)
			i = 0

		if USE_GPIO:
			######################################################
			# Scan for any button presses on the GPIO pins
			######################################################
		
			logger.info("Received GPIO input")
		
			#cdata = ControlData()
			#cdata.setButton(mybutton)
			#cdata.setDuration(myduration)
			
			# Decode it, send it back up the actionQueue
			# actionQueue.put(cdata)
			pass
		
		if USE_STDIN:
			######################################################
			# Python3 and Python2 handle STDIN input in two
			# different ways
			######################################################
			if sys.version_info[0] == 3:
				myInput = input()
			else:
				myInput = raw_input()
			
			logger.info("Received keyboard input: [%s]" % myInput)
			
			######################################################
			# We only pass through control signals that are 
			# defined in the settings file - not just any random button press!
			######################################################
			if myInput in settings.BUTTON_MAP.keys():
				mybutton = myInput
				mydest = settings.BUTTON_MAP[mybutton]['dest']
				cdata = ControlData()
				cdata.setButton(mybutton)
				cdata.setPayload(data = {'status' : True, 'description' : "Button press detected"})
				actionQueue.put(cdata)
				logger.info("Send controldata message: BUTTON[%s] DESTINATION[%s]" % (mybutton, mydest))
			
		######################################################
		# Sleep until next time
		######################################################
		time.sleep(settings.GPIO_SLEEP_TIME)
				
