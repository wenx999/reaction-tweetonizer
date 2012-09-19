# -*- coding: UTF-8 -*-

'''
Created on Apr 21, 2011

@author: samir
'''

import Persons 
import SentiTokens
import Utils
from MultiWordHelper import MultiWordHelper
from NaiveClassifier import Naive
from RulesClassifier import Rules
from TargetDetector import TargetDetector
from Opinion import Opinion

from datetime import datetime,timedelta
import time
import urllib
import urllib2
import simplejson
import codecs
import sys
import re


TARGET = 0
N_TWEETS = 1
POSITIVES = 2
NEUTRALS = 3
NEGATIVES = 4

SENTI_CACHE = "../cache/sentiTokens.cache"
PERSONS_CACHE = "../cache/persons.cache"
MULTIWORD_CACHE = "../cache/multiwords.cache"
"""
WIN_SENTI_CACHE = "D:\workspace\Opinionizer\cache\sentiTokens.cache"
WIN_PERSONS_CACHE = "D:\workspace\Opinionizer\cache\persons.cache"
WIN_MULTIWORD_CACHE = "D:\workspace\Opinionizer\cache\multiwords.cache"
"""
access_key_test = "284707222-ZRvtSilVFXGcEYT8AZ04STWP9q7VXofN3L3Ufx2s"
access_secret_test = "1PkYjXaJWzSyd0K6Z4g5Wsg6NZ9iVNNOxI277ELrbqA"

access_key_prod = "300277144-taeETTFSRiQLUvOc667Y84PnobK0lley8jtC4zJg"
access_secret_prod = "tDms9BFzHAwhVmVoPbIpwdVblPHrAdxEsYJCzw4q1k"

"""
ID = 0
TARGET = 2
MENTION = 3
PPC = 5
TEXT = 7
"""
debug = False
    

def usage(commandName):
    
    print "usage: " + commandName + " [-pt (post to twitter and stats)|-ptr (post to twitter but randomize posts)|-pts (post stats only)|-pf (post to file)] [-tgt=targets file] [-sent=sentiment tokens file] [-excpt=exception sentiment tokens file] [-mw=multiwords file] [-bd=begin date (yyyy-mm-dd)] [-ed=end date (yyyy-mm-dd)] [-log=log file] [-excpt=sentilex accent exceptions file]"

def logClassifiedTweets(listOfTweets,path):
    
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

def postResults(tweets):
        
    """ Posts the statistics via a webservice 
        
        Params: stats -> list of tuples(target,nTweets,nPositives,nNeutrals,nNegatives)
                proxy -> proxy url 
                date  -> results of date
    """
    print "\nPosting results...\n"
    
    #postResultsUrl = "http://voxx.sapo.pt/cgi-bin/Euro2012/insert_mention.pl?tweetId=210026441759395841&extractionMethod=amigavel01&competitionId=568&teamId=7184&valency=pos"
    postResultsUrl =  "http://voxx.sapo.pt/cgi-bin/Euro2012/insert_mention.pl?tweetId={0}&extractionMethod=OpinionizerV0&competitionId=568&{1}&valency={2}"   

    opener = urllib2.build_opener()
    
    i=1
    
    for tweet in tweets:
        
        target = ''
        
        if tweet.target == 'player':
            target = 'playerId=' + tweet.mention
        else:
            target = 'teamId=' + tweet.mention
        
        response = opener.open(postResultsUrl.format(tweet.id,target,str(tweet.polarity)))
        jsonData = simplejson.loads(unicode(response.read().decode("utf-8")))
                
        status = jsonData["insertStatus"]
        print "response: ", status
        
        if status != "INSERT_OK":
            print "insert failed...(tweetId:"+tweet.id+")"
            #log it   
        
        i = i + 1
        
        if i%10 == 0:
            time.sleep(1) 
            
def getStats(tweetsByTarget):
    
    """
        Generates statistics based on the processed tweets
        
        Param: tweetsByTarget -> dictionary {target;[tweets of that target]}
        Returns: list of tuples(target,nTweets,nPositives,nNeutrals,nNegatives)
    """
    
    positives = 0
    negatives = 0
    neutrals = 0
    stats = []
    
    for target,tweets in tweetsByTarget.items():   
        
        positives = 0
        negatives = 0
        neutrals = 0
        
        for tweet in tweets: 
            
            if tweet.polarity == -1:
                
                negatives += 1
            
            elif tweet.polarity == 0:
                
                neutrals += 1
            
            elif tweet.polarity == 1:
                
                positives += 1
        
        stats.append((target,len(tweets),positives,neutrals,negatives))
        
    return stats

