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

def twitAgain(proxy):
    
    consumer_key = "sEwbkfgkFU4B7l5DBuRvXw"
    consumer_secret = "aUAKFq3qpB7NqeHh89AIJL85ZXHORlmZ7WIczLoxE"    
    access_key = "284707222-ZRvtSilVFXGcEYT8AZ04STWP9q7VXofN3L3Ufx2s"
    access_secret = "1PkYjXaJWzSyd0K6Z4g5Wsg6NZ9iVNNOxI277ELrbqA"
    
    if proxy != None:
        #os.environ['HTTP_PROXY'] = proxy        
        proxy_handler = urllib2.ProxyHandler({'http': proxy})    
        opener = urllib2.build_opener(proxy_handler)
        urllib2.install_opener(opener)        
              
    # auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    #auth.set_access_token(access_key, access_secret)
    # api = tweepy.API(auth)
    
    #for f in api.followers():
        
    #     print f.name
        
    #api.update_status(status="And now for something completely different...")

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

def tokenizer():
    
    s = "Good muffins cost $3.88\nin New York.  Please!!! buy me\ntwo of them.\n\nThanks."
    
    print word_tokenize(s)
    print "-----------------------" 
    print wordpunct_tokenize(s)    

if __name__ == '__main__':
    
    print "GOOO!"
    
    print isFalsePositive("portas", "O portas é fixe")
    print isFalsePositive("portas", "O portas não sabe nadar")
    print isFalsePositive("portas", "às portas é fixe")
    print isFalsePositive("portas", "miguel portas é fixe")
    print isFalsePositive("portas", "portas de benfica é fixe")
    print isFalsePositive("portas", "eles abrem portas")
    print isFalsePositive("socrates", "eles abrem portas")
    
    
    
    print "Done!"