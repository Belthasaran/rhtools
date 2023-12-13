#!/usr/local/bin/python3
#!/usr/bin/python3

import requests
import json
import csv
import os
import time
import yaml
import apptoken
import sys

outjson = 0
max_query_tags = 3
tag_queries_made = 0

tagfile = open("tags.json","r")
known_tags = json.load(tagfile)
tagfile.close()

if 'json' in sys.argv:
    outjson = 1


excluded = {}

with open("filter.yaml", 'r') as ex:
  try:
      excluded_y = yaml.safe_load(ex)
  except yaml.YAMLError as exc:
      print(exc)

if 'excluded' in excluded_y:
  for ex in excluded_y['hide']:
    excluded[ex]=1


readTokens = apptoken.get_tokens()
client_id = readTokens[0]
client_secret = readTokens[1]
app_token = readTokens[2]
gameid = 'game_id=1505160567&game_id=1229'

url1 = 'https://api.twitch.tv/helix/streams?first=100&'+str(gameid)
#print("Lookup request:" + url1)
if outjson == 0:
   print("Search for channels with " + str(gameid) + " : " )

headersdict=headers = {'Client-ID' : client_id,  'Authorization' : 'Bearer ' +app_token,
         'Accept' : 'application/vnd.twitchtv.v5+json'}
lookup_request = requests.get(url1, headers=headersdict)

if lookup_request.status_code == 200:
    j1 = json.loads(lookup_request.text)
    vtotal = 0
    vmedian = 0
    scount = 0
    iter = 0
    try:
        for stream in j1["data"]:
            if stream['user_login'] in excluded and outjson == 0:
                continue

            scount = scount + 1

        for stream in j1["data"]:
            #print(str(stream))
            #
            tagstringlist = ''
            if 'tag_ids' in stream and stream['tag_ids'] != None:
                streamtagids = stream['tag_ids']
            else:
                streamtagids = []

            for tagid in streamtagids:
                if tagid in known_tags:
                    try:
                        if len(tagstringlist) > 0:
                            tagstringlist = tagstringlist + ', '
                        tagstringlist = tagstringlist + known_tags[tagid]["localization_names"]["en-us"]
                    except:
                        pass
                else:
                    if outjson == 0 :
                        print('Unknown tag: ' + str(tagid))
                    if tag_queries_made < max_query_tags:
                       tag_queries_made = tag_queries_made + 1
                       url2 = 'https://api.twitch.tv/helix/streams/tags?broadcaster_id=' + str(stream["user_id"])
                       tag_lookup_request = requests.get(url2, headers = headersdict)
                       try:
                           if tag_lookup_request.status_code == 200:
                               j2 = json.loads(tag_lookup_request.text)
                               #print(str(j2))
                               for foundtag in j2["data"]:
                                   #print('Output: ' + str( foundtag['tag_id']  ))
                                   if not(foundtag["tag_id"] in known_tags):
                                       #print("Ok: " + str( foundtag["tag_id"]  ))
                                       known_tags[ foundtag["tag_id"] ] = dict(foundtag)
                               #known_tags[tagid] = 
                       except Exception as xerr:
                           print('Err[' +  str(url2)  + '] :' + str(xerr))
                       #
                    if outjson == 0:
                        print('Spotted unknown tag: ' + str(tagid))
                    break           
            #
            if outjson == 0:
                print(": channel (%15s) playing game_id=%-10s  game_name='%s' type=%-8s is_mature=%-5s language=%s viewers=%3s"  % (stream['user_login'],  stream['game_id'],  stream['game_name'], stream['type'], stream['is_mature'], stream['language'], stream['viewer_count']))
            else:
                print(json.dumps(stream))
                #print(str(stream))
            vtotal = vtotal + int(stream['viewer_count'])
            if iter == scount / 2:
                vmedian = int(stream['viewer_count'])
            iter = iter + 1
    except Exception as err:
        raise Exception("Could not lookup " + str(err))
    if outjson == 0:
        print("SMW-Category:Viewers total=%s  streams=%s  median=%s" % (str(vtotal), str(scount), str(vmedian / 1) ))
else:
    raise Exception("Could not lookup " + str(lookup_request.text))	
 


tagfile = open("tags.json.new","w")
tagfile.write(json.dumps(known_tags))
tagfile.close()
os.rename("tags.json.new", "tags.json")
   
