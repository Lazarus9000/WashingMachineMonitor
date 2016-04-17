import json
import sys
import time
#import datetime
#!/usr/bin/env python
from datetime import datetime, time as datetime_time, timedelta
import pushybullet as pb

import gspread
from oauth2client.client import SignedJwtAssertionCredentials

import smbus
import math

#setup for PB
API_KEY = 'o.4j3lgYYD14vc62HIjYmZ5m8y37ReC6bh'
api = pb.PushBullet(API_KEY)
devices = api.devices()

device = devices[0]
push = pb.NotePush('Hello world!', 'The little pi that could')

# Power management registers
power_mgmt_1 = 0x6b
power_mgmt_2 = 0x6c

def try_io(call, tries=10):
    assert tries > 0
    error = None
    result = None

    while tries:
        try:
            result = call()
        except IOError as e:
            error = e
            tries -= 1
        else:
            break

    if not tries:
        raise error

    return result

def read_byte(address, adr):
    return bus.read_byte_data(address, adr)

def read_word(address, adr):
    high = bus.read_byte_data(address, adr)
    low = bus.read_byte_data(address, adr+1)
    val = (high << 8) + low
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

bus = smbus.SMBus(1) # or bus = smbus.SMBus(1) for Revision 2 boards

# Now wake the 6050's up as it starts in sleep mode
bus.write_byte_data(address1, power_mgmt_1, 0)
bus.write_byte_data(address2, power_mgmt_1, 0)

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

def login_open_sheet(oauth_key_file, spreadsheet):
    #Connect to Google Docs spreadsheet and return the first worksheet
    try:
        json_key = json.load(open(oauth_key_file))
        credentials = SignedJwtAssertionCredentials(json_key['client_email'],
                                                    json_key['private_key'],
                                                    ['https://spreadsheets.google.com/feeds'])
        gc = gspread.authorize(credentials)
        worksheet = gc.open(spreadsheet).sheet1
        return worksheet
    except Exception as ex:
        print 'Unable to login and get spreadsheet.  Check OAuth credentials, spreadsheet name, and make sure spreadsheet is shared to the client_email address in the OAuth .json file!'
        print 'Google sheet login failed with error:', ex
        #sys.exit(1)


print 'Logging sensor measurements to {0} every {1} seconds.'.format(GDOCS_SPREADSHEET_NAME, FREQUENCY_SECONDS)
print 'Press Ctrl-C to quit.'
worksheet = None
s = datetime.now()
e = datetime.now()
