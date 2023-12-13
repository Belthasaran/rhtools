import json
import logging
import re
import crm114
import unidecode

class crm114test(object):
   def __init__(self):
       self.cltext = crm114.Classifier('/home/swtbot/textdata', ['good','spam','toxic'])


    
   def checkMessageFilter(self,text):
       label, confidence = self.cltext.classify( str(text) )
       text2 = unidecode.unidecode( str(text)  ).lower().replace('[?]','')
       label2, confidence2 = self.cltext.classify( str(text2) )

       if label != b'good'  or confidence < 1:
           logger.info("Line:{" + str(text) + "}")
           logger.info("Text2:" + str(text2))
           logger.info("Classification: {" + str(label) + "} {probability: " + str(confidence) + "} label2=" + str(label2) + ", prob2=" + str(confidence2))




            
logger = logging.getLogger("tester")
logging.basicConfig(format='%(asctime)-15s %(message)s')
logger.setLevel(logging.DEBUG)
tester = crm114test()

while True :
    val = input('')
    if val == None :
       exit()
    tester.checkMessageFilter(val)




