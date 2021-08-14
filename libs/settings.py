#!/usr/bin/env python
# -*- coding: utf8 -*-

# Settings.py - a configuration file for PyCosworth.
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

##############################################################
#
# Weber / Magneti Marelli / Cosworth serial diagnostic port
#
##############################################################

# Total amount of time the main process sleeps until trying to load data from the
# receiving queue
MAIN_SLEEP_TIME = 0.02

# Maximum number of errors that can be retrieved and buffered
MAX_ERRORS = 255

# Standard types of message we may get back from the SensorIO process
TYPE_ERROR = "ERR_MSG"
TYPE_DATA = "DATA_MSG"
TYPE_STATUS = "STATUS_MSG"

##############################################################
#
# Turn various features on/off
#
##############################################################

# Selct the various worker modules
USE_MATRIX = False			# Output to a Matrix Orbital compatible character mode LCD
USE_CONSOLE = False			# Output to a standard terminal / command prompt
USE_BUTTONS = True			# Run a process which monitors Raspberry Pi GPIO buttons for button presses
USE_GRAPHICS = True			# Output to OLED modules or on-screen graphics
USE_DATALOGGER = True		# Run the datalogger module to record ecudata to disk
USE_OLED_GRAPHICS = True 	# Try to output to an OLED module
USE_SDL_GRAPHICS = True  	# Try to output to on-screen windows

# Sensor modules
USE_GEAR_INDICATOR = False	# Try to read gear indicator position via GPIO 
USE_COSWORTH = False 		# Try to connect to a Cosworth L8/P8 ECU over serial
USE_AEM = False				# Try to connect to an AEM Wideband AFR module over serial
USE_SENSOR_DEMO = True 	# Enable demo data mode from the SensorIO module instead of real data

# Should INFO category messages be shown
INFO = True
DEBUG = False

##############################################################
#
# Sensor information
#
##############################################################

# A list of the sensors we check on each normal loop in the SensorIO process.
#
# This also controls the refresh rate of the sensors. The Magneti Marelli hardware can refresh some data
# more frequently than others, but we can control, to some degree, how fast we refresh the data.
#
# We also have the possibility of adding other sensors to a Pi, or similar, that cannot be provided by an ECU
# for example, an analogue temperature sensor for outside air temp, a DIY gearstick position sensor, brake pedal angle, etc.
#
# Any sensor available in a back-end sensor module, needs to be listed below.
#
# 'sensorId' 		value is the keyword by which that sensor value is accessed in any display routine. DO NOT CHANGE!
# 'maxValue'		used to calculate maximum height of any graphs or displays for this sensor
# 'warnValue'		the value, which, if exceeded, the system will try to warn the driver of that sensor

# This needs to be simplified to remove min/max, unit, refresh etc. as it is all now defined per sensor module backend (see iomodules/sensors/Cosworth.py, demo.py etc.)
SENSORS = [
	{	'sensorId' 	: 'AFR',		'minValue' : 0,		'maxValue'	: 20,	'warnValue' : 15,	},
	{	'sensorId' 	: 'AMAL',	'minValue' : 0,		'maxValue'	: 100,	'warnValue' : 110,	},
	{	'sensorId' 	: 'BAT',		'minValue' : 0,		'maxValue'	: 14,	'warnValue' : 15,	},
	{	'sensorId' 	: 'CO',		'minValue' : 0,		'maxValue'	: 50,	'warnValue' : 100,	},	
	{	'sensorId' 	: 'ECT',		'minValue' : 0,		'maxValue'	: 150,	'warnValue' : 110, 	},
	{	'sensorId'	: 'IAT',		'minValue' : 0,		'maxValue'	: 60,	'warnValue' : 50,	},
	{	'sensorId' 	: 'IGNADV',	'minValue' : 0,		'maxValue'	: 40,	'warnValue' : 36,	},
	{	'sensorId' 	: 'INJDUR',	'minValue' : 0,		'maxValue'	: 5,		'warnValue' : 20,	},	
	{	'sensorId' 	: 'MAP',		'minValue' : -350,	'maxValue'	: 3000,	'warnValue' : 2500,	},
	{ 	'sensorId'	: 'RPM',		'minValue' : 0,		'maxValue'	: 7500, 'warnValue' : 6000,	},
	{	'sensorId' 	: 'TPS',		'minValue' : -0.3,	'maxValue'	: 90,	'warnValue' : 100,	},
]
# A list of all sensor id's
SENSOR_IDS = []
for s in SENSORS:
	SENSOR_IDS.append(s['sensorId'])
	
