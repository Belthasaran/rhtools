import os
import re
import sys
import json
import time
import loadsmwrh
import requests
from os.path import exists
import zipfile
#4959:31956

# Load built index
hkdata = loadsmwrh.get_hacklist_data(filename='rhindex.dat')
hkdict = {}

if not(os.path.exists("zips")):
   os.mkdir("zips")

if not(os.path.exists("tried")):
   os.mkdir("tried")



for u in range(len(hkdata)):
    hkdict[  str(hkdata[u]['id'])  ] = hkdata[u]

# Data fetch file
fr = open('fetch_rhlist_smwc.json', 'r')
hacklist  = json.load(fr)

untried = []

for x in hacklist :
    idstr = str(x["id"])
    if str(x["id"]) in hkdict:
        continue
    if exists("hacks/" + str(x["id"])):
        continue
    if exists("tried/" + str(x["id"])):
        continue
    print("New: %s | %s | %s" % ( x["id"], x["name"], x["author"]  ))
    if not(exists(os.path.join("zips", idstr + ".zip"))):
        failed = False
        url= x["name_href"]
        if (re.match('^\/\/.*', url)):
            url = 'http:' + url

        sys.stderr.write('Downloading ' + url + "\n")
        req = requests.get(url)

        if req.status_code == 200:
            try:
                zipfile.ZipFile(req.content)
            except zipfile.BadZipFile: 
                sys.stderr.write('ERR: HTTP Response for URL ' + url + ' is not a Zip file' + "\n")
                failed = True
                xg = open(os.path.join("tried", idstr), "w")
                xg.close()

        if req.status_code == 200 and failed == False:
            sys.stderr.write(f'Got response 200: saving {idstr}.zip.new' + "\n")
            f = open(os.path.join("zips", idstr + ".zip.new"), "wb")
            f.write(req.content)
            f.close()
            os.replace(os.path.join("zips", idstr + ".zip.new"), os.path.join("zips", idstr + ".zip"))
            sys.stderr.write(f"Saved to file " + os.path.join("zips", idstr + ".zip") + "\n")
        else:
            sys.stderr.write('ERR: Error download id ' + idstr + "\n")
        sys.stderr.write("Pausing for 12 seconds\n")
        time.sleep(12)
        #









