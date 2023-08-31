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
    if romfile:
        #syscmd = r'C:\stream\QUsb2Snes\SendToSd2Snes.exe ' + romfile
        if os.path.exists('/mnt/c'):
            syscmd = os.path.join('/mnt', 'c', 'stream', 'QUsb2Snes', 'SendToSd2Snes.exe') + ' ' + romfile
        else:
            syscmd = 'C:\\' + os.path.join('stream', 'QUsb2Snes', 'SendToSd2Snes.exe') + ' ' + romfile
        print('Running   ' + syscmd)
        os.system(syscmd)
    pass

if __name__ == '__main__':
    sendtosnes_function(sys.argv)
    
    
    
    
 
