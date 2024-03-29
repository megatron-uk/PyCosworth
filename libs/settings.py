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
USE_AEM = True				# Try to connect to an AEM Wideband AFR module over serial
USE_SENSOR_DEMO = False 	# Enable demo data mode from the SensorIO module instead of real data

# Should INFO category messages be shown
INFO = True
DEBUG = False

# Enable/Disable support for the Super Watchdog V2 Raspberry Pi hat
USE_PI_WATCHDOG = True

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

# How often to sleep between broadcasting ECU/comms error messages
SENSOR_ERROR_HEARTBEAT_TIMER = 5

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

# Button/status definitions
BUTTON_TOGGLE_DEMO 			= "d" # Start/stop demo mode
BUTTON_LOGGING_RUNNING 		= "L" # Logging is running
BUTTON_LOGGING_STOPPED 		= "l" # Logging is stopped
STATUS_ECU_ERROR		 		= "e1" # Main ECU error
STATUS_AEM_ERROR		 		= "e2" # AEM module error
STATUS_POW_ERROR		 		= "e3" # AEM module error
STATUS_ECU_OK	 			= "o1" # Main ECU error
STATUS_AEM_OK		 		= "o2" # AEM module error
STATUS_POW_OK		 		= "o3" # AEM module error
STATUS_SHUTDOWN				= "xxx"
STATUS_DEMO_ENABLED	 		= "d1" #
STATUS_DEMO_DISABLED	 		= "d2" # 
BUTTON_LOGGING_STATUS 		= "S" # Logging status/heartbeat response
BUTTON_RESET_COSWORTH_ECU 	= "R" # Reset Cosworth ECU serial comms
BUTTON_RESET_AEM_ECU 		= "r" # Reset AEM serial comms

# For the simple, 3 button interface
BUTTON_LOGGING_TOGGLE 		= "1" # Logging is stopped or started
BUTTON_SENSOR_NEXT			= "2" # Select next sensor
BUTTON_RESET_ECU				= "3" # Reset all comms

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
	BUTTON_RESET_ECU				: { 'dest' : BUTTON_DEST_ALL }, # Attempt comms reset
	BUTTON_TOGGLE_DEMO			: { 'dest' : BUTTON_DEST_SENSORIO }, # Toggle demo start/stop
	BUTTON_LOGGING_TOGGLE		: { 'dest' : BUTTON_DEST_DATALOGGER }, # Toggle demo start/stop
	BUTTON_SENSOR_NEXT			: { 'dest' : BUTTON_DEST_GRAPHICSIO }, # Show next sensor
	BUTTON_LOGGING_RUNNING		: { 'dest' : BUTTON_DEST_ALL }, # Logging is running
	BUTTON_LOGGING_STOPPED		: { 'dest' : BUTTON_DEST_ALL }, # Logging is stopped
	STATUS_ECU_ERROR				: { 'dest' : BUTTON_DEST_GRAPHICSIO }, # ECU comms problem
	STATUS_AEM_ERROR				: { 'dest' : BUTTON_DEST_GRAPHICSIO }, # AEM AFR comms problem
	STATUS_ECU_OK				: { 'dest' : BUTTON_DEST_GRAPHICSIO }, # ECU comms problem
	STATUS_AEM_OK				: { 'dest' : BUTTON_DEST_GRAPHICSIO }, # AEM AFR comms problem
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
GFX_OLED_SIZE = GFX_MASTER_SIZE

# Where we keep images, icons etc.
GFX_ASSETS_DIR = "images/"
GFX_CACHE_DIR = "cache/"

# Boot up logo for the OLED screens
GFX_BOOT_LOGO 		= "logo/ford.bmp"
GFX_BOOT_LOGO1 		= "logo/cosworth.bmp"
GFX_BOOT_LOGO2 		= "logo/pycosworth.bmp"
GFX_BOOT_LOGO_BIG 	= "logo/cosworth_outline.bmp"

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

GFX_MODE_NUMERIC = "Numeric"
GFX_MODE_OFF = "OFF"

# Available modes that a sensor can be shown in
#GFX_MODES = [GFX_MODE_WAVEFORM, GFX_MODE_SEGMENTS, GFX_MODE_CLOCK, GFX_MODE_LINE, GFX_MODE_OFF]
GFX_MODES = [GFX_MODE_NUMERIC]

GFX_MASTER_WINDOW = {
	'windowName'			: 'Master',
	'oledType'			: 'sh1106',
	'width'				: GFX_MASTER_SIZE[0],
	'height'				: GFX_MASTER_SIZE[1],
	'spiAddress'			: 0,
	'value_refreshTime'	: 0.05,
	'sdl_framebuffer'	: None,
	'luma_framebuffer'	: None,
	'luma_driver'		: None,
	'screen_refreshTime': 0.02,
	'i2cPort'			: 8,
	'i2cAddress'		: 0x3c,
	'mode'				: [GFX_MODE_NUMERIC],
	'currentModeIdx'		: 0,
	'currentMode'		: GFX_MODE_NUMERIC,
	'sensorIds'			: ['AFR', 'AMAL', 'BAT', 'CO', 'ECT', 'IAT', 'IGNADV', 'INJDUR', 'MAP', 'RPM', 'TPS'],
	'currentSensorIdx'	: 0,
	'screen_cycleTime'	: 5,
	'value_refreshTime'	: 0.1,
	'screen_refreshTime': 0.05,
}

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


#######################################################
#
# Logging module config
#
#######################################################

# Broadcast logging status every 'X' seconds
LOGGING_HEARTBEAT_TIMER = 3

# How often to sleep between loops, should be no more than the sensor module
# otherwise we may miss datapoints
LOGGING_ACTIVE_SLEEP = 0.1 	# How long to sleep while recording (interval between data recorded to log file)
LOGGING_SLEEP = 1 			# How long to sleep while recording inactive

LOGGING_DIR = "logs"
LOGGING_FILE_PREFIX = "pycosworth_"
LOGGING_FILE_SUFFIX = ".csv"

########################################################
#
# Watchdog timers and Power Monitoring
# 
########################################################

# How often, in seconds, to send a 'alive' message to the 
# watchdog timer on the Raspberry Pi UPS hat
WATCHDOG_HEARTBEAT_TIMER = 30

# How often, in seconds, to detect the current power state
# of the Raspberry Pi
WATCHDOG_POWER_TIMER = 5

# How long to run the Pi on battery backup after a power-loss is
# detected, until we begin a controlled shutdown
WATCHDOG_POWER_SHUTDOWN_TIMER = 20

# How many volts should be nominal input
WATCHDOG_POWER_NOMINAL = 5.0