# How many previous sensor samples, for each sensor, to keep in memory
SENSOR_MAX_HISTORY = 256

# The amount of time, in seconds, that the SensorIO process sleeps between each loop
SENSOR_SLEEP_TIME = 0.05

##########################################################
#
# Cosworth ECU settings
#
##########################################################
COSWORTH_ECU_TYPE = "L8 Pectel" # see iomodules/sensors/CosworthSensors.py for available types

# Which USB interface your USB to serial device is on
COSWORTH_ECU_USB = "/dev/ttyUSB0" 
	
#########################################################
#
# AEM Wideband AFR settings
#
#########################################################
AEM_USB = "/dev/ttyUSB1"
	
#######################################################
#
# Demo data module config
#
#######################################################

# The number of steps between the minValue and the maxValue of a
# sensor to simulate.
DEMO_STEPS = 64

#######################################################
#
# GPIO module config - this sends button presses and 
# configuration change messages between the various worker
# processes.
#
#######################################################

# How long to sleep between button scans
GPIO_SLEEP_TIME = 0.2

# Length of time each press takes (min time, max time)
BUTTON_TIME_SHORT 	= (0, 	0.3)
BUTTON_TIME_MEDIUM 	= (0.5, 1.0)
BUTTON_TIME_LONG 	= (2.0, 5.0)

# Button definitions
BUTTON_LEFT 				= "\x1b[D" # Left cursor
BUTTON_RIGHT 				= "\x1b[C" # Right cursor
BUTTON_UP 					= "\x1b[A" # Up
BUTTON_DOWN 				= "\x1b[B" # Down
BUTTON_SELECT 				= " " # Space/select
BUTTON_CANCEL 				= "x" # Cancel/escape
BUTTON_TOGGLE_DEMO 			= "d" # Start/stop demo mode
BUTTON_LOGGING_RUNNING 		= "L" # Logging is running
BUTTON_LOGGING_STOPPED 		= "l" # Logging is stopped
BUTTON_LOGGING_STATUS 		= "S" # Logging status/heartbeat response
BUTTON_RESET_COSWORTH_ECU 	= "R" # Reset Cosworth ECU serial comms

# For the simple, 3 button interface
BUTTON_LOGGING		 		= "1" # Logging is stopped or started
BUTTON_SENSOR_NEXT			= "2" # Select next sensor

# Button message types
MESSAGE_TYPE_PRESS 	= 0x01 # message is a button press
MESSAGE_TYPE_PAUSE 	= 0xFE # message is to pause logging/display
MESSAGE_TYPE_EXIT 	= 0xFF # message is to shut down

# Button durations
BUTTON_SHORT 	= 0x11 # short duration press
BUTTON_MEDIUM 	= 0x12 # medium duration press
BUTTON_LONG 	= 0x13 # long press

# Set destination types
BUTTON_DEST_ALL 		= 0x00 # send to all workers
BUTTON_DEST_MAIN 		= 0x01 # send to main PyCosworth process
BUTTON_DEST_SENSORIO 	= 0x02 # send to serial process
BUTTON_DEST_CONSOLEIO 	= 0x03 # send to console process
BUTTON_DEST_MATRIXIO 	= 0x04 # send to matrix lcd process
BUTTON_DEST_GRAPHICSIO 	= 0x05 # send to SDL/OLED graphics process
BUTTON_DEST_DATALOGGER 	= 0x06 # send to datalogger process

