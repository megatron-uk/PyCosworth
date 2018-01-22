#!/usr/bin/env python

# SensorDisplayInit - initialise defaults for the display modes that GraphicsIO
# uses, for any of the defined sensors.
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

# Graphics libs
import sdl2
import sdl2.ext

# Settings file
from libs import settings

# Start a new logger
from libs.newlog import newlog
if getattr(sys, 'frozen', False):
	__file__ = os.path.dirname(sys.executable)
logger = newlog(__file__)

def sensorDisplayInit(windowSettings, x_res, y_res):
	""" Set up an sdl window to emulate a OLED screen """
	pass

def sensorInitWaveform(sensor, windowSettings):
	""" Set the defaults for a waveform display mode, for the given sensor """
	
	local_sensors[sensorId]['waveform'] = {}
	local_sensors[sensorId]['waveform']['valuePerLine'] = ((local_sensors[sensorId]['maxValue'] - local_sensors[sensorId]['minValue']) * 1.0) / settings.GFX_OLED_SIZE[1]
	if sensor['minValue'] < 0:
		local_sensors[sensorId]['waveform']['zeroline'] = settings.GFX_OLED_SIZE[1] - int(abs(sensor['minValue']) / local_sensors[sensorId]['waveform']['valuePerLine'])
		local_sensors[sensorId]['waveform']['baseline'] = settings.GFX_OLED_SIZE[1]
	elif sensor['minValue'] > 0:
		local_sensors[sensorId]['waveform']['zeroline'] = None
		local_sensors[sensorId]['waveform']['baseline'] = settings.GFX_OLED_SIZE[1]
	else:
		local_sensors[sensorId]['waveform']['zeroline'] = settings.GFX_OLED_SIZE[1]
		local_sensors[sensorId]['waveform']['baseline'] = None
	local_sensors[sensorId]['waveform']['maxline'] = 0
	