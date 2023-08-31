import json
import base64
import os
import re
import requests
import hashlib
import base64
import time
from compress import Compressor

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from zipfile import ZipFile

def rhmd_key(fpath):
    # used for sample data
    return 'JtSYvgCpAX4Hz_J63g-5dmDKbJp_Dl2GnKL_yuhoEck='
    

def hacklist_path():
    return "data/hacklist.json"

def rhmd_path():
    if 'RHMD_FILE' in os.environ:
        return os.environ['RHMD_FILE']
    if os.path.exists("rhmd.dat"):
        return "rhmd.dat"
    if os.path.exists("rhmd_dist.dat"):
        return "rhmd_dist.dat"
    if os.path.exists("rhmd_sample2.dat"):
        return "rhmd_sample2.dat"
    if os.path.exists("rhmd_sample.dat"):
        return "rhmd_sample.dat"
    return "rhmd_dist.dat"


cachepnums = {}

def get_pnum(hackid):
    result = None
    found = False
    if hackid in cachepnums:
        return cachepnums[hackid]
    if len(cachepnums) > 1:
        return None

    try:
       f = open('pnums.dat', 'r')
       for line in f.readlines():
           entry = line.strip().split(' ')
           cachepnums[entry[0]] = entry[1]
           if entry[0] == hackid:
               found = True
               result = entry[1]
    except:
         return result
    return result

def has_pnum(hackid):
    return not(get_pnum(hackid) == None)

    

def path_rerequisites():
    romerror = False
    if not os.path.exists('smw.sfc'):
        print('Could not find smw.sfc')
        romerror = True

    romf = open('smw.sfc', 'rb')
    romdata = romf.read()
    romf.close()
    expected = 'fdc4c00e09a8e08d395003e9c8a747f45a9e5e94cbfedc508458eb08'
    actual = hashlib.sha224(romdata).hexdigest()
    if hashlib.sha224(romdata).hexdigest() == expected : 
       pass
    else:
        print('Sha224 checksum of your supplied smw.sfc is other than expected..  This might not work.')
        print('Expected sha224(smw.sfc) =' + expected )
        print('Actual   sha224(smw.sfc) =' + actual   )
    romdata = None


    if romerror:
        print('Note: Need to copy smw.sfc and flips.exe To startup directory ' + os.getcwd() + ' in order to patch ROMs')
        print('SMW.sfc should be your legally obtained SMW ROM with file hash code sha224(smw.sfc) = fdc4c00e09a8e08d395003e9c8a747f45a9e5e94cbfedc508458eb08')
        print('Please find flips at: https://github.com/Alcaro/Flips ')

    if (not os.path.exists("temp") or not os.path.exists("patch") or not os.path.exists("blobs") or not os.path.exists("rom") or
       not os.path.exists("patch") or not os.path.exists("data")):
        print('Subfolders of start directory missing, please create folders below: ' + os.getcwd() + ' named '
              ' temp, blobs, rom, patch  and data')
        return False
    return True

def get_userauth_data():
    listfile = open('smwpicker_auth.json', 'r')
    data = listfile.read()
    value = json.loads(data)
    listfile.close()
    return value

def get_core_meta():
     uad = get_userauth_data()

def get_hacklist_data(filename=None):
     dekey = base64.urlsafe_b64decode( bytes(rhmd_key(rhmd_path()), 'ascii') )
     frn = Fernet( rhmd_key(rhmd_path())  )

     if filename == None:
         listfile = open(rhmd_path(), 'r')
     else:
         listfile = open(filename, 'r')
     data = listfile.read()
     if data[0]=='*':
        comp = Compressor()
        comp.use_lzma()
        hacklist = json.loads( comp.decompress(frn.decrypt(  bytes(data,'utf8') )) )
     elif data[0] == '[' or data[0] == '{':
          if data[0] == '{':
              data =  '[' + data + ']'
          hacklist = json.loads(data)  # Handle file if not encoded
     else:
         hacklist = json.loads(base64.b64decode(data))
     data = None
     return hacklist

def get_hackdict():
     hacklist = get_hacklist_data()
     hackdict = {}
     for u in range(len(hacklist)):
         if hacklist[u]['id'] in hackdict.keys():
            raise Exception('Oops: duplicate hack ids in list')
         hackdict[ hacklist[u]['id']] = hacklist[u]
     return hackdict

