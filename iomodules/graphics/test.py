# requires RPi_I2C_driver.py
import I2CLCDInit
from time import *

mylcd = I2CLCDInit.i2clcd(i2c_address = 0x27)
mylcd.backlight(1)
mylcd.lcd_clear()
# test 2
mylcd.lcd_display_string("1 RPi I2C test", 1)
mylcd.lcd_display_string("2 Custom chars", 2)
mylcd.lcd_display_string("3 Custom chars", 3)
mylcd.lcd_display_string("4 Custom chars", 4)
sleep(2)
mylcd.backlight(0)
sleep(2) # 2 sec delay
mylcd.backlight(1)
sleep(1)
mylcd.clear()
mylcd.set_cursor_position(10,2)
mylcd.write("Help!")