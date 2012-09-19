# -*- coding: utf-8 -*-

'''
Created on Apr 12, 2011

@author: samir
'''

import codecs
import Preprocessor

debug = False

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

def loadPoliticians(filename):
    # this function to be deprecated. Please invoke loadTargetsFromFile below
    return loadTargetsFromFile(filename)

def loadTargetsFromFile(filename):
    # load targets, their names, nicknames and ergonyms from given file into an array of three lists.
    # returns the array.
    # names with accents and cedilla are duplicated after normalization, except if escaped with ^.
    #
    
    NAMES = 0
    NICKNAMES = 1
    ERGOS = 2
    
    f = codecs.open(filename,"r", "utf-8")
    
    targets = []
    
    for fileLine in f:
        
        line = fileLine.lower()


        # lines starting with "#" are skipped -- mjs 2011.10.27
        if line[0] == '#':
            if debug: print "skipped: ", line
            continue
        
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

                    if debug: print "cleanName = ", cleanName
                    
                    if cleanName != '':
                        if cleanName[0] != '^':
                            names.append(cleanName)
                            if cleanName != Preprocessor.normalize(cleanName): 
                                names.append(Preprocessor.normalize(cleanName))
                                if debug: print "appended clean name", cleanName

                        else:
                            names.append(cleanName[1:])
                            if debug: print "appended unclean name", cleanName,  cleanName[1:]
                       
            except IndexError:
                None
            
            try: 
                nicknamesTokens = mentions[NICKNAMES]
                
                for name in nicknamesTokens.split(','):
                    
                    cleanName = name.replace("\n","").strip(' ').rstrip(' ')

                    if debug: print "cleanName (nickname) = ", cleanName


                    if cleanName != '':
                        if cleanName[0] != '^':
                            nicknames.append(cleanName)
                            if cleanName != Preprocessor.normalize(cleanName): 
                                nicknames.append(Preprocessor.normalize(cleanName))
                                if debug: print "appended clean nickname", cleanName, Preprocessor.normalize(cleanName)

                        else:
                            nicknames.append(cleanName[1:])
                            if debug: print "appended uncleaned nickname ", cleanName, cleanName[1:]

            except IndexError:
                None
                
            try:                        
                ergoTokens = mentions[ERGOS]
                
                for name in ergoTokens.split(','):
                    cleanName = name.replace("\n","").strip(' ').rstrip(' ')

                    if debug: print "cleanName (ergonym) = ", cleanName


                    if cleanName != '':
                        if cleanName[0] != '^':
                            ergos.append(cleanName)
                            if cleanName != Preprocessor.normalize(cleanName): 
                                ergos.append(Preprocessor.normalize(cleanName))
                                if debug: print "appended clean ergonym", cleanName, Preprocessor.normalize(cleanName)

                        else:
                            ergos.append(cleanName[1:])  
                            if debug: print "appended uncleaned ergonym", cleanName, cleanName[1:],
            
            except IndexError:
                None
                   
            targets.append(Person(id,names,nicknames,ergos))
                
    f.close()

    return targets


    
if __name__ == "__main__":        

    debug = True
    
    targetsFilename = "../Resources/euroTargets.txt"
    
    print "Go, persons file is ", targetsFilename
    
    targets = loadTargetsFromFile(targetsFilename) 

    print "...loaded"
    
    for a in targets:
        
        print "**** target: "

        print a.tostring()

        #for m in a.listOfMentions.iterkeys():
        #    print m
    
    
    print "------ multi palavras: ------"
    
    #for mw in getMultiWords(targets):
        
    #    print mw 
    
    print "Done."    
