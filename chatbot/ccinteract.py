#!/usr/bin/python

import sys
import os
import requests
import apptoken
import platform
import urllib.parse
import re
import json
import random
import time
import logging

class CrowdInteract():
    """
    Attempts to interact with Crowd Control website to create self-imposed effects.

    Pre-requisites:
       Have the crowd control app setup and working.

       Have an active crowd control Pro subscription first, or it probably won't work.
       (The anonymous effects, & other aspects of this script,
       I believe require this.)

       Be  logged in to their website through your interact link.

       Have a game session already active, that you are the owner of (Start session in the app)

    Other pre-requisites:
       You'll need to extract secrets from your web browser.
       And store these values in your secrets storage:

       ccuid
       cc_auth_token

       Presuming you already ran cmd_addtoken.py SETUP
       to create encrypted secrets storage, and set the
       environment variables in your session:

       # python3 cmd_addtoken.py
       Enter key string:ccuid
       Enter vlaue string:(ENTER VALUE HERE)

       # python3 cmd_addtoken.py
       Enter key string:cc-auth-token
       Enter vlaue string:(ENTER VALUE HERE)

    """
    def __init__(self,logger=None):
        self.logger = logger
        if not(logger):
            self.logger = logging.getLogger("ccinteract.py")

    def getRequestHeaders(self, cc_auth_token):
        headers = {
                'authority': 'trpc.crowdcontrol.live',
                'accept': '*/*',
                'accept-language': 'en',
                'authorization' : f'{cc_auth_token}',
                'origin' : 'https://interact.crowdcontrol.live',
                'pragma' : 'no-cache',
                'user-agent' : f'ccinteracct/0.01 ({platform.platform()}; Python/{platform.python_version()})'
                }
        return headers
    def getSessionInfo(self):
        cc_auth_token = apptoken.get_token_secrets(onekey='cc-auth-token')
        ccuid_raw = apptoken.get_token_secrets(onekey='ccuid')
        ccuid_urlencoded = urllib.parse.quote(ccuid_raw)
        url = 'https://trpc.crowdcontrol.live/gameSession.getUsersActiveGameSession?' + \
              f'input=%7B%22ccUID%22%3A%22{ccuid_urlencoded}%22%7D'
        response = requests.get(url, None, headers = self.getRequestHeaders(cc_auth_token))
        if response.status_code == 200:
                         self.logger.info('getSessionInfo - 200 OK Response')
                         #print(f'Content = {response.content}')
                         try:
                             sessionInfo = json.loads(response.content)['result']['data']['session']

                             # Make sure our query result is a session that the current ccUID owns, etc
                             if (sessionInfo and len(sessionInfo['owner']['subscriptions']) > 0 and
                                     sessionInfo['owner']['ccUID'] == sessionInfo['ccUID'] and 
                                     ccuid_raw == sessionInfo['owner']['ccUID']):
                                 return sessionInfo
                             else:
                                 self.logger.error(f'ccinteract: Sorry, could not find a game session')
                                 return None
                         except Exception as xerr:
                             self.logger.error(f'ccinteract: Sorry, could not find active game session')
                             return None
        else:
            self.logger.error(f'ccinteract:getSessionInfo fail status={response.status_code} {response.text}')
            return None
    def getSessionMenu(self, game_session_id):
        cc_auth_token = apptoken.get_token_secrets(onekey='cc-auth-token')
        ccuid_raw = apptoken.get_token_secrets(onekey='ccuid')
        ccuid_urlencoded = urllib.parse.quote(ccuid_raw)
        game_session_id_urlencoded = urllib.parse.quote(game_session_id)

        url = 'https://trpc.crowdcontrol.live/gameSession.getGameSessionMenu?' + \
                f'input=%7B%22gameSessionID%22%3A%22{game_session_id_urlencoded}%22%7D'
        response = requests.get(url, None, headers = self.getRequestHeaders(cc_auth_token))
        if response.status_code == 200:
            self.logger.info('ccinteract:getSessionInfo success')
            #self.logger.debug(f'cci:getSessionInfo:Content = {response.content}')
            return json.loads(response.content)['result']['data']['menu']
        else:
            self.logger.error(f'ccinteract:getSessionInfo fail status={response.status_code} {response.text}')
            return None

    def requestEffect(self,game_session_id, effectObject, effectQuantity=1):
        cc_auth_token = apptoken.get_token_secrets(onekey='cc-auth-token')
        ccuid_raw = apptoken.get_token_secrets(onekey='ccuid')
        ccuid_urlencoded = urllib.parse.quote(ccuid_raw)
        game_session_id_urlencoded = urllib.parse.quote(game_session_id)

        if not('quantity' in effectObject):
            effectQuantity = 1
        else:
            if 'min' in effectObject['quantity'] and effectQuantity < effectObject['quantity']['min']:
                effectQuantity = effectObject['quantity']['min']
            if 'max' in effectObject['quantity'] and effectQuantity > effectObject['quantity']['max']:
                effectQuantity = effectObject['quantity']['max']
        
        url = 'https://trpc.crowdcontrol.live/gameSession.requestEffect'
        requestObject = {
                'gameSessionID' : game_session_id,
                'effectType' :  effectObject['type'],
                'effectID'   :  effectObject['effectID'],
                'price'      :  effectObject['price'],
                'quantity'   :  effectQuantity,
                'anonymous'  :  True
                }
        response = requests.post(url, 
                json = requestObject, 
                headers = self.getRequestHeaders(cc_auth_token))
        if response.status_code == 200:
            self.logger.info('ccinteract:requestEffect success')
            self.logger.debug(f'reqEff:Content = {response.content}')
            return json.loads(response.content)['result']['data']['effectRequest']
        else:
            self.logger.error(f'ccinteract:requestEffect fail status={response.status_code} {response.text}')
            return None

    #
    def poolToEffect(self,game_session_id, effectObject, effectQuantity=1, amountValue=1):
        cc_auth_token = apptoken.get_token_secrets(onekey='cc-auth-token')
        ccuid_raw = apptoken.get_token_secrets(onekey='ccuid')
        ccuid_urlencoded = urllib.parse.quote(ccuid_raw)
        game_session_id_urlencoded = urllib.parse.quote(game_session_id)

        if not('quantity' in effectObject):
            effectQuantity = 1
        else:
            if 'min' in effectObject['quantity'] and effectQuantity < effectObject['quantity']['min']:
                effectQuantity = effectObject['quantity']['min']
            if 'max' in effectObject['quantity'] and effectQuantity > effectObject['quantity']['max']:
                effectQuantity = effectObject['quantity']['max']

        #url = 'https://trpc.crowdcontrol.live/gameSession.requestEffect'
        url = 'https://trpc.crowdcontrol.live/gameSession.contributeToPool'
        requestObject = {
                'gameSessionID' : game_session_id,
                'effectType' :  effectObject['type'],
                'effectID'   :  effectObject['effectID'],
                'amount'     :  amountValue,
                'anonymous'  :  True
                }
        self.logger.debug(f'ccI:contributeToPool: {json.dump(requestObject)}')
        response = requests.post(url,
                json = requestObject,
                headers = self.getRequestHeaders(cc_auth_token))
        if response.status_code == 200:
            self.logger.info('ccinteract:getSessionInfo success')
            self.logger.debug(f'poolToEff:Content = {response.content}')
            return json.loads(response.content)['result']['data']['effectRequest']
        else:
            self.logger.error(f'ccinteract:getSessionInfo fail status={response.status_code} {response.text}')
            return None




#
#  Query the session and attempt to request a randomized affect -> 
#

def crowd_interact_cmd(args):
    time.sleep(10)

    interact = CrowdInteract()
    sessionInfo = interact.getSessionInfo()
    print('SESSION: ' + json.dumps(interact.getSessionInfo(), indent=4))

    # Get the affect menu from the active session
    game_session_id = sessionInfo["gameSessionID"]
    menuinfo = interact.getSessionMenu(game_session_id)
    print('GAME MENU: ' + json.dumps(menuinfo, indent=4))
    
    # set availableEffects to  the list of available affects minus the ones with 'inactive' true
    availableEffects = list(filter(lambda g: not('inactive' in g) or not(g['inactive']), menuinfo['effects']))

    # Shuffle the list randomly and request the first affect.
    random.shuffle(availableEffects)
    print('REQUESTEFFECT ' + json.dumps(availableEffects[0]))
    interact.requestEffect(game_session_id, availableEffects[0], 1)
    time.sleep(3)

if __name__ == '__main__':
    crowd_interact_cmd(sys.argv)



