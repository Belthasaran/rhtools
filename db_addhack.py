# Copyright C Belthasar 2023 All Rights Reserved

from zipfile import ZipFile
import re
import hashlib
import base64
import os
import json
import sys
import loadsmwrh

def addhack_function(args):
    if not loadsmwrh.path_rerequisites():
        return None

    hackid = (args[1])
    filename = os.path.join("hacks", "") + str(hackid) + ""

    hacklist = loadsmwrh.get_hacklist_data(filename=None)
    #
    for i in range(len(hacklist)): 
         if hacklist[i]['id'] == hackid:
             print('NOTE: Hack id '+hackid+' already exists in dataset, and database entry will be overwritten')
             del hacklist[i]
             break
    for i in range(len(hacklist)):
         if hacklist[i]['id'] == hackid:
             print('NOTE: Hack id '+hackid+' already exists in dataset, and database entry will be overwritten')
             del hacklist[i]
             break

    f1 = open(filename, 'r')
    #hackinfo  = loadsmwrh.get_hack_info( str(hackid)  )
    data = f1.read()
    f1.close()
    addhackinfo = json.loads(data)
    if not(type(addhackinfo) == list):
        addhackinfo = [addhackinfo]
    hacklist = hacklist + addhackinfo
    savepath = loadsmwrh.rhmd_path()
    loadsmwrh.save_hacklist_data(hacklist, filename=savepath, docompress=True)

if __name__ == '__main__':
    addhack_function(sys.argv)
    
    
    
    
 
