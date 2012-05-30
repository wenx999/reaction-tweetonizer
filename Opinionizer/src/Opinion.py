# -*- coding: UTF-8 -*-
'''
Created on Apr 8, 2011

@author: samir
'''

class Opinion:  
     
    def __init__(self, id, sentence, target=u'', mention=u'', polarity=u'', irony=u'',metadata=u'',user=None,date=None,processedSentence=None):        
        
        if sentence != None and type(sentence) != unicode: 
            raise Exception("\'sentence\' (" + sentence + ") must be in unicode! Not " + str(type(sentence)))
        
        if target != None and type(target) != unicode: 
            raise Exception("\'target\' (" + target + ") must be in unicode! Not " + str(type(target)))
        
        if mention != None and type(mention) != unicode :         
            raise Exception("\'mention\' (" + mention + ") must be in unicode! Not " + str(type(mention)))
        
        if metadata != None and type(metadata) != unicode: 
            raise Exception("\'metadata\' (" + metadata + " ) must be in unicode! Not " + str(type(metadata)))
        
        if user != None and type(user) != unicode: 
            raise Exception("\'user\' (" + user + " ) must be in unicode! Not " + str(type(user)))
        
        if processedSentence != None and type(processedSentence) != unicode: 
            raise Exception("\'processedSentence\' (" + processedSentence + " ) must be in unicode! Not " + str(type(processedSentence)))
                        
        self.id = id
        self.target = target
        self.irony = irony
        self.polarity = polarity
        self.sentence = sentence
        self.mention = mention
        self.metadata = metadata
        self.date = date
        self.user = user
        
        if processedSentence == None:
            self.processedSentence = sentence
        else:
            self.processedSentence = processedSentence
    
    def clone(self, target=u'', mention=u'', polarity=u'', irony=u'',metadata=u'',user=None,date=None,processedSentence = None):        
        
        newTarget = self.target
        newMention = self.mention
        newPolarity = self.polarity
        newIrony = self.irony
        newMetadata =  self.metadata
        newUser = self.user
        newDate = self.date
        newProcessedSentence = self.processedSentence
                         
        if target != None and target != '':
            newTarget = target
            
        if mention != None and mention != '':
            newMention = mention
            
        if polarity != None and polarity != '':
            newPolarity = polarity
            
        if irony != None and irony != '':
            newIrony = irony
            
        if metadata != None and metadata != '':
            newMetadata = metadata
            
        if user != None and user != '':
            newUser = user
            
        if date != None and date != '':
            newDate = date
        
        if processedSentence != None and processedSentence != '':
            newProcessedSentence = processedSentence
        
        return Opinion(self.id,self.sentence,newTarget,newMention,newPolarity,newIrony,newMetadata,newUser,newDate,newProcessedSentence) 
        
            
    def tostring(self):
        
        opinion = "id: " + str(self.id) + "\nsentence: " + self.sentence + "\nprocessed sentence: " + self.processedSentence         
        
        if self.target != None:
            opinion += "\ntarget: " + self.target
            
        if self.irony != None:
            opinion += "\nirony: " + self.irony
            
        if self.polarity != None:        
            opinion += "\npolarity: " + str(self.polarity)
        
        if self.mention != None:
            opinion += "\nmention: " + self.mention
            
        if self.metadata != None:
            opinion += "\nmetadata: " + self.metadata
        
        if self.user != None:
            opinion += "\nuser: " + str(self.user)
        
        if self.date != None:
            opinion += "\ndate: " + str(self.date)
            
        return opinion
    
    
if __name__ == '__main__': 
    
    
    o = Opinion(1,u"O sócrates e passos coelho são bff",u"socrates",u"sócrates",0,None,u"Manual",u"Manual",None)
    
    print o.tostring()   
    print "-----------------------"
    
    a = o.clone(polarity=-1,metadata=u"Clonado")
    
    print a.tostring() 
