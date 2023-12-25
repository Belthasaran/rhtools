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

import IPython
import nest_asyncio
import pdb
nest_asyncio.apply()
#IPython.embed()

class SmwEffectRunner(py2snes.snes):
    def SmwEffectRunner():
        self.is_running = 0
        self.time_left = 0
        self.name = "Generic Effect"
        smw.game = "SuperMarioWorld"
        smw.description = "Unspecified"
        smw.effectID = "smwGenericEffect"

    async def run(self,amount=1,duration=0):
       i = 60
       while (await self.ready(amount,duration)) == False and i > 1:
           print(f"Not ready, Retry    {i}")
           i = i - 1
           time.sleep(0.25)
       pass
       await self.initiate(amount,duration)
       self.is_running = 1
       self.time_left = duration
       while self.time_left > 0 :
           await self.tick(amount,duration,0.5)
           asyncio.sleep(0.5)
       await self.finalize(amount,duration)

    async def ready(self,amount,duration):
        return await self.inlevel()

    async def initiate(self,amount,duration):
        # Start the action
        pass

    async def refresh(self,amount,duration):
        # Refresh
        pass

    async def finalize(self,amount,duration):
        self.is_running = 0
        # Cleanup actions
        pass

    async def tick(self,amount,duration,tick_interval=0.5):
        if self.time_left > 1 :
            asyncio.sleep(tick_interval)
            self.time_left = self.time_left - tick_interval
        if self.time_left >= 0:
            await self.refresh(amount,duration)
        # Refresh status
        pass

    async def c_item_empty(self, value=b'\x00'):
        await self.PutAddress( [ (0xF50dc2, value) ] )

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



async def smw_gen_effect_runner(args):
    ohash = loadsmwrh.get_local_options()
    print(f"snes_xmario: {ohash}")

    #snes = py2snes.snes()
    snes = SmwEffectRunner()
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
    asyncio.run(smw_gen_effect_runner(sys.argv))





