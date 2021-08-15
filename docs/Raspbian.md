# Raspberry Pi

## Raspbian Packages

In addition to the Python packages listed in [requirements.txt](requirements.txt), Most Raspbian (in fact, most *Linux*) systems will also need the following system packages and libraries installing:

* python3-smbus
* python3-dev
* python3-pip
* python3-sdl2
* i2c-tools
* libsdl2-dev
* libatlas-base-dev
* libopenjp2-7-dev
* libtiff-dev

These will generally need to be installed *before* you attempt to install the Python packages in the *requirements.txt* file.

On Raspbian and other debian flavours of Linux, these can get installed as:

```
sudo apt-get install python3-smbus \
python3-dev python3-pip python3-sdl2 \
i2c-tools libsdl2-dev \
libatlas-base-dev libopenjpg2-7-dev libtiff-dev
```

or, for Python 2.x

```
sudo apt-get install python-smbus \
python-dev python-pip python-sdl2 \
i2c-tools libsdl2-dev \
libatlas-base-dev libopenjpg2-7-dev libtiff-dev
```

On other Linux distributions the package names may differ *slightly*.

## Faster Startup

A Raspberry Pi 3 with a standard installation of Raspbian can take well over 10 seconds from power on to fully booted. This isn't ideal for a device in a car, so I've written up a list of changes I've made that results in a consistent boot time of 5 to 5.5 seconds.

**Disable unecessary services**

```
systemctl mask alsa-restore
systemctl mask triggerhappy
systemctl mask bluetooth
systemctl mask avahi
```

## Activate I2C and SPI device interfaces

The various display devices that this project can use interface with the Pi using either I2C or SPI bus - they are all presented on the Pi GPIO pins.

The [installation guide](https://luma-oled.readthedocs.io/en/latest/hardware.html) for the OLED displays from the luma.oled Python project has a simple guide on how to enable (and speed up) the I2C and SPI interfaces.

## Uninterruptible Power Supply

The live circuit on a car is not the most relable place for a computer to live. Ideally you should run your Pi with a UPS hat which can detect when the ignition circuit goes away and powers the device for a few seconds/minutes until the power comes back, or shut down the device cleanly.