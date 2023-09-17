from zipfile import ZipFile
import re
import hashlib
import base64
import os
import json
import sys
import loadsmwrh

def repatch_function(args):
    if not loadsmwrh.path_rerequisites():
        return None

    if os.path.exists("flips"):
       flips_cmd = os.path.join('.','flips')
    elif os.path.exists("flips.exe"):
       flips_cmd = 'flips.exe'
    elif os.path.exists("/mnt/c/snesgaming/bin/flips"):
       flips_cmd = '/mnt/c/snesgaming/bin/flips'
    elif os.path.exists("/usr/local/bin/flips"):
       flips_cmd = 'flips'
    else:
       print('Please put flips or flips.exe and smw.sfc in start directory ' + os.getcwd())
       return None
        

    filename = os.path.join("temp","in.zip")
    
    hackid = (args[1])
    filename = os.path.join("zips", "") + str(hackid) + ".zip"
    
    hackinfo  = loadsmwrh.get_hack_info( str(hackid)  )
    blobinfo  = {}

    if not hackinfo:
        print('Err: Could not load hack metadata for hack #' + str(hackid))
        sys.exit(1)
    #fr = open(os.path.join('hacks', str(hackid) ))
    #hackinfo = json.load(fr)
    #fr.close()
 
    print('Patching Hack#' + str(hackid) + ' name:' + hackinfo["name"] +  '  authors:' + hackinfo["authors"]  )   
    data = loadsmwrh.get_patch_blob( str(hackid), blobinfo  )
    shake1 = (base64.b64encode(hashlib.shake_128(data).digest(24), b"_-")).decode('latin1')
    sha1 = (hashlib.sha1(data).hexdigest())
    xsha224 = hashlib.sha224(data).hexdigest()
    
    f1 = open(os.path.join("temp",  xsha224) + ".new" , "wb")
    f1.write(data)
    f1.close()
    os.replace(os.path.join("temp", xsha224) + ".new", os.path.join("patch", shake1))
    hackinfo["patch"] = os.path.join("patch", shake1)
    if not os.path.exists('smw.sfc'):
        print('Could not find ' + os.path.join(os.getcwd(), 'smw.sfc') + ': SMW Romfile required - Unable to patch')
        return None
    print('')
    print('Running command: '+flips_cmd+' --apply ' + os.path.join('patch', shake1) +"  smw.sfc " + os.path.join('temp', 'result'))
    os.system(flips_cmd+" --apply " + os.path.join('patch', shake1) +"  smw.sfc " + os.path.join('temp', 'result'))
    ##data = bytearray()
    ##with open(os.path.join("temp", "result"), "rb") as patched:
    ##    data += patched.read(1)
    resultf = open(os.path.join("temp", "result"), "rb")
    data = resultf.read()
    resultf.close()
    
    shake1_patched = (base64.b64encode(hashlib.shake_128(data).digest(24), b"_-")).decode('latin1')
    sha1_patched = (hashlib.sha1(data).hexdigest())
    xsha224_patched = hashlib.sha224(data).hexdigest()

    jsonfilename = ''
    
    if re.match('.*repatch.*', args[0]):
        romfilename = hackinfo["id"] + "_" + shake1_patched  + ".sfc"
        jsonfilename = hackinfo["id"] + "_" + shake1_patched  + ".sfcjson"
    else:
        romfilename = hackinfo["id"] + "_" +  str(args[0]) + ".sfc"
        jsonfilename = hackinfo["id"] + "_" +  str(args[0]) + ".sfcjson"

    f0 = open(os.path.join("rom", romfilename) + ".new", "wb")
    f0.write(data)
    f0.close()

    f0 = open(os.path.join("rom", jsonfilename) + ".new", "w")
    f0.write(json.dumps(hackinfo))
    f0.close()
    print('Expected sha224(result) = ' + hackinfo["result_sha224"])
    print('Actual sha224(result) = ' + xsha224_patched)
    if xsha224_patched == hackinfo["result_sha224"]:
        os.replace(os.path.join("rom", romfilename) + ".new", os.path.join("rom", romfilename))
        os.replace(os.path.join("rom", jsonfilename) + ".new", os.path.join("rom", jsonfilename))
    else:
        print('Error: Checksum of patched ROM does not match expected value.   Possible file corruption or incorrect SMW ROM')
    
    hackinfo["pat_sha224"] = xsha224
    hackinfo["pat_sha1"] = sha1
    hackinfo["pat_shake_128"] = shake1
    hackinfo["result_sha224"] = xsha224_patched
    hackinfo["result_sha1"] = sha1_patched
    hackinfo["result_shake1"] = shake1_patched
    hackinfo["rom"] = os.path.join("rom",  romfilename)
    hackinfo["romjson"] = os.path.join("rom",  jsonfilename)
    #            f2 = open(os.path.join("pat_meta",  shake1) + ".new", "w")
    #            f2.write( json.dumps(hackinfo) + "\n" )
    #            f2.close()
    #            os.replace(os.path.join("pat_meta", shake1) + ".new", os.path.join("pat_meta", shake1) + "")
    
    #            f2 = open(os.path.join("rom_meta", shake1_patched) + ".new", "w")
    #            f2.write( json.dumps(hackinfo) + "\n" )
    #            f2.close()
    #            os.replace(os.path.join("rom_meta", shake1_patched) + ".new", os.path.join("rom_meta", shake1_patched) + "")
    #            f2 = open(os.path.join("hacks", hackinfo["id"])  + ".new", "w")
    #            f2.write( json.dumps(hackinfo) + "\n" )
    #            f2.close()
    #            os.replace(os.path.join("hacks", hackinfo["id"])  + ".new", os.path.join("hacks", hackinfo["id"])  + "")

    print('Patch was successful!  ROM Location:')
    print(os.path.join('rom', romfilename))
    found = True
    return os.path.join('rom', romfilename)

if __name__ == '__main__':
    repatch_function(sys.argv)
    
    
    
    
 
