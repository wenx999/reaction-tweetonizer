# -*- coding: UTF-8 -*-
'''
Created on Sep 10, 2012

@author: samir
'''

import re
import Preprocessor
import contextRestrictions

class TargetDetector:
    
    '''
    classdocs
    '''

    targets = None    
    targetsRegex = ""
    
    def __init__(self,targets):
    
        self.targets = targets
        
        for target in self.targets:            
            
            for name in target.names:
                    
                    self.targetsRegex += ".?" +name + ".?|"                   
            
            for name in target.nicknames:
                    
                    self.targetsRegex += ".?" +name + ".?|"
                    
            for name in target.ergos:
                    
                    self.targetsRegex += ".?" +name + ".?|"

        self.targetsRegex = self.targetsRegex.strip('|')
    
    def isFalsePositive(self,mention,sentence):
        
        """
            Determines if a mention is a false positive
            by looking for the context (ahead and behind)
        """
        
        tokens = re.findall(u'\w+',sentence,re.U)
        nMention = unicode(mention)
        
        try:
            if nMention in contextRestrictions.left_context:
        
                badTokens = contextRestrictions.left_context[nMention]
                
                if tokens[tokens.index(nMention)-1] in badTokens:
                    print "Discarded (left) " + nMention + " in " + "**" + sentence.replace('\n',' ') + "**"
                    return True
            
            if mention in contextRestrictions.right_context:
                
                badTokens = contextRestrictions.right_context[nMention]             
                
                if tokens[tokens.index(nMention)+1] in badTokens:
                    print "Discarded (right) " + nMention + " in " + "**" +  sentence.replace('\n',' ') + "**"
                    return True
                
            return False
        except:            
            return False
            
    
    def inferTarget(self,opinion):
        
        """ 
            Tries to identify mentions of the targets in a message
            Params: opinion -> Opinion object
            Returns: tuple(inferred target, algorithm metadata)
        """
       
        info = u"Targets: "
        sentence = Preprocessor.separateSpecialSymbols(opinion.sentence.lower()) 
        #print sentence
        
        matches = []
        
        for target in self.targets:            
            
            for name in target.names:
                                   
                if sentence.find(" "+name+" ") != -1:
                    
                    matches.append(name)
            
            for nickName in target.nicknames:
                    
                if sentence.find(" "+nickName+" ") != -1:
                    
                    matches.append(nickName)
                    
            for ergo in target.ergos:
                
                if sentence.find(" "+ergo+" ") != -1:
                    
                    matches.append(ergo)                
            
        targets = {}
        
        for mention in matches:
            
            targetId = self.getTargetByMention(mention)
            
            if targetId != None and not self.isFalsePositive(mention, sentence):                    
                
                if mention not in info:
                    info += mention + ","
                    
                targets[targetId] = mention
        
        if len(targets) > 0:
            
            results = []
            info = info.strip(',')
        
            for target,mention in targets.items():
                
                results.append(opinion.clone(target=target,mention=mention,metadata=info))
             
            return results
        else:
            
            return None                     
                
    def getTargetByMention(self,mention):       
        
        """
            Returns the target name by mention
        """
        
        for target in self.targets:
            
            if target.isMatch(mention):
                
                return target.id
        
        return None

                
    def replaceNameWithTarget(self,name):       
                
        for target in self.targets:
            
            if target.isMatch(name):
                
                return target.id
        
        return None

    