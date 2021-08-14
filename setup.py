#!/usr/bin/env python
from distutils.core import setup
from Cython.Build import cythonize

setup(
	name = "PyCosworth IO Modules",
	ext_modules = cythonize(
		[
			"iomodules/SerialIO.py",
			"iomodules/MatrixIO.py",
			"iomodules/GraphicsIO.py",
			"iomodules/ConsoleIO.py",
			"iomodules/GPIOButtonIO.py"
		]
	),
)
