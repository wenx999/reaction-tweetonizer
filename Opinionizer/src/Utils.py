# -*- coding: UTF-8 -*-

'''
Created on Apr 13, 2011

@author: samir
'''

import codecs
import pickle

def getFromCache(filename):
    
    obj = None
    
    try:
        f = open(filename, "r")
        print filename    
        obj = pickle.load(f)
    except IOError:
        obj = None
        
    return obj

def putInCache(obj, filename):
    
    f = open(filename, "w")
    
    try:
        pickle.dump(obj,f, pickle.HIGHEST_PROTOCOL)
    except IOError:
        print "ERROR: Couldn't save cache..."
    


def logAnalyzedTweets(listOfTweets,path):
    
    """ Writes a log (csv file) of the classified tweets """
    
    print "Writting log of analyzed tweets: " + path
     
    f = codecs.open(path,"w","utf-8")
    
    #Column headers
    f.write("DATE|ID|USER|TARGET|MENTION|POLARITY|INFO|MESSAGE|TAGGED\n")    
        
    for tweet in listOfTweets:            
        
        date = tweet.date
        target = tweet.target.replace("\n"," ")
        mention = tweet.mention.replace("\n"," ")
        metadata = tweet.metadata.replace("\n"," ")
        sentence = tweet.sentence.replace("|","\\").replace("\n"," ").replace("\t"," ").replace("\r"," ")
        processedSentence = tweet.processedSentence.replace("|","\\").replace("\n"," ").replace("\t"," ").replace("\r"," ")
        
        f.write(str(date)+"|"+"\""+str(tweet.id) + "\"|" + tweet.user + "|\"" + target  + "\"|\"" + mention + "\"|" + str(tweet.polarity ) + "|\"" + metadata +  "\"|\"" + sentence + "\"|\"" + processedSentence + "\"\n")
    
    f.close()

if __name__ == '__main__':
    
    print "go"