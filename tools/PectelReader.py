#!/usr/bin/env python3

import serial
import time

ser = serial.Serial(port = '/dev/ttyUSB0', baudrate=1952, bytesize=8, parity='N', stopbits=1, xonxoff=0, rtscts=0, dsrdtr=1, timeout=0.25)
send = 0x85
print("Writing [0x%x]" % send)
while True:
	ser.write(bytes([0x85]))
	#print("Reading 1 bytes")
	b = ser.read()
	print("Read [%s]" % b)
	time.sleep(0.1)