def getNewTweets_old(beginDate,endDate,proxy):
    
    """
        Gets tweets from a service for a certain period
        Params: begin date 
                end date
                proxy
    
        Returns: list of Opinion instances
    """
    
    print "Getting new tweets..."
    
    #username = "twitter_crawl_user"
    #password = "twitter_crawl_pass"
    requestTweets = "http://pattie.fe.up.pt/solr/eurocopa/select?q=created_at:[{0}%20TO%20{1}]&indent=on&wt=json&rows={2}&fl=text,id,created_at,user_id"
    #requestTweets = "http://pattie.fe.up.pt/solr/portugal/select?q=created_at:[2012-05-25T13:00:00Z%20TO%202012-05-25T15:00:00Z]&indent=on&wt=json&rows=1000&fl=text,id,created_at,user_id"
    
    #Password manager because the service requires authentication
    #password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
    #password_mgr.add_password(None, top_level_url, username, password)
    #auth_handler = urllib2.HTTPBasicAuthHandler(password_mgr)
    opener = None   
    
    if proxy != None:
        proxy_handler = urllib2.ProxyHandler({'http': proxy})        
        #opener = urllib2.build_opener(auth_handler,proxy_handler)
        opener = urllib2.build_opener(proxy_handler)       
    else:
        #opener = urllib2.build_opener(auth_handler)
        opener = urllib2.build_opener()
    
    if beginDate.strftime('%Y') == "1900":
       
        print "Getting Tweets from STDIN ..."
        twitterData = sys.stdin;
        
    else:
        #First we need to know how many tweets match our query (so we can retrieve them all
        #at once
        request = requestTweets.format(urllib.quote(beginDate.strftime('%Y-%m-%dT%H:%M:%SZ')),
                                       urllib.quote(endDate.strftime('%Y-%m-%dT%H:%M:%SZ')),
                                       1)        
        
        data = opener.open(request)
        
        numOfTweets = simplejson.loads(unicode(data.read().decode("utf-8")))["response"]["numFound"]
        
        #now we know how many rows to ask..
        request = requestTweets.format(urllib.quote(beginDate.strftime('%Y-%m-%dT%H:%M:%SZ')),
                                       urllib.quote(endDate.strftime('%Y-%m-%dT%H:%M:%SZ')),
                                       numOfTweets)
        
        print "Requesting: " + request
        
        twitterData = opener.open(request)
        
    #Read the JSON response
    jsonTwitter = simplejson.loads(unicode(twitterData.read().decode("utf-8")))  
                                
    listOfTweets = []
    
    #Build a dictionary
    for tweet in jsonTwitter["response"]["docs"]:
    
        date =  datetime.strptime(tweet["created_at"], '%Y-%m-%dT%H:%M:%Sz')
        
        listOfTweets.append(Opinion(tweet["id"],
                                    unicode(tweet["text"]),
                                    user=unicode(tweet["user_id"]),
                                    date=date))
    
    print len(listOfTweets), " tweets loaded\n"  
   
    return listOfTweets

def getNewTweets(beginDate,endDate):
    
    """
        Gets tweets from a service for a certain period
        Params: begin date 
                end date
                    
        Returns: list of Opinion instances
    """
    
    print "Getting new tweets..."

    #requestTweets = "http://pattie.fe.up.pt/solr/portuguese/select/?q=created_at:[2012-09-06T00:00:00Z%20TO%202012-09-10T00:00:00Z]&indent=on&wt=json&rows=10&fl=text,id,created_at,user_id"
    requestTweets = "http://pattie.fe.up.pt/solr/portuguese/select/?q=created_at:[{0}%20TO%20{1}]&indent=on&wt=json&rows=10000000&fl=text,id,created_at,user_id"   
    
    opener = urllib2.build_opener()
            
    request = requestTweets.format(urllib.quote(beginDate.strftime('%Y-%m-%dT%H:%M:%SZ')),
                                   urllib.quote(endDate.strftime('%Y-%m-%dT%H:%M:%SZ')))
             
    print "Requesting: " + request
    
    twitterData = opener.open(request)
        
    #Read the JSON response
    jsonTwitter = simplejson.loads(unicode(twitterData.read().decode("utf-8")))  
                                
    listOfTweets = []
    i = 0
    
    for tweet in jsonTwitter["response"]["docs"]:
        
        i+=1
            
        date =  datetime.strptime(tweet["created_at"], '%Y-%m-%dT%H:%M:%SZ')
         
        listOfTweets.append(Opinion(tweet["id"],
                                    unicode(tweet["text"]),
                                    user=unicode(tweet["user_id"]),         
                                    date=date))
                    
    print len(listOfTweets), " tweets (of "+ str(i) + ") loaded\n"  
   
    return listOfTweets
    