# Mapping of buttons to modules
# i.e. button 1 and 2 to GraphicsIO, button 3 to datalogger, etc
BUTTON_MAP = {
	BUTTON_LEFT 				: { 'dest' : BUTTON_DEST_GRAPHICSIO }, # Left
	BUTTON_RIGHT 				: { 'dest' : BUTTON_DEST_GRAPHICSIO }, # Right
	BUTTON_UP 					: { 'dest' : BUTTON_DEST_GRAPHICSIO }, # Up
	BUTTON_DOWN 				: { 'dest' : BUTTON_DEST_GRAPHICSIO }, # Down
	BUTTON_SELECT 				: { 'dest' : BUTTON_DEST_GRAPHICSIO }, # Select
	BUTTON_CANCEL				: { 'dest' : BUTTON_DEST_GRAPHICSIO }, # Cancel
	BUTTON_TOGGLE_DEMO			: { 'dest' : BUTTON_DEST_SENSORIO }, # Toggle demo start/stop
	BUTTON_RESET_COSWORTH_ECU	: { 'dest' : BUTTON_DEST_SENSORIO }, # Toggle demo start/stop
	BUTTON_LOGGING_RUNNING		: { 'dest' : BUTTON_DEST_DATALOGGER }, # Toggle demo start/stop
	BUTTON_LOGGING_STOPPED		: { 'dest' : BUTTON_DEST_DATALOGGER }, # Toggle demo start/stop
	BUTTON_SENSOR_NEXT			: { 'dest' : BUTTON_DEST_GRAPHICSIO }, # Show next sensor
}

#######################################################
#
# Graphics module config
#
#######################################################

# Size of the main control screen
# This is the master screen that shows settings, config
# and higher resolution data
# NOTE: The on-desktop SDL window will be created at the same size
GFX_MASTER_SIZE = (128, 64)

# Size of the OLED miniature screen.
# These are the sub-screens that generally display a single gauge or sensor.
# NOTE: The on-desktop SDL window will be created at the same size
GFX_OLED_SIZE = (128, 64)

# Where we keep images, icons etc.
GFX_ASSETS_DIR = "images/"
GFX_CACHE_DIR = "cache/"

# Boot up logo for the OLED screens
GFX_BOOT_LOGO 		= "logo/cosworth.bmp"
#GFX_BOOT_LOGO_BIG 	= "logo/cosworth_256.bmp"
GFX_BOOT_LOGO_BIG 	= "logo/cosworth_outline.bmp"

# Font used for most on-screen text
GFX_FONT 		= "pixelmix.ttf"
GFX_FONT_BIG 	= "neoletters.ttf"

# Time to sleep between graphics updates
# The lower the sleep time, the smoother the gfx display,
# but the more CPU power the process will take.
#
# NOTE: Certain I2C connected OLED devices are effectively
# throttled in how fast they can update, so decreasing this
# value may not result in a faster refresh for those devices.
# Enable 'INFO' logging, above and check the output messages from 
# the console to see what the average fps for rendering to
# the OLED devices is;
#
# For example, with a single, no-name SH1106 controller, 128x64 
# pixel OLED on I2C bus, I see 17-20fps with GFX_SLEEP_TIME = 0.05, 
# but decreasing the sleep time doesn't result in any faster refresh.
#
# Assuming your hardware can keep up, 0.05 should average 20fps, which
# is plenty fast to update an LCD/OLED gauge.
GFX_SLEEP_TIME = 0.01

# How long a period to measure framerate over
GFX_FRAME_COUNT_TIME = 5

# As with the MATRIX_CONFIG, the OLED screens can either be
# set to show a single sensor all the time (until manually changed), 
# or can cycle through a number of sensors in turn after a 
# pre-determined amount of time.
#
# NOTE: Currently CYCLE is not supported
GFX_SETTING_CYCLE = 0x01
GFX_SETTING_FIXED = 0x02

