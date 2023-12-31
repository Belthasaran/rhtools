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
import base64
import traceback
import hashlib
import urllib.parse

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

def save_token_secrets(dict, filename=None,frnkeyd=None,storename=''):
    """
    dict - Dictionary containing the   secret  key-data pairs

    Optional from function parameters or system environment:
    filename - The file to store secrets at
    frnkeyd - The fernet key used for encryption

    If optional values are not set, then the corresponding environment variables must be present.
    """
    if frnkeyd == None and f'TXDKEYZ0{storename}' in os.environ:
        frnkeyd = os.environ[f'TXDKEYZ0{storename}']
    if filename == None and  not(f'TWSECFILE{storename}' in os.environ):
        raise Exception("TW Secrets path unspecified")
    if filename == None:
        filename = os.environ[f'TWSECFILE{storename}']
    else:
        filename = str(filename)
    
    frnkey = None
    if frnkeyd:
        frnkey = Fernet(frnkeyd)

    client_id = ''
    client_secret = ''
    app_token = ''

    if 'client_id' in dict:
        client_id = dict['client_id']
    if 'client_secret' in dict:
        client_secret = dict['client_secret']
    if 'app_token' in dict:
        app_token = dict['app_token']

    original_umask = os.umask(0o077)
    try:
        with open(str(filename) + ".new", 'w') as soutfile:
            buffer = ''
            for ik in dict.keys():
                if  ik in ['client_id', 'client_secret', 'app_token']:
                    continue
                buffer = buffer + base64.urlsafe_b64encode( bytes(ik,'utf8') ).decode('utf8') + "\n"
                buffer = buffer + base64.urlsafe_b64encode( bytes(dict[ik],'utf8') ).decode('utf8') + "\n"
            soutfile.write(str(frnkey.encrypt(bytes(client_id + "\n" + client_secret + "\n" + app_token + "\n" + buffer + "\n", 'utf8')).decode('utf8') ))
        os.umask(original_umask)
        os.rename(str(filename) + ".new", filename)
    finally:
        os.umask(original_umask)
    #except Exception as xerr:
    #    raise self.exc_info[1], None, self.exc_info[2]
    return 1

def get_token_secrets(filename=None,frnkeyd=None,onekey=None,storename=''):
    """
    Retrieve a secret from the secrets storage

    Optional:
    filename - Path to file storing the secrets
    frnkeyd - Fernet key used to encrypt the secrets storage
    onekey -  Name of the database key to retrieve

    If onekey is specified, then the Return result is the contents of the database key.

    If onekey input is None, then the Return result is a dictionary of the stored secrets.
    """
    if frnkeyd == None and f'TXDKEYZ0{storename}' in os.environ:
        frnkeyd = os.environ[f'TXDKEYZ0{storename}']
    if filename == None and  not(f'TWSECFILE{storename}' in os.environ):
        raise Exception("TW Secrets path unspecified")
    if filename == None:
        filename = os.environ[f'TWSECFILE{storename}']
    else:
        filename = str(filename)

    frnkey = None
    if frnkeyd:
        frnkey = Fernet(frnkeyd)

    dict={}
    client_id=""
    client_secret=""
    app_token=""
    skipnext=0
    try:
        with open(filename, 'r') as secretfile:
            filedata = (frnkey.decrypt( bytes(secretfile.read(),'utf8') )).decode('utf8').split('\n')
            #print(str(filedata))
            dict['client_id'] = filedata[0]
            dict['client_secret'] = filedata[1]
            dict['app_token'] = filedata[2]
            for i in range(3,len(filedata),2):
                if skipnext:
                    skipnext=0
                    continue
                if not(filedata[i]) or filedata[i] == '':
                    #print('SK')
                    skipnext=1
                    continue
                ###
                key_s = base64.urlsafe_b64decode(filedata[i]).decode('utf8')
                value_s = base64.urlsafe_b64decode(filedata[i+1]).decode('utf8')
                dict[key_s] = value_s
                key_s = None
                value_s = None
        if not(onekey):
            return dict
        if onekey in dict:
            return dict[onekey]
        return None
    except Exception as exc1:
        print("Unable to read Twitch API secrets from twsecrets: " + str(exc1))
        traceback.print_exc()
        return None