def formatStats(stats,nTweets,beginDate,endDate):
    
    """
        Formats the statistics of the processing phase for posting in twitter
        
        Params: stats -> list of tuples(target,nTweets,nPositives,nNeutrals,nNegatives)
                nTweets -> number of processed tweets
                beginDate
                endDate
    """
    
    tweetMessages = []
    nTweetsWithTarget = 0
    tweetMessage = "{0}: {1} tweets (positivos:{2}|neutros:{3}|negativos:{4}) >> De {5} a {6}"     
    summaryMessage = "{0} tweets ({1} com alvo) > {2} >> From {3} to {4}"
    summaryTargets = ""
    
    for target in stats:
        
        pos = str(target[POSITIVES])
        neut = str(target[NEUTRALS])
        neg = str(target[NEGATIVES])
        
        tweetMessages.append(tweetMessage.format(target[TARGET].upper(),
                                               str(target[N_TWEETS]),
                                               pos,neut,neg,
                                               beginDate.strftime('%Y-%m-%d %H:%M'),
                                               endDate.strftime('%Y-%m-%d %H:%M')))
        nTweetsWithTarget += target[N_TWEETS]
        
        summaryTargets += target[TARGET].upper() + ":" + str((target[POSITIVES] + target[NEUTRALS] + target[NEGATIVES])) + "|"
    
    summaryTargets = summaryTargets.strip('|')
    
    tweetMessages.append(summaryMessage.format(str(nTweets),str(nTweetsWithTarget),
                                               summaryTargets,
                                               beginDate.strftime('%Y-%m-%d %H:%M'),
                                               endDate.strftime('%Y-%m-%d %H:%M')))
    
    return tweetMessages

def processTweets(targetsFile,sentiTokensFile,exceptSentiTokens,multiWordsFile,tweets):
    
    """ 
        Processes a list of tweets, for each:
        1. Identifies the target
        2. If the message contains a target of interest infer the polarity
        
        targetsFile -> path to the politicians list file
        sentiTokensFile -> path to the sentiTokens list file
        exceptSentiTokens -> path to the list of sentiTokens that cannot lose their accents without
                             causing ambiguity for ex: más -> mas
        multiWordsFile -> path to a file that contains the words that should be considered as a unit, e.g. "primeiro ministro"
         tweets -> list of tweets
    """
    
    print "hell yeah!"
    print "Loading resources...\nTargets: " + targetsFile
        
    targets = Utils.getFromCache(PERSONS_CACHE)
    
    if targets != None:
        print "Target list found on cache!"
    else:
        targets = Persons.loadPoliticians(targetsFile)
        Utils.putInCache(targets, PERSONS_CACHE) 
    
    print "SentiTokens: " + sentiTokensFile + "\nExceptTokens: " +  exceptSentiTokens
    
    sentiTokens = Utils.getFromCache(SENTI_CACHE)  
    
    if sentiTokens != None:
        print "SentiTokens found on cache!"
    else:
        sentiTokens = SentiTokens.loadSentiTokens(sentiTokensFile,exceptSentiTokens)
        Utils.putInCache(sentiTokens, SENTI_CACHE)
    
    print "Multiword Tokenizer: " + multiWordsFile
    
    multiWordTokenizer = Utils.getFromCache(MULTIWORD_CACHE)
    
    if multiWordTokenizer != None:
        print "Multiword Tokenizer found on cache"
    else:
        multiWordTokenizer = MultiWordHelper(multiWordsFile)
        multiWordTokenizer.addMultiWords(Persons.getMultiWords(targets))
        multiWordTokenizer.addMultiWords(SentiTokens.getMultiWords(sentiTokens))
        Utils.putInCache(multiWordTokenizer, MULTIWORD_CACHE)
    
    print "Resources loaded! Starting analysis..."
    
    
    targetDetector = TargetDetector(targets)
    #TODO:Estes senhores já não precisam de receber os targets
    naive = Naive(sentiTokens)
    rules = Rules(None,sentiTokens)   
    
    analyzedTweets = []
    rejectedTweets = []
    
    for tweet in tweets:
        
        t0 = datetime.now()
        
        tweetsWithTarget = targetDetector.inferTarget(tweet)
        
        if tweetsWithTarget != None :
            
            #a tweet can have multiple targets (in that case the message is replicated)
            for tweet in tweetsWithTarget:       
        
                #try to classify with rules...
                analyzedTweet = rules.inferPolarity(tweet,False)
                
                #if not possible use the naive classifier
                if analyzedTweet.polarity == 0:
                    analyzedTweet = naive.inferPolarity(analyzedTweet,False)
                
                #If the polarity is still 0 it can mean:
                #1) The sum of the polarities of the sentiTokens is 0,
                #2) There was no evidence usable to assess the sentiment                
                if analyzedTweet.polarity == 0:
                    
                    regex = ur'(\W|^)sentiTokens:(.*?);(\W|$)'            
                    
                    #Try to find if there are any evidence of matched sentiTokens
                    match = re.search(regex,analyzedTweet.metadata).group(2)
                    
                    if debug:
                        print "match: ", match
                    
                    if len(match.strip(' ')) == 0:
        
                        rejectedTweets.append(analyzedTweet)
                    else:
                        analyzedTweets.append(analyzedTweet)
                else:
                    analyzedTweets.append(analyzedTweet)
                
                t1 = datetime.now()
            
                print tweet.id + " ("+ str(t1-t0) + ")"
            
    logClassifiedTweets(rejectedTweets, "./rejectedTweets.csv")    
    
    return analyzedTweets    
           
