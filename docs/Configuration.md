# Configuring PyCosworth

PyCosworth is a combination of code-reader/sensor reader, data logger and digital dashboard.

The software can be configured to enable or disable most of those options.

## Main Configuration File

Configuration for all aspects of the software are held in the file `libs/settings.py`.

The configuration file is divided up in to several sections:

* Enable or disable programme features
* Module configuration

---

## Enable Programme Features

**Main modules**

This section enables or disables the modules of the software which are activated at run-time. 

Note that all of the modules run in their own process and communicate their state, so whilst the GraphicsIO module is running, all of the other modules are not blocked from using the processor. The main reason is that the SensorIO module is *always* running in the background, gathering sensor readings, and is never blocked from running by one of the other modules.

*For this reason, it is highly reccomended that the software be run on a Raspberry Pi 3 which has 4 processor cores.*

 * USE_CONSOLE
    * Enable or disable the **ConsoleIO** text output module which outputs sensor information to the command prompt in a basic, text-mode display.
 * USE_BUTTONS
    * Enable the **GPIOButtionIO** joystick/button control module. Also enables keyboard key-presses to emulate joystick features. Without this module, no user control of the software is possible; it will just run as-configured.
* USE_GRAPHICS
    * Enable the **GraphicsIO** graphics output module. This module can display to various types of OLED hardware, either connected via the Raspberry Pi I2C or SPI bus. Enabling this module *also* activates an *emulated* display which is only possible on a machine with a working graphics display (for example a Pi with a desktop session, or a Linux desktop).
* USE_DATALOGGER
    * Enable the module which records sensor datastream to disk for later analysis.

**Customisation of modules**

Some of the module have additional major functionality that can be enabled or disabled - for example, activating certain types of additional sensors or display modes.