def find_hacklist_index(hacklist, idval):
    for x in range(len(hacklist)):
        if hacklist[x]['id'] == str(idval):
             return x
    return None

def save_hacklist_data(newhacklist,filename=None,docompress=True):
     frn = Fernet(rhmd_key(rhmd_path()))
     comp = Compressor()
     comp.use_lzma()

     if not(type(newhacklist) == type([])):
         raise TypeError('newhacklist wrong type')
     if filename == None:
         filename = rhmd_path()
     for x in range(len(newhacklist)):
         if not('authors' in newhacklist[x]) and 'author' in newhacklist[x]:
             newhacklist[x]['authors'] = newhacklist[x]['author']
     listfile = open(filename+".new", 'w')
     if docompress:
        listfile.write( '*' + ( bytearray(frn.encrypt(comp.compress(json.dumps(newhacklist)))) ).decode() )
     else: 
        listfile.write( base64.encodebytes( bytearray(json.dumps(newhacklist),'utf8') ).decode() )

     listfile.close()
     os.replace(filename + ".new", filename)
     #listfile.write( base64.encodebytes( json.dumps(newhacklist) ) )

def reduced_hacklist(hacklist, addxdata=False):
    for u in range(len(hacklist)):
        obj = hacklist[u]
        ea = ['author_href','comments','comments_href','featured','name_href',
              'patchblob1_name', 'patchblob1_sha224', 'romblob_salt',
              'patchblob1_key', 'patchblob1_kn', 'patchblob1_url',
              'patchblob1_ipfs_hash', 'patchblob1_ipfs_url' ]
        if addxdata and not('xdata' in obj):
            obj['xdata'] = {}
        elif not addxdata:
            if 'xdata' in obj:
                del obj['xdata']
            pass
        for i in ea:
            if i in obj:
                if addxdata:
                    obj['xdata'][i]=obj[i]
                del obj[i]
        hacklist[u] = obj
    return hacklist
     


def get_hack_info(hackid,merged=False):
     idstr = str(hackid)
     hacklist = get_hacklist_data()
     for x in hacklist:
         if str(x["id"]) == idstr:
             if merged:
                 x1 = dict(x)
                 if 'xdata' in x1:
                     for v in x1['xdata'].keys():
                        x1[v] = x1['xdata'][v]
                 if not('xdata' in x1):
                     if os.path.exists('rhmd_cache.dat'):
                         hl2 = get_hacklist_data(filename='rhmd_cache.dat')
                         hli = find_hacklist_index(hl2, hackid)
                         if not(hli == None):
                             if hackid == 'meta':
                                 if not('cachets' in hl2[hli]):
                                     hl2[hli] = {}
                                     hli = None
                                 elif int(hl2[hli['cachets']])+600 <int(time.time()) :
                                     hl2[hli] = {}
                                     hli = None
                             if ('cachets' in hl2[hli] and
                                 int(hl2[hli]['cachets'])+86400*10 < int(time.time()) ):
                                 hli = None
                         if not(hli == None):
                             x1['xdata'] = hl2[hli]['xdata']
                             for w in hl2[hli]:
                                 if re.match('patchblob.*', w):
                                     x1[w] = hl2[hli][w]
                 return x1
             else:
                 return x
     return None


def get_psets():
    f = open("psets.dat", "r")
    data = f.read()
    f.close()
    return json.loads(base64.b64decode(data))


