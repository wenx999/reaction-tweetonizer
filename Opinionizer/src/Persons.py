'''
Created on Apr 12, 2011

@author: samir
'''

import codecs
import Utils

class Person:    

    id = ""
    target = ""
    names = []
    nicknames = []
    ergos = []
          
    def __init__(self,id,names,nicknames,ergos,target=None):
        
        self.id = id
        self.names = names
        self.nicknames = nicknames
        self.ergos = ergos
        
        if target != None:
        
            self.target = target
        else:
            self.target = names[0]    
    
    def isMatch(self,name):
        
        return name in self.names or name in self.ergos or name in self.nicknames
    
    def isNickname(self,name):
        
        return name in self.nicknames
    
    def mentions(self):
        
        listOfMentions = []
        
        for name in self.names:
            
            listOfMentions.append(name)
        
        for nick in self.nicknames:
            
            listOfMentions.append(nick)
            
        for ergo in self.ergos:
            
            listOfMentions.append(ergo)
        
        return listOfMentions
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
    
    for a in loadPoliticians("../Resources/politicians.txt"):
        
        #None        
        print a.tostring()
        print "-----------------------"
    
    print "Done"    