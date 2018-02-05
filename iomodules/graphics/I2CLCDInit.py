# -*- coding: utf-8 -*-
"""
Compiled, mashed and generally mutilated 2014-2015 by Denis Pleic
Made available under GNU GENERAL PUBLIC LICENSE

# Modified Python I2C library for Raspberry Pi
# as found on http://www.recantha.co.uk/blog/?p=4849
# Joined existing 'i2c_lib.py' and 'lcddriver.py' into a single library
# added bits and pieces from various sources
# By DenisFromHR (Denis Pleic)
# 2015-02-10, ver 0.1

"""
#
import smbus
import time

# commands
LCD_CLEARDISPLAY = 0x01
LCD_RETURNHOME = 0x02
LCD_ENTRYMODESET = 0x04
LCD_DISPLAYCONTROL = 0x08
LCD_CURSORSHIFT = 0x10
LCD_FUNCTIONSET = 0x20
LCD_SETCGRAMADDR = 0x40
LCD_SETDDRAMADDR = 0x80

# flags for display entry mode
LCD_ENTRYRIGHT = 0x00
LCD_ENTRYLEFT = 0x02
LCD_ENTRYSHIFTINCREMENT = 0x01
LCD_ENTRYSHIFTDECREMENT = 0x00

# flags for display on/off control
LCD_DISPLAYON = 0x04
LCD_DISPLAYOFF = 0x00
LCD_CURSORON = 0x02
LCD_CURSOROFF = 0x00
LCD_BLINKON = 0x01
LCD_BLINKOFF = 0x00

# flags for display/cursor shift
LCD_DISPLAYMOVE = 0x08
LCD_CURSORMOVE = 0x00
LCD_MOVERIGHT = 0x04
LCD_MOVELEFT = 0x00

# flags for function set
LCD_8BITMODE = 0x10
LCD_4BITMODE = 0x00
LCD_2LINE = 0x08
LCD_1LINE = 0x00
LCD_5x10DOTS = 0x04
LCD_5x8DOTS = 0x00

# flags for backlight control
LCD_BACKLIGHT = 0x08
LCD_NOBACKLIGHT = 0x00

En = 0b00000100 # Enable bit
Rw = 0b00000010 # Read/Write bit
Rs = 0b00000001 # Register select bit

