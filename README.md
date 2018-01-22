# PyCosworth

PyCosworth is a monitoring, data-logging and diagnostic tool for vehicles equipped with the [Magneti Marelli L8/P8 ECU](http://www.bigturbo.co.uk) which have the serial datastream protocol enabled.

This feature is often called the *Pectel Datastream*, but is simply a feature of the ECU itself - being turned on or off based on the type of ROM chip fitted to the ECU. Some aftermarket ROM chips available from tuning firms can optionally enable this feature where it was not available by the manufacturer.

*PyCosworth* interfaces with the serial datastream to display, monitor and log the information available via the serial datastream, similar to such products as:

* The [SECS Monitor](https://www.google.co.uk/search?q=cosworth+secs+monitor)
* RP Labs IAW Monitor available from [RPLabs](http://rp-lab.com/iaw_monitor.shtml) or [Motorsports Developments](http://www.motorsport-developments.co.uk/iaw.html)

These products are great for their intended use, but are either *a: very expensive*, or *b: designed for use on a laptop*. PyCosworth is intended to to on a cheap embedded device such as a Raspberry Pi, BeagleBoard or other small Linux system and be permanently connected to the vehicle.

---

# Using PyCosworth

## Hardware Requirements

* A vehicle with a **serial datastream enabled** Magneti Marelli ECU, specifically:

| Model | ECU Type |
| ----- | ------------ |
| Ford Sierra Cosworth 4x4 | Weber/Marelli L8 ECU (with serial comms enabled via software) |
| Ford Escort Cosworth | Weber/Marelli P8 ECU |

*Any other Cosworth YB engine with one of the above ECU variants retro-fitted should also work*

* A diagnostic cable that interfaces with the ECU.

*Please note that these are specific diagnostic cables that connect to the 3 pin flash-code cable on the factory Ford loom, convert it to a RS232 compatible serial interface and then convert that serial interface into a USB plug for use on modern computers. Common OBD/OBDII interfaces will **not** work with the Weber Marelli serial datastream. Ask your usual Cosworth specialist or forum on how to obtain one.*

* A Linux computer running Python (both 2.x and 3.x supported) with at least one free USB port for the diagnostic cable.

* *Optionally:* An Adafruit *HD44780* or *Matrix Orbital* character mode LCD board with USB to serial backpack, such as [this one on Adafruit](https://www.adafruit.com/product/782), for **in-car** sensor readout and error code monitoring.

* *Optionally:* A Raspberry Pi (1/2/3, A, B or B+) with exposed GPIO pins to use optional **in-car** push buttons to control system functionality. 

* *Optionally:* One or more OLED screens supported by the Python [luma.oled driver](https://luma-oled.readthedocs.io/en/latest/) (minimum of 128x32 pixels, though 128x64 is strongly reccomended) for **in-car** live sensor/data visualisation.

* *Optionally:* A supported X11 display or desktop interface to emulate the live sensor/data visualisation as would be seen in the OLED screens, in a desktop window.

None of the optional components are necessary in any way to run the software, but functionality will be limited to text-mode display and datalogging to file.

It it not designed to work (and I have no way to test) on the Fiat/Lancia or *Ferrari F40!* version of the ECU, but *may* work. However, an [excellent tool already exists](http://www.nailed-barnacle.co.uk/coupe/startrek/startrek.html), that the comms protocol part of PyCosworth is partly based on. Many thanks to Neil, the author of that tool, for his technical information. 

## Software Requirements

All of the *Python* software library requirements are listed in the *requirements.txt* file, simply run:
```
pip install -r requirements.txt
```
... to install them on your Linux system.

On Raspbian systems, first check [Raspbian.md](docs/Raspbian.md) for any pre-requisites needed. There are several software packages needed to support the hardware devices used on that platform.

The [Raspbian.md](docs/Raspbian.md) guide also lists a number of software configuration changes you may need to make to your Pi in order make it boot faster as well as increase speed of data display and enable the optional hardware listed above, to work.

## Running PyCosworth

To start the monitoring programme, type `./run.sh` in the programme directory. The monitor will start and within a few seconds it should communicate with the ECU and start gathering data.

To run manually, just call the `main()` method of the script `PyCosworth.py`.

## Configuration

All of the user-customisable settings are found in the file `libs/settings.py`. This includes an extensive set of optional modules and complete customisation over which sensors are monitored, their update frequency (subject to the speed of the ECU) as well as total control over the layout and display modes of the in-car visualisation and display options.

Please see [the configuration guide](docs/Configuration.md) for full details.

---

# Pectel Datastream

## Description

For full details of the Pectel serial datastream, see [the Cosworth Pectel datastream protocol](docs/Pectel.md) document.