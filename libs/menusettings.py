MASTER_MENU = [
	{
		'itemName'	: 'sensor',
		'itemType'	: 'menu',
		'itemText'	: 'Choose which sensor will be displayed on the master screen. You can also split the screen and show up to two sensors simultaneously.',
		'items' 	: [
			{
				'itemName'	: 'RPM',
				'itemType'	: 'menu',
				'itemText'	: 'Engine speed sensor',
				'items'		: [
					{
						'itemName'	: 'Fullscreen',
						'itemType'	: 'item',
						'itemText'	: 'Select as fullscreen sensor',
						'itemSelect': 'sensorSelectFull',
					},
					{
						'itemName'	: 'Left',
						'itemType'	: 'item',
						'itemText'	: 'Select as left sensor',
						'itemSelect': 'sensorSelectLeft',
					},
					{
						'itemName'	: 'Right',
						'itemType'	: 'item',
						'itemText'	: 'Select as right sensor',
						'itemSelect': 'sensorSelectRight',
					},
					{
						'itemName'	: 'Leftb',
						'itemType'	: 'item',
						'itemText'	: 'Select as left sensor',
						'itemSelect': 'sensorSelectLeft',
					},
					{
						'itemName'	: 'Rightb',
						'itemType'	: 'item',
						'itemText'	: 'Select as right sensor',
						'itemSelect': 'sensorSelectRight',
					}
				]
			},
			{
				'itemName'	: 'ECT',
				'itemType'	: 'item',
				'itemText'	: 'Engine coolant temperature',
			},
			{
				'itemName'	: 'IAT',
				'itemType'	: 'item',
				'itemText'	: 'Intake Air Temperature',
			},
			{
				'itemName'	: 'MAP',
				'itemType'	: 'item',
				'itemText'	: 'Inlet manifold pressure',
			},
			{
				'itemName'	: 'TPS',
				'itemType'	: 'item',
				'itemText'	: 'Throttle position sensor',
			},
			{
				'itemName'	: 'CO',
				'itemType'	: 'item',
				'itemText'	: 'Fuel base',
			},
			{
				'itemName'	: 'Battery',
				'itemType'	: 'item',
				'itemText'	: 'Battery voltage',
			},
			{
				'itemName'	: 'Injector',
				'itemType'	: 'item',
				'itemText'	: 'Injector pulse width',
			},
			{
				'itemName'	: 'BCV',
				'itemType'	: 'item',
				'itemText'	: 'Boost control valve',
			},
			{
				'itemName'	: 'IGN',
				'itemType'	: 'item',
				'itemText'	: 'Ignition advance',
			}
		]
	},
	{
		'itemName'	: 'config',
		'itemType'	: 'menu',
		'itemText'	: 'Configure how sensor data is displayed on all connected devices. Choose visualisation modes and set cycle times.',
		'items'		: []
	},
	{
		'itemName'	: 'data',
		'itemType'	: 'menu',
		'itemText'	: 'Access data logging functions.',
		'items'		: [
			{
				'itemName'	: 'Status',
				'itemType'	: 'item',
				'itemText'	: 'Options relating to datalogging',
				'itemSelect': 'showLoggingState',
			},
			{
				'itemName'	: 'Start Log',
				'itemType'	: 'item',
				'itemText'	: 'Start datalogging',
				'itemSelect': 'startLogging',
			},
			{
				'itemName'	: 'Stop Log',
				'itemType'	: 'item',
				'itemText'	: 'Stop datalogging',
				'itemSelect': 'stopLogging',
			},
			{
				'itemName'	: 'Comms Config',
				'itemType'	: 'menu',
				'itemText'	: 'Configure serial comms and data',
				'items'		: [
					{
						'itemName'	: 'Start/Stop demo',
						'itemType'	: 'item',
						'itemText'	: 'Toggle demo mode',
						'itemSelect': 'toggleDemo',
					},
					{
						'itemName'	: 'Reset comms',
						'itemType'	: 'item',
						'itemText'	: 'Restart ECU comms',
						'itemSelect': 'restartSerialIO',
					},
					{
						'itemName'	: 'Comms status',
						'itemType'	: 'item',
						'itemText'	: 'Show ECU comms status',
						'itemSelect': 'showECUComms',
					},
				]
			},
		]
	},
	{
		'itemName'	: 'diag',
		'itemType'	: 'menu',
		'itemText'	: 'Run diagnostics to check system functionality. View system information and performance data. Restart the PyCosworth application.',
		'itemSelect': 'unfoldMenu',
		'items'		: [
			{
				'itemName'	: 'All Sensors',
				'itemType'	: 'item',
				'itemText'	: 'Show status of all sensors on-screen',
				'itemSelect': 'showSensorText',
			},
			{
				'itemName'	: 'System Info',
				'itemType'	: 'item',
				'itemText'	: 'Show system status and performance informace',
				'itemSelect': 'showSysInfo',
			},
			{
				'itemName'	: 'Restart',
				'itemType'	: 'item',
				'itemText'	: 'Restart the software',
				'itemSelect': 'showRestartConfirmation',
			},
			{
				'itemName'	: 'Shutdown',
				'itemType'	: 'item',
				'itemText'	: 'Exit the software and shut down',
				'itemSelect': 'showShutdownConfirmation',
			},
		]
	}
]