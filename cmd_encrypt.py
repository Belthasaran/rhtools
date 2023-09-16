from zipfile import ZipFile
import re
import hashlib
import base64
import os
import os
import json
import sys
from compress import Compressor               

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

keytext = input('Enter key:')
frnkey = Fernet(keytext)
filename = input('Enter filename:')
f1 = open(filename,'r')
frndata = frnkey.encrypt(f1.read().encode('utf8'))
f1.close()
print(frndata.decode('utf8'))

#frndata = frn.encrypt(bindata)
#print(key.decode('utf8'))

