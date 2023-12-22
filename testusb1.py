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
    powerupstate = 0xF50019
    powerupvalues = { 'fire' : b'\x03', 'cape': b'\x02', 'super': b'\x01', 'normal': b'\x00'  }

    itemboxvalues = { 'super' : b'\x01', 'fire' : b'\x02', 'star' : b'\x03', 'cape': b'\x04',
                      'blueyoshi': b'\x05',  'grayyoshi': b'\x06', 'orb': b'\xd7'  }

    switchpalaceflags_addr = { 'green' : 0x1F27,  'yellow' : 0x1F28,  'blue' : 0x1F29, 'red': 0x1F2A }    
    switchpalaceflags_values = { 'off' : 0x00,  'on' : 0x01 }
    async def setswitchpalace(self, name, value = b'\x01' ):
        addr = switchpalaceflags_addr[name + 0xF50000]
        await self.PutAddress( [  (addr, value) ] )

    async def setspring(self):
       await self.PutAddress( [ (0xF51EEB, 0) ] )
    async def setautumn(self):
       await self.PutAddress( [ (0xF51EEB, 0) ] )

    async def setgamemode(self, value) :
       # 0=reset b=ow f=enter level
       await self.PutAddress( [ (0xF50100, value) ])

    async def setleveloverride(self, value=b'\x03'):
       await self.PutAddress( [ (0xF50109, value)] )

    async def groundshake(self, value=b'\x70'):
       await self.PutAddress( [ (0xF51887, value) ] )

    async def give3up(self, value=b'\x03'):
       await self.PutAddress( [ (0xF5e18e4, value) ] )

    async def morton(self):
        b1 = 0xF50000
        await self.PutAddress( [ (b1 + 0x1F11, b'\x00'), 
                                 (b1 + 0x1f17, b'\xd8'), 
                                 (b1 + 0x1f18, b'\x00'),
                                 (b1 + 0x1f19, b'\xc8'), 
                                 (b1 + 0x1f1a, b'\x00'),
                                 (b1 + 0x0100, b'\x0b') ]  )
    async def setbrightness(self, value=b'\x0f') :
         b1 =0xF50000
         await self.PutAddress([ (b1 + 0x0dae, value) ])

    async def saveprompt(self,value=b'\x01'):
        await self.PutAddress( [ (0xF513CA, value) ] )
    async def moretime(self):
         await self.PutAddress([  (0xF50F31, b"\x09") ])
    async def powerdown(self):
         await self.PutAddress([ ( 0xF50019, b'\x00' ) ])
    async def setpowerup(self, value=b'\x01'):
         await self.PutAddress([ ( 0xF50019, value ) ])
    async def firepower(self):
         await self.PutAddress([ ( 0xF50019, b'\x03' ) ])
    async def capepower(self):
         await self.PutAddress([ ( 0xF50019, b'\x02' ) ])
    async def starpower(self):
         await self.PutAddress([ ( 0xF51490, b'\x7e' ) ])
    async def lives99(self):
         await self.PutAddress([ ( 0xF50DBE, b'\x62' ) ])
    async def coins99(self):
         await self.PutAddress( [ (0xF50DBF, b'\x62' ) ])
    async def blueswitch(self, value=b'\x7e'):
         await self.PutAddress( [ (0xF514AD, value) ] )
    async def silverswitch(self, value=b'\x7e'):
         await self.PutAddress( [ (0xF514AE, value) ] )
    async def setitembox(self, value=b'\x00' ):
         await self.PutAddress( [ (0xF50DC2, value) ] )
    async def setwater(self, value=b'\x01'):
         await self.PutAddress( [ (0xF50085, value) ] )
    async def setslippery(self, value=b'\x01'):
         await self.PutAddress( [ (0xF50086, value) ] )
    async def setpballoon(self):
         await self.PutAddress( [ (0xF5009e,b'\x8D'), 
              (0xF514C8, b'\x0B'), (0xF513F3,b'\x09'),
              (0xF5167A, b'\x9A'), (0xF51686,b'\x29'),
              (0xF51DF9, b'\x1e') ] )

    async def setkeyhole(self, value=b'\x01'):
         await self.PutAddress( [ (0xF51434, value) ] )
    async def setendlevel(self, value=b'\xFF'):  # Set to FF or 28?
         await self.PutAddress( [ (0xF51493, value) ] )
    async def setonoff(self, value=b'\x01'):
         await self.PutAddress( [ (0xF514AF, value) ] )

    async def setnumevents(self, value):
         await self.PutAddress( [ (0xF51F2E, value)] )
    async def getnumevents(self):
         await self.GetAddresss( 0xF51F2E, 1 )

    #c.vanilla addresses#
    async def c_idpad(self, value=b'\1'):
        await self.PutAddresS( [ (0xF61980, value) ] )

    async def c_water(self, value=b'\1'):
        await self.PutAddress( [ (0xF50085, value) ] )

    async def c_disappearing(self, value=b'\1'):
        await self.PutAddress( [ (0xF60000, value) ] )

    async def c_munchers( self, value=b'\1'):
        await self.PutAddress( [ (0xF60003, value) ] )

    async def c_duplicating(self, value=b'\1'):
        await self.PutAddress( [ (0xF60002, value) ])

    async def c_window(self, value=b'\1'):
        await self.PutAddress( [ 0xF60004, value) ] )

    async def c_speed(self, value=b'\1'):
        await self.PutAddress( [ (0xF60001, value) ] )

    async def c_sticky(self, value=b'\1'):
        await self.PutAddress( [ (0xF60005, value) ] )

    async def c_balloon(self, value=b'\1'):
        await self.PutAddress( [ (0xF60007, value) ] )

    async def inlevel(self):
        game_unpaused = (await snes.GetAddress(0xF513D4,1)) == b'\x00'
        noanimation = (await snes.GetAddress(0xF50071,1)) == b'\x00'
        no_endlevel_keyhole = (await snes.GetAddress(0xF51434,1)) == b'\x00'
        no_endlevel_timer = (await snes.GetAddress(0xF51493,1)) == b'\x00'
        normal_level = (await snes.GetAddress(0xF50D9B,1)) == b'\x00'
        return game_unpaused and noanimation and no_endlevel_keyhole and no_endlevel_timer and normal_level

     #14AF onoffstatus



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





