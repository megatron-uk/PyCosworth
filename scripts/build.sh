#!/bin/bash

echo ""
echo "#############################################"
echo "#"
echo "# This script (optionally) compiles various"
echo "# parts of PyCosworth to C to get a speed up."
echo "#"
echo "# Do not worry if this fails - PyCosworth will"
echo "# still run perfectly fine without it, just a"
echo "# little slower."
echo "#"
echo "#############################################"
echo ""

# Python 2.x
#CYTHON=`which cython`
#PYTHON=`which python`

# Python 3.x
CYTHON=`which cython3`
PYTHON=`which python3`

if [ "$CYTHON" == "" ]
then
	echo ""
	echo "ERROR: No cython compiler found"
	echo ""
	exit 1
fi

rm -vf build
rm -vf pycosworth/iomodules/*.so
rm -vf iomodules/*.c
rm -vf iomodules/*.so

$PYTHON setup.py build_ext --inplace
if [ "$?" == "0" ]
then
	echo ""
	echo "#############################################"
	echo "#"
	echo "# SUCCESS: All modules compiled"
	echo "#"
	echo "#############################################"
	echo ""
	/bin/ls pycosworth/iomodules/*.so | while read SO
	do
		cp -v "$SO" iomodules/
	done
	echo ""
	echo "#############################################"
	echo "#"
	echo "# You can run PyCosworth normally (use run.sh)"
	echo "# and it will automatically use the compiled"
	echo "# module versions instead."
	echo "#"
	echo "#############################################"
	echo ""
	exit 0
else
	echo ""
	echo "#############################################"
	echo "#"
	echo "# ERROR: One or more modules failed to compile"
	echo "#"
	echo "#############################################"
	echo ""
	exit 1
fi
