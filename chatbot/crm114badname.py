import json
import logging
import re
import crm114nam

class crm114test(object):
   def __init__(self):
       self.cltext = crm114nam.Classifier('/home/swtbot/namedata', ['good','bad'])


    
   def checkMessageFilter(self,text):
       if len(text)<8:
           return
       logger.info("Before:" + str( self.cltext.classify( str(text) )  ) )
       self.cltext.learn('bad', str(text))
       label, confidence = self.cltext.classify( str(text) )
       logger.info("After:" + str( self.cltext.classify( str(text) )  ) )

       if label != b'good'  or confidence < 0.60:
           logger.info("Line:{" + str(text) + "}")
           logger.info("Classification: {" + str(label) + "} {probability: " + str(confidence) + "}")




            
logger = logging.getLogger("tester")
logging.basicConfig(format='%(asctime)-15s %(message)s')
logger.setLevel(logging.DEBUG)
tester = crm114test()

while True :
    val = input('')
    if val == None :
       exit()
    tester.checkMessageFilter(val)




