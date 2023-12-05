import os
import sys
import json
import time
import loadsmwrh
from os.path import exists
#4959:31956

# Load built index
hkdata = loadsmwrh.get_hacklist_data(filename='rhindex.dat')
hkdict = {}

for u in range(len(hkdata)):
    hkdict[  str(hkdata[u]['id'])  ] = hkdata[u]

# Data fetch file
fr = open('fetch_rhlist_smwc.json', 'r')
hacklist  = json.load(fr)

untried = []

for x in hacklist :
    if str(x["id"]) in hkdict:
        continue
    if exists("hacks/" + str(x["id"])):
        continue
    if exists("tried/" + str(x["id"])):
        continue
    print("New: %s | %s | %s" % ( x["id"], x["name"], x["author"]  ))
    #