def validate_token(token,client_id=None):
    validateRequest = requests.get('https://id.twitch.tv/oauth2/validate', headers = {'Client-ID' : client_id,  'Authorization' : 'OAuth ' +token})
    validToken = 0

    print(f'validate_token(): response {validateRequest.status_code} {validateRequest.text}')
    if validateRequest.status_code == 200 :
        return 1
    return 0

def new_db_token(authorizationcode, tokenkey, refreshtokenkey, clientidkey='client_id', clientsecretkey='client_secret'):
    token = get_token_secrets(onekey=tokenkey)
    refreshtoken = get_token_secrets(onekey=refreshtokenkey)
    client_id = get_token_secrets(onekey=clientidkey)
    client_secret = get_token_secrets(onekey=clientsecretkey)
    #
    tokenRequestBody = {
                'client_id' : client_id,
                'client_secret': client_secret,
                'code': authorizationcode,
                'grant_type': 'authorization_code',
                'redirect_uri': 'http://localhost'
                }
    tokenRequest = requests.post('https://id.twitch.tv/oauth2/token', params=tokenRequestBody)
                #?client_id=' + client_id +'&client_secret=' + client_secret + '&grant_type=client_credentials')
    print(f'tokenRequest.status_code={tokenRequest.status_code} | {tokenRequest.text}')
    if tokenRequest.status_code == 200:
            j = json.loads(tokenRequest.text)
            newtoken = j["access_token"]
            newfreshtoken = j["refresh_token"]
            secrets = get_token_secrets()
            secrets[tokenkey]=newtoken
            secrets[refreshtokenkey]=newfreshtoken
            save_token_secrets(secrets)
    pass




def check_db_token(tokenkey, refreshtokenkey, clientidkey='client_id', clientsecretkey='client_secret'):
    """
    Checks if the token named 'tokenkey' in the secrets storage is still valid, and if not, then attempt to Refresh the token.

    Inputs:

    tokenkey - The database key name for the token to be checked
    refreshtokenkey - The database key that the refresh token is stored at

    Optional:
    clientidkey - The database key the client_id is stored at
    clientsecretkey - The database key the client_secret is stored at
    """
    token = get_token_secrets(onekey=tokenkey)
    refreshtoken = get_token_secrets(onekey=refreshtokenkey)
    client_id = get_token_secrets(onekey=clientidkey)
    client_secret = get_token_secrets(onekey=clientsecretkey)
    #
    validateRequest = requests.get('https://id.twitch.tv/oauth2/validate', headers = {'Client-ID' : client_id,  'Authorization' : 'OAuth ' +token})
    validToken = 0
    if validateRequest.status_code == 200 :
        validToken = 1
    if validToken == 0 :
        #tokenRequest = requests.post('https://id.twitch.tv/oauth2/token?client_id=' + client_id +'&client_secret=' + client_secret + '&grant_type=client_credentials')
        tokenRequestBody = {
                'client_id' : client_id,
                'client_secret': client_secret,
                'grant_type': 'refresh_token',
                'refresh_token': refreshtoken # urllib.parse.quote(refreshtoken)
                }
        tokenRequest = requests.post('https://id.twitch.tv/oauth2/token', params=tokenRequestBody)
                #?client_id=' + client_id +'&client_secret=' + client_secret + '&grant_type=client_credentials')
        if tokenRequest.status_code == 200:
            j = json.loads(tokenRequest.text)
            newtoken = j["access_token"]
            newfreshtoken = j["refresh_token"]
            secrets = get_token_secrets()
            secrets[tokenkey]=newtoken
            secrets[refreshtokenkey]=newfreshtoken
            save_token_secrets(secrets)
    pass


