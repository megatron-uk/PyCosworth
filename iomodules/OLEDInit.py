#!/usr/bin/env python

# OLEDInit - initialise any OLED connected display windows
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

# Standard Libraries
import sys
import os
import traceback

# OLED libraries
from luma.core.interface.serial import i2c, spi
from luma.oled.device import ssd1306 as luma_ssd1306
from luma.oled.device import ssd1325 as luma_ssd1325
from luma.oled.device import ssd1331 as luma_ssd1331
from luma.oled.device import sh1106 as luma_sh1106

# Settings file
from libs import settings

# Start a new logger
from libs.newlog import newlog
if getattr(sys, 'frozen', False):
	__file__ = os.path.dirname(sys.executable)
logger = newlog(__file__)

def oledInit(windowSettings, x_res, y_res):
	try:
		logger.info("Attempting to connect to I2C device for OLED screen [%s]" % windowSettings['windowName'])
		windowSettings['x_size'] = x_res
		windowSettings['y_size'] = y_res
		if windowSettings['oledType'] == 'sh1106':
			serial = i2c(port=1, address=windowSettings['i2cAddress'])
			windowSettings['luma_driver'] = luma_sh1106(serial)
		else:
			logger.warn("OLED type %s is not yet supported" % windowSettings['oledType'])
			return False
		logger.info("Initialised OLED device %s [%s@%sx%s]" % (windowSettings['windowName'], windowSettings['oledType'], windowSettings['x_size'], windowSettings['y_size']))
		return windowSettings
	except Exception as e:
		logger.error("Unable to set up OLED device [%s] - is it connected and configured for I2C or SPI?" % windowSettings['windowName'])
		logger.error("%s" % e)
		logger.debug("%s" % traceback.print_exc())
		return False