def get_patch_blob(hackid, blobinfo=None):
    idstr = str(hackid)
    rawblob = get_patch_raw_blob(hackid, blobinfo)
    hackinfo = get_hack_info(hackid, True)
    #print(json.dumps(hackinfo, indent=4))
    print('Expected patchblob1_sha224 = ' + str(hackinfo["patchblob1_sha224"]))
    print('sha224(rawblob) = ' + hashlib.sha224(rawblob).hexdigest())
    if hashlib.sha224(rawblob).hexdigest() == hackinfo["patchblob1_sha224"]:
        comp = Compressor()
        comp.use_lzma()
        decomp_blob = comp.decompress(rawblob)

        key = base64.urlsafe_b64decode( bytes(hackinfo["patchblob1_key"], 'ascii') )
        frn = Fernet(key)
        decrypted_blob  = frn.decrypt(decomp_blob)

        comp = Compressor()
        comp.use_lzma()
        decoded_blob = comp.decompress(decrypted_blob)
        #frn_sha224 = hashlib.sha224(comp_frndata).hexdigest()
        print('Expected pat_sha224 = ' + hackinfo["pat_sha224"]  )
        print('sha224(decoded_blob) = ' + hashlib.sha224(decoded_blob).hexdigest())
        if hashlib.sha224(decoded_blob).hexdigest() ==  hackinfo["pat_sha224"]:
            return decoded_blob
        print('Error: Decoded patch does not match expected file checksum - possible data corruption.')
        return None

    print('[*] Error: Possible file corruption: Sha224 data checksum of received file does not match')
    return None


def fill_blob_data(hacklist, hackid, redo=False):
    blobinfo = {}
    hinfo = get_hack_info(hackid,True)
    if not('patchblob1_name' in hinfo):
        return
    if redo == False:
        if "xdata" in hinfo and hinfo["xdata"] and hinfo["xdata"]["patchblob1_url"] and  'patchblob1_ipfs_url' in hinfo["xdata"]:
            return
    try:
        blob = get_patch_blob(hackid, blobinfo)
        if blob == None:
            return
        print('BLOBINFO: ' + str(blobinfo))
    except Exception as err:
        print('ERROR filling ' + hackid + ' :: ' + str(err))
        raise Exception('Err')
        
    idx = find_hacklist_index(hacklist, hackid)
    if not("xdata" in hacklist[idx]):
        hacklist[idx]["xdata"] = {}
    hacklist[idx]["xdata"]["patchblob1_url"] = blobinfo["patchblob1_url"]
    hacklist[idx]["xdata"]["patchblob1_kn"] = blobinfo["patchblob1_kn"]
    hacklist[idx]["xdata"]["patchblob1_ipfs_hash"] = blobinfo["patchblob1_ipfs_hash"]
    hacklist[idx]["xdata"]["patchblob1_ipfs_url"] = blobinfo["patchblob1_ipfs_url"]

    

def get_pc_address(addr, offset=512):
    if addr < 0 :
        return offset
    if addr >= 0xFFFFFF:
        return offset

    if (addr & 0xFE0000) == 0x7E0000:
        return offset
    if (addr & 0x408000) == 0x000000:
        return offset
    if (addr & 0x708000) == 0x700000:
        return offset;

    h = addr & 0x7F0000
    h = h >> 1
    h = h | (addr & 0x7FFF)
    h = h + offset
    return h

def complete_hack_metadata(hackinfo):
     if not('xdata' in hackinfo) and not('patchblob1_name' in hackinfo):
          adata = get_userauth_data()
          s_userkey = str(adata["userkey"])
          objkey_s = hackinfo["objkey"]
          rhid_s = hackinfo["id"]

          values = { 'encryptedvalue' : adata["encryptedvalue"] } 
          urlmd1 = 'https://smw.iparpa.com/md/%s/%s' % (objkey_s, rhid_s)
          req = requests.post(urlmd1,
                  headers = {  
                             'userkey' : s_userkey,
                             'twid' : adata["twid"],
                             'twlogin' : adata["twlogin"],
                             'Content-Type' : 'application/json'
                            }, json = values)
          print("Request.post " + urlmd1)
          if req.status_code == 200:
              print('Got metadata from server')
              print(str(req.content))
              augment = json.loads(req.content)
              if 'xdata' in augment:
                  newhld = []
                  if os.path.exists('rhmd_cache.dat'):
                      newhld = get_hacklist_data(filename='rhmd_cache.dat')
                  hackinfo['xdata'] = augment['xdata']
                  for w in augment:
                     if re.match('patchblob.*', w):
                         hackinfo[w] = augment[w]
            
                  for w in augment['xdata']:
                      print(str(w))
                      hackinfo[w] = augment['xdata'][w]

                  idx00 = find_hacklist_index(newhld,hackinfo['id'])
                  newentry = { "id" : hackinfo['id'], "xdata" : augment['xdata']  }
                  if idx00 == None:
                      newhld = newhld + [newentry]
                  else: 
                      newhld[idx00] = newentry
                  newentry = None

                  idx00 = find_hacklist_index(newhld,hackinfo['id'])
                  for w in augment.keys():
                     if re.match('patchblob.*', w):
                         #hackinfo[w] = augment[w]
                         newhld[idx00][w] = augment[w]
                  newhld[idx00]["xdata"] = augment['xdata']
                  newhld[idx00]["cachets"] = int(time.time())
                  save_hacklist_data(newhld, filename='rhmd_cache.dat')
              
          else:
              print('HTTP Error:'+str(req)+ ' ' + str(req.text))
     return hackinfo
     pass

