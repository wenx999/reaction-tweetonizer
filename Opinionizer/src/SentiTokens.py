# -*- coding: UTF-8 -*-
'''
Created on Apr 12, 2011

@author: samir
'''

import codecs
import Utils
import re

class SentiToken:
    
    lemma = ""
    flexions = []
    polarity = None

    def __init__(self,lemma,polarity,flexions=None):
    
        self.lemma = lemma
        self.flexions = flexions
        self.polarity = polarity
        
    def tostring(self):
        
        adj = "lemma: " + self.lemma + "\npolarity: " + self.polarity + "\nflexions: {"
        
        for f in self.flexions:
            
            adj += f+","
        
        return adj.strip(",") + "}"

    def isMatch(self,adjective):
            
            return adjective == self.lemma or adjective in self.flexions  
    
    def getTokens(self):
        
        tokens = [self.lemma]
        
        for flexion in self.flexions:
            
            tokens.append(flexion)
        
        return tokens
        
    
def loadSentiTokens(path,pathExceptions):

    f = codecs.open(path,"r", "utf-8")
    adjectives = []
    firstLine = f.next()
    exceptions = unicode(loadExceptionTokens(pathExceptions))       
    
    lemmaRegex = ",.*?\."     
    flexRegex = "^.*?,"
    polarityRegex = "POL=-1|POL=0|POL=1"
    
    currentLemma = re.findall(lemmaRegex,firstLine)[0].lstrip(',').rstrip('.')
    currentPolarity = re.findall(polarityRegex,firstLine)[0][4:]
    currentFlex = re.findall(flexRegex,firstLine)[0].rstrip(',')
    currentFlexions = []
    currentFlexions.append(currentFlex)
    
    if currentFlex not in exceptions and currentFlex != Utils.normalize(currentFlex):
                        
        currentFlexions.append(Utils.normalize(currentFlex))
       
    for line in f:
        
        try:
            if "REV=Amb" not in line:
                                                    
                lemma = re.findall(lemmaRegex,line)[0].lstrip(',').rstrip('.')
                
                if lemma != currentLemma:            
                    
                    if currentLemma not in exceptions and currentLemma != Utils.normalize(currentLemma):
                        
                        currentFlexions.append(Utils.normalize(currentLemma))
                                       
                    adjectives.append(SentiToken(currentLemma,currentPolarity,currentFlexions))                    
                    currentLemma = lemma
                    currentPolarity = re.findall(polarityRegex,line)[0][4:]                                   
                    currentFlexions = []
                    currentFlexions.append(re.findall(flexRegex,line)[0].rstrip(','))
                    
                else:   
                    currentFlex = re.findall(flexRegex,line)[0].rstrip(',')
                    currentFlexions.append(currentFlex)
                    
                    if currentFlex not in exceptions and currentFlex != Utils.normalize(currentFlex):
                        
                        currentFlexions.append(Utils.normalize(currentFlex))
                    
        except:
            None
    f.close()
    
    return adjectives

def loadExceptionTokens(path): 
    
    f = codecs.open(path,"r", "utf-8")    
    
    excpt = unicode(f.read())
    
    return excpt
    
if __name__ == "__main__":        
    
    print "Go"
    
    #loadExceptionTokens("../Resources/SentiLexAccentExcpt.txt")
    
    
    for a in loadSentiTokens("../Resources/sentiTokens.txt","../Resources/SentiLexAccentExcpt.txt"):
        
        None
        #print "-----------------------"
        #print a.tostring().encode("utf-8")
    
    print "Done"    