def get_tokens(filename=None,frnkeyd=None,storename=''):
    """
    Retrieve primary Twitch credentials from secrets storage Including the App token

    Attempts to automatically refresh  app_token if expired or invalid.

    Returns an array containing   [ client_id, client_secret, app_token ]
    """
    if frnkeyd == None and f'TXDKEYZ0{storename}' in os.environ:
        frnkeyd = os.environ[f'TXDKEYZ0{storename}']
    if filename == None and  not(f'TWSECFILE{storename}' in os.environ):
        raise Exception("TW Secrets path unspecified")
    if filename == None:
        filename = os.environ[f'TWSECFILE{storename}']
    else:
        filename = str(filename)

    frnkey = None
    if frnkeyd:
        frnkey = Fernet(frnkeyd)

    client_id=""
    client_secret=""
    app_token=""
    try:
        dict = get_token_secrets(filename,frnkeyd)
        client_id = dict['client_id']
        client_secret = dict['client_secret']
        app_token = dict['app_token']
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
            original_umask = os.umask(0o077)

            try:
                with open(str(filename) + ".new", 'w') as soutfile:
                    buffer = ''
                    for ik in dict.keys():
                        if  ik in ['client_id', 'client_secret', 'app_token']:
                            continue
                        buffer = buffer + base64.urlsafe_b64encode( ik ) + "\n"
                        buffer = buffer + base64.urlsafe_b64encode( dict[ik] ) + "\n"
                    soutfile.write(str(frnkey.encrypt(bytes(client_id + "\n" + client_secret + "\n" + app_token + "\n" + buffer, 'utf8'))))
                os.umask(original_umask)
                os.rename(str(filename) + ".new", filename)
            finally:
                os.umask(original_umask)
    return [client_id, client_secret, app_token]


# REQUEST CREDENTIALS 
# https://id.twitch.tv/oauth2/authorize?client_id=%%CID%%&response_type=code&state=%%STATEHASH%%&redirect_uri=http://localhost&scope=channel%3Abot+user%3Abot+chat%3Aread+user%3Aread%3Achat+channel%3Amoderate+channel%3Aread%3Aredemptions

def mktoken_url_pubsub(client_id):
    data = bytes(32) + bytes(str(get_tokens_secrets(onekey='client_secret')),'utf8') +  bytes(str(time.time()),'utf8') + bytes(32)
    statehash= xsha224_patched = hashlib.sha224(data).hexdigest()
    data = None
    url=f'https://id.twitch.tv/oauth2/authorize?client_id={client_id}&response_type=code&state={statehash}&redirect_uri=http://localhost&scope=channel%3Abot+user%3Abot+chat%3Aread+user%3Aread%3Achat+channel%3Amoderate+channel%3Aread%3Aredemptions'
    print(url)

def mktoken_url_bottoken(client_id=None):
    if not(client_id):
        client_id = get_token_secrets(onekey='client_id')
    data = bytes(32) + bytes(str(get_tokens_secrets(onekey='client_secret')),'utf8') +  bytes(str(time.time()),'utf8') + bytes(32)
    statehash= xsha224_patched = hashlib.sha224(data).hexdigest()
    data = None
    scope_list = '+'.join(map(lambda g: urllib.parse.quote(g), [
        'moderation:read',
        'moderator:manage:announcements',
        'moderator:read:automod_settings',
        'moderator:manage:banned_users',
        'moderator:manage:chat_messages',
        'moderator:read:chatters',
        'moderator:read:followers',
        'moderator:read:guest_star',
        'moderator:read:shield_mode',
        'moderator:manage:shield_mode',
        'moderator:read:shoutouts',
        'user:read:follows',
        'channel:bot',
        'channel:moderate',
        'chat:edit',
        'chat:read',
        'user:bot',
        'user:read:chat'
        ]))
    scope_list_e = scope_list # urllib.parse.quote(scope_list)
    url=f'https://id.twitch.tv/oauth2/authorize?client_id={client_id}&response_type=code&state={statehash}&redirect_uri=http://localhost&scope={scope_list_e}'
    print(url)







