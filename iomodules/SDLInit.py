#!/usr/bin/env python

# sdlInit - initialise SDL windows
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

def sdlInit(windowSettings, x_res, y_res):
	""" Set up an sdl window to emulate a OLED screen """
	
	try:
		sdl2.ext.init()
		k = "Master"
		logger.info("Creating a graphics SDL screen for window [%s]" % windowSettings['windowName'])	
		if sys.version_info[0] == 3:
			title = bytes(windowSettings['windowName'], 'utf-8')
		else:
			title = b"%s" % windowSettings['windowName']
		windowSettings['sdlWindow'] = sdl2.SDL_CreateWindow(title,
						   sdl2.SDL_WINDOWPOS_UNDEFINED,
						   sdl2.SDL_WINDOWPOS_UNDEFINED,
						   x_res,
						   y_res,
						   sdl2.SDL_WINDOW_SHOWN)
		
		windowSettings['sdlSurface'] = sdl2.SDL_GetWindowSurface(windowSettings['sdlWindow'])
		windowSettings['sdlWindowContents'] = windowSettings['sdlWindow'].contents
		windowSettings['sdlSurfaceContents'] = windowSettings['sdlSurface'].contents
		windowSettings['sdlWindowArray'] = sdl2.ext.pixels3d(windowSettings['sdlSurfaceContents'])
		windowSettings['x_size'] = x_res
		windowSettings['y_size'] = y_res
		logger.info("Created SDL screen %s [%sx%s]" % (windowSettings['windowName'], windowSettings['x_size'], windowSettings['y_size']))
		return windowSettings
	except Exception as e:
		logger.error("Error while creating a graphics SDL screen for window [%s]" % windowSettings['windowName'])
		logger.error("%s" % e)
		logger.debug("%s" % traceback.print_exc())
		return False	
	