class i2clcd:
	
	def __init__(self, i2c_address = 0x27, i2c_port = 1, ):
		""" initializes a new lcd interface using i2c """
		self.i2c_address = i2c_address
		self.i2c_port = i2c_port
		self.i2c_init()
		
		self.lcd_write(0x03)
		self.lcd_write(0x03)
		self.lcd_write(0x03)
		self.lcd_write(0x02)
		
		self.lcd_write(LCD_FUNCTIONSET | LCD_2LINE | LCD_5x8DOTS | LCD_4BITMODE)
		self.lcd_write(LCD_DISPLAYCONTROL | LCD_DISPLAYON)
		self.lcd_write(LCD_CLEARDISPLAY)
		self.lcd_write(LCD_ENTRYMODESET | LCD_ENTRYLEFT)
		
		time.sleep(1)
		
		self.rows = 2
		self.columns = 16
		self.x = 0
		self.y = 1

	############ I2C routines here #######################

	def i2c_init(self):
		self.bus = smbus.SMBus(self.i2c_port)

	def write_cmd(self, cmd):
		""" Write a single command """
		self.bus.write_byte(self.i2c_address, cmd)
		time.sleep(0.0001)

	def write_cmd_arg(self, cmd, data):
		""" Write a command and argument """
		self.bus.write_byte_data(self.i2c_address, cmd, data)
		time.sleep(0.0001)

	def write_block_data(self, cmd, data):
		""" Write a block of data """
		self.bus.write_block_data(self.i2c_address, cmd, data)
		time.sleep(0.0001)

	def read(self):
		""" Read a single byte """
		return self.bus.read_byte(self.i2c_address)

	def read_data(self, cmd):
		""" Read """
		return self.bus.read_byte_data(self.i2c_address, cmd)

	def read_block_data(self, cmd):
		""" Read a block of data """
		return self.bus.read_block_data(self.i2c_address, cmd)

	############ Compatability functions with lcdbackpack ##########
	#
	# These methods make the I2CLCD class compatible (mostly) with
	# the existing lcdbackpack driver from pypi.
	#
	################################################################

	def connect(self):
		pass

	def set_lcd_size(self, columns = 16, rows = 2):
		""" Set size of display """
		self.columns = columns
		self.rows = rows

	def set_brightness(self, level):
		""" Set brightness level to mimic lcdbackpack """
		if level > 0:
			self.backlight(1)
			return True
		elif level == 0:
			self.backlight(0)
			return True
		else:
			return True

	def set_cursor_position(self, col, row):
		""" Internal representation of current cursor position """
		# Compared to lcdbackpack, we index col from 0
		self.x = col - 1
		self.y = row
		
		if self.x > self.columns:
			self.x = self.columns
			
		if self.y > self.rows:
			self.y = self.rows

	def write(self, string):
		""" Write a string of text at the current cursor position """
		
		self.lcd_display_string_pos(string, self.y, self.x)
		self.x += len(string)

	def set_underline_cursor(self, underline_cursor = False):
		""" No-op """
		pass
	
	def set_contrast(self, contrast):
		""" No-op """
		pass
	
	def set_backlight_rgb(self, r, g, b):
		""" No-op """
		pass
	
	def display_on(self):
		""" No-op """
		self.backlight(1)
	
	def display_off(self):
		""" No-op """
		self.backlight(0)	

	def _write_command(self, command):
		""" No-op """
		pass

	def clear(self):
		self.lcd_clear()

	############ LCD routines below here ###########################

	def lcd_strobe(self, data):
		"""# clocks EN to latch command"""
		self.write_cmd(data | En | LCD_BACKLIGHT)
		time.sleep(.0005)
		self.write_cmd(((data & ~En) | LCD_BACKLIGHT))
		time.sleep(.0001)

	def lcd_write_four_bits(self, data):
		self.write_cmd(data | LCD_BACKLIGHT)
		self.lcd_strobe(data)

	def lcd_write(self, cmd, mode=0):
		"""# write a command to lcd"""
		self.lcd_write_four_bits(mode | (cmd & 0xF0))
		self.lcd_write_four_bits(mode | ((cmd << 4) & 0xF0))

	def lcd_write_char(self, charvalue, mode=1):
		"""# write a character to lcd (or character rom) 0x09: backlight | RS=DR<"""
		"""# works!"""
		self.lcd_write_four_bits(mode | (charvalue & 0xF0))
		self.lcd_write_four_bits(mode | ((charvalue << 4) & 0xF0))

	def lcd_display_string(self, string, line):
		"""# put string function"""
		if line == 1:
			self.lcd_write(0x80)
		if line == 2:
			self.lcd_write(0xC0)
		if line == 3:
			self.lcd_write(0x94)
		if line == 4:
			self.lcd_write(0xD4)

		for char in string:
			self.lcd_write(ord(char), Rs)

	def lcd_clear(self):
		"""# clear lcd and set to home"""
		self.lcd_write(LCD_CLEARDISPLAY)
		self.lcd_write(LCD_RETURNHOME)

	def backlight(self, state):
		"""	# define backlight on/off (lcd.backlight(1); off= lcd.backlight(0)"""
		""" # for state, 1 = on, 0 = off"""
		if state == 1:
			self.write_cmd(LCD_BACKLIGHT)
		elif state == 0:
			self.write_cmd(LCD_NOBACKLIGHT)

	def lcd_load_custom_chars(self, fontdata):
		"""	# add custom characters (0 - 7)"""
		self.lcd_write(0x40);
		for char in fontdata:
			for line in char:
				self.lcd_write_char(line)         
	
	def lcd_display_string_pos(self, string, line, pos):
		""" define precise positioning (addition from the forum) """
		if line == 1:
			pos_new = pos
		elif line == 2:
			pos_new = 0x40 + pos
		elif line == 3:
			pos_new = 0x14 + pos
		elif line == 4:
			pos_new = 0x54 + pos

		self.lcd_write(0x80 + pos_new)
		for char in string:
			self.lcd_write(ord(char), Rs)