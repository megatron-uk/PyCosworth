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

*Depending on how often you want to sample data, that's really not a lot at all.*

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
| Status code 1 | 0x8b | Error status codes |
| Status code 2 | 0x8c | Error status codes |
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
data = ser.read()

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
rpm_upper = ser.read()

# Write the byte code for the lower RPM byte
ser.write(bytes([0x81]))

# The ECU responds with a single data byte
rpm_lower = ser.read()

# Shift the upper byte by 8 and add the lower byte
rpm_data = (rpm_upper << 8) + rpm_lower
```

It's a little awkward (you would have thought it would just respond with a two byte data response), but I guess it's relatively easy to deal with.

*Note that there is **no** initialisation needed over the serial port; the ECU automatically brings the serial comms up and starts listening for control bytes over the interface. This is greatly simplified compared to the FIAT/Alfa/Lancia implementation.*

---

## Data Transforms

*The below taken from FIAT documentation - yet to be fully verified on Cosworth implementation:*

```
RPM (most significant byte), 30000000 / DATUM = RPM
RPM (lest significant byte), 30000000 / DATUM = RPM
Injection duration (msb), 4 * DATUM / 10^3 = milliseconds
Injection duration (lsb), 4 * DATUM / 10^3 = milliseconds
Ignition advance, DATUM 1L/4 = degrees (I dont understand this one!)
Intake pressure, DATUM * 6.4161 + 45.63 = mmHg
Air temp, (see lookup tables)
Water temp, (see lookup tables)
TPS, if < 0x30 (DATUM * 0.1848) - 1.41 = Degrees, if >= 0x30 (DATUM * 0.7058) - 90 = degrees 
Battery Voltage, DATUM * 0.0628 = volts
CO Fuel trimmer, DATUM - 128
Injection timing angle, 720 - (DATUM * 90) / 4 = Degrees

All transforms where DATUM == data byte returned
```