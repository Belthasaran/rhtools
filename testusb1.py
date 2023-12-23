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

    # 0x7E1DF9 - 1DFC values
    _1dfcvalues = {
            'nothing' : b'\x00',
            'coin' : b'\x01',
            'hitblock': b'\x02',
            'vineblock': b'\x03',
            'spinjump': b'\x04',
            '1up': b'\x05',
            'fireball': b'\x06',
            'breakblock' : b'\x07',
            'springboard': b'\x08',
            'boom': b'\x09',  # b.bill / thwomp landing
            'egghatch': b'\x0a',
            'itembox': b'\x0b',
            'itemfalls': b'\x0c',
            'sameas0xc': b'\x0d',
            'screenscroll': b'\x0e',
            'door': b'\x0f',
            #x10 same as x09
            'drumroll': b'\x11', #(looped)
            'drumrollend': b'\x12',
            'loseyoshi': b'\x13',
            #x14 unused
             'tilerevealed': b'\x15',
             'castlecollapsed': b'\x16',
             'firespit': b'\x17',
             'thunder': b'\x18',
             'chuck_clap': b'\x19',
             'castle_destruction_b': b'\x1a',
             'castle_destruction_fuse': b'\x1b',
             'ow_palace_stomp': b'\x1c',
             'timerunningout': b'\x1d', # Running out of time (combine with the one in $1DF9, does not speed up tempo)
             'chuck_whistle' : b'\x1e',
             'yoshi_mount': b'\x1f',
             'koopaling_lands_in_lava': b'\x20',
             'yoshi_tongue': b'\x21',
             'messagebox': b'\x22',
             'ow_mariomove' : b'\x23',  # Mario moves onto level tile
             'pswitch_timeout': b'\x24', #p-switch time running out
             'yoshi_stomp': b'\x25',
             'swooper': b'\x26',
             'podoboo': b'\x27',
             'enemy_stunned': b'\x28',
             'correct': b'\x29',
             'wrong': b'\x2a',
             'firework_whistle': b'\x2b',
             'firework_bang': b'\x2c',
             'podoboo-m100' : b'\x2d',
             'podoboo-m71' : b'\x2e',
             'podoboo-m43' : b'\x2f',
             'podoboo-m14' : b'\x30',
             'podoboo-p14' : b'\x31',
             'podoboo-p43' : b'\x32',
             'podoboo-p71' : b'\x33',
             'podoboo-p100' : b'\x34'
              #35+	Mirror of $1DF9's sound effects, starting at the "Hit head" SFX
            }

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
    async def starpower(self): #x7e -> xff
         await self.PutAddress([ ( 0xF51490, b'\xff' ) ])
    async def lives99(self):
         await self.PutAddress([ ( 0xF50DBE, b'\x62' ) ])
    async def coins99(self):
         await self.PutAddress( [ (0xF50DBF, b'\x62' ) ])
    async def blueswitch(self, value=b'\xb0'):  #\x7e
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
         evnum =  await self.GetAddresss( 0xF51F2E, 1 )
         return evnum

    async def gettime(self):
        hundreds = await self.GetAddress(0xF50F31, 1)
        tens = await self.GetAddress(0xF50F32, 1)
        ones = await self.GetAddress(0xF50F33, 1)
        curtime = hundreds[0] * 100  + tens[0] * 10 + ones[0]
        return int(curtime)

    async def settime(self,seconds):
         curtime = seconds
         hundreds = int(curtime / 100)
         tens = int((int(curtime) - hundreds*100)/10)
         ones = (int(curtime) - hundreds*100 - tens*10)  % 10
         await self.PutAddress([ (0xF50F31, bytes([hundreds]) ),
                                 (0xF50F32, bytes([tens]) ),
                                 (0xF50F33, bytes([ones]) )])

    async def addtime(self,seconds):
         seconds = 0
         hundreds = await self.GetAddress(0xF50F31, 1)
         tens = await self.GetAddress(0xF50F32, 1)
         ones = await self.GetAddress(0xF50F33, 1)
         curtime = hundreds[0] * 100  + tens[0] * 10 + ones[0] 
         curtime = curtime + seconds
         hundreds = int(curtime / 100) 
         tens = int((int(curtime) - hundreds*100)/10)
         ones = (int(curtime) - hundreds*100 - tens*10)  % 10
         await self.PutAddress([ (0xF50F31, bytes([hundreds]) ),
                                 (0xF50F32, bytes([tens]) ),
                                 (0xF50F33, bytes([ones]) )])



         await self.PutAddress([  (0xF50F31, b"\x09") ])

    #c.vanilla addresses# found to work
    async def c_invertcontrols(self, value=b'\x02'): 
         # x01 invert dpand
         # x02 invert buttons
         # x04 dpad and buttons mixed up
        await self.PutAddress( [ (0xF61980, value) ] )

    async def c_magicsound(self, value=b'\x00'):
        await self.PutAddress( [(0xF51DF9, b'\x10')] )

    async def c_resetgame(self, value=b'\x00'):
        await self.PutAddress( [(0xF50100, value)] )
    async def c_exitlevel(self, value=b'\x0b'):
        await self.PutAddress( [(0xF50100, value)] )

    async def c_pixelate(self, value=b'\x02'):
        await self.PutAddress([(0xF60723,b'\x01')])

    async def c_spawnthwomp(self, value=b'\x01'):
        #F60725=>spawns
        await self.PutAddress([(0xF60006, b'\x01'), (0xF60725, b'\x01')])

    async def c_kaizoblock(self, value=b'\x01'):
        await self.PutAddress([(0xF60729,b'\x01')])

    async def c_fishgen(self, value=b'\7'): # \a
        await self.PutAddress( [ (0xF518B9, value) ] )

    async def c_item_empty(self, value=b'\x00'):
        await self.PutAddress( [ (0xF50dc2, value) ] )

    async def c_item_mushroom(self, value=b'\x01'):
        await self.PutAddress( [ (0xF50dc2, value) ] )

    async def c_item_flower(self, value=b'\x02'):
        await self.PutAddress( [ (0xF50dc2, value) ] )

    async def c_item_starman(self, value=b'\x03'):
        await self.PutAddress( [ (0xF50dc2, value) ] )

    async def c_starman(self):
         await self.PutAddress([ ( 0xF51490, b'\xff' ) ])

    async def c_item_capefeather(self, value=b'\x04'):
        await self.PutAddress( [ (0xF50dc2, value) ] )

    async def c_item_blueyoshi(self, value=b'\xc2'): #(0xf50dc2, b'\xc2')
        await self.PutAddress( [ (0xF50dc2, value) ] )

    async def sfx_mountyoshi(self, value=b'\x1f'):
        await self.PutAddress( [ (0xF51DFC, value)])

    async def c_blueswitch(self, value=b'\xb0', value2='\x0e'):
         await self.PutAddress( [ (0xF514AD, value), (0xF51DFB, value2) ] )

    async def c_silverswitch(self, value=b'\xb0', value2='\x0e'):
             # F60728 => turns enemies into coins on x01
         await self.PutAddress( [ (0xF514AE, value), (0xF51DFB, value2), (0xF60728, b'\x01') ] )


    async def c_bulletbillgen(self, value=b'\x0b', value2=b'\x09'):  # Set F51889 to 0x0b
        await self.PutAddress( [ (0xF518B9, value), (0xF51DFC, value2) ] )

    async def c_addlives(self, value=b'\x01', value2=b'\x05'):       # To increment lives gradually by n,  set 0xF518E4 to n
        await self.PutAddress( [ (0xF518E4, value), (0xF51DFC, value2) ] )

    async def c_5up(self, value=b'\x03', value2=b'\x05'):
        await self.PutAddress( [ (0xF518E4, value), (0xF51DFC, value2) ] )

    async def c_5up(self, value=b'\x05', value2=b'\x05'):
        await self.PutAddress( [ (0xF518E4, value), (0xF51DFC, value2) ] )

    async def c_lippery(self, value=b'\x01'):
         await self.PutAddress( [ (0xF50086, value) ] )

    async def c_water(self, value=b'\1'):
        await self.PutAddress( [ (0xF50085, value) ] )

    async def c_disappearing(self, value=b'\1'):
        await self.PutAddress( [ (0xF60000, value) ] )

    async def c_munchers( self, value=b'\1'):
        await self.PutAddress( [ (0xF60003, value) ] )

    async def c_duplicating(self, value=b'\1'):
        await self.PutAddress( [ (0xF60002, value) ])

    async def c_window(self, value=b'\1'):
        await self.PutAddress( [ (0xF60004, value) ] )
 
    # (0xf61981, b'\x06')
    # (0xf50dc2, b'\xc2'), (0xf51dfc, b'\x1f')
    # write 1f to 0xf51dfc

    # (0xf61981, b'\x04')
    # (0xF50DC2, b'\xc2')
    # (0xF51DFC, b'\x1f') 

    async def c_yellow_yoshi(self):
        await self.PutAddress( [(0xf61981, b'\x04'), (0xF50DC2, b'\xc2'), (0xF51DFC, b'\x1f') ])

    async def c_speed(self, value=b'\1'): # bx01 activates
        await self.PutAddress( [ (0xF60001, value) ] )

    async def sfx_item_reservebox(self, value=b'\x0b'): # c_1dfc_write0b
        await self.PutAddress( [ (0xF51DFC, value) ] )

    async def c_stickyfloor(self, value=b'\1'):
        await self.PutAddress( [ (0xF60005, value) ] )

    async def sfx_springboard(self, value=b'\x08'):
        await self.PutAddress( [ (0xF51DFC, value) ])

    async def c_balloon(self, value=b'\1'):
        await self.PutAddress( [ (0xF60007, value) ] )

    async def inlevel(self):
        run_game = ((await self.GetAddress(0xF50010,1)) == b'\x00')
        game_unpaused = (await self.GetAddress(0xF513D4,1)) == b'\x00'
        noanimation = (await self.GetAddress(0xF50071,1)) == b'\x00'
        no_endlevel_keyhole = (await self.GetAddress(0xF51434,1)) == b'\x00'
        no_endlevel_timer = (await self.GetAddress(0xF51493,1)) == b'\x00'
        normal_level = (await self.GetAddress(0xF50D9B,1)) == b'\x00'
        return run_game and game_unpaused and noanimation and no_endlevel_keyhole and no_endlevel_timer and normal_level

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





