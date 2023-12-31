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

class mysnes(py2snes.snes):
    async def a_endmario(self):
        i = 60
        while (await self.inlevel()) == False and i > 1:
            print(f"Retry    {i}")
            i = i - 1
            time.sleep(0.25)
        await self.settime(2)
        await self.PutAddress([(0xF50096, b'\xf0')])

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



async def snes_xmario(args):
    ohash = loadsmwrh.get_local_options()
    print(f"snes_xmario: {ohash}")

    #snes = py2snes.snes()
    snes = mysnes()
    await snes.connect(address=ohash['wsaddress']) # ws://hostname:8080
    devices = await snes.DeviceList()
    print('Devices =' + str(devices))
    print('Attaching')
    await snes.Attach(devices[0])
    print('Attach done')
    print('usb2snes information:')
    print(await snes.Info())
    #image = args[1]
    result = await snes.a_endmario()
    print('Result = ' + str(result))
    return snes

if __name__ == '__main__':
    asyncio.run(snes_xmario(sys.argv))





