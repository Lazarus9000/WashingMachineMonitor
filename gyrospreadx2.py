#!/usr/bin/env python
import json
import sys
import time
#import datetime
from datetime import datetime, time as datetime_time, timedelta
import pushybullet as pb

import gspread
from oauth2client.client import SignedJwtAssertionCredentials

import smbus
import math
import RPi.GPIO as GPIO

time.sleep(240)

DIR= '/home/pi/FTP/git/WashingMachineMonitor/'

GPIO.setmode(GPIO.BCM)
DEBUG = 1

#setup for PB
API_KEY = 'o.4j3lgYYD14vc62HIjYmZ5m8y37ReC6bh'
api = pb.PushBullet(API_KEY)
devices = api.devices()

device = devices[0]
push = pb.NotePush('Hello world!', 'The little pi that could')

# Power management registers
power_mgmt_1 = 0x6b
power_mgmt_2 = 0x6c

# read SPI data from MCP3008 chip, 8 possible adc's (0 thru 7)
def readadc(adcnum, clockpin, mosipin, misopin, cspin):
        if ((adcnum > 7) or (adcnum < 0)):
                return -1
        GPIO.output(cspin, True)
 
        GPIO.output(clockpin, False)  # start clock low
        GPIO.output(cspin, False)     # bring CS low
 
        commandout = adcnum
        commandout |= 0x18  # start bit + single-ended bit
        commandout <<= 3    # we only need to send 5 bits here
        for i in range(5):
                if (commandout & 0x80):
                        GPIO.output(mosipin, True)
                else:
                        GPIO.output(mosipin, False)
                commandout <<= 1
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)
 
        adcout = 0
        # read in one empty bit, one null bit and 10 ADC bits
        for i in range(12):
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)
                adcout <<= 1
                if (GPIO.input(misopin)):
                        adcout |= 0x1
 
        GPIO.output(cspin, True)
        
        adcout >>= 1       # first bit is 'null' so drop it
        return adcout

# change these as desired - they're the pins connected from the
# SPI port on the ADC to the Cobbler
SPICLK = 18
SPIMISO = 23
SPIMOSI = 24
SPICS = 25
 
# set up the SPI interface pins
GPIO.setup(SPIMOSI, GPIO.OUT)
GPIO.setup(SPIMISO, GPIO.IN)
GPIO.setup(SPICLK, GPIO.OUT)
GPIO.setup(SPICS, GPIO.OUT)
 
# 10k trim pot connected to adc #0
mic1 = 6;		
mic2 = 7;
miclist1 = [];
miclist2 = [];
samples = 100;
templist = [];

def getMicIn(mic):
	totalmic = 0
	del templist [:];
	for x in range(0, samples):
		micout = readadc(mic, SPICLK, SPIMOSI, SPIMISO, SPICS)
		templist.append(abs(micout-512.0))
		totalmic += abs(micout-512.0)
		time.sleep(0.001)
	#print templist
	return 	totalmic

def try_io(call, tries=10):
	assert tries > 0
	error = None
	result = None

	while tries:
		try:
			print 'Trying sensor'
			result = call()
		except IOError as e:
			error = e
			tries -= 1
			time.sleep(1)
			print 'Failed - tries remaining: ', tries
		else:
			break

	if not tries:
		print '10 fails - crash!'
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
##bus.write_byte_data(address1, power_mgmt_1, 0)
##bus.write_byte_data(address2, power_mgmt_1, 0)
##
##try_io(lambda: read_word_2c(address1, 0x3b))
##
##prevX1 = try_io(lambda: read_word_2c(address1, 0x3b))
##print 'output from tryPI!: ', prevX1
##prevY1 = try_io(lambda: read_word_2c(address1, 0x3d))
##prevZ1 = try_io(lambda: read_word_2c(address1, 0x3f))
##
##prevX2 = try_io(lambda: read_word_2c(address2, 0x3b))
##prevY2 = try_io(lambda: read_word_2c(address2, 0x3d))
##prevZ2 = try_io(lambda: read_word_2c(address2, 0x3f))

time.sleep(1)
GDOCS_OAUTH_JSON       = DIR + 'MyProject-07f7568ae491.json'

status = "off"

# Google Docs spreadsheet name.
GDOCS_SPREADSHEET_NAME = 's2sheet'

# How long to wait (in seconds) between measurements.
FREQUENCY_SECONDS      = 30

#initialise s
s = datetime.now()

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
while True:
	print datetime.now()
	diffAcc1 = 0
	diffAcc2 = 0
