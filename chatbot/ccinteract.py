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

class CrowdInteract():
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
                         print('getSessionInfo success')
                         print(f'Content = {response.content}')
                         return json.loads(response.content)['result']['data']['session']
        else:
            print(f'getSessionInfo fail status={response.status_code} {response.text}')
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
                         print('getSessionInfo success')
                         print(f'Content = {response.content}')
                         return json.loads(response.content)['result']['data']['menu']
        else:
            print(f'getSessionInfo fail status={response.status_code} {response.text}')
            return None

    def requestEffect(self,game_session_id, effectObject, effectQuantity=1):
        cc_auth_token = apptoken.get_token_secrets(onekey='cc-auth-token')
        ccuid_raw = apptoken.get_token_secrets(onekey='ccuid')
        ccuid_urlencoded = urllib.parse.quote(ccuid_raw)
        game_session_id_urlencoded = urllib.parse.quote(game_session_id)

        if not('quantity' in effectObject):
            effectQuantity = 1
        else:
            if 'min' in effectObect['quantity'] and effectQuantity < effectObject['quantity']['min']:
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
                         print('getSessionInfo success')
                         print(f'Content = {response.content}')
                         return json.loads(response.content)['result']['data']['effectRequest']
        else:
            print(f'getSessionInfo fail status={response.status_code} {response.text}')
            return None

#
#  Query the session and attempt to request a randomized affect -> 
#

def crowd_interact_cmd(args):
    time.sleep(10)
    interact = CrowdInteract()
    sessionInfo = interact.getSessionInfo()
    print('SESSION: ' + json.dumps(interact.getSessionInfo(), indent=4))
    game_session_id = sessionInfo["gameSessionID"]
    menuinfo = interact.getSessionMenu(game_session_id)
    print('GAME MENU: ' + json.dumps(menuinfo, indent=4))
    availableEffects = list(filter(lambda g: not('inactive' in g) or not(g['inactive']), menuinfo['effects']))

    random.shuffle(availableEffects)
    print('REQUESTEFFECT ' + json.dumps(availableEffects[0]))
    interact.requestEffect(game_session_id, availableEffects[0], 1)
    time.sleep(3)

if __name__ == '__main__':
    crowd_interact_cmd(sys.argv)



