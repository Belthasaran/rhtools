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
    async def moretime(self):
         await self.PutAddress([  (0xF50F31, b"\x09") ])
    async def firepower(self):
         await snes.PutAddress([ ( 0xF50019, b'\x03' ) ])
    async def capepower(snes):
         await snes.PutAddress([ ( 0xF50019, b'\x02' ) ])

async def runsnes():
    ohash = loadsmwrh.get_local_options()

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
    ramplus = 0x77
    rambase = 0x85
    #code.interact(local=locals())
    IPython.embed(using='asyncio')
    return snes

if __name__ == '__main__':
    asyncio.run(runsnes())





