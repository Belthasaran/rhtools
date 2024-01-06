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

class SnesLink(py2snes.snes):
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        ####
        super().__init__(cls._instance)
        ####
        return cls._instance

    def __init__(self, *args, **kwargs):
        pass



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
    #rambase = 0x85
    rambase = 0xF5
    #code.interact(local=locals())
    IPython.embed(using='asyncio')
    return snes

if __name__ == '__main__':
    asyncio.run(runsnes())





