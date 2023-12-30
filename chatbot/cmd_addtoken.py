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
from pathlib import Path

import apptoken
import segno
import re
import uuid
import random

def setup_secret_storage(args):
    """
    Walk through secret storage setup
    """
    prompt_s = "Please enter some text:"

    print("This is either blank, or a short word or number to name the storage")
    print("(Default is blank. Make sure the storage name is configured in the application)")
    while True:
        storename = input('Storage name:')
        if re.match('^[a-zA-Z0-9]{0,20}$', storename):
            break
        print('Try again')
    if not(storename == ''):
        storename = '_' + storename
    #
    print("*"*70)
    print("   ")
    print("For the next step:")
    print("Please enter some random sentences and press enter")
    print("This will be used to generate an encryption key")
    print(" ")
    print("")
    print("   ")
    print("*"*70)
    textdata = ""
    textdata_e = ""

    while len(textdata_e) < 64:
         textdata = textdata + input(prompt_s)
         prompt_s = f"Please enter more text ({len(textdata_e)}/100): "
         textdata_e = re.sub(r'(.)\1+','',textdata.lower())
         textdata_e = re.sub(r'\W+','',textdata_e)
         textdata_e = re.sub(r'(.)\1+','',textdata_e)

    print("Generating key...")  # use PBKDF2 to make a key based on the user input + 128-bit random salt
    xsha224 = hashlib.sha224( (bytes(32) + bytes(textdata,'utf8') + bytes(32))  ).hexdigest()
    password = bytes(xsha224, 'ascii')
    salt = os.urandom(16)
    kdf = PBKDF2HMAC( algorithm=hashes.SHA256(), length=32, salt=salt, iterations=390000+random.randint(0,50000) )
    key = base64.urlsafe_b64encode(kdf.derive(password))
    frn = Fernet(key)
    print('Enter record to store in slot0: client_id')
    s_client_id = input('client_id: ')
    print('Enter record to store in slot1: client_secret')
    s_client_secret = input('client_secret: ')
    print('(Optional) app_token:')
    s_app_token = input('app_token: ')
    token_secrets = {
         'client_id' : s_client_id,
         'client_secret' : s_client_secret,
         'app_token' : s_app_token
    }
    fpath = os.path.join(Path.home(), f".twsecrets{storename}")
    apptoken.save_token_secrets(token_secrets,filename=fpath,frnkeyd=key)

    print("Ok,")
    print("This is your decrypt/encrypt key:")
    #print(f" {key.decode('utf8')}")
    segno.make_qr(f"{key.decode('utf8')}").terminal(compact=True)
    print("Add the following to your shell environment variables:")
    print(f"TXDKEYZ0{storename}=\"{key.decode('utf8')}\"")
    print(f"TWSECFILE{storename}={fpath}")
    ##

    pass


def add_app_token(args):
    tkeys = apptoken.get_token_secrets().keys()
    print("Existing entries:")
    for ik in tkeys:
        print(str(ik))
    key_s = input('Enter key string:').lower()
    value_s = input('Enter vlaue string:')
    tdict = apptoken.get_token_secrets()
    tdict[key_s] = str(value_s)
    apptoken.save_token_secrets(tdict)
    #print(str(tdict))


if __name__ == '__main__':
    if len(sys.argv)>1 and sys.argv[1].upper()=='SETUP':
        setup_secret_storage(sys.argv)
    elif len(sys.argv)>1 and sys.argv[1].upper()=='READ':
        confirm=input('Press [y] to confirm read: ')
        if (confirm=='y'):
            print(json.dumps(apptoken.get_token_secrets(),indent=4))
    else:
        add_app_token(sys.argv)





