'''
Created on Apr 12, 2011

@author: samir
'''

import codecs
import Utils

class Person:    
          
    def __init__(self,id,names,nicknames,ergos,target=None):
        
        self.id = id
        self.names = names
        self.nicknames = nicknames
        self.ergos = ergos
        self.listOfMentions = {}
        
        if target != None:
        
            self.target = target
        else:
            self.target = names[0]
        
        for name in self.names:
            
            self.listOfMentions[name] = ''
        
        for nick in self.nicknames:
            
            self.listOfMentions[nick] = ''
            
        for ergo in self.ergos:
            
            self.listOfMentions[ergo] = ''    
    
    def isMatch(self,name):
        
        return name in self.listOfMentions
    
    def isNickname(self,name):
        
        return name in self.nicknames
    
    def mentions(self):
        
        return list(self.listOfMentions.iterkeys())
    
    def tostring(self):
        
        per = "id: " + self.id + "\ntarget: " + self.target + "\nnames: {"
        
        for name in self.names:
            
            per += name + ","
        
        per = per.strip(",\n") + "}\nnickname: {"
        
        for nickname in self.nicknames:
            
            per += nickname + ","
        
        per = per.strip(",\n") + "}\nergonyms: {"
        
        for ergonym in self.ergos:
            
            per += ergonym + ","
        
        return per.strip(",\n") + "}"
        

def getMultiWords(listOfPersons):
    
    multiWords = []
    
    for person in listOfPersons:
        
        mentions = person.mentions()
        
        for mention in mentions:
            
            if mention.find(" ") > 0:
                
                multiWords.append(mention)
    
    return multiWords

def loadPoliticians(path):
    
    NAMES = 0
    NICKNAMES = 1
    ERGOS = 2
    
    f = codecs.open(path,"r", "utf-8")
    
    politicians = []
    
    #The first line contains the exceptions
    exceptions = f.next().lower()
   
    
    for fileLine in f:
        
        line = fileLine.lower()   
        
        sepIndex = line.find(":")
        id = line[0:sepIndex]
        
        names = []
        nicknames = []
        ergos = []
        
        if id != None and id != '':
        
            mentions = line[sepIndex+1:].split(';') 
            
            try:
            
                namesTokens = mentions[NAMES]
                
                for name in namesTokens.split(','):                    
                    
                    cleanName = name.replace("\n","").strip(' ').rstrip(' ')
                    
                    if cleanName != '':
                        names.append(cleanName)
                       
                        if cleanName not in exceptions and cleanName != Utils.normalize(cleanName): 
                       
                            names.append(Utils.normalize(cleanName))
            
            except IndexError:
                None
            
            try: 
                nicknamesTokens = mentions[NICKNAMES]
                
                for name in nicknamesTokens.split(','):
                    
                    cleanName = name.replace("\n","").strip(' ').rstrip(' ')                    
                    
                    if cleanName != '' and len(cleanName) > 1:
                        nicknames.append(cleanName)
                        
                        if cleanName not in exceptions and cleanName != Utils.normalize(cleanName): 
                            nicknames.append(Utils.normalize(cleanName))
                    
            except IndexError:
                None
                
            try:                        
                ergoTokens = mentions[ERGOS]
                
                for name in ergoTokens.split(','):
                    
                    cleanName = name.replace("\n","").strip(' ').rstrip(' ')
                    
                    if cleanName != '':
                        ergos.append(cleanName)
                        
                        if cleanName not in exceptions and cleanName != Utils.normalize(cleanName): 
                            
                            ergos.append(Utils.normalize(cleanName))     
            
            except IndexError:
                None
                   
            politicians.append(Person(id,names,nicknames,ergos))
                
    f.close()

    return politicians


    
if __name__ == "__main__":        
    
    print "Go"
    
    politicians = loadPoliticians("../Resources/politicians.txt") 
    
    for a in politicians:
        
        #None        
        print a.tostring()
        for m in a.listOfMentions.iterkeys():
            print m
        print "-----------------------"
    
    mws = getMultiWords(politicians)
    
    print "multi palavras:"
    
    for mw in mws:
        
        print mw 
    
    print "Done"    