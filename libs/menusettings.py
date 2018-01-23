#!/usr/bin/env python

from libs.MenuFunctions import *

MASTER_MENU = [
	{
		'itemName'	: 'sensor',
		'itemType'	: 'menu',
		'itemText'	: 'Choose which sensor will be displayed on the master screen. You can also split the screen and show up to two sensors simultaneously.',
		'items' 	: []
	},
	{
		'itemName'	: 'config',
		'itemType'	: 'menu',
		'itemText'	: 'Configure how sensor data is displayed on all connected devices. Choose visualisation modes for all displays.',
		'items'		: []
	},
	{
		'itemName'	: 'data',
		'itemType'	: 'menu',
		'itemText'	: 'Access data logging functions, check ECU communication status or enable demo mode to simulate sensor data.',
		'items'		: [
			{
				'itemName'	: 'Status',
				'itemType'	: 'item',
				'itemText'	: 'Options relating to datalogging',
				'itemSelect': showLoggingState,
			},
			{
				'itemName'	: 'Start Log',
				'itemType'	: 'item',
				'itemText'	: 'Start datalogging',
				'itemSelect': startLogging,
			},
			{
				'itemName'	: 'Stop Log',
				'itemType'	: 'item',
				'itemText'	: 'Stop datalogging',
				'itemSelect': stopLogging,
			},
			{
				'itemName'	: 'Comms Config',
				'itemType'	: 'menu',
				'itemText'	: 'Configure or check serial comms. Start or stop demo mode to emulate actual sensor data.',
				'items'		: [
					{
						'itemName'	: 'Start/Stop demo',
						'itemType'	: 'item',
						'itemText'	: 'Toggle demo mode',
						'itemSelect': toggleDemo,
					},
					{
						'itemName'	: 'Reset comms',
						'itemType'	: 'item',
						'itemText'	: 'Restart ECU comms',
						'itemSelect': restartSensorIO,
					},
					{
						'itemName'	: 'Comms status',
						'itemType'	: 'item',
						'itemText'	: 'Show ECU comms status',
						'itemSelect': showSensorComms,
					},
				]
			},
		]
	},
	{
		'itemName'	: 'diag',
		'itemType'	: 'menu',
		'itemText'	: 'Run diagnostics to check system functionality. View system information and performance data. Restart or shutdown the PyCosworth application.',
		'itemSelect': 'unfoldMenu',
		'items'		: [
			{
				'itemName'	: 'All Sensors',
				'itemType'	: 'item',
				'itemText'	: 'Show status of all sensors on-screen',
				'itemSelect': showSensorText,
			},
			{
				'itemName'	: 'System Info',
				'itemType'	: 'item',
				'itemText'	: 'Show system status and performance informace',
				'itemSelect': showSysInfo,
			},
			{
				'itemName'	: 'Restart',
				'itemType'	: 'item',
				'itemText'	: 'Restart the software',
				'itemSelect': showRestartConfirmation,
			},
			{
				'itemName'	: 'Shutdown',
				'itemType'	: 'item',
				'itemText'	: 'Exit the software and shut down',
				'itemSelect': showShutdownConfirmation,
			},
		]
	}
]