def get_patch_raw_blob(hackid, rdv):
     idstr = str(hackid)
     idstra = idstr[0:2]
     idstrb = idstr[0:1]
     mat = False

     if rdv == None:
        rdv = {}

     hackinfo = get_hack_info(hackid,True)
     hackinfo = complete_hack_metadata(hackinfo)
          
     if not('patchblob1_name' in hackinfo):
         return None
     #print(str(hackinfo))
     pblob_name = hackinfo["patchblob1_name"]
     if not os.path.exists( os.path.join("blobs", pblob_name)  ):
         print('Blob not cached.. searching')
         found = False
         for uu in get_psets():
             mat = False
             kn = uu["key"]
             #blobs/setpblob_pblob_12_0.zip
             prefix = kn.replace('.zip','')

             if (kn == hackinfo["patchblob1_name"]  or
                 kn == 'blobs/' + hackinfo["patchblob1_name"]) :
                 mat = True

             #s_pblob_32_31_sm_cc.zip  # 
             if re.match('.*_pblob.*_' + idstra +'[_\.].*', kn): 
                 mat = True
             if re.match('.*_pblob.*_' + idstrb +'[_\.].*', kn): 
                 mat = True
             if mat:
                 #rdv['kn'] = kn
                 #rdv['publicUrl'] =  uu["publicUrl"]
                 print('get_patch_blob(' + idstr + '): Look at ' + kn)
                 if not os.path.exists(kn):
                     print('Zip not stored, need to download.')
                     print('Downloading ...' + str(uu))
                     #publicUrl
                     url = uu["publicUrl"]
                     req = requests.get(url)
                     if req.status_code == 200:
                         print('Download from server was successful')
                         print('')
                         f = open(kn + ".new", "wb")
                         f.write(req.content)
                         f.close()
                         os.replace(kn + ".new", kn)
                     else:
                         print('HTTP Error:'+str(req))
                 if os.path.exists(kn):
                     if re.match('.*.zip', kn):
                        with ZipFile(kn, 'r') as zip:
                            for info in zip.infolist():
                                if info.filename == pblob_name:
                                    data = zip.read(info)
                                    rdv['patchblob1_kn'] = kn
                                    rdv['patchblob1_url'] = uu['publicUrl']
                                    rdv["patchblob1_ipfs_hash"] = uu['ipfs']
                                    rdv["patchblob1_ipfs_url"] = 'https://ipfs.fleek.co/ipfs/' + uu['ipfs']
                                    found = True
                                    return data
                            pass
                        pass
                     else:
                         pass
                         rdv['patchblob1_kn'] = uu['key']
                         rdv['patchblob1_url'] = uu['publicUrl']
                         rdv["patchblob1_ipfs_hash"] = uu['ipfs']
                         rdv["patchblob1_ipfs_url"] = 'https://ipfs.fleek.co/ipfs/' + uu['ipfs']
                     pass
                     #os.replace(kn + ".new", kn)

             pass

     if os.path.exists( os.path.join("blobs", pblob_name)  ):
         f = open( os.path.join("blobs", pblob_name), "rb")
         data = f.read()
         f.close()
         #rdv['patchblob1_kn'] = uu['key']
         #rdv['patchblob1_url'] = uu['publicUrl']
         #rdv["patchblob1_ipfs_hash"] = uu['ipfs']
         #rdv["patchblob1_ipfs_url"] = 'https://ipfs.fleek.co/ipfs/' + uu['ipfs']
         return data
         pass


