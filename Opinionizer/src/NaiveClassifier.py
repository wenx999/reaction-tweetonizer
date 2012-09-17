# -*- coding: UTF-8 -*-
'''
Created on Sep 10, 2012

@author: samir
'''

import re
import StringIO
import contextRestrictions
import Preprocessor

#import Utils 
#import Persons
#import SentiTokens
#import codecs
#from Opinion import Opinion
#import pickle

SENTI_CACHE = "../cache/sentiTokens.cache"
PERSONS_CACHE = "../cache/persons.cache"
MULTIWORD_CACHE = "../cache/multiwords.cache"

debug = False

class Naive:
 
    def __init__(self,sentiTokens):    
                
        self.sentiTokens = sentiTokens    
        
        buff = StringIO.StringIO()
        buff.write(u'')
        
        #regexTemplate = ur"(?:\W|^){0}(?:\W|$)|"
        regexTemplate = ur"(?:\W+|^){0}(?:\W+|$)|"
        #regexTemplate = ur"\W+{0}\W+|"        
                        
        buff = StringIO.StringIO()
                 
        # Build a regex for identifying sentiment tokens
        for sentiToken in sentiTokens:
            
            for token in sentiToken.getTokens():
                
                buff.write(regexTemplate.format(token))  
        
        self.sentiTokensRegex = buff.getvalue().strip('|')
    
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

    def inferPolarity(self,opinion,useProcessedSentence):        
        
        """ 
            Tries to identify the polarity of a sentence
            Params: opinion -> Opinion object
                    useProcessedSentence -> True to use the tagged (and tokenized) version of the sentence
            Returns: tuple(inferred polarity, algorithm metadata)
        """
        info = opinion.metadata + "; " + u'sentiTokens:'       
        specialChars = u' “”\"@)(!#;&:\\@/-_,?.«»\' ' 
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
            
        score = 0
        
        #Find matches
        matches = re.findall(self.sentiTokensRegex ,sentence)
        
        foundTokens = {}
                 
        if matches != None and len(matches) > 0:     
            
            for match in matches:
                
                token = match.rstrip(specialChars).lstrip(specialChars)
                
                for adj in self.sentiTokens:
            
                    if adj.isMatch(token): 
                        
                        #store found tokens in a dictionary to avoid duplicate tokens
                        foundTokens[token] = adj.polarity 
                        
            #register found tokens and sum scores of polarities                        
            for token, polarity in foundTokens.items():
                
                score += int(polarity)                        
                info += token + "(" + polarity + ") " 
        
        info += '; score:' + unicode(score) + ";"        
        
        polarity = None
        
        if score > 0:
            polarity = 1
        
        elif score < 0:
            polarity = -1
        else:
            polarity = 0            
                    
        return opinion.clone(polarity=polarity,metadata=info)
       
    def getSentiScore(self,opinion,useProcessedSentence):        
        
        """ 
            Tries to identify the polarity of a sentence
            Params: opinion -> Opinion object
                    useProcessedSentence -> True to use the tagged (and tokenized) version of the sentence
            Returns: tuple(inferred polarity, algorithm metadata)
        """
        info = opinion.metadata + "; " + u'sentiTokens:'       
        specialChars = u' “”\"@)(!#;&:\\@/-_,?.«»\' ' 
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
            
        score = 0
         
        #Find matches
        matches = re.findall(self.sentiTokensRegex ,sentence)
        
        foundTokens = {}
                 
        if matches != None and len(matches) > 0:     
            
            for match in matches:
                
                token = match.rstrip(specialChars).lstrip(specialChars)
                
                for adj in self.sentiTokens:
            
                    if adj.isMatch(token): 
                        
                        #store found tokens in a dictionary to avoid duplicate tokens
                        foundTokens[token] = adj.polarity 
                        
            #register found tokens and sum scores of polarities                        
            for token, polarity in foundTokens.items():
                
                score += int(polarity)                        
                info += token + "(" + polarity + ") " 
        
        info += '; score:' + unicode(score) + ";"        
        
        return (score,info)
    
    def getSentiFeats(self,opinion,useProcessedSentence):        
        
        """ 
            Tries to identify the polarity of a sentence
            Params: opinion -> Opinion object
                    useProcessedSentence -> True to use the tagged (and tokenized) version of the sentence
            Returns: tuple(inferred polarity, algorithm metadata)
        """
        info = opinion.metadata + "; " + u'sentiTokens:'       
        specialChars = u' “”\"@)(!#;&:\\@/-_,?.«»\' ' 
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
            
        score = 0
        
        #Find matches
        matches = re.findall(self.sentiTokensRegex ,sentence)
        
        foundTokens = {}
        
        scorePos = 0
        scoreNeg = 0
        scoreNeut = 0
        
        if matches != None and len(matches) > 0:     
            
            for match in matches:
                
                token = match.rstrip(specialChars).lstrip(specialChars)
                
                for adj in self.sentiTokens:
            
                    if adj.isMatch(token): 
                        
                        if int(adj.polarity) > 0:
                            scorePos += 1
                        elif int(adj.polarity) < 0:
                            scoreNeg += 1
                        else:
                            scoreNeut += 1
                                            
        
        return (scorePos,scoreNeut,scoreNeg)
    
    def getSentiTokens1(self,opinion,useProcessedSentence):        
        
        """ 
            Tries to identify the polarity of a sentence
            Params: opinion -> Opinion object
                    useProcessedSentence -> True to use the tagged (and tokenized) version of the sentence
            Returns: tuple(inferred polarity, algorithm metadata)
        """
        #info = opinion.metadata + "; " + u'sentiTokens:'       
        specialChars = u' “”\"@)(!#;&:\\@/-_,?.«»\' ' 
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        negativeTokens = []
        positiveTokens = []
        
        for sentiToken in self.sentiTokens:
            
            for s in sentiToken.getTokens():
                
                if sentence.find(s) > -1:
                    #print s, "(",sentiToken.polarity, ")"
                    if sentiToken.polarity == str(-1):
                        negativeTokens.append(s)
                    elif sentiToken.polarity == str(1):
                        positiveTokens.append(s)
                            
        return (positiveTokens,negativeTokens)
    
    def getSentiTokens(self,opinion,useProcessedSentence): 
    
        """ 
            Tries to identify the polarity of a sentence
            Params: opinion -> Opinion object
                    useProcessedSentence -> True to use the tagged (and tokenized) version of the sentence
            Returns: tuple(inferred polarity, algorithm metadata)
        """
        #info = opinion.metadata + "; " + u'sentiTokens:'       
        specialChars = u' “”\"@)(!#;&:\\@/-_,?.«»\' ' 
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        negativeTokens = []
        positiveTokens = []
        
        matches = re.findall(self.sentiTokensRegex ,sentence)        
                 
        if matches != None and len(matches) > 0:     
            
            for match in matches:
                
                token = match.rstrip(specialChars).lstrip(specialChars)                
                
                for adj in self.sentiTokens:
                    
                    if adj.isMatch(token):
                        if debug:
                            print "M)", match, " -> T)", token, " -> L)", adj.lemma                         
                        if adj.polarity == str(-1):
                            negativeTokens.append(token)
                        elif adj.polarity == str(1):
                            positiveTokens.append(token)
                        break                       
                            
        return (positiveTokens,negativeTokens)
    
    def tokenizeSentiTokens(self,opinion,useProcessedSentence): 
    
        """ 
            Tries to identify the polarity of a sentence
            Params: opinion -> Opinion object
                    useProcessedSentence -> True to use the tagged (and tokenized) version of the sentence
            Returns: tuple(inferred polarity, algorithm metadata)
        """
        #info = opinion.metadata + "; " + u'sentiTokens:'       
        specialChars = u' “”\"@)(!#;&:\\@/-_,?.«»\' ' 
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        negativeTokens = []
        positiveTokens = []
        
        splitter = re.compile(r'(\s+|\S+)')
        
        matches = splitter.findall(sentence)        
                 
        if matches != None and len(matches) > 0:     
            
            for match in matches:
                
                token = match.rstrip(specialChars).lstrip(specialChars)                
                
                for adj in self.sentiTokens:
                    
                    if adj.isMatch(token):
                        if debug:
                            print "M)", match, " -> T)", token, " -> L)", adj.lemma                         
                        if adj.polarity == str(-1):
                            negativeTokens.append(token)
                        elif adj.polarity == str(1):
                            positiveTokens.append(token)
                        break                       
                            
        return (positiveTokens,negativeTokens)