# We have multiple different visualisation options:
#
# WAVEFORM
#	An oscilloscope-like display
# SEGMENTS
#	A 'retro' style display with multiple bar graph segments which
#	display in turn as the sensor value increase
# CLOCK
#	An analogue clock / gauge with needle
# LINE	
#	A logarithmic vertical line chart with the same X-resolution as the
#	number of pixels your OLED display is in width.
# NUMERIC
#	A simple number display
GFX_MODE_WAVEFORM = "Waveform"
GFX_MODE_SEGMENTS = "LED Segment"
GFX_MODE_CLOCK = "Clock"
GFX_MODE_LINE = "Log Graph"
GFX_MODE_NUMERIC = "Numeric"
GFX_MODE_OFF = "OFF"

# Available modes that a sensor can be shown in
#GFX_MODES = [GFX_MODE_WAVEFORM, GFX_MODE_SEGMENTS, GFX_MODE_CLOCK, GFX_MODE_LINE, GFX_MODE_OFF]
GFX_MODES = [GFX_MODE_NUMERIC]

GFX_MASTER_WINDOW = {
	'windowName'			: 'Master',
	'oledType'			: 'sh1106',
	'width'				: 128,
	'height'				: 64,
	'spiAddress'			: 0,
	'value_refreshTime'	: 0.05,
	'sdl_framebuffer'	: None,
	'luma_framebuffer'	: None,
	'luma_driver'		: None,
	'screen_refreshTime': 0.02,
	'i2cAddress'			: 0x3C,
	'setting'			: GFX_SETTING_FIXED,
	'mode'				: [GFX_MODE_NUMERIC],
	'currentModeIdx'		: 0,
	'currentMode'		: GFX_MODE_NUMERIC,
	'sensorIds'			: ['AFR', 'AMAL', 'BAT', 'CO', 'ECT', 'IAT', 'IGNADV', 'INJDUR', 'MAP', 'RPM', 'TPS'],
	'currentSensorIdx'	: 0,
	'screen_cycleTime'	: 5,
	'value_refreshTime'	: 0.1,
	'screen_refreshTime': 0.05,
}

# All of the bitmaps that make up the main menu control screen
GFX_MASTER_BITMAPS = {
	'sensor': {
		'off'	: GFX_ASSETS_DIR + 'buttons/menu button - Sensor.bmp',
		'on'	: GFX_ASSETS_DIR + 'buttons/menu button - Sensor - selected.bmp',
		'size'	: (64, 20),
	},
	'display': {
		'off'	: GFX_ASSETS_DIR + 'buttons/menu button - Display.bmp',
		'on' 	: GFX_ASSETS_DIR + 'buttons/menu button - Display - selected.bmp',
		'size'	: (64, 20),
	},
	'data'	: {
		'off'	: GFX_ASSETS_DIR + 'buttons/menu button - Data.bmp',
		'on'	: GFX_ASSETS_DIR + 'buttons/menu button - Data - selected.bmp',
		'size'	: (64, 20),
	},	
	'diag'	: {
		'off'	: GFX_ASSETS_DIR + 'buttons/menu button - Diag.bmp',
		'on'	: GFX_ASSETS_DIR + 'buttons/menu button - Diag - selected.bmp',
		'size'	: (64, 20),
	},
	'arrow'	: {
		'up'	: GFX_ASSETS_DIR + 'buttons/arrow - up.bmp',
		'down'	: GFX_ASSETS_DIR + 'buttons/arrow - down.bmp',
		'size'	: (5, 13),
	},	
}

