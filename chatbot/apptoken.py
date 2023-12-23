#!/usr/bin/python
# Requires Python language Version 3.x

# Quick and dirty Twitch API Token credential management
#
# The Client_Id and Client_Secret  are used to create an Application Token.
# Twitch expires Application Tokens after 60 days, so we need to have a check
# to ensure validity and autogenerate a new token if the saved one is no longer valid.
#
#
# Example usage:
#       import apptoken

#       [client_id, client_secret, apptoken=  apptoken.get_tokens(filename='/path/to/tokens/file', frnkeyd='ferney key here')
#
# Alternative, get_tokens() can be called without parameters:
# the user should be directed to set environment variable TWSECFILE to the filename
# and  TXDKEYZ0 to the Fernet key used to encrypt credentials.
#  
import requests
import json
import csv
import os
import time

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

def get_tokens(filename=None,frnkeyd=None):
    if frnkeyd == None and 'TXDKEYZ0' in os.environ:
        frnkeyd = os.environ['TXDKEYZ0']
    if filename == None and  not('TWSECFILE' in os.environ):
        raise Exception("TW Secrets path unspecified")
    if filename == None:
        filename = os.environ['TWSECFILE']
    else:
        filename = str(filename)

    frnkey = None
    if frnkeyd:
        frnkey = Fernet(frnkeyd)

    client_id=""
    client_secret=""
    app_token=""
    try:
        with open(filename, 'r') as secretfile:
            filedata = (frnkey.decrypt( bytes(secretfile.read(),'utf8') )).decode('utf8').split('\n')
            client_id = filedata[0]
            client_secret = filedata[1]
            app_token = filedata[2]
    except Exception as exc1:
        print("Unable to read Twitch API secrets from twsecrets: " + str(exc1))
        return None
    validToken = 0

    if client_secret=="":
        print("Please enter client_id and client_secret for the Twitch API access from app on your Twitch dev console https://dev.twitch.tv/console")
        client_id=input("Twitch API Client-ID:")
        client_secret=input("Twitch API Client-Secret:")

    # To get  App token
    # POST to 'https://id.twitch.tv/oauth2/token?client_id=XXX&client_secret=YYYY&grant_type=client_credentials'
    # The reply will look like
    # {"access_token":"secret app auth token here","expires_in":5429457,"token_type":"bearer"}
    # app_token = 'xx'

    validateRequest = requests.get('https://id.twitch.tv/oauth2/validate', headers = {'Client-ID' : client_id,  'Authorization' : 'OAuth ' +app_token})
    if validateRequest.status_code == 200 :
        validToken = 1
    if validToken == 0 :
        tokenRequest = requests.post('https://id.twitch.tv/oauth2/token?client_id=' + client_id +'&client_secret=' + client_secret + '&grant_type=client_credentials')
        if tokenRequest.status_code == 200:
            j = json.loads(tokenRequest.text)
            atoken = j["access_token"]
            app_token = atoken
            with open(str(filename) + ".new", 'w') as soutfile:
                soutfile.write(str(frnkey.encrypt(bytes(client_id + "\n" + client_secret + "\n" + app_token + "\n", 'utf8'))))
            os.rename(str(filename) + ".new", filename)
    return [client_id, client_secret, app_token]

