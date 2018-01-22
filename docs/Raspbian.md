# Raspberry Pi - Raspbian Packages

In addition to the Python packages listed in [requirements.txt](requirements.txt), Most Raspbian (in fact, most *Linux*) systems will also need the following system packages and libraries installing:

* python3-smbus
* python3-dev
* python3-pip
* python3-sdl2
* cython3
* i2c-tools
* libsdl2-dev
* libatlas-base-dev
* libopenjp2-7-dev
* libtiff-dev

These will generally need to be installed *before* you attempt to install the Python packages in the *requirements.txt* file.

On Raspbian and other debian flavours of Linux, these can get installed as:

```
sudo apt-get install python3-smbus python3-dev python3-pip python3-sdl2 i2c-tools libsdl2-dev libatlas-base-dev libopenjpg2-7-dev libtiff-dev
```

or, for Python 2.x

```
sudo apt-get install python-smbus python-dev python-pip python-sdl2 i2c-tools libsdl2-dev libatlas-base-dev libopenjpg2-7-dev libtiff-dev
```

On other Linux distributions the package names may differ *slightly*.