def main(targetsFile,sentiTokensFile,exceptSentiTokens,multiWordsFile,logFolder,beginDate,endDate,post):       
    
    listOfTweets = getNewTweets(beginDate,endDate)
    
    if len(listOfTweets) > 0:
        processedTweets = processTweets(targetsFile,sentiTokensFile,exceptSentiTokens,multiWordsFile,listOfTweets)
    
        logFilename = logFolder + "tweets"+str(beginDate.month)+str(beginDate.day)+str(endDate.day)+".csv"
        logClassifiedTweets(processedTweets,logFilename)
            
        if post:
            #post statistcs for the charts
            postResults(processedTweets)
    else:
        print "found no tweets"
        
if __name__ == '__main__':   
    
    #Default values    
    post = False
    beginDate = datetime.today() - timedelta(1)
    endDate = datetime.today()     
    targetsFile = "../Resources/politicians.txt"
    sentiTokensFile = "../Resources/SentiLex-flex-PT03.txt"    
    exceptSentiTokens = "../Resources/SentiLexAccentExcpt.txt"
    multiWordsFile = "../Resources/multiwords.txt"
    logFolder = "../Results/"
    
    #Get command line parameters
    for param in sys.argv[1:]:
                
        if param.startswith("-bd="):
            beginDate = datetime.strptime(param.replace("-bd=","").replace(","," "), '%Y-%m-%d %H:%M') 
        elif param.startswith("-ed="):             
            endDate = datetime.strptime(param.replace("-ed=","").replace(","," "), '%Y-%m-%d %H:%M')
        elif param.startswith("-tgt="):             
            targetsFile = param.replace("-tgt=","")
        elif param.startswith("-sent="):             
            sentiTokensFile = param.replace("-sent=","")
        elif param.startswith("-excpt="):             
            exceptSentiTokens = param.replace("-excpt=","")
        elif param.startswith("-log="):             
            logFolder = param.replace("-log=","")
            if not logFolder.endswith("/"):
                logFolder = logFolder + "/"        
        elif param.startswith("-mw="):                     
            multiWordsFile = param.replace("-mw=","")        
        elif param == "-ptr":
            print "Warning: Tweets will be randomized!"
            postTwitter = True
            randomizeTweets = True
        elif param == "-pt":
            postTwitter = True
            postStats = True        
        elif param == "-pts":            
            postStats = True       
        elif param == "-pf":            
            postFile = True
        else:            
            print "Error! " + param
            usage(sys.argv[0])
            sys.exit(-1)    
    
        
    print "Go!"

    #Set the processing time frame between 19h16 of the previous day 19h15 of the current day
    beginDate = beginDate.replace(second=0,microsecond=0)
    endDate = endDate.replace(second=0,microsecond=0)    
    
    beginDate = datetime.strptime("2012-09-07 00:00", '%Y-%m-%d %H:%M')
    endDate = datetime.strptime("2012-09-08 00:00", '%Y-%m-%d %H:%M')
    
    #evaluate(targetsFile, sentiTokensFile, exceptSentiTokens, multiWordsFile, "../gold_standard_PT-Turquia2.csv", "./silvioTestNew.csv")
    #genFeatures(targetsFile, sentiTokensFile, exceptSentiTokens, multiWordsFile, "../gold_standard_PT-Turquia2.csv", "./silvioFeatss.arff")
    
    main(targetsFile,sentiTokensFile,exceptSentiTokens,multiWordsFile,logFolder,beginDate,endDate,post)
    print "Done!"
    
