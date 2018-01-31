# The Cosworth Pectel Serial Datastream

The Pectel datastream is an RS232 TTL level signal. It uses 3 wires from the ECU which need level shifting down to your USB<->Serial device.

## Serial Configuration

The following serial configuration is needed when talking to a Pectel serial datastream enabled ECU:

| Parameter | Value | Information |
| --------- | ----- | ----------- |
| Baud rate | 1952  | The speed at which the serial port and ECU exchange data |
| Data bits | 8     |  Standard 8N1 settings           |
| Stop bits | 1     |  Standard 8N1 settings           |
| Parity    | N     |  Standard 8N1 settings           |
| XON/XOFF  | Off   | RS232 software flow control |
| RTS/CTS   | Off   | RS232 hardware flow control |
| DSR/DTR   | Off    | RS232 hardware flow control |

*Note: The baud rate is very low, this means that the amount of data we can transfer in a given space of time is going to be limited. With stop bits and flow control taken in to consideration, we're probably looking at something in the order of 1.2 - 1.5kbits/second.* 

Performance testing has revealed that the [Python code](../iomodules/sensors/Cosworth.py) I have written to query the ECU sensor data can retrieve a single sensor value in approximately 25-27ms. There may be some savings to be made if the code was written in C or assembly, but I doubt much more could be shaved off those times.

Most sensors are single 8bit values, and the above timing applies to them, however RPM and injector duration, amongst a few others, are 16bit values, and require two writes and two reads - almost doubling the time to around 45ms.

Extrapolating these numbers out, we see that we can get around 60-62 single byte samples per second, which isn't a lot, but probably enough to get a reasonable update speed in any digital dashboard code.

Moving to 2-byte sensors, the figure halves (approximately 30 updates a second). 

So we'll have to be careful when configuring the software so that we only efresh those sensors we want a quick update speed on, leaving those that are slower-chaning (temperature, for example), or pre-set (mixture screw) with a much longer interval between reads.

When configuring which sensors you use in the software, remember that you can only get, at most, 60 updates a second, and configure your refresh timers appropriately.

## Available Sensors

The type and number of sensors varies depending on which car and which ECU is being used. Below is listed the available sensors and the code to retrieve them.

**Sierra Cosworth 4x4 (L8 ECU)**

| Sensor | Byte Code | Information |
| ------ | --------- | ----------- |
| RPM  a  | 0x80      | Upper byte of a 16bit value |
| RPM   b | 0x81      | Lower byte of a 16bit value |
| Inlet manifold pressure | 0x82 | Boost/vacuum |
| Intake air temp | 0x83 | Temperature of the air charge in the inlet manifold |
| Engine coolant temp | 0x84 | Water temperature |
| Throttle position | 0x85 | Angle of TPS |
| Ignition timing | 0x86 | Ignition advance, in degrees BTDC |
| Injector duration a | 0x87 | Upper byte of a 16bit value |
| Injector duration b | 0x88 | Lower byte of a 16bit value |
| Battery voltage | 0x89 | Current battery / supply circuit voltage |
| CO mixture trim pot | 0x8a | Fuel mixture trim screw position |
| Status code 1 | 0x8b | Error status codes |
| Status code 2 | 0x8c | Error status codes |
| ? | 0x8d | ? |
| ? | 0x8e | ? |
| ? | 0x8f | ? |
| Boost control valve | 0x90 | Duty cycle of Amal valve |

*Note: There are other codes available, as well as a few diagnostic routines. I have not yet documented or tested these.*

---

**Escort Cosworth (P8 ECU)**

| Sensor | Byte Code | Information |
| ------ | --------- | ----------- |

*To be added*

## Reading Sensor Data

Getting data out of the ECU is quite straight forward once you have a serial connection open to it.

My language of choice for these kinds of tasks is Python, and indeed it is what the PyCosworth project is written in, but the details below should be portable to pretty much any other language.

The general principle is:

```
Open connection to serial port
Write byte code of sensor to serial port
Read one byte from serial port
Translate the returned byte to human-format
```

In Python, this translates to:

