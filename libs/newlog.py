#!/usr/bin/env python

# newlog, a wrapper around the Python logging class
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

# Use as follows:
#
# from newlog import newlog
#
# logger = newlog(__file__)
# logger.debug("something")
# logger.error("boom!")
#

# Standard libraries
import logging
import os

# Settings
from libs import settings

def newlog(name, logging_level = None, raven = True):
	""" Configure a new Python standard logger with sensible values for time, filename etc. """
	
	filename = os.path.basename(name)
	
	# The name of this method, should always be 'newlog'
	myname = __name__
	
	# Create a new, named logger with the filename of the script that called us
	logger = logging.getLogger(name)
	
	# Set the output log level
	if settings.DEBUG:
		logger.setLevel(logging.DEBUG)
	else:
		if settings.INFO:
			logger.setLevel(logging.INFO)
		else:
			logger.setLevel(logging.WARNING)
	
	# Set the output to console for now
	logger.addHandler(logging.StreamHandler())
	
	# Set the format of the message
	# asctime = datetime of the event
	# levelname = DEBUG/INFO/WARNING/ERROR etc..
	# filename = the name of the script generating the log
	# lineno = the line in the script generating the log
	# funcname = the name of the method or class generating the log
	# message = the output being displayed
	format = logging.Formatter('[%(asctime)s] [%(levelname)8s] (%(filename)16s:%(lineno)4s) | %(processName)s | %(message)s')

	# Enable *only* this logger to output, override any existing handler
	basic_logger = logging.StreamHandler()
	basic_logger.setFormatter(format)
	logger.handlers = []
	logger.addHandler(basic_logger)	
	
	return logger