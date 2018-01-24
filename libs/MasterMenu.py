#!/usr/bin/env python
# -*- coding: utf8 -*-
#
# masterWindow - class and state machine representing the master display screen
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
import time
import timeit 
import sys
import os
import copy
import traceback
from collections import deque

# Graphics libs
from PIL import Image
from PIL import ImageOps
from PIL import ImageDraw
from PIL import ImageFont

from iomodules.GraphicsIO import updateSDLWindow, updateOLEDScreen, blankImage

# Settings file
from libs import settings

# Menu settings
from libs import menusettings
from libs.MenuFunctions import *

# Control data
from libs.ControlData import ControlData

# Start a new logger
from libs.newlog import newlog
logger = newlog(__name__)

class MasterMenu():
	""" A class which encapsulates the main master window """
	
	def __init__(self, 
		windowSettings = None,
		subWindowSettings = [],
		actionQueue = None,
		ecudata = None, 
		use_sdl = False, 
		use_oled = False
		):
		""" Instaniate the class """
		
		# A queue to pass messages back up the main process
		self.actionQueue = actionQueue
		
		# A list of any sub windows
		self.subWindowSettings = subWindowSettings
		
		# Ecu/sensor data class
		self.ecudata = ecudata
		
		# Flags to indicate OLED and/or SDL are in use
		self.use_sdl = use_sdl
		self.use_oled = use_oled
		
		# Load window settings for the master screen
		if windowSettings:
			self.windowSettings = windowSettings
		else:
			self.windowSettings = settings.GFX_MASTER_WINDOW
		
		# Default to menu NOT showing
		self.menuShow = False
		
		# Index into the menu
		self.menuIndex = None
		self.subMenuIndex = None
		self.finalMenuIndex = None
		self.selectedItem = None
		
		# Cache of assembled bitmap fragments (menus, icons, etc)
		self.bitmapCache = {}
		
		# Cache of previously generated images
		self.frameCache = {}
		self.useFrameCache = True
				
		# Cache of previous loaded fonts
		self.fontCache = {}
				
		# This defines the menu structure of the master window
		# itemType = menu|item
		self.menu = menusettings.MASTER_MENU
		
		# Preload any essential fonts
		self.preloadFonts()
		
		#######################################################################################
		# Record how much available display space we have above
		# the bottom menu
		first_menu_item = self.menu[0]['itemName']
		self.availableLines = self.windowSettings['y_size'] - settings.GFX_MASTER_BASE_MENU_SIZE[1]
		logger.info("[%s] lines of pixels above bottom menu" % self.availableLines)
		
		# How many complete lines of items can we show above the 1st level menu
		self.submenuFont = self.getFont(size = settings.GFX_MASTER_SUBMENU_FONTSIZE)
		self.submenuFontSize = self.submenuFont.getsize("TestItem")
		self.menuItemsShown = int(self.availableLines / self.submenuFontSize[1])
		logger.info("[%s] lines of text available at size %s" % (self.menuItemsShown, settings.GFX_MASTER_SUBMENU_FONTSIZE))
		
		# How many free pixels are left over?
		self.menuFreeLines = self.availableLines - (self.menuItemsShown * self.submenuFontSize[1])
		logger.info("[%s] lines of pixels left" % self.menuFreeLines)
		
		#######################################################################################
		# Record how many lines we have for help text in the submenu or final menu area
		self.helpTextFont = self.getFont(size = settings.GFX_MASTER_HELP_FONTSIZE)
		self.helpTextFontSize = self.helpTextFont.getsize("TestItem")
		self.helpTextLines = int(self.availableLines / self.helpTextFontSize[1])
		logger.info("[%s] lines of help text available at size %s" % (self.helpTextLines, settings.GFX_MASTER_HELP_FONTSIZE))
		
		# Offset any submenu items this many pixels from the LHS.
		self.leftOffset = 1
		
		self.slideIn = False
		self.slideOut = False
		self.slideOutIn = False
		
		# Add all current sensors to the Sensor menu
		self.sensor_keys = []
		self.addSensors()
		
		# The custom function and its associated data which run
		# run every time the mastermenu class has 'buildimage' called
		# and we are *not* in a menu.
		self.customFunction = None
		self.customData = None
		
		######################################################################################
		#
		# Class methods
		#
		######################################################################################
		
	def addSensors(self):
		""" Construct the sensor sub-menu with the current active sensors """
		
		refreshBitmaps = False
		
		for sensor_menu in self.menu[0]['items']:
			self.sensor_keys.append(sensor_menu['itemName'])
				
		sensor_ids = settings.SENSOR_IDS
		sensor_ids.sort()
		for sensorId in sensor_ids:
			if sensorId not in self.sensor_keys:
				sensorData = self.ecudata.getSensorData(sensorId)
				if sensorData:
					logger.info("Adding new sensor to menu %s" % sensorId)
					sensor_submenu = {
						'itemName'	: sensorId,
						'itemType'	: 'menu',
						'itemText'	: sensorData['description'],
						'items'		: [
							{
								'itemName'	: 'Fullscreen',
								'itemType'	: 'item',
								'itemText'	: 'Select as fullscreen sensor',
								'itemSelect': sensorSelectFull,
							},
							{
								'itemName'	: 'Left',
								'itemType'	: 'item',
								'itemText'	: 'Select as left sensor',
								'itemSelect': sensorSelectLeft,
							},
							{
								'itemName'	: 'Right',
								'itemType'	: 'item',
								'itemText'	: 'Select as right sensor',
								'itemSelect': sensorSelectRight,
							},
						]
					}
					
					# The sensor menu is always element 0 of the main menu
					self.menu[0]['items'].append(sensor_submenu)
					refreshBitmaps = True
				else:
					logger.warn("Unable to find sensor data definition for %s" % sensorId)
		
		# No sensors found
		if len(self.menu[0]['items']) == 0:
			no_sensor_entry = {
				'itemName'	: 'No sensors!',
				'itemType'	: 'item',
				'itemText'	: 'No sensors have been detected. Have you configured the right sensor modules in the settings.py file?',
				'itemSelect': doNothing
			}
			self.menu[0]['items'].append(no_sensor_entry)
		elif len(self.menu[0]['items']) > 1:
			# Remove 'No sensors' menu entry
			idx = 0
			if len(self.menu[0]['items']) > 0:
				for item in self.menu[0]['items']:
					if item['itemName'] == 'No sensors!':
						del self.menu[0]['items'][idx]
				idx += 1
		
		# Refresh the bitmaps, if we added any new sensors
		if refreshBitmaps:
			# Remove submenu bitmaps
			keys = list(self.bitmapCache.keys())
			for k in keys:
				del self.bitmapCache[k]
				
			# Remove full screen bitmap
			keys = list(self.frameCache.keys())
			for k in keys:
				del self.frameCache[k]
		
	def preloadFonts(self):
		
		# A font for the 2nd level menu
		self.getFont(name = "sans", style = "bold", size = settings.GFX_MASTER_SUBMENU_FONTSIZE)
		
	def getFont(self, name = "sans", style = "plain", size = 8):
		""" Load a font from disk, at a specified size """
		
		key = str(name) + "_" + str(style) + "_" + str(size)
		
		if key in self.fontCache.keys():
			return self.fontCache[key]
		else:
			logger.debug("Loading font %s" % key)
			font = ImageFont.truetype(settings.GFX_FONTS[name][style]['font'], size)	
			self.fontCache[key] = font
		return font
		
	def processControlData(self, controlData):
		""" Respond to button presses and other control data. """
		
		self.addSensors()
		
		if self.finalMenuIndex is not None:
			# 3rd level menus
		
			# Scroll up the final menu
			if controlData.button == settings.BUTTON_UP:
				subitems = copy.copy(self.menu[self.menuIndex]['items'])
				subitems.reverse()
				finalitems = copy.copy(subitems[self.subMenuIndex]['items'])
				if (self.finalMenuIndex < (len(finalitems) - 1)):
					self.finalMenuIndex += 1
					
			# Scroll down the final menu
			if controlData.button == settings.BUTTON_DOWN:
				if (self.finalMenuIndex >0):
					self.finalMenuIndex -= 1
			
			# Open the 3rd level menu item that is selected
			if controlData.button == settings.BUTTON_SELECT:
				if self.finalMenuIndex > -1:
					# Is this a menu or item?
					#logger.info(self.menu[self.menuIndex]['items'][self.subMenuIndex]['items'][self.finalMenuIndex])
					subitems = copy.copy(self.menu[self.menuIndex]['items'])
					subitems.reverse()
					finalitems = copy.copy(subitems[self.subMenuIndex]['items'])
					finalitems.reverse()
					if finalitems[self.finalMenuIndex]['itemType'] == 'item':
						logger.info("Selected a final menu item to launch: %s/%s/%s %s" % (self.menuIndex, self.subMenuIndex, self.finalMenuIndex, finalitems[self.finalMenuIndex]))
						self.customFunction = finalitems[self.finalMenuIndex]['itemSelect']
						self.buildCustomData()
						self.resetMenus()
						self.slideOut = True
						return
					# if item, then mark it as an item selected
					# otherwise open final menu
					self.finalMenuIndex = -1
		
			# cancel menu selection - make it dissappear
			if controlData.button == settings.BUTTON_CANCEL:
				self.finalMenuIndex = None
				self.selectedItem = None
		
		elif self.subMenuIndex is not None:
			# 2nd level menu selected
			
			# Scroll up the submenu
			if controlData.button == settings.BUTTON_UP:
				if (self.subMenuIndex < (len(self.menu[self.menuIndex]['items']) - 1)):
					self.subMenuIndex += 1
					
			# Scroll down the submenu
			if controlData.button == settings.BUTTON_DOWN:
				if (self.subMenuIndex >0):
					self.subMenuIndex -= 1
			
			# Open the 2nd level menu item that is selected
			if controlData.button == settings.BUTTON_SELECT:
				if self.subMenuIndex > -1:
					# Is this a menu or item?
					#logger.info(self.menu[self.menuIndex]['items'][self.subMenuIndex])
					subitems = copy.copy(self.menu[self.menuIndex]['items'])
					subitems.reverse()
					#logger.info(subitems[self.subMenuIndex])
					if subitems[self.subMenuIndex]['itemType'] == 'item':
						logger.info("Selected a submenu item to launch: %s/%s/%s %s" % (self.menuIndex, self.subMenuIndex, self.finalMenuIndex, subitems[self.subMenuIndex]))
						self.customFunction = subitems[self.subMenuIndex]['itemSelect']
						self.buildCustomData()
						self.resetMenus()
						self.slideOut = True
						return
					# if item, then mark it as an item selected
					# otherwise open final menu
					self.finalMenuIndex = -1
			
			# cancel menu selection - make it dissappear
			if controlData.button == settings.BUTTON_CANCEL:
				self.subMenuIndex = None
				self.finalMenuIndex = None
				self.selectedItem = None
			
		elif self.menuIndex is not None:
			# Scroll left
			if controlData.button == settings.BUTTON_LEFT:
				if (self.menuIndex >0):
					self.menuIndex -= 1
				elif (self.menuIndex <0):
					self.menuIndex = (len(self.menu) - 1)
			# Scroll right
			if controlData.button == settings.BUTTON_RIGHT:
				if (self.menuIndex < (len(self.menu) - 1)):
					self.menuIndex += 1
				
			# Open the 1st level menu item that is selected
			if controlData.button == settings.BUTTON_SELECT:
				if self.menuIndex > -1:
					self.subMenuIndex = -1
				
			# cancel menu selection - make it dissappear
			if controlData.button == settings.BUTTON_CANCEL:
				self.selectedItem = None
				self.subMenuIndex = None
				self.finalMenuIndex = None
				self.menuIndex = None
				self.menuShow = -1
				self.slideOut = True
				
		elif self.customFunction is not None:
			# Pass any control data to the current custom function
			self.customFunction(menuClass = self, controlData = controlData)
			
		else:
			# Nothing selected, bring up the menu
			if controlData.button == settings.BUTTON_SELECT:
				# Enable menu selection - make base menu appear
				self.menuIndex = -1
				self.menuShow = True
				self.slideIn = True
				# Store the last running function
				self.resetCustomFunction()
			
			elif controlData.button == settings.BUTTON_CANCEL:
				# cancel menu selection - make it dissappear
				self.menuIndex = None
				self.menuShow = True
				self.slideOut = True
				# Return to the last running function
				self.returnCustomFunction() 
		
		#logger.info("menuIndex:%s subMenuIndex:%s finalMenuIndex:%s menuShow:%s slideIn:%s slideOut:%s" % (self.menuIndex, self.subMenuIndex, self.finalMenuIndex, self.menuShow, self.slideIn, self.slideOut))
	
	def buildCustomData(self):
		""" Record the state of the menu variables at the time the custom function was called 
		as many of the custom functions will want to know which menu item was selected to call
		them - i.e. which sensor to use. """
		
		# Record the state of the menu variables at the time the custom function was called
		self.customData = {
			'selectedItem' : (self.menuIndex, self.subMenuIndex, self.finalMenuIndex),	
		}
	
	def resetMenus(self, showMenu = False):
		""" Reset menu structure back to default """
		
		if showMenu:
			self.menuIndex = -1
			self.menuShow = True
			self.slideOutIn = True
		else:
			self.menuIndex = None
			self.menuShow = None	
		
		self.selectedItem = None
		self.subMenuIndex = None
		self.finalMenuIndex = None
		
	
	def resetCustomFunction(self):
		""" Disable any current custom function """
		
		# Make a copy of the current custom function, in case
		# we return to it
		self.previousCustomFunction = copy.copy(self.customFunction)
		self.previousCustomData = copy.copy(self.customData)
		
		# Reset the custom function so that it does not execute
		# the next time processControlData
		self.customFunction = None
		self.customData = None
	
	def returnCustomFunction(self):
		""" Return to the last custom function """
		
		self.customFunction = copy.copy(self.previousCustomFunction)
		self.customData = copy.copy(self.previousCustomData)
	
	def buildImage(self):
		""" Called """
		
		if self.menuShow:
			
			if self.slideOutIn:
				# Slide out the previous frame and then slide in the menu
				self.slideBitmapVertical(
					bitmap = self.image.copy(), 
					x_start = 0, 
					y_start = 0, 
					y_end = (self.windowSettings['y_size']), 
					direction = "down", 
					steps = 20,
					sleep = 0.025)
				# Slide in the base menu
				bitmap = self.createBaseMenuBitmap()
				self.slideBitmapVertical(
					bitmap = bitmap, 
					x_start = 0, 
					y_start = self.windowSettings['y_size'], 
					y_end = (self.windowSettings['y_size'] - bitmap.size[1]), 
					direction = "up", 
					steps = 10,
					sleep = 0.025)
				self.slideOutIn = False
			elif self.slideIn:
				# Slide in the base menu
				bitmap = self.createBaseMenuBitmap()
				self.slideBitmapVertical(
					bitmap = bitmap, 
					x_start = 0, 
					y_start = self.windowSettings['y_size'], 
					y_end = (self.windowSettings['y_size'] - bitmap.size[1]), 
					direction = "up", 
					steps = 10,
					sleep = 0.025)
				self.slideIn = False
			elif self.slideOut:
				# Slide out the entire screen
				self.slideBitmapVertical(
					bitmap = self.image.copy(), 
					x_start = 0, 
					y_start = 0, 
					y_end = (self.windowSettings['y_size']), 
					direction = "down", 
					steps = 20,
					sleep = 0.025)
				self.slideOut = False
				self.menuShow = False
			else:
				# Display a normal menu screen from the selected menu options
				self.buildMenu()
		else:
			if self.slideOut:
				# Slide out the entire screen
				self.slideBitmapVertical(
					bitmap = self.image.copy(), 
					x_start = 0, 
					y_start = 0, 
					y_end = (self.windowSettings['y_size']), 
					direction = "down", 
					steps = 20,
					sleep = 0.025)
				self.slideOut = False
				self.menuShow = False
			# Did the last run through the menu set a target to run?
			if self.customFunction:
				logger.debug("Running current custom function")
				self.customFunction(menuClass = self)
			else:
				blank = blankImage(self.windowSettings)
				self.image = blank['image']
				
		self.update()

	def createBaseMenuBitmap(self):
		""" Create a bitmap for the first level menu (with the current item highlighted, if necessary) - just the height of the menu itself """
		
		key = "basemenuBitmap|menuIndex:" + str(self.menuIndex)
		if key in self.bitmapCache.keys():
			logger.info("Cache result found for base menu bitmap")
		else:
			x_pos = 0
			index = 0
			image = Image.new('1', (settings.GFX_MASTER_BASE_MENU_SIZE[0], settings.GFX_MASTER_BASE_MENU_SIZE[1]))
			for menuItem in self.menu:
				if index == self.menuIndex:
					bitmap = Image.open(settings.GFX_MASTER_BITMAPS[menuItem['itemName']]['on'])
				else:
					bitmap = Image.open(settings.GFX_MASTER_BITMAPS[menuItem['itemName']]['off'])
				image.paste(bitmap,(x_pos, 0))
				x_pos += settings.GFX_MASTER_BITMAPS[menuItem['itemName']]['size'][0]
				index += 1
			self.bitmapCache[key] = copy.copy(image)
			logger.info("Base menu bitmap assembled")
		return self.bitmapCache[key].copy()

	def createSubMenuBitmap(self):
		""" Create a bitmap for the second level menu (with the current item highlighted, if necessary) """
		
		key = "submenuBitmap|menuIndex:" + str(self.menuIndex) + ",subMenuIndex:" + str(self.subMenuIndex) + ",finalMenuIndex:" +str(self.finalMenuIndex)
		if key in self.bitmapCache.keys():
			logger.info("Cache result found for sub menu bitmap key %s" % key)
		else:
			submenuFont = self.getFont(style = "bold", size = settings.GFX_MASTER_SUBMENU_FONTSIZE)
			image = Image.new('1', (settings.GFX_MASTER_SUBMENU_SIZE[0], settings.GFX_MASTER_SUBMENU_SIZE[1]))
			draw = ImageDraw.Draw(image)
			# Can we show the full list of items
			if self.menuItemsShown >= len(self.menu[self.menuIndex]['items']):
				logger.info("Building submenu bitmap [name:%s id:%s] has %s items - we can show them all (max:%s)" % (self.menu[self.menuIndex]['itemName'], self.menuIndex, len(self.menu[self.menuIndex]['items']), self.menuItemsShown))
				x_pos = 0
				y_pos = settings.GFX_MASTER_BASE_MENU_SIZE[1] + settings.GFX_MASTER_SUBMENU_FONTSIZE
				index = 0
				menuItems = copy.copy(self.menu[self.menuIndex]['items'])
				menuItems.reverse()				
				for menuItem in menuItems:
					if index == self.subMenuIndex:
						# This is a selected menu item.
						# Create an inverted image for the currently highlighted line
						# Is this bitmap fragment in the cache? if so, return it
						# otherwise create a new tiny image just to hold the menu item
						# fill it in white
						# draw the text in black
						# paste in to the submenu where a normal menu text would go
						# save bitmap fragment for next time
						bitmapKey = "menu|menuIndex:" + str(self.menuIndex) + ",subMenuIndex:" + str(self.subMenuIndex) + ",itemName:" + menuItem['itemName'] + "|selected"
						if bitmapKey in self.bitmapCache.keys():
							logger.debug("Returning submenu selected item bitmap for %s" % menuItem['itemName'])
							i = self.bitmapCache[bitmapKey].copy()
						else:
							logger.debug("Building new selected item bitmap for %s" % menuItem['itemName'])
							i = Image.new('1', (settings.GFX_MASTER_SUBMENU_SIZE[0], settings.GFX_MASTER_SUBMENU_FONTSIZE))
							d = ImageDraw.Draw(i)
							d.rectangle([(0,0), (settings.GFX_MASTER_SUBMENU_SIZE[0], settings.GFX_MASTER_SUBMENU_FONTSIZE)], fill = "white")
							d.text((0, 0), menuItem['itemName'], fill="black", font = submenuFont)
							self.bitmapCache[bitmapKey] = copy.copy(i)
						image.paste(i, (0, y_pos))
					else: 
						# This is an unselected menu item.
						draw.text((0, y_pos), menuItem['itemName'], fill="white", font = submenuFont)
					y_pos -= settings.GFX_MASTER_SUBMENU_FONTSIZE
					index += 1
			else:
				logger.info("Building submenu bitmap [name:%s id:%s] has %s items - too many to show at once (max:%s)" % (self.menu[self.menuIndex]['itemName'], self.menuIndex, len(self.menu[self.menuIndex]['items']), self.menuItemsShown))
				x_pos = 0
				y_pos = settings.GFX_MASTER_BASE_MENU_SIZE[1] + settings.GFX_MASTER_SUBMENU_FONTSIZE
				
				# Adjust the list of items by the scrolling window start and end positions
				if (self.subMenuIndex + 1) > self.menuItemsShown:
					start = (self.subMenuIndex + 1) - self.menuItemsShown
					end = (self.subMenuIndex + 1)
					menuItems = copy.copy(self.menu[self.menuIndex]['items'])
					menuItems.reverse()
					menuItems = menuItems[start:end]
					index = start
					if end <= len(self.menu[self.menuIndex]['items']):
						show_up_arrow = True
					else:
						show_up_arrow = False
					if start >= self.menuItemsShown:
						show_down_arrow = True
					else:
						show_down_arrow = False
					if (self.subMenuIndex + 1) > self.menuItemsShown:
						show_down_arrow = True
				else:
					menuItems = copy.copy(self.menu[self.menuIndex]['items'])
					menuItems.reverse()
					index = 0
					show_up_arrow = True
					show_down_arrow = False
				
				for menuItem in menuItems:
					if index == self.subMenuIndex:
						# This is a selected menu item.
						# Create an inverted image for the currently highlighted line
						# Is this bitmap fragment in the cache? if so, return it
						# otherwise create a new tiny image just to hold the menu item
						# fill it in white
						# draw the text in black
						# paste in to the submenu where a normal menu text would go
						# save bitmap fragment for next time
						bitmapKey = "menu|menuIndex:" + str(self.menuIndex) + ",subMenuIndex:" + str(self.subMenuIndex) + ",itemName:" + menuItem['itemName'] + "|selected"
						if bitmapKey in self.bitmapCache.keys():
							logger.debug("Returning submenu selected item bitmap for %s" % menuItem['itemName'])
							i = self.bitmapCache[bitmapKey].copy()
						else:
							logger.debug("Building new selected item bitmap for %s" % menuItem['itemName'])
							i = Image.new('1', (settings.GFX_MASTER_SUBMENU_SIZE[0], settings.GFX_MASTER_SUBMENU_FONTSIZE))
							d = ImageDraw.Draw(i)
							d.rectangle([(0,0), (settings.GFX_MASTER_SUBMENU_SIZE[0], settings.GFX_MASTER_SUBMENU_FONTSIZE)], fill = "white")
							d.text((0, 0), menuItem['itemName'], fill="black", font = submenuFont)
							self.bitmapCache[bitmapKey] = copy.copy(i)
						image.paste(i, (0, y_pos))
					else: 
						# This is an unselected menu item.
						draw.text((0, y_pos), menuItem['itemName'], fill="white", font = submenuFont)
					y_pos -= settings.GFX_MASTER_SUBMENU_FONTSIZE
					index += 1
				if show_up_arrow:
					bitmap = Image.open(settings.GFX_MASTER_BITMAPS['arrow']['up'])
					image.paste(bitmap, (settings.GFX_MASTER_ARROW_1_XPOS, settings.GFX_UP_ARROW_YPOS))
				if show_down_arrow:
					bitmap = Image.open(settings.GFX_MASTER_BITMAPS['arrow']['down'])
					image.paste(bitmap, (settings.GFX_MASTER_ARROW_1_XPOS, settings.GFX_DOWN_ARROW_YPOS))
			
			self.bitmapCache[key] = copy.copy(image)
		return self.bitmapCache[key].copy()

	def createFinalMenuBitmap(self):
		""" Create a bitmap for the finale level menu (with the current item highlighted, if necessary) """
		
		key = "finalmenuBitmap|menuIndex:" + str(self.menuIndex) + ",subMenuIndex:" + str(self.subMenuIndex) + ",finalMenuIndex:" +str(self.finalMenuIndex)
		if key in self.bitmapCache.keys():
			logger.info("Cache result found for final menu bitmap key %s" % key)
		else:
			logger.info("Creating new final menu bitmap for key %s" % key)
			submenuFont = self.getFont(style = "bold", size = settings.GFX_MASTER_SUBMENU_FONTSIZE)
			image = Image.new('1', (settings.GFX_MASTER_SUBMENU_SIZE[0], settings.GFX_MASTER_SUBMENU_SIZE[1]))
			draw = ImageDraw.Draw(image)
			# Can we show the full list of items
			
			# Flip the item list to match sub menu order
			items = copy.copy(self.menu[self.menuIndex]['items'])
			items.reverse()
			if self.menuItemsShown >= len(items[self.subMenuIndex]['items']):
				logger.info("Building final menu bitmap [name:%s id:%s] has %s items - we can show them all (max:%s)" % (items[self.subMenuIndex]['itemName'], self.subMenuIndex, len(items[self.subMenuIndex]['items']), self.menuItemsShown))
				x_pos = 0
				y_pos = settings.GFX_MASTER_BASE_MENU_SIZE[1] + settings.GFX_MASTER_SUBMENU_FONTSIZE
				index = 0
				menuItems = copy.copy(items[self.subMenuIndex]['items'])
				menuItems.reverse()				
				for menuItem in menuItems:
					if index == self.finalMenuIndex:
						# This is a selected menu item.
						# Create an inverted image for the currently highlighted line
						# Is this bitmap fragment in the cache? if so, return it
						# otherwise create a new tiny image just to hold the menu item
						# fill it in white
						# draw the text in black
						# paste in to the submenu where a normal menu text would go
						# save bitmap fragment for next time
						bitmapKey = "menu|menuIndex:" + str(self.menuIndex) + ",subMenuIndex:" + str(self.subMenuIndex) + ",finalMenuIndex:" + str(self.finalMenuIndex) + ",itemName:" + menuItem['itemName'] + "|selected"
						if bitmapKey in self.bitmapCache.keys():
							logger.info("Returning final menu selected item bitmap for %s" % menuItem['itemName'])
							i = self.bitmapCache[bitmapKey].copy()
						else:
							logger.info("Building new selected item bitmap for %s" % menuItem['itemName'])
							i = Image.new('1', (settings.GFX_MASTER_SUBMENU_SIZE[0], settings.GFX_MASTER_SUBMENU_FONTSIZE))
							d = ImageDraw.Draw(i)
							d.rectangle([(0,0), (settings.GFX_MASTER_SUBMENU_SIZE[0], settings.GFX_MASTER_SUBMENU_FONTSIZE)], fill = "white")
							d.text((0, 0), menuItem['itemName'], fill="black", font = submenuFont)
							self.bitmapCache[bitmapKey] = copy.copy(i)
						image.paste(i, (0, y_pos))
					else: 
						# This is an unselected menu item.
						logger.info("Drawing unselected item %s" % menuItem['itemName'])
						draw.text((0, y_pos), menuItem['itemName'], fill="white", font = submenuFont)
					y_pos -= settings.GFX_MASTER_SUBMENU_FONTSIZE
					index += 1
			else:
				logger.info("Building final menu bitmap [name:%s id:%s] has %s items - too many to show at once (max:%s)" % (self.menu[self.menuIndex]['itemName'], self.menuIndex, len(self.menu[self.menuIndex]['items']), self.menuItemsShown))
				x_pos = 0
				y_pos = settings.GFX_MASTER_BASE_MENU_SIZE[1] + settings.GFX_MASTER_SUBMENU_FONTSIZE
				
				# Adjust the list of items by the scrolling window start and end positions
				if (self.finalMenuIndex + 1) > self.menuItemsShown:
					start = (self.finalMenuIndex + 1) - self.menuItemsShown
					end = (self.finalMenuIndex + 1)
					menuItems = copy.copy(items[self.subMenuIndex]['items'])
					menuItems.reverse()
					menuItems = menuItems[start:end]
					index = start
					if end <= len(items[self.subMenuIndex]['items']):
						show_up_arrow = True
					else:
						show_up_arrow = False
					if start >= self.menuItemsShown:
						show_down_arrow = True
					else:
						show_down_arrow = False
					if (self.finalMenuIndex + 1) > self.menuItemsShown:
						show_down_arrow = True
				else:
					menuItems = copy.copy(items[self.subMenuIndex]['items'])
					menuItems.reverse()
					index = 0
					show_up_arrow = True
					show_down_arrow = False
				
				for menuItem in menuItems:
					if index == self.finalMenuIndex:
						# This is a selected menu item.
						# Create an inverted image for the currently highlighted line
						# Is this bitmap fragment in the cache? if so, return it
						# otherwise create a new tiny image just to hold the menu item
						# fill it in white
						# draw the text in black
						# paste in to the submenu where a normal menu text would go
						# save bitmap fragment for next time
						bitmapKey = "menu|menuIndex:" + str(self.menuIndex) + ",subMenuIndex:" + str(self.subMenuIndex) + ",finalMenuIndex:" + str(self.finalMenuIndex) + ",itemName:" + menuItem['itemName'] + "|selected"
						if bitmapKey in self.bitmapCache.keys():
							logger.debug("Returning final menu selected item bitmap for %s" % menuItem['itemName'])
							i = self.bitmapCache[bitmapKey].copy()
						else:
							logger.debug("Building new selected item bitmap for %s" % menuItem['itemName'])
							i = Image.new('1', (settings.GFX_MASTER_SUBMENU_SIZE[0], settings.GFX_MASTER_SUBMENU_FONTSIZE))
							d = ImageDraw.Draw(i)
							d.rectangle([(0,0), (settings.GFX_MASTER_SUBMENU_SIZE[0], settings.GFX_MASTER_SUBMENU_FONTSIZE)], fill = "white")
							d.text((0, 0), menuItem['itemName'], fill="black", font = submenuFont)
							self.bitmapCache[bitmapKey] = copy.copy(i)
						image.paste(i, (0, y_pos))
					else: 
						# This is an unselected menu item.
						draw.text((0, y_pos), menuItem['itemName'], fill="white", font = submenuFont)
					y_pos -= settings.GFX_MASTER_SUBMENU_FONTSIZE
					index += 1
				if show_up_arrow:
					bitmap = Image.open(settings.GFX_MASTER_BITMAPS['arrow']['up'])
					image.paste(bitmap, (settings.GFX_MASTER_ARROW_1_XPOS, settings.GFX_UP_ARROW_YPOS))
				if show_down_arrow:
					bitmap = Image.open(settings.GFX_MASTER_BITMAPS['arrow']['down'])
					image.paste(bitmap, (settings.GFX_MASTER_ARROW_1_XPOS, settings.GFX_DOWN_ARROW_YPOS))
			
			# Draw bar to right of menu
			#logger.debug("Drawing submenu bar line x:%s,y:%s - x:%s,y:%s" % (settings.GFX_MASTER_LINE_1_XPOS, 0, settings.GFX_MASTER_LINE_1_XPOS, settings.GFX_MASTER_SUBMENU_SIZE[1]))
			#draw.line([(settings.GFX_MASTER_LINE_1_XPOS - 1, 0), (settings.GFX_MASTER_LINE_1_XPOS - 1, settings.GFX_MASTER_SUBMENU_SIZE[1])], width = 1, fill = "white")
			self.bitmapCache[key] = copy.copy(image)
		return self.bitmapCache[key].copy()

	def slideBitmapVertical(self, bitmap = None, x_start = 0, y_start = 0, y_end = 0, steps = 0, direction = "up", sleep = 0.1):
		""" Slide in a bitmap vertically - either from top or bottom of screen """
		
		y_pos = y_start
		y_increment = int(bitmap.size[1]/steps)
		
		if direction == "up":
			# Slide a bitmap from bottom to top
			logger.debug("Vertically sliding image up from y:%s to y:%s in x%s %spx steps" % (y_start, y_end, steps, y_increment))
			for i in range(0, steps + 1):
				self.image = Image.new('1', (self.windowSettings['x_size'], self.windowSettings['y_size']))
				logger.debug("Pasting bitmap at x:%s,y:%s" % (x_start, y_pos))
				self.image.paste(bitmap,(x_start, y_pos))
				self.update()
				time.sleep(sleep)
				y_pos -= y_increment
		else:
			logger.debug("Vertically sliding image up from y:%s to y:%s - %s steps" % (y_start, y_end, steps))
			l = list(range(0, steps + 1))
			l.reverse()
			for i in l: 
				self.image = Image.new('1', (self.windowSettings['x_size'], self.windowSettings['y_size']))
				logger.debug("Pasting bitmap at x:%s,y:%s" % (x_start, y_pos))
				self.image.paste(bitmap,(x_start, y_pos))
				self.update()
				time.sleep(sleep)
				y_pos += y_increment
			# Slide a bitmap from top to bottom
		
	def wrappedHelpWindowText(self, text = "Default text", windowLevel = "main"):
		""" Display text, wrapped over several lines, for a given menu level """
				
		if windowLevel == "main":
			logger.info("Assembling help text for main menu")
			x_size = self.windowSettings['x_size'] - 2
			x_pos = 1
			key = "helptextBitmap|windowLevel:" + windowLevel + ",menuIndex:" + str(self.menuIndex)
		elif windowLevel == "sub":
			logger.info("Assembling help text for submenu")
			x_size = self.windowSettings['x_size'] - settings.GFX_MASTER_SUBMENU_SIZE[0]
			x_pos = settings.GFX_MASTER_SUBMENU_SIZE[0]
			key = "helptextBitmap|windowLevel:" + windowLevel + ",menuIndex:" + str(self.menuIndex) + ",subMenuIndex:" + str(self.subMenuIndex) 
		elif windowLevel == "final":
			logger.info("Assembling help text for a final menu item")
			x_size = self.windowSettings['x_size'] - (2 * settings.GFX_MASTER_SUBMENU_SIZE[0])
			x_pos = (2 * settings.GFX_MASTER_SUBMENU_SIZE[0])
			key = "helptextBitmap|windowLevel:" + windowLevel + ",menuIndex:" + str(self.menuIndex) + ",subMenuIndex:" + str(self.subMenuIndex) + ",finalMenuIndex:" + str(self.finalMenuIndex)
		
		if key in self.bitmapCache.keys():
			logger.info("Cache result found for helptext bitmap key %s" % key)
		else:
			logger.info("Generating new helptext bitmap key %s" % key)
			y_pos = 0
			y_size = self.windowSettings['y_size'] - settings.GFX_MASTER_BASE_MENU_SIZE[1]
			
			wrap_text = self.wrapText(text = text, font = self.helpTextFont, max_width = x_size, max_lines = self.helpTextLines)
			logger.info("Help text will be on %s lines" % len(wrap_text))
			helptextBitmap = Image.new('1', (x_size, y_size))
			draw = ImageDraw.Draw(helptextBitmap)
			x = 0
			y = 0
			for line in wrap_text:
				draw.text((x,y), line, font = self.helpTextFont, fill = "white")
				y += self.helpTextFontSize[1]
			self.bitmapCache[key] = copy.copy(helptextBitmap)
		return self.bitmapCache[key].copy()
		
		
	def buildMenu(self):
		""" If at least one menu item is selected, build and show a menu screen """
		
		# Have we generated an image frame for this combination of selected menu and items before?
		key = "menu|menuIndex:" + str(self.menuIndex) + ",subMenuIndex:" + str(self.subMenuIndex) + ",finalMenuIndex:" + str(self.finalMenuIndex)
		if (key in self.frameCache.keys()) and (self.useFrameCache):
			# Serve the previously generated image
			self.image = self.frameCache[key]
		else:
			# Create a new image from scratch
			logger.info("Generating new image for key %s" % key)
			blank = blankImage(self.windowSettings)
			self.image = blank['image']
			self.draw = ImageDraw.Draw(self.image)
			font = blank['font']
			font_small = blank['font_small']
			
			####################################
			# Generate the main, bottom menu
			####################################
			x_pos = 0
			index = 0
			# The main menu is shown
			if (self.menuIndex is not None):
				
				# Always show the bottom menu
				logger.info("Show the main menu")
				menuBitmap = self.createBaseMenuBitmap()
				logger.info("Pasting menu image [%sx%sx%s] at x:%s,y:%s" % (menuBitmap.size[0], menuBitmap.size[1], menuBitmap.mode, 0, self.windowSettings['y_size'] - menuBitmap.size[1]))
				self.image.paste(menuBitmap, (0, self.windowSettings['y_size'] - menuBitmap.size[1]))
					
				###########################################
				# This section only shows if a sub-menu 
				# has not been activated - i.e. we've
				# only highlighted an item in the bottom menu
				# but not yet clicked on it
				###########################################
				if (self.menuIndex > -1) and (self.subMenuIndex is None) and (self.finalMenuIndex is None):
					# Show a description of the main menu item we've got highlighted
					helpBitmap = self.wrappedHelpWindowText(text = self.menu[self.menuIndex]['itemText'], windowLevel = "main")
					logger.info("Pasting helptext image [%sx%sx%s] at x:%s,y:%s" % (helpBitmap.size[0], helpBitmap.size[1], helpBitmap.mode, 0, 0))
					self.image.paste(helpBitmap, (self.leftOffset, 0))
				else:
					# No main menu item is highlighted yet
					logger.info("Show main logo")
					pass
				
			####################################
			# Generate any sub-menu
			####################################
			if (self.subMenuIndex is not None):
				logger.info("Show a submenu")
				# A sub-menu is selected, so build and show that sub-menu list
				subMenuBitmap = self.createSubMenuBitmap()
				logger.info("Pasting submenu image [%sx%sx%s] at x:%s,y:%s" % (subMenuBitmap.size[0], subMenuBitmap.size[1], subMenuBitmap.mode, 0, 0))
				self.image.paste(subMenuBitmap, (0, 0))
					
				###########################################
				# This section only shows if we have highlighted 
				# an element from the submenu, but we've
				# not yet gone on to the final menu.
				###########################################
				if (self.subMenuIndex > -1) and (self.finalMenuIndex is None):
					# Show a description of the sub menu item we've got highlighted
					items = copy.copy(self.menu[self.menuIndex]['items'])
					items.reverse()
					helpBitmap = self.wrappedHelpWindowText(text = items[self.subMenuIndex]['itemText'], windowLevel = "sub")
					logger.info("Pasting helptext image [%sx%sx%s] at x:%s,y:%s" % (helpBitmap.size[0], helpBitmap.size[1], helpBitmap.mode, settings.GFX_MASTER_LINE_1_XPOS + 1, 0))
					self.image.paste(helpBitmap, (settings.GFX_MASTER_LINE_1_XPOS + 1, 0))
					
			####################################
			# Generate any third level menu
			####################################
			if (self.finalMenuIndex is not None):
				# No item in the sub-menu is highlighted
				logger.info("Show the final menu")			
			
				# In the submenu list we reverse the list of items so that we
				# draw from the bottom up, we need to do that here so that the
				# selected item number matches the list order
				items = copy.copy(self.menu[self.menuIndex]['items'])
				items.reverse()
			
				if items[self.subMenuIndex]['itemType'] == 'menu':
					finalMenuBitmap = self.createFinalMenuBitmap()
					logger.info("Pasting final menu image [%sx%sx%s] at x:%s,y:%s" % (finalMenuBitmap.size[0], finalMenuBitmap.size[1], finalMenuBitmap.mode, settings.GFX_MASTER_LINE_1_XPOS + 1, 0))
					self.image.paste(finalMenuBitmap, (settings.GFX_MASTER_LINE_1_XPOS + 1, 0))
			
				###########################################
				# This section only shows if we have highlighted 
				# an element from the final menu.
				###########################################
				if (self.finalMenuIndex > -1):
					# Show a description of the final menu item we've got highlighted
					subitems = copy.copy(self.menu[self.menuIndex]['items'])
					subitems.reverse()
					finalitems = copy.copy(subitems[self.subMenuIndex]['items'])
					finalitems.reverse()
					helpBitmap = self.wrappedHelpWindowText(text = finalitems[self.finalMenuIndex]['itemText'], windowLevel = "final")
					logger.info("Pasting helptext image [%sx%sx%s] at x:%s,y:%s" % (helpBitmap.size[0], helpBitmap.size[1], helpBitmap.mode, settings.GFX_MASTER_LINE_2_XPOS + 1, 0))
					self.image.paste(helpBitmap, (settings.GFX_MASTER_LINE_2_XPOS + 2, 0))
				
			self.frameCache[key] = copy.copy(self.image)		
	
	def textWidth(self, text, font):
		return font.getsize(text)[0]

	# Set max_lines to 0 for no limit
	def wrapText(self, text, font, max_width, max_lines=0):
		words = text.split()
		lines = []
		while(words):
			word = words.pop(0)
			# Append word if it's not too long
			if len(lines) > 0 and (self.textWidth(" ".join(lines[-1]), font) + 1 + self.textWidth(word,font)) < max_width:
				lines[-1].append(word)
			else:
				# Brute-force: chunkify word until it fits
				chunk = len(word)
				while chunk > 0:
					while (self.textWidth(word[:chunk],font) > max_width and chunk > 1):
						chunk -= 1
					lines.append( [word[:chunk]] )
					word = word[chunk:]
					chunk = len(word)
		lines = [" ".join(words) for words in lines]
		if max_lines and len(lines) > max_lines:
			lines[max_lines-1] = lines[max_lines-1][:-1] + "..."
		return lines
	
	def update(self):
		""" Redraw the screen with the current bitmap stored in self.image """
		
		if self.use_sdl:
			updateSDLWindow(self.image, self.windowSettings)
			
		if self.use_oled:
			updateOLEDScreen(self.image, self.windowSettings)