```
ser = serial.Serial(port = '/dev/ttyUSB0', baudrate=1952, bytesize=8, parity='N', stopbits=1, xonxoff=0, rtscts=0, dsrdtr=0)

# Write the byte code for battery voltage to the serial port
ser.write(bytes([0x89]))

# The ECU responds with a single data byte
data = ser.read(1)[0]

# Transform the returned data into a real world number
# The transform for voltage is returned data / 0.0628
voltage = int(data) / 0.0628 

print("Battery voltage is %sv" % voltage)
```

Most sensors report data as a single byte, for those sensors that return a 16bit value, two writes and two reads are necessary:

```
# Write the byte code RPM upper 8 bits
ser.write(bytes([0x80]))

# The ECU responds with a single data byte
rpm_upper = ser.read(1)[0]

# Write the byte code for the lower RPM byte
ser.write(bytes([0x81]))

# The ECU responds with a single data byte
rpm_lower = ser.read(1)[0]

# Shift the upper byte by 8 and add the lower byte
rpm_data = (rpm_upper << 8) + rpm_lower
```

It's a little awkward (you would have thought it would just respond with a two byte data response), but I guess it's relatively easy to deal with.

*Note that there is **no** initialisation needed over the serial port; the ECU automatically brings the serial comms up and starts listening for control bytes over the interface. This is greatly simplified compared to the FIAT/Alfa/Lancia implementation.*

---

## Data Transforms

The data bytes that are sent back from the ECU need to be converted into real world numbers, as they are just 0-255 (single bytes) or 0-65535 (16bit) unsigned integers by default.

Firstly, here are the FIAT versions - this is where we started from:

```
RPM = 30000000 / (upper byte + lower byte) = RPM
Injection duration =  4 * (upper byte + lower byte) / 10^3 = milliseconds
Ignition advance = byte /4 = Degrees BTDC
Inlet manifold pressure = (byte * 6.4161) + 45.63 = mmHg
Air temp, (see lookup tables)
Water temp, (see lookup tables)
Throttle position = if < 0x30 (byte * 0.1848) - 1.41 = Degrees open 
Throttle position = if >= 0x30 (byte * 0.7058) - 90 = Degrees open
Battery Voltage = byte * 0.0628 = Volts
CO Fuel trimmer = byte - 128 = Position
```

Not all of the FIAT transform formulae are correct. However, the calculations below *are* correct:

```
RPM = 1875000 / ((upper byte << 8) + (lower byte)) 
# Bitshift upper byte left by 8, add lower byte, divide into 1875000.
# Result = Engine speed in rpm

Injector duration = (((upper byte << 8) + (lower byte)) * 4) / 1000
# Bitshift upper byte left by 8, add lower byte, multiply by 4, divide result by 1000
# Result = Injector duration in milliseconds.

Ignition Advance = byte / 4
# Result = Ignition advance in degrees before top dead centre

Inlet manifold pressure = (byte * 6.4161) + 45.63
# Result = pressure in millimetres of mercury

Inlet manifold pressure = ((byte * 6.4161) + 45.63) * 0.75006156130264
# Result = pressure in millibars

Inlet manifold pressure = ((byte * 6.4161) + 45.63) * 51.714924102396
# Result = pressure in pounds per square inches

Air/Water temperature = -55 + (0.75 * byte)
# Result = Temperature in degrees Celsius

CO Mixture trim pot = ((byte - 128) / 128) * 50
# Result = Mixture trim screw position

Battery Voltage = byte * 0.0628
# Result = Battery voltage
```

The calculations for *CO MIxture trim* and *Temperature* were generously supplied and confirmed by [RP Lab](http://www.rp-lab.com/), developers of the Weber Marelli ECU diagnostic software.

In addition, forum user *Foxy44* from [Turbosport](http://www.turbosport.co.uk/member.php?u=14707) as well as [RP Lab](http://www.rp-lab.com/) both confirmed the calculation of *RPM*.

## Status and Error Codes

*TO DO: We don't have any information on how to decode status code values (from the control codes 0x8b and 0x8c) at this time.*

## Missing Information

Lambda sensor information - is it available? Can we check for open/closed loop mode?