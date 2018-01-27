# Configuring PyCosworth

PyCosworth is a combination of code-reader/sensor reader, data logger and digital dashboard.

The software can be configured to enable or disable any of those options.

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

* USE_MATRIX
    * Enable or disable the **MatrixIO** LCD character display output module. Supported displays are either 16x2 or 20x4 text mode LCD's, using the Matrix Orbital or Adafruit LCD Python display library `lcdbackpack`.
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
    * Within the **GraphicsIO** module, activate output to one or more OLED graphics display screens. These are mono, or grayscale, dot matrix style displays that are used to show sensor information, error status codes or visualise performance data in real time.
* USE_SDL_GRAPHICS
    * Within the **GraphicsIO** module, activates an emulated OLED graphics display screen for each actual OLED screen that is configured. This way the visualisation and other display output can be tested on a desktop or laptop system without access to the specific OLED hardware. This requires a display that is supported by *SDL* libraries for graphics output. Generally this means X11 on Linux or Windows on PC.
* USE_GEAR_INDICATOR
    * Try read gear lever position within the **SensorIO** module. See the [Gearlever Sensor](gearlever.md) documentation for more information.
* USE_COSWORTH
    * Try to activate Cosworth L8/P8 Pectel serial datastream sensors within the **SensorIO** module. See the [Pectel Serial Datastream](Pectel.md) guide which explains the format of the serial interface and how we use it.
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

### Cosworth ECU Settings

### Matrix LCD Settings

### GPIO / Button Settings

### Graphics / OLED Display Settings

### Datalogger Settings