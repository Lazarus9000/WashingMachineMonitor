#!/usr/bin/env python
import json
import sys
import time

import gspread
from oauth2client.client import SignedJwtAssertionCredentials

import math


time.sleep(1)
GDOCS_OAUTH_JSON       = 'C:\Users\jegha\Documents\GitHub\WashingMachineMonitor\MyProject-07f7568ae491.json'

status = "off"

# Google Docs spreadsheet name.
GDOCS_SPREADSHEET_NAME = 's2sheet'

# How long to wait (in seconds) between measurements.
FREQUENCY_SECONDS      = 30

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
# Login if necessary.
if worksheet is None:
	worksheet = login_open_sheet(GDOCS_OAUTH_JSON, GDOCS_SPREADSHEET_NAME)

	# Append the data in the spreadsheet, including a timestamp
	try:
		a = 12;
		b = 24;		
		worksheet.append_row([a,b,8765.56])
	except:
		# Error appending data, most likely because credentials are stale.
		# Null out the worksheet so a login is performed at the top of the loop.
		print 'Append error, logging in again'
		worksheet = None
		
		#continue

	# Wait 30 seconds before continuing
	print 'Wrote a row to {0}'.format(GDOCS_SPREADSHEET_NAME)
    
