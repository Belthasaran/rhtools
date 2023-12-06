#!/usr/bin/python
#
# This program queries SMWC for the complete list of all games
# and creates the index file   fetch_rhlist_smwc.json
#
# This saved Index file can then be used by do_smwc_findnew.py to
# automate the download of "new hacks"  not yet stored in zips/
#
# And by the Twitch Chatbot module to search for SMW romhacks /
# display hack info. 
# ( Chat command: !rhinfo <keywords> ) - Search for SMW hacks URL by Name, author, or id
#

import requests
import json
import re
import os
import sys
import time
import random
import base64
import loadsmwrh

# Number of seconds extra to wait between requests to server
time_between_requests = 10

hacklist_file = 'fetch_rhlist_smwc.json'
hacklist_new_file = f'{hacklist_file}.new'
f = open(hacklist_new_file, 'w')

nexturl = base64.b64decode('aHR0cHM6Ly93d3cuc213Y2VudHJhbC5uZXQvYWpheC5waHA/YT1nZXRzZWN0aW9ubGlzdCZwPXNlY3Rpb24mcz1zbXdoYWNrcyZ1PTAmZz0wJm49MSZvPWRhdGUmZD1kZXNj').decode('utf8')
hacklist = []
lastrequest = 0
pagenum = 0

urlprefix = base64.b64decode('aHR0cHM6Ly93d3cuc213Y2VudHJhbC5uZXQv').decode()
sys.stderr.write("Begin operation\n")

while nexturl and nexturl[0:len(urlprefix)] == urlprefix:
    pageurl = nexturl
    pagenum = pagenum + 1
    nexturl = None
    time.sleep(10)

    while int(time.time()) < lastrequest + time_between_requests:
         sys.stderr.write("Just a second...\n")
         time.sleep(1)
    sys.stderr.write(f"Requesting page number {pagenum}\n")
    pagerequest = requests.get ( pageurl )

    if pagerequest.status_code == 200:
        time.sleep(random.random()*3)
        try:
            j1 = json.loads(pagerequest.text)
            if type(j1["data"]) == type([]) and len(j1["data"]) > 0 :
                hacklist.extend( j1["data"] )
            lastrequest = time.time()
            nexturl = j1["next_page_url"]
        except Exception as err:
            raise Exception(f"ERR: HTTP Request To {pageurl} | {pagenum} Error_1:: " + str(err))
            pass
    else:
        raise Exception(f"ERR: HTTP Request to {pageurl} | {pagenum} Error_2:: " + str(pagerequest.text))

for x in range(len(hacklist)):
   # def fix_hentry(data):
   try:
       item = hacklist[x]
       itemf = loadsmwrh.fix_hentry(item)
       hacklist[x] = itemf
   except:
       pass

f.write(json.dumps(hacklist))
f.close()
os.replace(hacklist_new_file,hacklist_file)
sys.stderr.write(f"Saved output file {hacklist_file}\n")