# Icons that can be shown in top right to indicate mode
GFX_ICONS = {
	'stopwatch' : {
		'icon'	: GFX_ASSETS_DIR + 'icons/stopwatch.bmp',
		'alt'	: GFX_ASSETS_DIR + 'icons/stopwatch_alt.bmp',
		'size'	: (48, 48)
	},
	'microchip' : {
		'icon'	: GFX_ASSETS_DIR + 'icons/microchip.bmp',
		'alt'	: GFX_ASSETS_DIR + 'icons/microchip.bmp',
		'size'	: (48, 48)
	},
	'sensor' : {
		'icon'	: GFX_ASSETS_DIR + 'icons/sensor.bmp',
		'alt'	: GFX_ASSETS_DIR + 'icons/sensor.bmp',
		'size'	: (48, 48)
	},
	'monitor' : {
		'icon'	: GFX_ASSETS_DIR + 'icons/monitor.bmp',
		'alt'	: GFX_ASSETS_DIR + 'icons/monitor.bmp',
		'size'	: (48, 48)
	},
	'vis-select' : {
		'waveform'	: GFX_ASSETS_DIR + 'icons/vis-waveform.bmp',
		'segment'	: GFX_ASSETS_DIR + 'icons/vis-segment.bmp',
		'line'		: GFX_ASSETS_DIR + 'icons/vis-segment.bmp',
		'clock'		: GFX_ASSETS_DIR + 'icons/vis-segment.bmp',
		'size'	: (48, 48)
	},
	'selector' : {
		'inner'	: GFX_ASSETS_DIR + 'icons/selector-inner.bmp',
		'outer'	: GFX_ASSETS_DIR + 'icons/selector-outer.bmp',
		'size'	: (16, 16)
	},
}

# Size of each menu
GFX_MASTER_BASE_MENU_SIZE = (GFX_MASTER_SIZE[0], 20)
GFX_MASTER_SUBMENU_SIZE = (85,43)

# Where to draw the first menu vertical divider line
GFX_MASTER_ARROW_1_XPOS = 80
GFX_MASTER_LINE_1_XPOS = GFX_MASTER_ARROW_1_XPOS + GFX_MASTER_BITMAPS['arrow']['size'][0]
# Where to draw the second menu divider line
GFX_MASTER_ARROW_2_XPOS = 165
GFX_MASTER_LINE_2_XPOS = GFX_MASTER_ARROW_2_XPOS + GFX_MASTER_BITMAPS['arrow']['size'][0]
GFX_UP_ARROW_YPOS = 0
GFX_DOWN_ARROW_YPOS = 30

# All of the fonts used in the graphics routines
#
# Fonts available from: https://www.dafont.com/
GFX_FONTS = {
	'sans' 	: { 
		'plain' 	: { 'font' : GFX_ASSETS_DIR + 'fonts/DejaVuSansCondensed.ttf' },
		'italic' 	: { 'font' : GFX_ASSETS_DIR + 'fonts/DejaVuSansCondensed-Oblique.ttf' },
		'bold' 		: { 'font' : GFX_ASSETS_DIR + 'fonts/DejaVuSansCondensed-Bold.ttf' },
		'bolditalic': { 'font' : GFX_ASSETS_DIR + 'fonts/DejaVuSansCondensed-BoldOblique.ttf' },
	},
	'pixel'	: {
		'plain' 	: { 'font' : GFX_ASSETS_DIR + 'fonts/pixelmix_8px.ttf' },
		'large' 	: { 'font' : GFX_ASSETS_DIR + 'fonts/Minecraft_16px.ttf' },
		'header' 	: { 'font' : GFX_ASSETS_DIR + 'fonts/neoletters_16px.ttf' },
	},
	'lcd'	: {
		'plain' 	: { 'font' : GFX_ASSETS_DIR + 'fonts/CFLCD-Regular.ttf' },
	},
}

# Size of font for each menu
GFX_MASTER_SUBMENU_FONTSIZE = 11
GFX_MASTER_HELP_FONTSIZE = 10

# Number of segments in a LED segment style visualisation
# This should always be a power of 2 so that it divides cleanly
# in to the width of all OLED screens.
GFX_LED_SEGMENT_NUMBER = 16
GFX_LED_SEGMENT_NUMBER_MASTER = 32

#######################################################
#
# Logging module config
#
#######################################################

# Broadcast logging status every 'X' seconds
LOGGING_HEARTBEAT_TIMER = 1

# How often to sleep between loops, should be no more than the sensor module
# otherwise we may miss datapoints
LOGGING_ACTIVE_SLEEP = 0.02 # How long to sleep while recording
LOGGING_SLEEP = 1 # How long to sleep while recording inactive

LOGGING_DIR = "logs"
LOGGING_FILE_PREFIX = "pycosworth_"
LOGGING_FILE_SUFFIX = ".csv"
