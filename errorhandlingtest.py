import json
import sys
import time
#import datetime
#!/usr/bin/env python
from datetime import datetime, time as datetime_time, timedelta
#import pushybullet as pb

#import gspread
#from oauth2client.client import SignedJwtAssertionCredentials

#import smbus
import math

# Power management registers
power_mgmt_1 = 0x6b
power_mgmt_2 = 0x6c

def try_io(call, tries=10):
	assert tries > 0
	error = None
	result = None

	while tries:
		try:
			print("Trying")
			result = call()
		except IOError as e:
			error = e
			tries -= 1
			print("error happened - ", tries)
			print(e)
		else:
			break

	if not tries:
		raise error

	return result

#def read_byte(address, adr):
    #return bus.read_byte_data(address, adr)

def read_word(address, adr):
    #high = bus.read_byte_data(address, adr)
    #low = bus.read_byte_data(address, adr+1)
	high = 12
	low = 1
	val = (high << 8) + low
	raise IOError('A very specific bad thing happened', address, adr)
	return val 

def read_word_2c(address, adr):
    val = read_word(address, adr)
    if (val >= 0x8000):
        return -((65535 - val) + 1)
    else:
        return val

def dist(a,b):
    return math.sqrt((a*a)+(b*b))

def get_y_rotation(x,y,z):
    radians = math.atan2(x, dist(y,z))
    return -math.degrees(radians)

def get_x_rotation(x,y,z):
    radians = math.atan2(y, dist(x,z))
    return math.degrees(radians)

address1 = 0x68       # This is the address value read via the i2cdetect command
address2 = 0x69       # This is MPU #2

#bus = smbus.SMBus(1) # or bus = smbus.SMBus(1) for Revision 2 boards

# Now wake the 6050's up as it starts in sleep mode
#bus.write_byte_data(address1, power_mgmt_1, 0)
#bus.write_byte_data(address2, power_mgmt_1, 0)
print(address1)
print(0x3b)
try_io(lambda: read_word_2c(address1, 0x3b))

#prevX1 = read_word_2c(address1, 0x3b)
#prevY1 = read_word_2c(address1, 0x3d)
#prevZ1 = read_word_2c(address1, 0x3f)

#prevX2 = read_word_2c(address2, 0x3b)
#prevY2 = read_word_2c(address2, 0x3d)
#prevZ2 = read_word_2c(address2, 0x3f)

#time.sleep(1)
#GDOCS_OAUTH_JSON       = 'MyProject-43a6520ce94c.json'

#status = "off"

# Google Docs spreadsheet name.
#GDOCS_SPREADSHEET_NAME = 'Sensor test'

# How long to wait (in seconds) between measurements.
#FREQUENCY_SECONDS      = 30

#initialise s
#s = datetime.now()

worksheet = None
s = datetime.now()
e = datetime.now()
