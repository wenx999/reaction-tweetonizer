# -*- coding: UTF-8 -*-

'''
Created on Apr 27, 2011

@author: samir
'''

#import tweepy
import os
import urllib2
from nltk import word_tokenize, wordpunct_tokenize
import re
import contextRestrictions

def isFalsePositive(mention,sentence):
        
        left_context = {'portas': ['as','nas','às','miguel','abriu','abriram','abre','abrem','numeral','mais']}
        right_context = {'portas': ['de','do','da','das','dos']}
        
        tokens = re.findall(u'\w+',unicode(sentence),re.X)
        print tokens
        badTokens = []
        
        try:
            if mention in left_context:
                
                badTokens = left_context[mention]
                
                if tokens[tokens.index(mention)-1] in badTokens:
                    return True
            
            if mention in right_context:
    
                badTokens = right_context[mention]             
                
                if tokens[tokens.index(mention)+1] in badTokens:
                    return True
                
            return False
        except:
            print mention, " in ", sentence

def tokenizer2():
    
    regex = ur"(?:\W?macaquinho do chinês\W?)|(?:\W?nova iorque\W?)|(?:\W?big ben\W?)|(?:\W?qualquer coisa\W?)"
    
    str = u"Estava lá em plena ,nova iorque! Um macaquinho do chinês, tinha uma camisola do big ben ou qualquer coisa e não qualquer outra coisa"
    newSentence = str
    
    matches = re.findall(regex,str)
    print matches
    for match in matches:
            
            a = match.strip(' ').rstrip(' ')
            
            if a != "":
            
                r = a.replace(" ","_")
                newSentence = newSentence.replace(a,r)
            
            
    print str, " -> ", newSentence
    
def tokenizer():
    
    regex = ur"(?:\W?macaquinho do chinês\W?)|(?:\W?nova iorque\W?)|(?:\W?big ben\W?)|(?:\W?qualquer coisa\W?)"
    
    str = u"Estava lá em plena ,nova iorque! Um macaquinho do chinês, tinha uma camisola do big ben ou qualquer coisa e não qualquer outra coisa"
    newSentence = str
    
    matches = re.findall(regex,str)
    print matches
    for match in matches:
        
        for m in match:
            
            a = m.strip(' ').rstrip(' ')
            
            if a != "":
            
                r = a.replace(" ","_")
                newSentence = newSentence.replace(a,r)
            
            
    print str, " -> ", newSentence
   
if __name__ == '__main__':
    
    print "GOOO!"
    
    for v in contextRestrictions.left_context.itervalues():
        print v
    
    print "Done!"