* USE_OLED_GRAPHICS
    * Within the **GraphicsIO** module, activate output to one or more OLED graphics display screens. These are mono, or grayscale, dot matrix style displays that are used to show sensor information, error status codes or visualise performance data in real time. Most development work has been done using the SSD1306 and SSH1102 monochrome displayed connected via a simple 4-wire I2C bus. You should read the documentation for the [Python luma.oled module](https://luma-oled.readthedocs.io/en/latest/hardware.html) to understand how to connect one of these devices to your computer/Pi.
* USE_SDL_GRAPHICS
    * Within the **GraphicsIO** module, activates an emulated OLED graphics display screen for each actual OLED screen that is configured. This way the visualisation and other display output can be tested on a desktop or laptop system without access to the specific OLED hardware. This requires a display that is supported by *SDL* libraries for graphics output. Generally this means X11 on Linux or Windows on PC.
* USE_COSWORTH
    * Try to activate Cosworth L8/P8 Pectel serial datastream sensors within the **SensorIO** module. See the [Pectel Serial Datastream](Pectel.md) guide which explains the format of the serial interface and how we use it. You will of course need the correct USB to RS232 adaptor on your laptop or Raspberry Pi to use it.
* USE_AEM
    * Try to activate AEM Wideband X-series AFR sensors within the **SensorIO** module. You need an AEM wideband sensor with serial datastream connected to a secondary USB to RS232 adaptor on your laptop or Raspberry Pi. The [AEM installation guide](https://www.aemelectronics.com/files/instructions/30-0300.pdf) shows the wiring to use for the serial data output, as well as the comms parameters.
* USE_SENSOR_DEMO
    * Activate demo-mode sensor data within the **SensorIO** module which supplies a never-ending stream of bogus, demo data, as if the software was really connected to active sensors which were sending data. If enabled, this can be activated or de-activated at will, from the software whilst running.

**Debug messages**

By default, only warnings and errors are output whilst the software is running. However, for debugging, either or both of these options can be set and will result in a lot more output from the software about what it is doing.

* INFO
    * Prints mainly status messages, some performance information
* DEBUG
    * Even more verbose output, including information of variable contents, timers, system calls, etc.
    
For most of the time, both items are best left as **False** in production mode.

---

## Module Configuration

### Sensor Information

* SENSOR_MAX_HISTORY
    * The number of previous readings to keep at any point in time for any sensor. This can be used to smooth readings, generate graphics/waveforms etc. Not currently used for the simple numeric display mode. **Reccomendation: 256**

* SENSOR_SLEEP_TIME
    * The amount of time, in seconds, to sleep between each loop through the entire list of sensors. This should be greater than 0 in order to prevent CPU lockup. Values of 0.02 to 0.05 would enable between 50 (1/0.02) and 20 (1/0.05) sensor passes per second. **Reccomendation: 0.02**

* SENSOR_ERROR_HEARTBEAT_TIMER
    * The time, in seconds, between error/status messages sent from the **SensorIO** process to the user interface. Lower values enable the user interface to react faster to errors connecting to the ECU and AFR sensors, but will reduce the overall responsiveness of the interface. **Reccomendation: 2-5 seconds**

### Cosworth ECU Settings

* COSWORTH_ECU_USB
    * The serial to USB device which is connected to the L8/P8/Pectel Datastream enabled ECU. The first USB to serial device on Linux will generally be **/dev/ttyUSB0**. There are no other settings to configure as the serial protocol is fixed.

### AEM Wideband AFR Settings

* AEM_USB
    * The serial to USB device which is connected to the AEM Wideband AFR sensor module/gauge.

### Graphics / OLED Display Settings

* GFX_MASTER_SIZE
    * The size of the emulated display and the physical OLED screen (if equipped). This is in the form of a Python tuple. PyCosworth has been mainly tested with 128x64 pixel resolution screens. Operation with other size displays is untested. **Reccomendation: (128, 64)**

* GFX_BOOT_LOGO
    * An image to be shown at power-on time. This should be a 1bpp image no larger than the size of your display configured at GFX_MASTER_SIZE. **Reccomendation: "logs/cosworth.bmp"**

* GFX_SLEEP_TIME
    * The time, in seconds, between updates of the emulated and physical screens. This is *not* the time between data updates - the screen could be refreshed faster than the data is updated, in which case the data will not have changed since the last update. Lower values will result in faster screen updates, but depending on the OLED screen being used may have tearing effects above a certain point. Again this should be left as a positive value to avoid unnecessary CPU use. Values of 0.01 (1/0.01 = 100 updates/sec) and 0.05 (1/0.02 = 20 updates/sec) should be tested to find the right one for your display device. **Reccomendation: 0.01 - 0.05**

* GFX_MASTER_WINDOW
    * Definitions for the main display window, including the list of SensorID's to show (and the sequence in which to show them), which OLED device to use (and which I2C address to connect to it with). This data structure should ideally be left as-is, other than to alter the sequence of sensors, if you desire a certain sensor to always be shown first.

* GFX_FONTS
    * Which fonts to use for various parts of the user interface.

### Datalogger Settings

* LOGGING_HEARTBEAT_TIMER
    * The time, in seconds, between update messages sent from the **DataLoggerIO** process to the user interface. This updates the user interface on whether the logger is running or not, or if it has encountered an error (such as disk space). **Reccomendation: 2-3 seconds**

* LOGGING_ACTIVE_SLEEP
    * Controls the granularity of the data logs which are written with sensor data. A higher value lowers the frequency at which a line of sensor data is written to disk. A value of **0.1** indicates that 10 lines of log data are written to disk in 1 second. The value of a sensor at the point it is written to disk is dependent on  the refresh value of that sensor. Bear in mind that with the Cosworth ECU particularly, we have a very slow serial baud rate that means we can only do, **at best** 60 single-byte sensor queries per second.
    * All sensors have a different refresh value (it doesn't make sense to look up battery voltage every 100 milliseconds, for example), and these are written in the back-end ECU support classes:
    * [iomodules/sensors/Cosworth.py](../iomodules/sensors/Cosworth.py)
    * [iomodules/sensors/AEM.py](../iomodules/sensors/AEM.py)

* LOGGING_SLEEP
    * How long to sleep, in seconds, before responding to an 'Activate Logging' signal. Again, a compromise between CPU over-use and responsiveness. **Reccomendation: 1-2 seconds**

* LOGGING_DIR
    * The directory where sensor logs should be written to. If the directory does not exist, it will be attempted to be created the first time the application runs. This should be in a location that the application can write to, not in a system directory or an administrative user.

* LOGGING_FILE_PREFIX
    * The first part of the filename of your sensor log files - this will be suffixed with an auto-incrementing numeric value. **Reccomendation: "pycosworth_"**

* LOGGING_FILE_SUFFIX
    * The last part of your sensor log file names. **Reccomendation: ".csv"**