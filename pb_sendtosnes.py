# Copyright C Belthasar 2023 All Rights Reserved

from zipfile import ZipFile
import re
import hashlib
import base64
import os
import json
import sys
import loadsmwrh

def sendtosnes_function(args):
    if (len(args) < 2):
        print('Usage: pb_sendtosnes <FILENAME>')
        return None
    romfile = args[1]
    if (romfile and len(args) >= 2):
        if args[0] == 'launch1':
             ohash = loadsmwrh.get_local_options()
             syscmd = str(ohash['launcher1']).replace('%file',romfile)
             print('Running '+syscmd)
             if not(os.system(syscmd)):
                 return True
             print('ERROR: Launch error for ' +str(syscmd))
    if romfile:
        #syscmd = r'C:\stream\QUsb2Snes\SendToSd2Snes.exe ' + romfile
        if os.path.exists('/mnt/c'):
            syscmd = os.path.join('/mnt', 'c', 'stream', 'QUsb2Snes', 'SendToSd2Snes.exe') + ' ' + romfile
        else:
            syscmd = 'C:\\' + os.path.join('stream', 'QUsb2Snes', 'SendToSd2Snes.exe') + ' ' + romfile
        print('Running   ' + syscmd)
        if os.system(syscmd):
            return None
        return True
    pass

if __name__ == '__main__':
    sendtosnes_function(sys.argv)
    
    
    
    
 
