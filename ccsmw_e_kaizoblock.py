from zipfile import ZipFile
import re
import hashlib
import base64
import os
import json
import sys
import loadsmwrh
from py2snes import py2snes
import asyncio
import time
import code
import random

import IPython
import nest_asyncio
from smw_e_generic import *
import pdb
nest_asyncio.apply()
#IPython.embed()

class KaizoBlockEffect(SmwEffectRunner):
    #async def run(self,amount=1,duration=0):
    #    self.super.run(amount,duration)
    #async def ready(self):
    #    return await self.inlevel()
    def __init__(self,amount=1,duration=20,retries=300,tick_interval=2):
        super().__init__(amount,duration,retries,tick_interval)
        # Timed-effect: Little Mario
        #   For the duration of affect: Mario shrinks and continuously loses
        #   any mushroom, cape, or flower status.
        self.name = "Make Kaizo Blocks (x10)"
        self.game = "SuperMarioWorld"
        self.description = "Make kaizo blocks"
        self.effectId = "makeKaizos"
    async def ready(self):    # ready(): Effect pre-requisites
        return await self.inlevel()
    async def isactive(self): # isactive(): Pause countdown if game is paused or player no longer in a level.
        return await self.inlevel()
    async def initiate(self):  # initiate() -> Initially apply affect
        print(f'KaizoBlockEffect.Initiate({self._amount},{self._duration})')
        await self.PutAddress([(0xF60729,b'\x01')])
    async def refresh(self):   # refresh() -> Actions to repeat every tick to preserve effect
        waitValue = random.randint(0,10)/10
        await asyncio.sleep(waitValue)
        print('KaizoBlockEffect.refresh time_left='+str(self.time_left))
        if await self.inlevel():
            await self.PutAddress([(0xF60729,b'\x01')])
        pass
    async def finalize(self):   # finalize() -> Actions to take to remove effect
        # This affect ends on its own when refresh() is no longer called every tick
        pass

    async def settime(self,seconds):
         curtime = seconds
         hundreds = int(curtime / 100)
         tens = int((int(curtime) - hundreds*100)/10)
         ones = (int(curtime) - hundreds*100 - tens*10)  % 10
         await self.PutAddress([ (0xF50F31, bytes([hundreds]) ),
                                 (0xF50F32, bytes([tens]) ),
                                 (0xF50F33, bytes([ones]) )])

    async def inlevel(self):
        run_game = ((await self.GetAddress(0xF50010,1)) == b'\x00')
        game_unpaused = (await self.GetAddress(0xF513D4,1)) == b'\x00'
        noanimation = (await self.GetAddress(0xF50071,1)) == b'\x00'
        no_endlevel_keyhole = (await self.GetAddress(0xF51434,1)) == b'\x00'
        no_endlevel_timer = (await self.GetAddress(0xF51493,1)) == b'\x00'
        normal_level = (await self.GetAddress(0xF50D9B,1)) == b'\x00'
        return run_game and game_unpaused and noanimation and no_endlevel_keyhole and no_endlevel_timer and normal_level



async def effect_runner(args):
    ohash = loadsmwrh.get_local_options()
    print(f"snes_xmario: {ohash}")

    #snes = py2snes.snes()
    snes = KaizoBlockEffect()
    await snes.connect(address=ohash['wsaddress']) # ws://hostname:8080
    devices = await snes.DeviceList()
    print('Devices =' + str(devices))
    print('Attaching')
    await snes.Attach(devices[0])
    print('Attach done')
    print('usb2snes information:')
    print(await snes.Info())
    #image = args[1]
    result = await snes.run()
    print('Result = ' + str(result))
    return snes

if __name__ == '__main__':
    asyncio.run(effect_runner(sys.argv))




