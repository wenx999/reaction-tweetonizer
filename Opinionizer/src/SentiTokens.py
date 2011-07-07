# -*- coding: UTF-8 -*-
'''
Created on Apr 12, 2011

@author: samir
'''

import codecs
import Utils
import re

class SentiToken:

    def __init__(self,lemma,polarity,pos,flexions=None):
    
        self.lemma = lemma        
        self.polarity = polarity
        self.pos = pos
        self.flexions = []
        self.tokens = {} 
        
        token = lemma.strip(' ').rstrip(' ')
        
        self.tokens[token] = ''        
        multiword = token.replace(" ","_")
        
        #if ' ' was replaced with '_' then it's a multiword        
        if "_" in multiword:            
            self.tokens[multiword] = ''            
        
        #for words with "-" generate a version without the "-"
        #and a version "multiword friendly" (with "_" instead of " ")
        if "-" in token and token not in self.tokens:
            self.tokens[token.replace("-"," ")] = ''
            self.tokens[token.replace("-","_")] = ''
            self.flexions.append(token.replace("-"," "))
            self.flexions.append(token.replace("-","_"))
            
        
        if flexions != None:
            
            for flexion in flexions: 
                
                token = flexion.strip(' ').rstrip(' ')
                self.flexions.append(token)
                self.tokens[token] = ''    
                
                multiword = token.strip(' ').rstrip(' ').replace(" ","_")
                
                if "_" in multiword:
                    self.flexions.append(multiword)
                    self.tokens[multiword] = ''     
                
                #for words with "-" generate a version without the "-"
                #and a version "multiword friendly" (with "_" instead of " ")
                if "-" in token and token not in self.tokens:
                    self.tokens[token.replace("-"," ")] = ''
                    self.flexions.append(token.replace("-"," "))
                    self.flexions.append(token.replace("-","_"))
                    self.tokens[token.replace("-","_")] = ''
        
    def tostring(self):
        
        adj = "lemma: " + self.lemma + "\npolarity: " + self.polarity + "\nPOS:" + self.pos + "\nflexions: {"
        
        for f in self.flexions:
            
            adj += f+","
        
        return adj.strip(",") + "}"

    def isMatch(self,token):
            
            #return adjective == self.lemma or adjective in self.flexions
            return token in self.tokens  
    
    def getTokens(self):
        
        return list(self.tokens.iterkeys())
        
    
def loadSentiTokens(path,pathExceptions):

    f = codecs.open(path,"r", "utf-8")
    adjectives = []
    firstLine = f.next()
    exceptions = unicode(loadExceptionTokens(pathExceptions))       
    
    lemmaRegex = ",(.*?)\."     
    flexRegex = "^(.*?),"    
    polarityRegex = "POL:..=(-1|0|1)(;|$)"
    posRegex = "PoS=(.*?);"
    
    currentLemma = re.search(lemmaRegex,firstLine).group(1)
    currentPolarity = re.search(polarityRegex,firstLine).group(1)
    currentPos = re.search(posRegex,firstLine).group(1).lower()
    currentFlex = re.search(flexRegex,firstLine).group(1)
    currentFlexions = []
    currentFlexions.append(currentFlex)
    
    if currentFlex not in exceptions and currentFlex != Utils.normalize(currentFlex):
                        
        currentFlexions.append(Utils.normalize(currentFlex))
       
    for line in f:
        
        try:
            if "REV=Amb" not in line:               
                
                lemma = re.search(lemmaRegex,line).group(1)
                #print re.search(lemmaRegex,line).groups()
                
                if lemma != currentLemma:            
                    
                    if currentLemma not in exceptions and currentLemma != Utils.normalize(currentLemma):
                        
                        currentFlexions.append(Utils.normalize(currentLemma))
                                
                    adjectives.append(SentiToken(currentLemma,currentPolarity,currentPos,currentFlexions))
                                        
                    currentLemma = lemma                    
                    currentPolarity = re.search(polarityRegex,line).group(1)                    
                    currentPos = re.search(posRegex,line).group(1).lower()
                    currentFlexions = []
                    currentFlex = re.search(flexRegex,line).group(1)
                    currentFlexions.append(currentFlex)    
                    
                    #print "L:", currentLemma,"P:",currentPolarity,"POS:",currentPos,"F:",currentFlex
                    
                    if currentFlex not in exceptions and currentFlex != Utils.normalize(currentFlex):
                        
                        currentFlexions.append(Utils.normalize(currentFlex))
                    
                else:   
                    currentFlex = re.search(flexRegex,line).group(1)
                    currentFlexions.append(currentFlex)
                    
                    #print "l:", lemma, "f:", currentFlex, "p:", currentPos
                    if currentFlex not in exceptions and currentFlex != Utils.normalize(currentFlex):
                        
                        currentFlexions.append(Utils.normalize(currentFlex))
                    
        except:
            None
    f.close()    
    
    return adjectives

def getMultiWords(listOfSentiTokens):
    
    multiWords = []
    
    for sentiToken in listOfSentiTokens:
        
        tokens = sentiToken.getTokens()
        
        for token in tokens:
            
            if token.find(" ") > 0:
                
                multiWords.append(token)
    
    return multiWords

def loadExceptionTokens(path): 
    
    f = codecs.open(path,"r", "utf-8")    
    
    excpt = unicode(f.read())
    
    return excpt
    
if __name__ == "__main__":        
    
    print "Go"
    
    #loadExceptionTokens("../Resources/SentiLexAccentExcpt.txt")
    f = codecs.open("res.txt","w","utf-8")
    
    sentiTokens = loadSentiTokens("../Resources/sentiTokens-2011-05-30.txt","../Resources/SentiLexAccentExcpt.txt")
        
    for a in sentiTokens:
        
        None
        print "-----------------------"
        print a.tostring().encode("utf-8")        
        #f.write(a.tostring().encode("utf-8"))
        #f.write("\n-----------------------\n")
    
    print len(sentiTokens)
    f.close()
    
    #mws = getMultiWords(sentiTokens)
    
    #print "multi palavras"
    
   # for mw in mws:
        
   #     print mw
    
    print "Done"    