import os
import sys
import traceback

from twitchio.ext import commands
import yaml
import json
import re
import requests
import apptoken
import datetime
import logging
import mysql.connector as mysql
from pymemcache.client import base
import dateutil.parser
import time
import traceback
import crm114
import unidecode
import asyncio
import path

botmoduledir = path.Path(__file__).abspath()
sys.path.append(botmoduledir.parent.parent)
import loadsmwrh

os.chdir(os.environ['BOTDIR'])

class JsonSerde(object):
    def serialize(self, key, value):
        if isinstance(value, str):
            return value, 1
        return json.dumps(value), 2

    def deserialize(self, key, value, flags):
       if flags == 1:
           return value
       if flags == 2:
           return json.loads(value)
       raise Exception("Unknown serialization format")


class Bot(commands.Bot):
    def init_db(self):
        self.logger.debug("Connecting to database server" )
        try:
            return mysql.connect(
                host = "localhost",
                user = botconfig["mysql"]["user"],
                passwd = botconfig["mysql"]["password"],
                database = botconfig["mysql"]["database"]
                )
            self.logger.debug("OK, Connected to MySQL Database")
        except Exception as err:
            self.logger.error("Exception connecting to MySQL Database: " + str(err))
            time.sleep(10)

    def __init__(self,bci):
        self.cltext = crm114.Classifier('/home/swtbot/textdata', ['good','spam','toxic'])
        self.msgbuffers = {}
        self.chatters_ts = {}
        self.chatters_filt = {}
        self.last_temp = {}
        self.nukenames = {}
        self.nuketexts  = {}
        self.controlchannels = []
        self.filterItems = []
        self.filterWords = []
        self.filterExpr = ''
        self.filterjson = None
        self.wordFilterRE = None

        self.spamfilterItems = []
        self.spamfilterWords = []
        self.spamfilterExpr = []
        self.spamfilterjson = None
        self.spamfilterRE = None

        self.namefilterItems = []
        self.namefilterWords = []
        self.namefilterExpr = []
        self.namefilterjson = None
        self.nameFilterRE = None

        #self.asciiArtRE = re.compile(' [^a-zA-Z0-9]{23,}\\b')
        
        with open('messagefilter.json') as json_file:
            self.filterjson = json.load(json_file)
            for wentry in self.filterjson:
                self.filterWords = self.filterWords + [wentry["word"]] 
                self.filterItems = self.filterItems + [wentry] 
            #print( '(?:%s)' % '|'.join(filterWords) )
            self.wordFilterRE = re.compile( '(%s)' % '|'.join(self.filterWords), re.I )
            #self.homoglyphs = hg.Homoglyphs(languages={'en'}, strategy=hg.STRATEGY_LOAD)

        with open('spamfilter.json') as json_file:
            self.spamfilterjson = json.load(json_file)
            for wentry in self.spamfilterjson:
                self.spamfilterWords = self.spamfilterWords + [wentry["word"]]
                self.spamfilterItems = self.spamfilterItems + [wentry]
            self.spamFilterRE = re.compile( '(%s)' % '|'.join(self.spamfilterWords), re.I )

        with open('namefilter.json') as json_file:
            self.namefilterjson = json.load(json_file)
            for wentry in self.namefilterjson:
                self.namefilterWords = self.namefilterWords + [wentry["word"]]
                self.namefilterItems = self.namefilterItems + [wentry]
            self.nameFilterRE = re.compile( '(%s)' % '|'.join(self.namefilterWords), re.I )


        self.readTokens = apptoken.get_tokens()
        self.readTokensTS = time.time()
        self.cachettl = 86400
        self.logger = logging.getLogger("swtbot")
        self.logging = logging.getLogger("swtbot")
        self.client = base.Client("localhost", serde=JsonSerde())
        self.client2 = base.Client("localhost")
        self.chandata = None
        self.channums = {}
        self.botconfig = bci
        self.dbconnection = self.init_db()
        self.requiretimes = []
        self.logger.info("Swtbot starting up")
        self.controlchannels = bci["twitch"]["controlchannels"]
        self.loop = asyncio.get_event_loop()
        u = super().__init__(token=bci["twitch"]["token"], client_id=bci["twitch"]["client_id"], 
                nick=bci["twitch"]["nick"], prefix='!', loop=self.loop,
                         initial_channels=bci["twitch"]["basechans"],
                         client_secret=bci["twitch"]["client_secret"],
                        api_token=bci["twitch"]["initial_token"] )
        try:
            coro = asyncio.start_server(self.handle_echo, '127.0.0.1', 1888, loop=self.loop)
            server = self.loop.run_until_complete(coro)
        except Exception as ex1:
            self.logger.debug("ExZ:" + str(ex1))
            pass
        return u

    async def get_cursor(self):
        try:
            self.logger.debug("get_cursor: ping database")
            self.dbconnection.ping(reconnect=True, attempts=3, delay=5)
        except mysql.Error as err:
            self.logger.debug("get_cursor: database ping error, reconnecting")
            time.sleep(10)
            self.dbconnection = self.init_db()             
        return self.dbconnection.cursor()

    async def event_pubsub(self, data):
        self.logger.debug("event_pubsub: " + str(data))
        return

    async def event_raw_pubsub(self, data):
        self.logger.debug("event_raw_pubsub: " + str(data))
        return

    #@bot.event
    async def event_raw_data(self,data):
        #if re.match("^[^ ]+ :[^ ]+ PRIVMSG ", data):
        #    return # skip PRIVMSG messages
        if re.match("^[^ ]+ :[^ ]+ JOIN ", data):
            return #
        if re.match("^[^ ]+ :[^ ]+ PART ", data):
            return #
        if re.match("^PING ", data):
            return #
        self.logger.debug("raw_event: " + str(data))
        #print(data)

    async def handle_echo(self, reader, writer):
        data = await reader.read(100)
        message = data.decode()
        addr = writer.get_extra_info('peername')
        self.logger.debug("Socket: Received %r from %r" % (message, addr))

        try:
            matchResult = re.match(r'^(\S+)\s+(\S+)\s+(\S+)\s+(.*)', message)
            #
            #chan = self.get_channel('hh')
            chan = None
            if matchResult != None:
                try:
                    if matchResult.group(3) == None :
                        pass
                        #channelName = str(ctx.message.author.name).lower()
                    else:
                        a = matchResult.group(1) 
                        chnameval = matchResult.group(2)
                        chan = self.get_channel( chnameval )
                        b = matchResult.group(3)
                        c = matchResult.group(4)
                        params=c.split()
                        pmatches = []
                        self.logger.debug("CMD a = " + a)
                        if a != botconfig['twitch']['wskey'] :
                            self.logger.debug("Socket: Incorrect Credentials")
                            return

                        self.logger.debug("CMD b = " + b)
                        self.logger.debug("CMD c = " + c)
                        self.logger.debug("CMD params.1 = " + str(params))
                        self.logger.debug("chanName = " + str(chan.name))

                        for n,i in enumerate(params):
                            if i == 'done' : params[n] = ''
                            if i == 'started' : params[n] = '^'
                            if i == 'start': params[n] = '^'
                            if i == 'end': params[n] = '$'
                            if i == 'dot': params[n] = '.'
                            if i == 'star': params[n] = '*'
                            if i == 'zero' : params[n] = '0'
                            if i == 'tozero' : params[n] = '0'
                            if i == 'to0' : params[n] = '0'
                            if i == 'one' : params[n] = '1'
                            if i == 'two' : params[n] = '2'
                            if i == 'three' : params[n] = '3'
                            if i == 'four' : params[n] = '4'
                            if i == 'five' : params[n] = '5'
                            if i == 'six' : params[n] == '6'
                            if i == 'seven' : params[n] == '7'
                            if i == 'eight' : params[n] == '8'
                            if i == 'nine' : params[n] == '9'
                            if i == 'done' : params[n] == ''
                            if i == 'underscore' : params[n] == '_'
                        self.logger.debug("CMD params.2 = " + str(params))
                        while len(params) > 0 and  '' in params:
                            params.remove('')


                        target = ''.join(params).lower()
                        if len(params) >= 2:
                            chatters = []
                            if chan.name in self.chatters_filt:
                               chatters = self.chatters_filt[chan.name]
                            self.logger.debug("CMD chatters = " + str(  chatters ))


                            if params[0] == 'word' : 
                                self.logger.debug('Target: word')
                                params = params[1:]
                                target = ''.join(params).lower()
                            elif params[0] == 'last' : 
                                self.logger.debug('Target: last ')
                                params = params[1:]
                                if chan.name in self.last_temp :
                                    target = str(self.last_temp[chan.name])
                                #self.last_temp
                            elif params[0] == 'exact' :
                                self.logger.debug('Target: exact')
                                target = ''.join([a[0].lower() for a in params[1:]])
                                params = params[1:]
                            elif params[0] == 'match' or params[0] == 'pattern' :
                                self.logger.debug('Target: match')
                                params = params[1:]
                                psearch = ' '.join(params).lower()
                                psearch_r = re.compile(psearch)
                                pmatches = list( filter(psearch_r.match,  chatters ) )
                                if len(pmatches) > 0 :
                                    target = pmatches[0]
                                else:
                                    target = psearch.lower()
                            else: 
                                self.logger.debug('Target: match')
                                psearch = ''.join([a[0].lower() for a in params]).lower()
                                psearch_r = re.compile(psearch)
                                pmatches = list( filter(psearch_r.match,  chatters ) )
                                if len(pmatches) > 0 :
                                   target = pmatches[0]
                                else:
                                    target = psearch.lower()
                                pass
                            #self.chatters_filt[chan.name]
                            pass
                        self.logger.debug("CMD target = " + str(target))
                        self.logger.debug("CMD pmatches = " + str(pmatches))
                        if b == "target" : await chan.send("!votarget " + str(target))
                        if b == "addmod" : await chan.send("!voaction addmod " + str(target))
                        if b == "addvip" : await chan.send("!voaction addvip " + str(target))
                        if b == "ban" : 
                            await chan.ban(str(target))
                            await chan.send("!voaction ban " + str(target))
                        if b == "unban" : 
                            await chan.unban(str(target))
                            await chan.send("!voaction unban " + str(target))
                        if b == "clearchat" : await chan.send("!voaction clearchat " + str(target))

                        if b == "emoteonly" : 
                            ws0 = chan._get_socket
                            chan1, _ = chan._get_channel()
                            await ws0.send_privmsg(chan1, content='.emoteonly')
                            await chan.send("!voaction emoteonly")
                        if b == "followers" : 
                            ws0 = chan._get_socket
                            chan1, _ = chan._get_channel()
                            folTime = 0
                            try:
                                val = int(target)
                                folTime = val
                            except Exception as ex0a:
                                pass
                            await ws0.send_privmsg(chan1, content='.followers ' + str(folTime))
                            await chan.send("!fvoaction followers")

                        if b == "newword" : await chan.send("!voaction newword")
                        if b == "permit" : await chan.send("!permit " + str(target))
                        if b == "purge" : 
                            await chan.timeout(str(target), 2)
                            await chan.send("!voaction purge " + str(target))
                            self.last_temp[chan.name] = str(target)
                        if b == "timeout" : 
                            await chan.timeout(str(target), 600)
                            await chan.send("!voaction timeout " + str(target))
                            self.last_temp[chan.name] = str(target)
                        if b == "softkick" : 
                            await chan.timeout(str(target), 1800)
                            await chan.send("!voaction softkick " + str(target))
                            self.last_temp[chan.name] = str(target)
                        if b == "kick" : 
                            await chan.timeout(str(target), 3600)
                            await chan.send("!voaction kick " + str(target))
                            self.last_temp[chan.name] = str(target)
                        if b == "hardkick" : 
                            await chan.timeout(str(target), 86400)
                            await chan.send("!voaction hardkick " + str(target))
                            self.last_temp[chan.name] = str(target)
                        if b == "warn" : await chan.send("!voaction warn " + str(target))
                        if b == "marker" : await chan.send("!voaction marker " + str(target))
                        if b == "clip" : await chan.send("!voaction clip " + str(target))
                     
                        if b == "subonly" : await chan.send("!subon")
                        if b == "slow" : 
                            ws0 = chan._get_socket
                            chan1, _ = chan._get_channel()
                            slowSeconds = 5
                            try:
                                val = int(target)
                                slowSeconds = val
                            except Exception as ex0a:
                                pass
                            await ws0.send_privmsg(chan1, content='.slow '+str(slowSeconds))
                            await chan.send("!voaction slowon")
                        if b == "rawunrestrict" :
                            ws0 = chan._get_socket
                            chan1, _ = chan._geT_channel()
                            await ws0.send_privmsg(chan1, content='.unrestrict '+str(target))
                        if b == "rawban" :
                            ws0 = chan._get_socket
                            chan1, _ = chan._get_channel()
                            await ws0.send_privmsg(chan1, content='.ban '+str(target))
                        if b == "rawunban" :
                            ws0 = chan._get_socket
                            chan1, _ = chan._get_channel()
                            await ws0.send_privmsg(chan1, content='.unban '+str(target))
                        if b == "slowoff" : 
                            ws0 = chan._get_socket
                            chan1, _ = chan._get_channel()
                            await ws0.send_privmsg(chan1, content='.slowoff')
                            await chan.send("!voaction slowoff")
                        if b == "reset" :
                             ws0 = chan._get_socket
                             chan1, _ = chan._get_channel()
                             await ws0.send_privmsg(chan1, content='.slowoff')
                             await ws0.send_privmsg(chan1, content='.emoteonlyoff')
                             await ws0.send_privmsg(chan1, content='.followersoff')
                             await ws0.send_privmsg(chan1, content='.subscribersoff')
                             await ws0.send_privmsg(chan1, content='.r9kbetaoff')
                             await chan.send("!voaction reset")
                        if b == "restrict" :
                            ws0 = chan._get_socket
                            chan1, _ = chan._get_channel()
                            await ws0.send_privmsg(chan1, content='.slow 5')
                            await ws0.send_privmsg(chan1, content='.emoteonly')
                            await ws0.send_privmsg(chan1, content='.r9kbeta')
                        if b == "restrict1" :
                            ws0 = chan._get_socket
                            chan1, _ = chan._get_channel()
                            await ws0.send_privmsg(chan1, content='.slow 3')
                            await ws0.send_privmsg(chan1, content='.subscribers')
                            await ws0.send_privmsg(chan1, content='.r9kbeta')
                        if b == "restrict2" :
                            ws0 = chan._get_socket
                            chan1, _ = chan._get_channel()
                            await ws0.send_privmsg(chan1, content='.slow 5')
                            await ws0.send_privmsg(chan1, content='.followers 600')
                            await ws0.send_privmsg(chan1, content='.r9kbeta')
                        if b == "restrict3" :
                            ws0 = chan._get_socket
                            chan1, _ = chan._get_channel()
                            await ws0.send_privmsg(chan1, content='.slow 5')
                            await ws0.send_privmsg(chan1, content='.followers 300')
                            await ws0.send_privmsg(chan1, content='.r9kbeta')
                        if b == "lockdown" :
                            ws0 = chan._get_socket
                            chan1, _ = chan._get_channel()
                            await ws0.send_privmsg(chan1, content='.slow 5')
                            await ws0.send_privmsg(chan1, content='.emoteonly')
                            await ws0.send_privmsg(chan1, content='.clear')
                            await ws0.send_privmsg(chan1, content='.r9kbeta')
                        if b == "lockdown1" :
                            ws0 = chan._get_socket
                            chan1, _ = chan._get_channel()
                            await ws0.send_privmsg(chan1, content='.slow 3')
                            await ws0.send_privmsg(chan1, content='.subscribers')
                            await ws0.send_privmsg(chan1, content='.clear')
                            await ws0.send_privmsg(chan1, content='.r9kbeta')
                        if b == "lockdown2" :
                            ws0 = chan._get_socket
                            chan1, _ = chan._get_channel()
                            await ws0.send_privmsg(chan1, content='.slow 5')
                            await ws0.send_privmsg(chan1, content='.followers 600')
                            await ws0.send_privmsg(chan1, content='.clear')
                            await ws0.send_privmsg(chan1, content='.r9kbeta')
                        if b == "lockdown2" :
                            ws0 = chan._get_socket
                            chan1, _ = chan._get_channel()
                            await ws0.send_privmsg(chan1, content='.slow 5')
                            await ws0.send_privmsg(chan1, content='.followers 300')
                            await ws0.send_privmsg(chan1, content='.clear')
                            await ws0.send_privmsg(chan1, content='.r9kbeta')
                        if b == "revoke" : await chan.send("!voaction revoke " + str(target))
                        if b == "allow" :
                            values = ( str(target).lower(), )
                            dbc = await self.get_cursor()
                            dbc.execute('UPDATE userdata SET level=10 WHERE level>=0 AND level<10 AND username=%s', values)
                            self.dbconnection.commit()
                            await chan.send(f'Setting user option.')
                            await self.load_useropt(username)
                        if b == "require" :
                              requiredTimeVal = int(target)
                              dbc = await self.get_cursor()
                              values = ( requiredTimeVal , str(chan.name.lower()) )
                              dbc.execute('UPDATE chandata SET requiretime=%s WHERE channame=%s', values)
                              self.dbconnection.commit()
                              await self.load_chandata()
                              await chan.send(f'!votts Ok, reset r = %d.' % (requiredTimeVal))
                        if b == "require24" :
                              requiredTimeVal = 86400
                              dbc = await self.get_cursor()
                              values = ( requiredTimeVal , str(chan.name.lower()) )
                              dbc.execute('UPDATE chandata SET requiretime=%s WHERE channame=%s', values)
                              self.dbconnection.commit()
                              await self.load_chandata()
                              await chan.send(f'!votts Set level 2')

                except Exception as xerr0:
                    self.logger.debug("Exception xerr0: " + str(xerr0))
        except Exception as xerr1:
            self.logger.debug("Exception xerr1: " + str(xerr1))

        #self.logger.debug("Send: %r" % message)
        #writer.write(data)
        await writer.drain()
        self.logger.debug("Close the client socket")
        writer.close()


    # Events don't need decorators when subclassed
    #Chatters(count=5, all=[], broadcaster=[], vips=[], moderators=[], staff=[], admins=[], global_mods=[], viewers=[])
    async def event_ready(self):
        self.logger.debug("Bot event_ready entered")
        print(f'Ready | {self.nick}')
        if self.chandata == None :
            self.logger.debug("Chandata==None, invoking load_chandata()")
            await self.load_chandata()

        #self.logger.debug("Joining channels "+str( chobj['channame']  ))
        #        username_list = list(filter(lambda g: not g in found , username_list))
        joinIdList = list(filter(lambda g: self.chandata[g]['joinchannel']==1 , self.chandata.keys()))
        joinList = [ self.chandata[g]['channame']  for g in joinIdList]
        self.logger.debug("Joining channels "+str( joinList ))

        pubsub_topics = [ 'chat_moderator_actions.'+str(channelId) for channelId in joinIdList]
        self.logger.debug('Pubsub, subscribing to topics: ' + str( pubsub_topics  ))
        try: 
            self.tw_pubsub_nonce = None
            #self.tw_pubsub_nonce  = await self.pubsub_subscribe( self.readTokens[2], *pubsub_topics )
            #self.tw_pubsub_nonce  = await self.pubsub_subscribe( self.botconfig["twitch"]["pubsub_token"] , *pubsub_topics )

            self.logger.debug('Pubsub nonce =' + str(self.tw_pubsub_nonce)) 
        except Exception as err:
            self.logger.error('Pubsub, error subscribing: ' + str(err))
        #async def pubsub_subscribe(self, token: str, *topics):
        try:
            await self.join_channels(joinList)
        except Exception as err:
            self.logger.error("JoinChannels Exception: " + str(err))

        #self.load_userinfo([''])
        for chid in self.chandata.keys() :
            chobj = ( self.chandata[chid]  )
            #if chobj['joinchannel'] != 1:
            #    self.logger.debug('Skipping channel '+str(chobj['channame']) + ' joinchannel=0')
            #    continue
            ###[gone] chatters = await self.get_chatters( chobj['channame'] )
            chatters = []

            userinfo = None
            if len(chatters.all) > 1 :
                #self.logger.debug('ChattersV: ' + str(chatters.all))
                userinfo = await self.load_userinfo(chatters.all[0:98])

            if len(chatters.all)>99:
                self.logger.debug('More than 99 chatters in '+str(chobj['channame'])+' loading more')
                m = 0
                while (len(chatters.all[m:])>99):
                    m = m+99
                    userinfo = await self.load_userinfo(chatters.all[0+m:98+m])
                    time.sleep(1)
            pass

    async def message_privlevel(self,message):
        print('DEBUG: message.tags='  + str(message.tags))
        moderator = 0
        premium = 0
        if "user-type" in message.tags:
            if message.tags["user-type"] and message.tags["user-type"] == "mod":
                moderator = 1
            if message.tags["user-type"] and message.tags["user-type"] == "staff":
                moderator = 1
        if "badges" in message.tags:
            if message.tags["badges"] and re.search("(broadcaster|admin|staff|global_mod)", message.tags["@badge-info"]):
                moderator = 1
            if message.tags["badges"] and re.search("moderator", message.tags["@badge-info"]):
                moderator = 1
            if message.tags["badges"] and re.search("(vip|turbo|verified|subscriber|bits)", message.tags["badges"]):
                premium = 1
            if moderator == 1:
                return 1
            return premium 
        if moderator == 1:
            return 1


    async def load_userinfo(self,username_list):
        found = {}
        mcloaduo = None
        self.logger.debug('In load_userinfo on ' + str(username_list))
        for username in username_list:
            mcloaduo = self.client.get("usern_" + str(username).lower())
            if not mcloaduo :
                try:
                    dbc = await self.get_cursor()
                    dbc.execute('SELECT * from userdata WHERE LOWER(username)=LOWER(%s)', (username,))
                    records = dbc.fetchall()
                    for record in records:
                        rowval = dict(zip(dbc.column_names, record))
                        mcloaduo = record[2]
                        found[ record[1].lower() ]=1
                        self.client.set("usern_" + str(username).lower(), mcloaduo, self.cachettl)
                        useroptobj = dict(rowval)
                        useroptobj["jsondata"] = None
                        self.client.set("useron_" + str(username).lower(), json.dumps(useroptobj), 86400)
                        self.client.set("usero_" + str( useroptobj['twid']) , json.dumps(useroptobj), 86400 )
                        #print(str(rowval))
                except Exception as exv0:
                    self.logger.error('Error in load_userinfo dbread on ' + str(username) + ' : ' + str(exv0))
                    pass
            else:
                found[username] = 1
        
        username_list = list(filter(lambda g: not g in found , username_list))
        usersli = []

        if len(username_list) > 0 :
            self.logger.debug('About to ask Twitch for userinfo on: ' + str(username_list))

            #for username in username_list:
            #readTokens = apptoken.get_tokens()
            readTokens = self.readTokens
            client_id = readTokens[0]
            client_secret = readTokens[1]
            app_token = readTokens[2]
            theurl1 = 'https://api.twitch.tv/helix/users?login=' + '&login='.join(username_list)
            lookup_request = requests.get(theurl1 ,
                    headers = {'Client-ID' : client_id,  'Authorization' : 'Bearer ' +app_token
                               #'Accept'    : 'application/vnd.twitchtv.v5+json'
                               }
                              )
            if not lookup_request.status_code == 200:
                self.logger.error('Error on API request to ' +theurl1+ ' : ' + str(lookup_request))
                return None
                #self.client.set("user_" + str(userid), "", 300)
                #self.client.set("usern_" + str( message.author.name.lower() ), "", 300)
                
            self.logger.debug('invoking json.loads(lookup_request.text)')
            usersli = json.loads(lookup_request.text)
            #self.logger.debug("lookup_text=" + str(lookup_request.text))
            pass
        pass

        if 'users' in usersli:
            usersli = usersli['users']

        if 'data' in usersli:
            usersli = usersli['data']
            
        #usersli = await self.get_users(*usersla)
        #self.client.set("user_" + self.userid, json.dumps(usersli))
        #print("Z:"+str(usersli))
        for userent in usersli:
            #self.logger.debug("usersli = " + str(usersli))
            userent["_id"] = userent["id"]   # v5
            userent["name"] = userent["login"]
            userent["bio"] = userent["description"]
            userent["logo"] = userent["profile_image_url"]
            self.logger.debug("UserEnt Set " + str(userent["_id"]))
            #print("U:"+str(userent))
            #print("X\n")
            if self.client.set("user_" + str( userent["_id"]  ), json.dumps(userent)) == 0 :
                self.logger.error("memcached: Unable to set user_" + str( userent["_id"]  ))
            if self.client.set("usern_" + str( userent["name"].lower()), json.dumps(userent) ) == 0 :
                self.logger.error("memcached: Unable to set usern_" + str( userent["name"].lower() ))
            try:
                dbc = await self.get_cursor()
                values = ( str(userent["_id"]),   str(userent["name"]).lower()  , json.dumps(userent)   )
                dbc.execute('REPLACE INTO userdata (twid,username,jsondata) VALUES (%s,%s,%s)', values)
                self.dbconnection.commit()
            except Exception as exv0:
                self.logger.error('SQL Error on REPLACE INTO userdata: ' + str(exv0))
                print(f'Error: an exception occurred: ' + str(exv0) )
            pass
        if mcloaduo == None :
            self.logger.debug( 'mcloaduo == None on ' + str(username_list) )
            self.logger.debug('lookup tb: ' + str( traceback.format_exc()  ))
        return mcloaduo

    async def event_message(self, message):
        #            chobj = ( self.chandata[chid]  )
        chobj = None
        wasblocked  = False
        wordsearchresult = None
        namesearchresult = None
        youngaccount = False
        agedaccount = False
        accountage = None
        label = None
        label2 = None
        confidence2 = 0
        confidence = 0
        firstseen = time.time()
        #self.readTokens
        basetext = message.content
        userid_i = None

        try:
            basetext = unidecode.unidecode(message.content).replace('[?]', '')
            userid = None
            if 'user-id' in message.tags:
                userid = (message.tags["user-id"])
            userid_i = None
            if userid != None :
                userid_i = int(userid)
            ##
        except Exception as err:
            self.logger.debug("ERR(unidecode): "  + str(err))
            #self.logger.debug(traceback.format_exc())
            #self.logger.debug(traceback.exc_info()[2])
            pass


        # Refresh Twitch API OAuth app tokens if older than 2 hours
        if self.readTokensTS + 7200 > time.time() :
            self.readTokens = apptoken.get_tokens()
            self.readTokensTS = time.time()
        if message.echo == True :
            # Don't parse messages sent by us being echo'd back
            return
        if not message.tags or not('user-id' in message.tags) or not message.tags['user-id']:
            # Missing user-id tags, yikes.
            self.logger.debug('User-Id tag missing on chat message: ' + str(json.dumps(message.tags)))
            return

        if self.chandata == None :
            # If we have no in-memory state about our channels, then reload it from the database.
            await self.load_chandata()

        #self.logger.debug( str( dir(message.channel) )  )

        if self.channums != None :
            chid = self.channums[message.channel.name.lower()]
            if chid and self.chandata != None :
                chobj = self.chandata[ chid ]

        if chobj == None or int(chobj["blockchannel"]) > 0 :
            self.logger.debug('Message to unknown or blocked channel - ' + str(message.channel.name).lower()  )
            return

        # Lookup the user's initial privilege level  based on the message tags
        plev = await self.message_privlevel(message) 

        #
        wordsearchresult = None
        namesearchresult = None
        spamsearchresult = None
        label = None
        confidence = 0.0


        # Check message from a non-moderator against our patterns
        if plev < 20 :
            wordsearchresult = self.wordFilterRE.search(str(message.content).lower())
            if wordsearchresult == None:
                wordsearchresult = self.wordFilterRE.search(str(basetext).lower())
            namesearchresult = None
            if firstseen > time.time() - 86400*7 :
                namesearchresult = self.nameFilterRE.search(str(message.author.name).lower())
                if namesearchresult == None:
                    try:
                        namesearchresult = self.nameFilterRE.search( unidecode.unidecode( str(message.author.name).lower()))
                    except Exception as err:
                        self.logger.debug("ERR(author unidecode): "  + str(err))
                        pass
            spamsearchresult = None
            if firstseen > time.time() - 86400*7 :
                spamsearchresult = self.spamFilterRE.search(str(message.content).lower())
                if spamsearchresult == None :
                    spamsearchresult = self.spamFilterRE.search(str(basetext).lower())
            label = None
            confidence = 0.0
            #
        try:
             chname = str(message.channel.name)
             if not (chname in self.msgbuffers.keys()) :
                 self.msgbuffers[ chname ] = []
             self.msgbuffers[chname].append( [time.time(), str(message.author.name), str(message.content)]  )
             #
             try:
                 chatterList1 = list( set( g[1] for g in  self.msgbuffers[ chname ] ) )
                 if not (chname in self.chatters_ts.keys()) :
                     self.chatters_ts[chname] = 0
                     self.chatters_filt[chname] = []
                 if self.chatters_ts[chname] + 300 < time.time() :
                     self.chatters_ts[chname] = time.time()
                     try: 
                         self.chatters_filt[chname] = chatterList1
                         if chname in self.controlchannels :
                             ##[gone] chatters = await self.get_chatters( chname )
                             chatters = []
                             if chatters != None and type(chatters) == list and len(chatters) > 0 :
                                 self.chatters_filt[chname] = chatters
                     except Exception as err:
                         pass
                 if not ( str(message.author.name) in self.chatters_filt[chname] ) :
                     self.chatters_filt[chname].append( str(message.author.name) )

                 chatterList2 = list( filter(lambda x: x in self.chatters_filt[chname] , chatterList1) )
                 self.logger.debug ("CL = " + str(chatterList1))
                 self.client.set("chatters_" + str(chname).lower(),  json.dumps(chatterList1) )
                 self.client2.set("chatters0_" + str(chname).lower(),  json.dumps(chatterList2) )
                 self.client2.get("chattersall_" + str(chname).lower(),  json.dumps( self.chatters_filt[chname] ) )
                 pass
             except Exception as err:
                 self.logger.debug("Cache_set " + str(chname) + "_chatters : error: " + str(err))
                 pass
             #
             if len( self.msgbuffers[chname] ) >  400:
                 self.msgbuffers[chname].pop(0)
             while len( self.msgbuffers[chname] ) > 1 and  self.msgbuffers[chname][0][0] + 1800 < time.time() :
                 self.msgbuffers[chname].pop(0)
                 ##
             if (plev < 20 and firstseen > time.time() - 86400*7) and (userid_i == None or userid_i > 691426733)  :
                 label, confidence = self.cltext.classify( str(message.content) )
                 label2, confidence2 = self.cltext.classify( str(basetext).lower() )
                 self.logger.info('User ' + str(message.author.name) + ' label=' + str(label) + ' confidence=' + str(confidence) + ' label2=' + str(label2) + ' confidence2=' + str(confidence2) + ' uid=' + str(userid_i) + '  message:' + str(message.content) )
        except Exception as err:
             self.logger.debug("ERR: "  + str(err))


        if plev > 10 :
            self.logger.debug("ACCOUNT " + str(message.author.name) + " Account skips checks due to mod+" )
            await self.handle_commands(message)
            return

        # Not triggering actions against premium accounts, Unless the text hits the main phase filter
        if plev > 0 and wordsearchresult == None :
            self.logger.debug("ACCOUNT " + str(message.author.name) + " Account skips checks due to premium" )
            await self.handle_commands(message)
            return

        ###
        #
        # Beyond this point we have either a word match, or an unknown user.
        #
        ###

        #
        # Figure out if this user has an access level found in our in-memoy cache, or in the Database...
        #
        useroptobj = await self.get_useropt( message.author.name  )
        if  useroptobj != None :
            try:
                if useroptobj != None :
                    firstseen = int(useroptobj["firstseen"])
                    uolevel = int(useroptobj["level"])
                    if uolevel != 0 and (uolevel < 0 or uolevel > plev) :
                       plev = uolevel
                #
                # Users at level 10 are in the manual allow list.
                # For now, we are skipping even the main phase filter, for these users.
                #
                if int(useroptobj['level']) >= 10 :
                    self.logger.debug('User ' + str(message.author.name) + ' is on the allow list, skipping')
                    await self.handle_commands(message)
                    return

                if str(message.channel.name) in self.nuketexts.keys():
                    chname = str(message.channel.name)
                    for tentry in self.nuketexts[chname]:
                        if tentry[0].search( message.content):
                           message.channel.timeout(str(message.author.name), 1200, 'use of blocked text (b)')
                           #self.last_temp[message.channel.name] = message.author.name

                if str(message.channel.name) in self.nukenames.keys():
                    chname = str(message.channel.name)
                    for tentry in self.nukenames[chname]:
                        if tentry[0].search( str(message.autho.name)  ):
                           message.channel.timeout(str(message.author.name), 1200, 'use of blocked text (u)')
                           #self.last_temp[message.channel.name] = message.author.name

                if int(useroptobj['level']) == -90 :
                    await message.channel.ban(message.author.name, 'autoban -90')
                elif int(useroptobj['level']) <= -60 :
                    await message.channel.timeout(message.author.name, 2*86400, 'automatic timeout')
                elif int(useroptobj['level']) <= -50 :
                    await message.channel.timeout(message.author.name, 86400, 'automatic timeout')
                    return
            except Exception as err:
                self.logger.error('Exception in allow list proc: ' + str(err))
                pass

        # Beyond this point -- the user's privilege level stored in "plev" is enhanced to take into
        # account  users with special levels  based on past messages or allowlist, etc.


        if  plev >= 0 :
            #if namesearchresult != None and plev < 1 :
            #    self.logger.info('User ' + str(message.author.name) + 'username hit a filter - match:[' +
            #            str(message.author.name[namesearchresult.start():namesearchresult.end()])  + ']')
            #    wasblocked = True
            #    await message.channel.timeout(message.author.name, 86400, 'suspected troll')
            if wordsearchresult != None and wasblocked == False :
                self.logger.info('User ' + str(message.author.name) + 'hit the word filter - match:[' +
                        str(message.content[wordsearchresult.start():wordsearchresult.end()])  + '] full message:[' + str(message.content) +']' )
                await message.channel.timeout(message.author.name, 12*86400, 'message content')
                self.last_temp[message.channel.name] = message.author.name
                pass
            #mt = member.display_name[m1.start():m1.end()]

        if plev > 0 : 
            self.logger.debug("ACCOUNT " + str(message.author.name) + " Account skips checks due to premium" )
            if wasblocked == False:
                await self.handle_commands(message)
            return

        #if plev <= 0 :
        #    if spamsearchresult != None and wasblocked == False :
        #        self.logger.info('User ' + str(message.author.name) + 'hit the word filter - match:[' +
        #         str(message.content[spamsearchresult.start():spamsearchresult.end()])  + '] full message:[' + str(message.content) +']' )
        #        await message.channel.timeout(message.author.name, 12*86400, 'spam')

        userid = (message.tags["user-id"])
        userid_i = None
        if userid != None :
            userid_i = int(userid)

        #if message.tags["subscriber"] and re.match("1", message.tags["subscriber"]):
        #    self.premium = 1

        usersla=[userid]


        mcloaduo = self.client.get("user_" + str(userid))
        if not mcloaduo :
            try:
                dbc = await self.get_cursor()
                queryvalues = (str(userid),)
                dbc.execute('SELECT * from userdata WHERE twid=%s', queryvalues)
                records = dbc.fetchall()
                for record in records:
                    rowval = dict(zip(dbc.column_names, record))
                    mcloaduo = record[2]
                    self.client.set("user_" + str(userid), mcloaduo, self.cachettl)
                    useroptobj = dict(rowval)
                    useroptobj["jsondata"] = None
                    self.client.set("usero_" + str(userid), json.dumps(useroptobj), 1200)

                    #print(str(rowval))
            except Exception as exv0:
                self.logger.error("SQL Error on SELECT * from userdata i::: " + str(exv0))
                
        if not mcloaduo :
            #readTokens = apptoken.get_tokens()
            readTokens = self.readTokens
            client_id = readTokens[0]
            client_secret = readTokens[1]
            app_token = readTokens[2]
            self.logger.debug('About to ask Twitch for userinfo on single user: ['  + str(userid) + '] ' + str(message.author.name) + ' in ' +
                    str(message.channel.name))

            lookup_request = requests.get('https://api.twitch.tv/helix/users/?id=' + str(userid),
                    headers = {'Client-ID' : client_id,  'Authorization' : 'Bearer ' +app_token
                    #           'Accept'    : 'application/vnd.twitchtv.v5+json'
                      }
                     )
            if not lookup_request.status_code == 200:
                self.client.set("user_" + str(userid), "", 300)
                self.client.set("usern_" + str( message.author.name.lower() ), "", 300)
            else:
                usersli = [ json.loads(lookup_request.text) ]

                #usersli = await self.get_users(*usersla)
                #self.client.set("user_" + self.userid, json.dumps(usersli))
                #print("Z:"+str(usersli))
                for userent in usersli:
                    userent["_id"] = userent["id"]      #  v5 API fields from helix request
                    userent["name"] = userent["login"]  #  v5 API fields from helix request
                    userent["bio"] = userent["description"]
                    userent["logo"] = userent["profile_image_url"]

                    #print("U:"+str(userent))
                    #print("X\n")
                    self.client.set("user_" + str(userid), json.dumps(userent), self.cachettl )
                    self.client.set("usern_" + str(message.author.name.lower()), json.dumps(userent), self.cachettl )
                    mcloaduo = json.dumps(userent)
                    #mcloaduo = self.client.get("user_" + str(userid))
                    #
                    try:
                        dbc = await self.get_cursor()
                        #values = ( str(userid),  message.author.name, json.dumps(userent)   )
                        values = ( str(userid),  message.author.name, json.dumps(userent)   )
                        dbc.execute('REPLACE INTO userdata (twid,username,jsondata) VALUES (%s,%s,%s)', values)
                        self.dbconnection.commit()
                    except Exception as exv0:
                        self.logger.error(f'Error: exception during SQL query: ' + str(exv0) )
                    pass
                #
            #
        if mcloaduo != None :
            mcloaduobj = json.loads(mcloaduo)
            self.logger.debug('mcloaduo = ' + str(mcloaduo))
            self.logger.debug('mcloaduobj = ' + str(mcloaduobj))
            self.logger.debug('type(mcloaduobj) = ' + str(type(mcloaduobj)))
            acctcreatedat = mcloaduobj['created_at']
            acctbio = mcloaduobj['bio']
            acctlogo = mcloaduobj['logo']
            viewcount = 0

            if 'view_count' in mcloaduobj:
                viewcount = int(mcloaduobj['view_count'])

            # Default logo image:
            #https://static-cdn.jtvnw.net/user-default-pictures-uv/41780b5a-def8-11e9-94d9-784f43822e80-profile_image-300x300.png
            if mcloaduobj != None :
                try:
                    requiretimeopt  = int(self.chandata[ self.channums[message.channel.name.lower()]]['requiretime'])
                except Exception as err:
                    requiretimeopt = 0
                    self.logger.debug("Error loading requiretimeopt : " + str(err))

                #if requiretimeopt > 0 :
                #    print("REQVAL:" + str(requiretimeopt))
                #    print("CREATE:" + str(acctcreatedat))

                createdt = dateutil.parser.parse(acctcreatedat)
                createts =  (createdt - datetime.datetime(1970, 1, 1, 0, 0, 0, 0, tzinfo=datetime.timezone.utc  )).total_seconds()
                accountage = time.time() - createts
                if time.time() - 86400*14 > createts:
                    agedaccount = True
                if viewcount > 200:
                    agedaccount = True
                if createts + 86400 > time.time() and createts > 1599460370:
                    youngaccount = True
                    self.logger.debug("WARN: YOUNG ACCOUNT " + str(message.author.name) + " - (" + 
                            str( time.time() - createts) + ")   createts="+str(acctcreatedat) )
                if requiretimeopt > 0 and (createts + int(requiretimeopt)) > time.time() and createts > 1601879529 and viewcount < 50:
                    self.logger.debug("ACCOUNT " + str(message.author.name) + " Account newer than required " )
                    #await ctx.ban(ctx.author.name, 'Nope')
                    await message.channel.timeout(message.author.name, 3600, 'Account created too recently '+ str(datetime.timedelta(seconds=time.time() - createts)) +' (ts)')
                    self.last_temp[message.channel.name] = message.author.name
                    #await XXXX ctx.message.author
                else:
                    self.logger.debug("ACCOUNT " + str(message.author.name) + " Account age ("+str(datetime.timedelta(seconds=time.time()-createts))+"s)" )
                    # Wait, didn't we already do this?
                    #try: 
                    #    useroptobj = await self.get_useropt( author.name )
                    #    if useroptobj != None :
                    #        uolevel = int(useroptobj["level"])
                    #        if uolevel != 0 :
                    #            plev = uolevel
                    #except Exception as err:
                    #    self.logger.debug("ERROR uopt1: " + str(err))
                    #    pass

        if plev <= 0 :
            if spamsearchresult != None and wasblocked == False and agedaccount == False :
                self.logger.info('User ' + str(message.author.name) + 'hit the word filter - match:[' +
                 str(message.content[spamsearchresult.start():spamsearchresult.end()])  + '] full message:[' + str(message.content) +']' )
                await message.channel.ban(message.author.name, 'ts=' + str(time.strftime('%Y%m%d')) + 'spam')
                self.last_temp[message.channel.name] = message.author.name
                #await message.channel.timeout(message.author.name, 12*86400, 'spam')
            if namesearchresult != None and plev < 1 and agedaccount == False and str(message.author.name).lower() != 'manofsteel2141x' :
                self.logger.info('User ' + str(message.author.name) + 'username hit a filter - match:[' +
                        str(message.author.name[namesearchresult.start():namesearchresult.end()])  + ']')
                wasblocked = True
                await message.channel.timeout(message.author.name, 86400, 'tsn')
                self.last_temp[message.channel.name] = message.author.name
                #await message.channel.ban(message.author.name, 'troll prevention (nm)')
            if plev < 1 and createts+86400*21 > time.time()  and wasblocked == False and label != None and confidence > 0 :
                if label == b'spam' or label == b'toxic':
                    self.logger.info('User(S) ' + str(message.author.name) + ' label=' + str(label) + ' confidence=' + str(confidence) + '  message:' + str(message.content) )
                if ((label == b'spam' and confidence >= 0.95) or
                    (label2 == b'spam' and confidence2 >= 0.95)) and agedaccount == False :
                    await message.channel.timeout(message.author.name, 240, 'sm')
                    self.last_temp[message.channel.name] = message.author.name
                if  (  (label == b'toxic' and confidence >= 0.98) or 
                    (label2 == b'toxic' and confidence2 >= 0.98)) :
                    await message.channel.timeout(message.author.name, 240, 'tm')
                    self.last_temp[message.channel.name] = message.author.name



         #[User(id='1****, login='****', display_name='****', type='', broadcaster_type='', description='**', profile_image='**', offline_image='**', view_count=11)]
        #user_rec = self.client.get("user_" + message.)
        #from pymemcache.client import base
        #    
        #
        #[] "created_at": "2015-08-21T20:25:14.224473Z"
        #print(dir(message))
        #print(str(message.tags))
        #print(message.content)
        if wasblocked == False:
            await self.handle_commands(message)

    # Command help
    @commands.command(name='swhelp')
    async def do_help_command(self, ctx):
        # message.author is  <User name=hh channel=hh>
        print(str(ctx.message.author))
        self.logger.info('Command: ' + str(ctx.message.author.name) + ' :: ' + str(ctx.message.content))
        await ctx.send(f'@{ctx.author.name} commands are: !swrequire | !swjoin | !swallowlist | !swpart | !swtomsg ')
        if await self.cmd_privilege_level(ctx.message.author) < 20:
            return
            #await ctx.timeout(ctx.author.name, 600, 'Sorry, !swhelp is mod-only')

    # Commands use a different decorator
    @commands.command(name='swping')
    async def my_command(self, ctx):
        # message.author is  <User name=hh channel=hh>
        print(str(ctx.message.author))
        self.logger.info('Command: ' + str(ctx.message.author.name) + ' :: ' + str(ctx.message.content))
        await ctx.send(f'Hello {ctx.author.name}!')
        if await self.cmd_privilege_level(ctx.message.author) < 20:
            return
            #await ctx.timeout(ctx.author.name, 600, 'Sory, !swping is mod-only')

    # Permission levels :
    #    0   Default
    #    10  Global dont block list
    #    20  Mod in current channel
    #    30  Reserved  
    #    50  Broadcaster  (not implemented)
    async def cmd_privilege_level(self,author):
        useroptobj = await self.get_useropt( author.name )
        if  useroptobj != None :
            try:
                if int(useroptobj['level']) >= 51 :
                    return int(useroptobj['level'])
            except Exception as err:
                pass
        #cmd_privilege_level
        if author.is_mod == True:
            return 20
        return 0

    @commands.command(name='swjoin')
    async def do_swjoin(self,ctx):
        # Command not yet implemented
        try:
            privlev = await self.cmd_privilege_level(ctx.message.author)
            if privlev < 20:
                return
            #if privlev < 20 and str(message.channel.name).lower() != str(message.author.name).lower():
            #    return
            self.logger.info('Command: ' + str(ctx.message.author.name) + ' :: ' + str(ctx.message.content))
            matchResult = re.match(r'^join( +(.*)|)', ctx.message.clean_content)
            if matchResult != None:
                try:
                    if matchResult.group(2) == None :
                        channelName = str(ctx.message.author.name).lower()
                        #await ctx.send(f'Usage: !swjoin <username>')
                        #return
                    else:
                        #channelName  = ( matchResult.group(2) )
                        channelName = ( matchResult.group(2) )

                    channelInfo =  await self.load_userinfo( [channelName] )
                    if channelName != str(ctx.message.author.name).lower() and channelName != str(ctx.message.channel.name) and str(ctx.message.channel.name) not in self.controlchannels:
                        if  privlev < 50:
                            await ctx.send(f'@{ctx.message.author.name} Remote join requests outside my control channel are limited to the broadcaster.')
                            return

                    if channelInfo == None :
                        await ctx.send('Could not find that channel')
                        return

                    dbc = await self.get_cursor()

                    channelInfo = json.loads(channelInfo)
                    self.logger.debug(' swjoin channelInfo = ' + str(channelInfo))
                    values = ( channelInfo["_id"], channelInfo["name"].lower(), 0, 1 )
                    self.logger.debug(' SQL: INSERT IGNORE INTO chandata | ' + str(values))
                    dbc.execute('INSERT IGNORE INTO chandata (twid,channame,requiretime,joinchannel) VALUES (%s,%s,%s,%s)', values)
                    self.logger.debug(' SQL: UPDATE chandata')
                    dbc.execute('UPDATE chandata SET joinchannel=1 WHERE blockchannel=0 and channame=%s', (channelInfo["name"],))
                    self.logger.debug('join_channels ' + str( [ channelInfo["name"]  ]  ))
                    await self.join_channels( [ channelInfo["name"]  ] )
                    self.dbconnection.commit()
                    await self.load_chandata()
                    await ctx.send('Ok, @' + str(ctx.message.author.name) + ' - joining ' + str(channelName) + ' as requested')

                    #self.logger.debug('check get_chatters ' + channelName)
                except Exception as err:
                    self.logger.error('swjoin command error: ' + str(err))
                    self.logger.error('swjoin tb: ' + str( traceback.format_exc()  ))
                    pass
        except Exception as err:
            pass

    @commands.command(name='swtomsg')
    async def do_timeout_msg(self,ctx):
        #self.msgbuffers[chname][0][0] + 120 < time.time()
        try:
            privlev = await self.cmd_privilege_level(ctx.message.author)
            if privlev < 20:
                return
            self.logger.info('Command: ' + str(ctx.message.author.name) + ' :: ' + str(ctx.message.content))
            #
            matchResult = re.match(r'^tomsg( +([0-9]+) (.*)|)', ctx.message.clean_content)
            if matchResult == None or  matchResult.group(3) == None :
                matchResult = re.match(r'^tomsg( (.*)|)', ctx.message.clean_content)
                if matchResult == None or matchResult.group(2) == None :
                    await ctx.send(f'@{ctx.message.author.name} Usage: !tomsg [<duration>] <text>')
                    return
                else:
                    tomessage = matchResult.group(2)
                    totime = 600
            else:
                tomessage = matchResult.group(3)
                totime = matchResult.group(2)

            #
            to_re = re.compile( tomessage, re.I )
            to_ts = time.time()

            if totime == None or str(totime) == '' :
                totime = 600
            else:
                totime = int(totime)
            #
            #self.msgbuffers
            await ctx.send(f'@{ctx.message.author.name} Ok, timing out for {totime} everyone that said {tomessage} ')

            self.logger.debug(f'@{ctx.message.author.name} Ok, timing out for {totime} everyone that said {tomessage}')
            matchlist = list(filter( lambda g: g[0] + 600 >= to_ts and  to_re.search(g[2])  , self.msgbuffers[ str(ctx.message.channel.name)  ]  ))
            matchnames = list(set([ g[1]  for g in matchlist ]))
            self.logger.debug('Match buffer: ' + str(  self.msgbuffers[ str(ctx.message.channel.name)  ]   ))
            for target in matchnames:
                self.logger.debug(f'@{ctx.message.author.name} timeout ' + str(target) + ' ' + str(totime) + '  match_timeout')
                await ctx.timeout(target, totime, 'match_timeout')
                #self.last_temp[message.channel.name] = message.author.name
        except Exception as err:
            self.logger.error('tomsg error: ' + str(err))
            pass

    @commands.command(name='swcleanbuf')
    async def do_cleanbuffer(self,ctx):
        try:
            privlev = await self.cmd_privilege_level(ctx.message.author)
            if privlev < 20:
                return
            self.logger.info('Command: ' + str(ctx.message.author.name) + ' :: ' + str(ctx.message.content))
            chname = str(message.channel.name)
            self.msgbuffers[chname] = []
        except Exception as err:
            pass
        pass

    @commands.command(name='swbanallmsg')
    async def do_ban_msg(self,ctx):
        #self.msgbuffers[chname][0][0] + 120 < time.time()
        try:
            privlev = await self.cmd_privilege_level(ctx.message.author)
            if privlev < 20:
                return
            self.logger.info('Command: ' + str(ctx.message.author.name) + ' :: ' + str(ctx.message.content))
            #
            matchResult = re.match(r'^banallmsg( (.*)|)', ctx.message.clean_content)
            if matchResult == None or  matchResult.group(2) == None :
                await ctx.send(f'@{ctx.message.author.name} Usage: !banallmsg <text>')
                return
            #
            banmsg = matchResult.group(2)
            to_re = re.compile( banmsg, re.I )
            to_ts = time.time()
            #
            #self.msgbuffers
            self.logger.debug(f'@{ctx.message.author.name} Ok, banning everyone that said {banmsg}')
            matchlist = list(filter( lambda g: g[0] + 600 >= to_ts and  to_re.search(g[2])  , self.msgbuffers[ str(ctx.message.channel.name)  ]  ))
            matchnames = list(set([ g[1]  for g in matchlist ]))
            await ctx.send(f'@{ctx.message.author.name} Ok, banning everyone that said {banmsg} ')
            for target in matchnames:
                 self.logger.debug(f'@{ctx.message.author.name} ban ' + str(target) + '  match_ban')
                 await ctx.ban(target, 'match_ban')
        except Exception as err:
            self.logger.error('banmsg error: ' + str(err))
            pass

    @commands.command(name='swunnuke')
    async def do_unnuke_cl(self,ctx):
        try: 
            privlev = await self.cmd_privilege_level(ctx.message.author)
            if privlev < 20:
                return
            self.logger.info('Command: ' + str(ctx.message.author.name) + ' :: ' + str(ctx.message.content))
            chname = str(ctx.message.channel.name)
            self.nuketexts[chname] = []
            self.nukenames[chname] = []
            await ctx.send(f'@{ctx.message.author.name} Ok, temporary badlists cleared.')
        except Exception as err:
            self.logger.error('Error in command unnuke: ' + str(err))

    @commands.command(name='swnuketext')
    async def do_nuke_text(self,ctx):
        #self.msgbuffers[chname][0][0] + 120 < time.time()
        try:
            privlev = await self.cmd_privilege_level(ctx.message.author)
            if privlev < 20:
                return
            self.logger.info('Command: ' + str(ctx.message.author.name) + ' :: ' + str(ctx.message.content))
            #
            matchResult = re.match(r'^nuketext( (.*)|)', ctx.message.clean_content)
            if matchResult == None or  matchResult.group(2) == None :
                await ctx.send(f'@{ctx.message.author.name} Usage: !nuketext <text>')
                return
            #
            banmsg = matchResult.group(2)
            to_re = re.compile( banmsg, re.I )
            to_ts = time.time()
            chname = str(ctx.message.channel.name)

            if not (chname in self.nuketexts.keys()) :
                self.nuketexts[chname] = []
            if len( self.nuketexts[chname] ) > 10 :
                self.nuketexts[chname].pop(0)
            self.nuketexts[chname].append([to_re,banmsg])

            #
            #self.msgbuffers
            self.logger.debug(f'@{ctx.message.author.name} Ok, nuking text pattern: {banmsg}')
            matchlist = list(filter( lambda g: g[0] + 600 >= to_ts and  to_re.search(g[2])  , self.msgbuffers[ str(ctx.message.channel.name)  ]  ))
            matchnames = list(set([ g[1]  for g in matchlist ]))
            await ctx.send(f'@{ctx.message.author.name} Ok, nuking text pattern: {banmsg} ')
            for target in matchnames:
                 self.logger.debug(f'@{ctx.message.author.name} nuketext ' + str(target) + '  match_text')
                 await ctx.timeout(target, 1200, 'matched_text')
                 #self.last_temp[message.channel.name] = target
        except Exception as err:
            self.logger.error('nuketext error: ' + str(err))
            pass

    @commands.command(name='swnukename')
    async def do_nuke_name(self,ctx):
        #self.msgbuffers[chname][0][0] + 120 < time.time()
        try:
            privlev = await self.cmd_privilege_level(ctx.message.author)
            if privlev < 20:
                return
            self.logger.info('Command: ' + str(ctx.message.author.name) + ' :: ' + str(ctx.message.content))
            #
            matchResult = re.match(r'^nukename( (.*)|)', ctx.message.clean_content)
            if matchResult == None or  matchResult.group(2) == None :
                await ctx.send(f'@{ctx.message.author.name} Usage: !nukename <text>')
                return
            #
            banmsg = matchResult.group(2)
            to_re = re.compile( banmsg, re.I )
            to_ts = time.time()
            chname = str(ctx.message.channel.name)

            if not (chname in self.nukenames.keys()) :
                self.nukenames[chname] = []
            if len( self.nukenames[chname] ) > 10 :
                self.nukenames[chname].pop(0)
            self.nukenames[chname].append([to_re,banmsg])

            #
            #self.msgbuffers
            self.logger.debug(f'@{ctx.message.author.name} Ok, nuking name pattern: {banmsg}')
            matchlist = list(filter( lambda g: g[0] + 600 >= to_ts and  to_re.search(g[1])  , self.msgbuffers[ str(ctx.message.channel.name)  ]  ))
            matchnames = list(set([ g[1]  for g in matchlist ]))
            await ctx.send(f'@{ctx.message.author.name} Ok, nuking name pattern: {banmsg} ')
            for target in matchnames:
                 self.logger.debug(f'@{ctx.message.author.name} nukename ' + str(target) + '  matched_name')
                 await ctx.timeout(target, 1200, 'matched_name')
                 #self.last_temp[message.channel.name] = message.author.name
        except Exception as err:
            self.logger.error('nuketext error: ' + str(err))
            pass




    @commands.command(name='swpart')
    async def do_swpart(self,ctx):
        # Command not yet implemented
        try:
            privlev = await self.cmd_privilege_level(ctx.message.author)
            if privlev < 20:
                return
            self.logger.info('Command: ' + str(ctx.message.author.name) + ' :: ' + str(ctx.message.content))

            matchResult = re.match(r'^part( +(.*)|)', ctx.message.clean_content)
            if matchResult != None:
                try:
                    if matchResult.group(2) == None :
                        channelName = str(ctx.message.author.name).lower()
                        #await ctx.send(f'Usage: !swpart <username>')
                        #return
                    else:
                        #channelName  = ( matchResult.group(2) )
                        channelName = ( str(matchResult.group(2)).lower() )

                    if self.controlchannels and channelName in self.controlchannels :
                        await ctx.send(f'@{ctx.message.author.name} Wait, that is one of my control channels..')
                        return
                    if channelName != str(ctx.message.author.name).lower() and str(ctx.message.channel.name) not in self.controlchannels:
                        if  privlev < 50:
                            await ctx.send(f'@{ctx.message.author.name} Remote part requests outside my control channel are limited to the broadcaster.')
                            return


                    channelInfo =  await self.load_userinfo( [channelName] )

                    if channelInfo == None :
                        await ctx.send('Could not find that channel')
                        return
                    channelInfo = json.loads(channelInfo)

                    dbc = await self.get_cursor()

                    values = ( channelInfo["_id"], channelInfo["name"].lower(), 0, 0 )
                    #dbc.execute('INSERT IGNORE INTO chandata (twid,channame,requiretime,joinchannel) VALUES (%s,%s,%s,%s)', values)
                    self.logger.debug('SQL: UPDATE chanata SET joinchannel=0 where channame=' + str(channelInfo["name"]))
                    dbc.execute('UPDATE chandata SET joinchannel=0 WHERE channame=%s', (channelInfo["name"],))
                    self.logger.debug('part_channels ' + str( [ channelInfo["name"]  ]  ))

                    await ctx.send('Ok, @' + str(ctx.message.author.name) + ' - about to part  ' + str( [ channelInfo["name"]  ]  ) + '')
                    await self.part_channels( [ channelInfo["name"]  ] )
                    self.dbconnection.commit()
                    await self.load_chandata()

                    #self.logger.debug('check get_chatters ' + channelName)
                except Exception as err:
                    self.logger.error('swpart command error: ' + str(err))
                    self.logger.error('swpart tb: ' + str( traceback.format_exc()  ))
                    #traceback.print_exc()
                    pass
        except Exception as err:
            pass

    @commands.command(name='swallowlist')
    async def do_swallow(self,ctx):
        try:
            if await self.cmd_privilege_level(ctx.message.author) < 20:
                return
            self.logger.info('Command: ' + str(ctx.message.author.name) + ' :: ' + str(ctx.message.content))
            matchResult = re.match(r'^allowlist( +(.*)|)', ctx.message.clean_content)
            if matchResult != None:
                try:
                    if matchResult.group(2) == None :
                        await ctx.send(f'Usage: !allowlist <username>')
                        return
                    #channelName  = ( matchResult.group(2) )
                    username = ( matchResult.group(2) )
                    #self.logger.debug('check get_chatters ' + channelName)
                    dbc = await self.get_cursor()
                    #values = ( str(ctx.message.channel) ,  requiredTimeVal  )
                    #values = ( requiredTimeVal , str(ctx.message.channel.name.lower()) )
                    values = ( str(username).lower(), )
                    dbc.execute('UPDATE userdata SET level=10 WHERE level>=0 AND level<10 AND username=%s', values)
                    self.dbconnection.commit()
                    await ctx.send(f'Setting user option.')
                    await self.load_useropt(username)

                    #dbc.execute('REPLACE INTO chanrequire (channel, requiretime) VALUES (%s,%s)', values)
                    #self.dbconnection.commit()
                    #await self.load_chandata()
                    #await ctx.send(f'Ok, [ACTIVE] enforcement against accounts younger than  %d seconds.' % (requiredTimeVal))
                    #await ctx.send(f'Ok | {ctx.message.clean_content}')
                except Exception as err:
                    await ctx.send('Error processing request: ' + str(err))
                    pass
        except Exception as err:
            pass

    @commands.command(name='swblock')
    async def do_swblock(self,ctx):
        try:
            #await ctx.send(f'@{ctx.author.name} - swblock')
            c_plev = await self.cmd_privilege_level(ctx.message.author)
            if c_plev < 60:
                await ctx.send(f'@{ctx.message.author.name} - Privilege level too low ' + str(c_plev))
                return
            self.logger.info('Command: ' + str(ctx.message.author.name) + ' :: ' + str(ctx.message.content))
            matchResult = re.match(r'^block( +(.*)|)', ctx.message.clean_content)
            if matchResult != None:
                try:
                    if matchResult.group(2) == None :
                        await ctx.send(f'Usage: !swblock <username>')
                        return
                    username = ( matchResult.group(2) )
                    tuserobj = await self.load_useropt(str(username).lower())

                    if self.controlchannels and str(username).lower()  in self.controlchannels :
                        await ctx.send(f'@{ctx.message.author.name} Wait, that is one of my control channels..')
                        return
                    if tuserobj != None and tuserobj["level"] >= 60 :
                        await ctx.send(f'@{ctx.message.author.name} - No.  That username is a bot operator.')
                        return

                    dbc = await self.get_cursor()
                    values = ( str(username).lower(), )
                    dbc.execute('UPDATE userdata SET level=-1 WHERE level>=0 AND level<60 AND username=%s', values)
                    self.dbconnection.commit()
                    await ctx.send(f'Setting user option to block channel and user.')
                    await self.load_useropt(username)
                    dbc.execute('UPDATE chandata SET blockchannel=1 WHERE channame=%s', values)
                    self.dbconnection.commit()
                    await self.load_chandata()
                    await self.part_channels( [ str(username).lower()  ] )
                except Exception as err:
                    await ctx.send('Error processing request: ' + str(err))
                    pass
            else:
                await ctx.send(f'Usage: !swblock <username>')
        except Exception as err:
            self.logger.debug('swblock - exception: ' + str(err) )
            pass

    @commands.command(name='swunblock')
    async def do_swunblock(self,ctx):
        try:
            #await ctx.send(f'@{ctx.author.name} - swunblock')
            c_plev = await self.cmd_privilege_level(ctx.message.author)
            if c_plev < 60:
                await ctx.send(f'@{ctx.message.author.name} - Privilege level too low ' + str(c_plev))
                return
            self.logger.info('Command: ' + str(ctx.message.author.name) + ' :: ' + str(ctx.message.content))
            matchResult = re.match(r'^unblock( +(.*)|)', ctx.message.clean_content)
            if matchResult != None:
                try:
                    if matchResult.group(2) == None :
                        await ctx.send(f'Usage: !swunblock <username>')
                        return
                    username = ( matchResult.group(2) )
                    tuserobj = await self.load_useropt(str(username).lower())

                    dbc = await self.get_cursor()
                    values = ( str(username).lower(), )
                    dbc.execute('UPDATE userdata SET level=0 WHERE level=-1 AND username=%s', values)
                    self.dbconnection.commit()
                    await ctx.send(f'Setting user option to unblock channel and user.')
                    await self.load_useropt(username)
                    dbc.execute('UPDATE chandata SET blockchannel=0 WHERE channame=%s', values)
                    self.dbconnection.commit()
                    await self.load_chandata()
                except Exception as err:
                    await ctx.send('Error processing request: ' + str(err))
                    pass
            else:
                await ctx.send(f'Usage: !swunblock <username>')
        except Exception as err:
            self.logger.debug('swunblock - exception: ' + str(err) )
            pass

    @commands.command(name='swsetlevel')
    async def do_swsetlevel(self,ctx):
        try:
            #await ctx.send(f'@{ctx.author.name} - swunblock')
            c_plev = await self.cmd_privilege_level(ctx.message.author)
            if c_plev < 60:
                await ctx.send(f'@{ctx.message.author.name} - Privilege level too low ' + str(c_plev))
                return
            self.logger.info('Command: ' + str(ctx.message.author.name) + ' :: ' + str(ctx.message.content))
            matchResult = re.match(r'^setlevel( +(.*) (-?[0-9]+)|)', ctx.message.clean_content)
            if matchResult != None:
                try:
                    if matchResult.group(2) == None or matchResult.group(3) == None :
                        await ctx.send(f'Usage: !swsetlevel <username> <level>')
                        return
                    username = ( matchResult.group(2) )
                    newlevel = int( matchResult.group(3) )
                    if newlevel < -100 : 
                        newlevel = -100
                    if newlevel > 101 :
                        newlevel = 101
                    tuserobj = await self.load_useropt(str(username).lower())
                    if newlevel >= c_plev and c_plev < 100 :
                        await ctx.send(f'@{ctx.message.author.name} - Your level is only ' + str(c_plev) + ' cannot set a user higher than that.')
                        return
                    if (newlevel >= 60 or newlevel < -60) and c_plev < 70 : 
                        await ctx.send(f'@{ctx.message.author.name} - Your level is only ' + str(c_plev) + ' - you need to be level 70 or higher to make a bot admin or co-ordinated block.')
                        return
                    if (newlevel <= -80) and c_plev < 80: 
                        await ctx.send(f'@{ctx.message.author.name} - Your level is only ' + str(c_plev) + ' - you need to be level 80 or higher for this action.')
                    if c_plev >= 100 and str(username).lower() == str(ctx.message.author.name).lower() :
                        await ctx.send(f'@{ctx.message.author.name} - Do not reduce your own userlevel')
                        return
                    if tuserobj != None and int(tuserobj["level"]) >= c_plev and c_plev < 100 :
                        await ctx.send(f'@{ctx.message.author.name} - No. That username is same level or higher than yours.')
                        return

                    dbc = await self.get_cursor()
                    values = ( str(newlevel), str(username).lower(), )
                    dbc.execute('UPDATE userdata SET level=%s WHERE username=%s', values)
                    self.dbconnection.commit()
                    await ctx.send(f'Setting user option to update target user level.')
                    await self.load_useropt(username)
                except Exception as err:
                    await ctx.send('Error processing request: ' + str(err))
                    pass
            else:
                await ctx.send(f'Usage: !swsetlevel <username> <level>')
        except Exception as err:
            self.logger.debug('swunblock - exception: ' + str(err) )
            pass


    @commands.command(name='swcheck')
    async def do_load_chatters(self,ctx):
        try:
            requiredTimeVal = 0
            if await self.cmd_privilege_level(ctx.message.author) < 100:
                return
            self.logger.info('Command: ' + str(ctx.message.author.name) + ' :: ' + str(ctx.message.content))
            matchResult = re.match(r'^check( +(.*)|)', ctx.message.clean_content)
            if matchResult != None:
                try:
                    if matchResult.group(2) == None :
                        await ctx.send(f'Usage: !swcheck <channel>')
                        return
                    channelName  = ( matchResult.group(2) )
                    self.logger.debug('check get_chatters ' + channelName)
                    chatters = await self.get_chatters( channelName )
                    #
                    #
                    #
                    userinfo = await self.load_userinfo(chatters.all[0:98])
                    self.logger.debug('load_userinfo ' + str(chatters.all[0:98]))
                    if len(chatters.all)>99:
                        self.logger.debug('More than 99 chatters in '+str(channelName)+' loading more')
                        m = 0
                        while (len(chatters.all[m:])>99):
                            m = m+99
                            self.logger.debug('load_userinfo ' + str(chatters.all[0+m:98+m]))
                            userinfo = await self.load_userinfo(chatters.all[0+m:98+m])
                            time.sleep(1)
                    pass
                except Exception as rex1:
                    self.logger.error('do_load_chatters exception: ' + str(rex1))
                    pass
            else:
                await ctx.send(f'Usage: !swcheck <channel>')
                return

            #dbc = await self.get_cursor()
            ##values = ( str(ctx.message.channel) ,  requiredTimeVal  )
            #values = ( requiredTimeVal , str(ctx.message.channel.name.lower()) )
            #dbc.execute('UPDATE chandata SET requiretime=%s WHERE channame=%s', values)

            #dbc.execute('REPLACE INTO chanrequire (channel, requiretime) VALUES (%s,%s)', values)
            #self.dbconnection.commit()
            #await self.load_chandata()
            #await ctx.send(f'Ok, [ACTIVE] enforcement against accounts younger than  %d seconds.' % (requiredTimeVal))
            ##await ctx.send(f'Ok | {ctx.message.clean_content}')
            #print('XO:' + str( dir(ctx.message.author)  ) )
        except Exception as exv0: 
            await ctx.send(f'Error: an exception occurred: ' + str(exv0) )


    @commands.command(name='rhinfo')
    async def cmd_rhinfo(self,ctx):
        hacklist = loadsmwrh.get_hacklist_data(filename='../rhmd.dat')
        self.logger.debug('rhinfo  message:' + str(dir(ctx.message)))
        text = str(ctx.message.content)
        text = re.sub('[^ !_a-zA-z0-9]','_', str(text))
        paramResult = re.match(r'^!rhinfo( +(.*)|)', text)
        if paramResult != None:
           try:
              if paramResult.group(2) == None :
                 await ctx.send(f'Usage: !rhinfo <text>')
                 return
              else: 
                 text = paramResult.group(2).lower()
           except Exception as rex1:
                 self.logger.debug('ERR:rex1:' + str(rex1))
                 pass
        else:
           await ctx.send(f'Usage: !rhinfo <text>')
           return
        ###
        hresults = []
        hnames = ''
        foundEntry = None
        extras = '()'
        self.logger.debug('rhinfo:text=' + text)

        for h in hacklist: 
            if 'authors' in h and re.search(r'\b' + text + r'\b', h['authors'].lower()):
                hresults = hresults + [h]
                if not(hnames == ''):
                    hnames = hnames + '; '
                else:
                    hnames = hnames + ('By %s: ' % h['authors'])
                hnames = hnames + ('%s - %s' % (h['id'], h['name']))

        if hnames == '':
            for h in hacklist:
                namevalue = (':' + h['name'] + ':').lower()
                if len(text) < 2:
                    break
                if namevalue.find(':' + text + ':') >= 0:
                    foundEntry = h
                    break
                if text.lower() == h['id'].lower():
                    foundEntry = h
                    break
                if re.search(r'\b' + text + r'\b', h['name'].lower()):
                    foundEntry = h
                    break
                if re.search(r'\b' + text + r'\b', h['authors'].lower()):
                    foundEntry = h
                    break
                #
            #
            if foundEntry:
                fe = foundEntry
                urls = ''
                if 'url' in fe:
                    urls = fe['url']
                hnames = ('%s. %s by %s - %s - %s - %s - %s' % (fe['id'], fe['name'], fe['authors'], fe['length'], fe['type'], extras, urls))
            else:
                hnames = 'Could not find a game by that name.'
        await ctx.send('@' + str(ctx.message.author.name) + ' ' + str(hnames)  )
        ###

        
        


        
         
        



    @commands.command(name='require')
    async def age_setmin(self,ctx):
        try:
            requiredTimeVal = 0
            if await self.cmd_privilege_level(ctx.message.author) < 20:
                return
            self.logger.info('Command: ' + str(ctx.message.author.name) + ' :: ' + str(ctx.message.content))
            matchResult = re.match(r'^require( +(.*)|)', ctx.message.clean_content)
            if matchResult != None:
                try:
                    if matchResult.group(2) == None :
                        await ctx.send(f'Usage: !swrequire <duration>')
                        return
                    requiredTimeVal = int( matchResult.group(2) )
                except Exception as rex1:
                    pass
            else:
                await ctx.send(f'Usage: !swrequire <duration>')
                return

            dbc = await self.get_cursor()
            #values = ( str(ctx.message.channel) ,  requiredTimeVal  )
            values = ( requiredTimeVal , str(ctx.message.channel.name.lower()) )
            dbc.execute('UPDATE chandata SET requiretime=%s WHERE channame=%s', values)

            #dbc.execute('REPLACE INTO chanrequire (channel, requiretime) VALUES (%s,%s)', values)
            self.dbconnection.commit()
            await self.load_chandata()
            await ctx.send(f'Ok, [ACTIVE] enforcement against accounts younger than  %d seconds.' % (requiredTimeVal))
            #await ctx.send(f'Ok | {ctx.message.clean_content}')
            print('XO:' + str( dir(ctx.message.author)  ) )
        except Exception as exv0: 
            await ctx.send(f'Error: an exception occurred: ' + str(exv0) )

    async def load_useropt(self,username):
      try:
        dbc = await self.get_cursor()
        dbc.execute('SELECT * from userdata WHERE LOWER(username)=LOWER(%s)', (username,))
        records = dbc.fetchall()
        for record in records:
            rowval = dict(zip(dbc.column_names, record))
            mcloaduo = record[2]
            #self.client.set("usern_" + str(username), mcloaduo, self.cachettl)
            useroptobj = dict(rowval)
            useroptobj["jsondata"] = None
            self.client.set("useron_" + str(username).lower(), json.dumps(useroptobj), 86400)
            self.client.set("usero_" + str( useroptobj['twid']) , json.dumps(useroptobj), 86400 )
            return useroptobj
        return None
      except Exception as exv0:
        self.logger.error('Error in load_useropt dbread on ' + str(username) + ' : ' + str(exv0))
        pass

    async def get_useropt(self,username):
        aval = self.client.get("useron_" + str(username).lower())
        if aval == None :
            return await self.load_useropt(username)
        return json.loads(aval)

    async def load_chandata(self):
        try:
            if self.chandata == None : 
                chandata = {}
            else :
                chandata = {}
            dbc = await self.get_cursor()
            dbc.execute('SELECT * from chandata')
            records = dbc.fetchall()
            for record in records:
                rowval = dict(zip(dbc.column_names, record))
                self.channums[ record[1] ] = record[0]
                chandata[ record[0]  ] = rowval
                print(str(rowval))
            self.chandata = chandata
        except Exception as exv0:
            self.logger.error("ERR: load_chandata: " + str(exv0))


##############
setupfilename = 'botsetup.yaml'
if 'BOTCONFIG' in os.environ:
     setupfilename = os.environ['BOTCONFIG']

with open(setupfilename) as file:
     botconfig = yaml.load(file)

logger = logging.getLogger("swtbot")
logging.basicConfig(format='%(asctime)-15s %(message)s')
logger.setLevel(logging.DEBUG)

db = mysql.connect(
    host = "localhost",
    user = botconfig["mysql"]["user"],
    passwd = botconfig["mysql"]["password"],
    database = botconfig["mysql"]["database"]
)

logging.basicConfig(format='%(asctime)-15s %(clientip)s %(user)-8s %(message)s')
bot = Bot(botconfig)
bot.run()