##	for x in range(0, 10):
##        #gyro_xout = read_word_2c(adress1, 0x43)
##        #gyro_yout = read_word_2c(adress1, 0x45)
##        #gyro_zout = read_word_2c(adress1, 0x47)
##
##		accel_xout1 = try_io(lambda: read_word_2c(address1, 0x3b))
##		time.sleep(.1)
##		accel_yout1 = try_io(lambda: read_word_2c(address1, 0x3d))
##		time.sleep(.1)
##		accel_zout1 = try_io(lambda: read_word_2c(address1, 0x3f))
##		time.sleep(.1)
##
##		diffAcc1 += abs(prevX1-accel_xout1)+abs(prevY1-accel_yout1)+abs(prevZ1-accel_zout1)
##		#Consider not taking the derivate but just summing up the three outputs over time?
##		
##		#print(diffAcc1)
##		prevX1 = accel_xout1
##		prevY1 = accel_yout1
##		prevZ1 = accel_zout1
##
##		accel_xout2 = try_io(lambda: read_word_2c(address2, 0x3b))
##		#Got an error after a few hours of operation, which might be caused by accessing I/O to fast
##		#http://stackoverflow.com/questions/30325351/ioerror-errno-5-input-output-error-while-using-smbus-for-analog-reading-thr
##		time.sleep(.1)
##		accel_yout2 = try_io(lambda: read_word_2c(address2, 0x3d))
##		time.sleep(.1)
##		accel_zout2 = try_io(lambda: read_word_2c(address2, 0x3f))
##		time.sleep(.1)
##
##		diffAcc2 += abs(prevX2-accel_xout2)+abs(prevY2-accel_yout2)+abs(prevZ2-accel_zout2)
##		#print(diffAcc2)
##		prevX2 = accel_xout2
##		prevY2 = accel_yout2
##		prevZ2 = accel_zout2


		#time.sleep(.1)

		#accel_xout_scaled = accel_xout / 16384.0
		#accel_yout_scaled = accel_yout / 16384.0
		#accel_zout_scaled = accel_zout / 16384.0
	c = datetime.now()
	#c = datetime.strptime(t.strftime(), '%H:%M:%S')
	inputMic1 = getMicIn(mic1)
	miclist1 = templist;
	print miclist1
	#https://wiki.python.org/moin/HowTo/Sorting
	#print templist
	sortlist = sorted(miclist1)
	window = 20;
	mid1 = sortlist[window:samples-window]
	totalmid1 = 0;
	for x in range(window,samples-window):		
		totalmid1 += sortlist[x]
	
	totalhigh1 = 0;
	for x in range(samples-window,samples):		
		totalhigh1 += sortlist[x]
	
	inputMic2 = getMicIn(mic2)
	miclist2 = templist;
	print miclist2
	sortlist2 = sorted(miclist2)
	window = 20;
	mid2 = sortlist2[window:samples-window]
	totalmid2 = 0;
	for x in range(window, samples-window):		
		totalmid2 += sortlist2[x]
	totalhigh2 = 0;
	for x in range(samples-window,samples):		
		totalhigh2 += sortlist[x]
		
	if diffAcc1 < 50000 and status == "off":
		s = datetime.now()
		#s = datetime.strptime(t.strftime("%H:%M:%S"), '%H:%M:%S')
	
	if diffAcc1 > 50000 and status == "on":
		e = datetime.now()
	
	#print(time_diff(c, s))
	sdiff = (c-s) 
	print(sdiff.total_seconds())
	
	ediff = (c-e) 
	print(ediff.total_seconds())
	
	notify = 0
	
	if int(sdiff.total_seconds()) > 20 and status == "off":
		status = "on"
		push = pb.NotePush('Saa er der gang i svinet!', str(sdiff.total_seconds()))
		push.send(device)
		notify = 1
	
	if int(ediff.total_seconds()) > 180 and status == "on":
		status = "off"
		push = pb.NotePush('Nu er den done, gogogo!', str(ediff.total_seconds()))
		push.send(device)
		notify = 1
	
    # Login if necessary.
	if worksheet is None:
		worksheet = login_open_sheet(GDOCS_OAUTH_JSON, GDOCS_SPREADSHEET_NAME)

    # Append the data in the spreadsheet, including a timestamp
	try:
		print(diffAcc1)
		print(diffAcc2)
		print(inputMic1)
		print(inputMic2)
		worksheet.append_row([datetime.now(), diffAcc1, diffAcc2, inputMic1, totalmid1, totalhigh1, inputMic2, totalmid2, totalhigh2)
	except:
        # Error appending data, most likely because credentials are stale.
        # Null out the worksheet so a login is performed at the top of the loop.
		print 'Append error, logging in again'
		worksheet = None
        
		continue

    # Wait 30 seconds before continuing
	print 'Wrote a row to {0}'.format(GDOCS_SPREADSHEET_NAME)
    
