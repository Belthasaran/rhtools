import json
import logging
import re
import sys

class PatternTester(object):
   def __init__(self):
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
    
   def checkMessageFilter(self,text):
            wordsearchresult = self.wordFilterRE.search(str(text).lower())
            namesearchresult = self.nameFilterRE.search(str(text).lower())
            spamsearchresult = self.spamFilterRE.search(str(text).lower())
            logger = logging.getLogger("tester")

            #logger.info("Checking text:{" + str(text) + "}")
            if wordsearchresult != None :
                 logger.info("Line:{" + str(text) + "}")
                 logger.info("Match! Phrase filter: {" +
                  str(text[wordsearchresult.start():wordsearchresult.end()]) +
                       "}")
            if namesearchresult != None :
                 logger.info("Line:{" + str(text) + "}")
                 logger.info("Match! Phrase filter: {" + 
                  str(text[namesearchresult.start():namesearchresult.end()]) +
                       "}")
            if spamsearchresult != None :
                 logger.info("Line:{" + str(text) + "}")
                 logger.info("Match! Phrase filter: {" +
                  str(text[spamsearchresult.start():spamsearchresult.end()]) +
                       "}")




            
logger = logging.getLogger("tester")
logging.basicConfig(format='%(asctime)-15s %(message)s')
logger.setLevel(logging.DEBUG)
tester = PatternTester()

#while True :
    #val = input('')

for val in sys.stdin:
    if val == None :
       exit()
    tester.checkMessageFilter(val)




