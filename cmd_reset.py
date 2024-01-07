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
from sneslink import SnesLink

import IPython
import nest_asyncio
import pdb
nest_asyncio.apply()
#IPython.embed()

class mysnes(py2snes.snes):
    pass



async def snes_reset():
    ohash = loadsmwrh.get_local_options()

    #snes = py2snes.snes()
    #snes = mysnes()
    snes = SnesLink()
    await snes.readyup()
    #await snes.connect(address=ohash['wsaddress']) # ws://hostname:8080
    #devices = await snes.DeviceList()
    #print('Devices =' + str(devices))
    #print('Attaching')
    #await snes.Attach(devices[0])
    #print('Attach done')
    #print('usb2snes information:')
    print(await snes.Info())
    await snes.Reset()
    return snes

if __name__ == '__main__':
    asyncio.run(snes_reset())





