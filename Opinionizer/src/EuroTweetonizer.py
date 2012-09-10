# -*- coding: UTF-8 -*-

'''
Created on Apr 21, 2011

@author: samir
'''

from datetime import datetime,timedelta
import time
import Persons 
import SentiTokens
from EuroOpinionizers import Naive,Rules,MultiWordHandler
import urllib2
import urllib
import simplejson
from Opinion import Opinion
import codecs
import os
import sys
import Utils
import random
import json
import pickle
import Preprocessor
import cStringIO
import re

TARGET = 0
N_TWEETS = 1
POSITIVES = 2
NEUTRALS = 3
NEGATIVES = 4
SENTI_CACHE = "../cache/sentiTokens.cache"
PERSONS_CACHE = "../cache/persons.cache"
MULTIWORD_CACHE = "../cache/multiwords.cache"

WIN_SENTI_CACHE = "D:\workspace\Opinionizer\cache\sentiTokens.cache"
WIN_PERSONS_CACHE = "D:\workspace\Opinionizer\cache\persons.cache"
WIN_MULTIWORD_CACHE = "D:\workspace\Opinionizer\cache\multiwords.cache"

access_key_test = "284707222-ZRvtSilVFXGcEYT8AZ04STWP9q7VXofN3L3Ufx2s"
access_secret_test = "1PkYjXaJWzSyd0K6Z4g5Wsg6NZ9iVNNOxI277ELrbqA"

access_key_prod = "300277144-taeETTFSRiQLUvOc667Y84PnobK0lley8jtC4zJg"
access_secret_prod = "tDms9BFzHAwhVmVoPbIpwdVblPHrAdxEsYJCzw4q1k"

ID = 0
TARGET = 2
MENTION = 3
PPC = 5
TEXT = 7
    
def evaluate(targetsFile,sentiTokensFile,exceptSentiTokens,multiWordsFile,sourceFile,evaluationResultFile):
    
    print "Evaluation mode!!"
        
    corpus = codecs.open(sourceFile,"r","utf-8")
    
    listOfTweets = []
    i=0
    
    print "loading tweets..."
    
    for line in corpus:
        
        tweet = line.split('|')
        
        #skip the first line
        if tweet[0] != 'ID':
            
            fullSentence = tweet[TEXT]            
            
            o = Opinion(id = tweet[ID],
                        user = u"Teste",
                        sentence = unicode(fullSentence),
                        irony = tweet[PPC],                        
                        target = unicode(tweet[TARGET]),
                        mention = unicode(tweet[MENTION]))
                        
            listOfTweets.append(o)
    
            i = i+1            
            
            """
            if i!=0 and i%20 == 0:
                print "Only loaded a sample..."
                break
            """
            
    print  str(len(listOfTweets)) + " tweets loaded..."
    
    processedTweets = processTweets(targetsFile,sentiTokensFile,exceptSentiTokens,multiWordsFile,listOfTweets)
    calculatePrecisionRecall(processedTweets,"./precisionRecallNEW.txt")
    logEvaluationTweets(processedTweets, evaluationResultFile)

def genFeatures(targetsFile,sentiTokensFile,exceptSentiTokens,multiWordsFile,sourceFile,featuresFile):
    
    arffHeaders = """
    
@relation twitometro

@ATTRIBUTE ID NUMERIC
@ATTRIBUTE rulePos NUMERIC
@ATTRIBUTE ruleNeg NUMERIC
@ATTRIBUTE cluePos NUMERIC
@ATTRIBUTE clueNeg NUMERIC
@ATTRIBUTE sentiPos NUMERIC
@ATTRIBUTE sentiNeut NUMERIC
@ATTRIBUTE sentiNeg NUMERIC
@ATTRIBUTE pol? {1,0,-1}
@ATTRIBUTE lixo {lixo,naoLixo}

@data

"""
    print "generate weka file!!"
        
    corpus = codecs.open(sourceFile,"r","utf-8")
    
    listOfTweets = []
    i=0
    
    print "loading tweets..."
    
    for line in corpus:
        
        tweet = line.split('|')
        
        #skip the first line
        if tweet[0] != 'ID':
            
            fullSentence = tweet[TEXT]            
            
            o = Opinion(id = tweet[ID],
                        user = u"Teste",
                        sentence = unicode(fullSentence),
                        irony = tweet[PPC],                        
                        target = unicode(tweet[TARGET]),
                        mention = unicode(tweet[MENTION]))
                        
            listOfTweets.append(o)
    
            i = i+1            
            
            """
            if i!=0 and i%20 == 0:
                print "Only loaded a sample..."
                break
            """
            
    print  str(len(listOfTweets)) + " tweets loaded..."
    
    processedTweets = getFeatures(targetsFile,sentiTokensFile,exceptSentiTokens,multiWordsFile,listOfTweets)
    
    featuresFile = open(featuresFile,"w") 
    featuresFile.write(arffHeaders)
    
    for tweet in processedTweets:
        
        for feat in tweet:
            
            featuresFile.write(str(feat))
            featuresFile.write(",")
        
        featuresFile.write("lixo\n")
    
    featuresFile.close()
   
    print "Features File written"

def getFeatures(targetsFile,sentiTokensFile,exceptSentiTokens,multiWordsFile,listOfTweets):
    
    print "Loading resources...\nTargets: " + targetsFile
        
    targets = None#getFromCache(PERSONS_CACHE)
    
    if targets != None:
        print "Target list found on cache!"
    else:
        targets = Persons.loadPoliticians(targetsFile)
        putInCache(targets, PERSONS_CACHE) 
    
    print "SentiTokens: " + sentiTokensFile + "\nExceptTokens: " +  exceptSentiTokens
    
    sentiTokens = None#getFromCache(SENTI_CACHE)  
    
    if sentiTokens != None:
        print "SentiTokens found on cache!"
    else:
        sentiTokens = SentiTokens.loadSentiTokens(sentiTokensFile,exceptSentiTokens)
        putInCache(sentiTokens, SENTI_CACHE)
    
    print "Multiword Tokenizer: " + multiWordsFile
    
    multiWordTokenizer = None#getFromCache(MULTIWORD_CACHE)
    
    if multiWordTokenizer != None:
        print "Multiword Tokenizer found on cache"
    else:
        multiWordTokenizer = MultiWordHandler(multiWordsFile)
        multiWordTokenizer.addMultiWords(Persons.getMultiWords(targets))
        multiWordTokenizer.addMultiWords(SentiTokens.getMultiWords(sentiTokens))
        putInCache(multiWordTokenizer, MULTIWORD_CACHE)
    
    print  "Calculating features..."
    
    naive = Naive(targets,sentiTokens)
    rules = Rules(targets,sentiTokens)   
    
    analyzedTweets = []
    rejectedTweets = []
    
    for tweet in listOfTweets:
        
        feats = []
        
        t0 = datetime.now()
        
        rulesFeats = rules.getRulesFeats(tweet,True)
        cluesFeats = rules.getCluesFeats(tweet,True)        
        sentiFeats = naive.getSentiFeats(tweet,True)
        
        x = int(rulesFeats[0])+int(rulesFeats[1])+int(cluesFeats[0])+int(cluesFeats[1])+int(sentiFeats[0])+int(sentiFeats[1])+int(sentiFeats[2])
        
        if x == 0:
            tweetTest = naive.inferPolarity(tweet, True)
            regex = ur'(\W|^)sentiTokens:(.*?);(\W|$)'            
            
            match = re.search(regex,tweetTest.metadata).group(2)
            
            if len(match.strip(' ')) == 0:
                
                rejectedTweets.append(tweet)
                print "rejected: "
                print tweet.tostring()
            else:
                feats.append(tweet.id)
                feats.append(rulesFeats[0])
                feats.append(rulesFeats[1])
                feats.append(cluesFeats[0])
                feats.append(cluesFeats[1])
                feats.append(sentiFeats[0])
                feats.append(sentiFeats[1])
                feats.append(sentiFeats[2])
                feats.append(int(tweet.irony))
                
                analyzedTweets.append(feats)
        else:
            feats.append(tweet.id)
            feats.append(rulesFeats[0])
            feats.append(rulesFeats[1])
            feats.append(cluesFeats[0])
            feats.append(cluesFeats[1])
            feats.append(sentiFeats[0])
            feats.append(sentiFeats[1])
            feats.append(sentiFeats[2])
            feats.append(int(tweet.irony))
            
            analyzedTweets.append(feats)
        
        t1 = datetime.now()
        
        print tweet.id + " ("+ str(t1-t0) + ")"
        
    #logClassifiedTweets(rejectedTweets, "./rejectedTweets.csv")    
    
    return analyzedTweets            


def calculatePrecisionRecall(listOfTweets,file):
    
    goldPos = 0
    goldNeut = 0
    goldNeg = 0
    twitPos = 0
    twitNeut = 0
    twitNeg = 0
    corrPos = 0
    corrNeut = 0
    corrNeg = 0
    
    for tweet in listOfTweets:
        
        if int(tweet.irony) == 1:
            goldPos += 1
            
            if int(tweet.polarity) == 1:                
                corrPos += 1
                twitPos += 1
            elif int(tweet.polarity) == 0:
                twitNeut += 1
            else:
                twitNeg += 1
        
        if int(tweet.irony) == 0:
            goldNeut +=1
            
            if int(tweet.polarity) == 0:
                corrNeut += 1
                twitNeut += 1
            elif int(tweet.polarity) == 1:
                twitPos +=1
            else:
                twitNeg += 1
                
        if int(tweet.irony) == -1:
            goldNeg += 1
            
            if int(tweet.polarity) == -1:
                corrNeg += 1
                twitNeg += 1
            elif int(tweet.polarity) == 0:
                twitNeut += 1
            else:
                twitPos +=1
     
    try:        
        prePos = float(corrPos)/float(goldPos)
    except ZeroDivisionError:
        prePos = 0
    
    try:    
        recPos = float(corrPos)/float(twitPos)
    except ZeroDivisionError:
        recPos = 0
        
    try:
        preNeut = float(corrNeut)/float(goldNeut)
    except ZeroDivisionError:
        preNeut = 0
    try:
        recNeut = float(corrNeut)/float(twitNeut)
    except ZeroDivisionError:
        recNeut = 0
        
    try:
        preNeg = float(corrNeg)/float(goldNeg)
    except ZeroDivisionError:
        preNeg = 0
        
    try:
        recNeg = float(corrNeg)/float(twitNeg)
    except ZeroDivisionError:
        recNeg = 0
        
    f = open(file,"w")
    
    f.write("Precision Pos: " + str(prePos) + "\n")
    f.write("Recall Pos: " + str(recPos) + "\n\n")
    
    f.write("Precision Neut: " + str(preNeut) + "\n")
    f.write("Recall Neut: " + str(recNeut) + "\n\n")
    
    f.write("Precision Neg: " + str(preNeg) + "\n")
    f.write("Recall Neg: " + str(recNeg) + "\n\n")
    
    f.close()     
        
def logEvaluationTweets(listOfTweets,path):
    
    """ Writes a log (csv file) of the classified tweets """
    
    print "Writting log of analyzed tweets: " + path
     
    f = codecs.open(path,"w","utf-8")
    
    #Column headers
    f.write("ID|USER|TARGET|MENTION|INFO|GOLD|POLARITY|MESSAGE|TAGGED\n")    
        
    for tweet in listOfTweets:            
                    
        target = tweet.target.replace("\n"," ")
        mention = tweet.mention.replace("\n"," ")
        metadata = tweet.metadata.replace("\n"," ")
        sentence = tweet.sentence.replace("|","\\").replace("\n"," ").replace("\t"," ").replace("\r"," ")
        processedSentence = tweet.processedSentence.replace("|","\\").replace("\n"," ").replace("\t"," ").replace("\r"," ")
        
        f.write(str(tweet.id) + "|" + tweet.user + "|" + target  + "|" + mention + "|" + metadata + "|" + tweet.irony + "|" + str(tweet.polarity ) +  "|" + sentence + "|" + processedSentence + "\n")
    
    f.close()

def usage(commandName):
    
    print "usage: " + commandName + " [-pt (post to twitter and stats)|-ptr (post to twitter but randomize posts)|-pts (post stats only)|-pf (post to file)] [-pr=proxy] [-pol=politicians file] [-sent=sentiment tokens file] [-excpt=exception sentiment tokens file] [-mw=multiwords file] [-bd=begin date (yyyy-mm-dd)] [-ed=end date (yyyy-mm-dd)] [-rt=end date (yyyy-mm-dd hh:mm)|-rt (last hour)] [-ss=single sentence] [-ssw=single sentence and web output] [-log=log file] [-excpt=ex"

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

def logHourlyTweets(listOfTweets,logFolder,next,prev):
    
    """ Writes a hourly log (txt file) of tweets """
    
    print "Writting log of tweets: " + logFolder
     
    f = codecs.open(logFolder,"w","utf-8")
    
    #Column headers
    aux = {}
    aux[ "nrTweets" ] = len(listOfTweets)
    aux[ "query" ] = ""
    aux[ "endDate" ] = endDate.strftime("%Y-%m-%d %H:%M")
    aux[ "beginDate" ] = beginDate.strftime("%Y-%m-%d %H:%M")
    aux[ "prev" ] = prev
    aux[ "next" ] = next
    aux[ "tweets" ] = []
    
    for tweet in listOfTweets:

        aux1 = {}

        aux1["id"] = tweet.id
        aux1["target"] = tweet.target.replace('\n',' ')
        aux1["irony"] = tweet.irony
        aux1["polarity"] = tweet.polarity
        aux1["sentence"] = tweet.sentence.replace('|','\\').replace('\n',' ').replace('\t',' ').replace('\r',' ')
        aux1["mention"] = tweet.mention.replace('\n',' ')
        aux1["metadata"] = tweet.metadata.replace('\n',' ')
        aux1["date"] = tweet.date.strftime("%Y-%m-%d %H:%M:%S")
        aux1["user"] = tweet.user
        aux1["processedSentence"] = tweet.processedSentence.replace('|','\\').replace('\n',' ').replace('\t',' ').replace('\r',' ') 

        aux[ "tweets" ].append(aux1)

    f.write( json.dumps( aux ) )
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
    
    #requestTweets ="http://voxx.sapo.pt/cgi-bin/Euro2012/get_tweets.pl?flag=extra_fields&numTweets=100000&beginDate=2012-06-07%2014:30:00&endDate=2012-06-07%2018:30:00"
    requestTweets = "http://voxx.sapo.pt/cgi-bin/Euro2012/get_tweets.pl?flag=extra_fields&numTweets=900000&beginDate={0}&endDate={1}"
    users = loadPortugueseUsers("../Resources/top_portuguese_users.csv")
    
    opener = urllib2.build_opener()   
    
    if beginDate.strftime('%Y') == "1900":
       
        print "Getting Tweets from STDIN ..."
        twitterData = sys.stdin;
        
    else:        
        request = requestTweets.format(urllib.quote(beginDate.strftime('%Y-%m-%d %H:%M:%S')),
                                       urllib.quote(endDate.strftime('%Y-%m-%d %H:%M:%S')))
                 
        print "Requesting: " + request
        
        twitterData = opener.open(request)
        
    #Read the JSON response
    jsonTwitter = simplejson.loads(unicode(twitterData.read().decode("utf-8")))  
                                
    listOfTweets = []
    i = 0
    for tweet in jsonTwitter["lastTweets"]:
        
        i+=1
        
        if tweet["TwitterUserId"] in users:
            
            date =  datetime.strptime(tweet["tweetDate"], '%Y-%m-%d %H:%M:%S')
            target = ''
            mention = ''
            
            if int(tweet["playerId"]) > 0:
                target = u"player"
                mention = tweet["playerId"]
            else:
                target = u"team"
                mention = tweet["teamId"]
                
            listOfTweets.append(Opinion(tweet["tweetId"],
                                        unicode(tweet["tweetMessage"]),
                                        user=unicode(tweet["TwitterScreenName"]),
                                        target=target,
                                        mention=mention, 
                                        date=date))
                        
    print len(listOfTweets), " tweets (of "+ str(i) + ") loaded\n"  
   
    return listOfTweets

def getNewTweets2(beginDate,endDate):
    
    """
        Gets tweets from a service for a certain period
        Params: begin date 
                end date
                    
        Returns: list of Opinion instances
    """
    
    print "Getting new tweets..."
    #return []
    #requestTweets ="http://voxx.sapo.pt/cgi-bin/Euro2012/get_tweets.pl?flag=extra_fields&numTweets=100000&beginDate=2012-06-07%2014:30:00&endDate=2012-06-07%2018:30:00"
    #requestTweets = "http://pattie.fe.up.pt/solr/portuguese/select/?q=created_at:[2012-09-06T00:00:00Z%20TO%202012-09-07T00:00:00Z]&indent=on&wt=json&rows=100000&fl=text,id,created_at,user_id"
    #requestTweets = "http://pattie.fe.up.pt/solr/portuguese/select/?q=created_at:[2012-09-07T00:00:00Z%20TO%202012-09-08T00:00:00Z]&indent=on&wt=json&rows=100000&fl=text,id,created_at,user_id"
    requestTweets = "http://pattie.fe.up.pt/solr/portuguese/select/?q=created_at:[2012-09-06T00:00:00Z%20TO%202012-09-10T00:00:00Z]&indent=on&wt=json&rows=100000&fl=text,id,created_at,user_id"
    #requestTweets = "http://pattie.fe.up.pt/solr/portuguese/select/?q=passos%20coelho&created_at:[2012-05-25T13:00:00Z%20TO%202012-05-25T15:00:00Z]&indent=on&wt=json&rows=80000&fl=text,id,created_at,user_id%22"
    #users = loadPortugueseUsers("../Resources/top_portuguese_users.csv")
    
    opener = urllib2.build_opener()   
    
    if beginDate.strftime('%Y') == "1900":
       
        print "Getting Tweets from STDIN ..."
        twitterData = sys.stdin;
        
    else:        
        request = requestTweets.format(urllib.quote(beginDate.strftime('%Y-%m-%d %H:%M:%S')),
                                       urllib.quote(endDate.strftime('%Y-%m-%d %H:%M:%S')))
                 
        print "Requesting: " + request
        
        twitterData = opener.open(request)
        
    #Read the JSON response
    jsonTwitter = simplejson.loads(unicode(twitterData.read().decode("utf-8")))  
                                
    listOfTweets = []
    i = 0
    
    for tweet in jsonTwitter["response"]["docs"]:
        
        i+=1
        
        #print tweet
        #continue
    
        #if tweet["TwitterUserId"] in users:
            
        date =  datetime.strptime(tweet["created_at"], '%Y-%m-%dT%H:%M:%SZ')
         
        listOfTweets.append(Opinion(tweet["id"],
                                    unicode(tweet["text"]),
                                    user=unicode(tweet["user_id"]),         
                                    date=date))
                    
    print len(listOfTweets), " tweets (of "+ str(i) + ") loaded\n"  
   
    return listOfTweets


def loadPortugueseUsers(filename):
    
    f = open(filename,"r")
    
    users = f.read().split("\n")
    
    return users

def generateTargetList():
    
    targetList = cStringIO.StringIO()
    requestPlayersList = "http://voxx.sapo.pt/cgi-bin/Euro2012/get_players.pl"
   
    opener = urllib2.build_opener()       
        
    print "Requesting: " + requestPlayersList
        
    playersList = opener.open(requestPlayersList)
        
    #Read the JSON response
    jsonData = simplejson.loads(unicode(playersList.read().decode("utf-8")))  
    
    #{"player_name":"Cristiano Ronaldo","player_num":"7","player_photo":"http://desporto_stats.imgs.sapo.pt/9/People/382.png","player_position":"A","player_full_name":"Cristiano Ronaldo dos Santos Aveiro","player_id":"198","teamId":"7184"}
    
    for player in jsonData["listPlayers"]:
        
        targetList.write("p_"+player["player_id"])
        targetList.write(":")
        targetList.write(player["player_name"])
        targetList.write(",")
        targetList.write(player["alias"])
        targetList.write(",")
        targetList.write(player["player_full_name"])
        targetList.write(";;;\n")
       
    requestTeamsList = "http://voxx.sapo.pt/cgi-bin/Euro2012/get_teams.pl"
   
    opener = urllib2.build_opener()       
        
    print "Requesting: " + requestTeamsList
        
    teamsList = opener.open(requestTeamsList)
        
    #Read the JSON response
    jsonData = simplejson.loads(unicode(teamsList.read().decode("utf-8")))  
        
    #{"officialName":"Germany","aliasShort":"DE","name":"Alemanha","flag":"http://desporto_stats.imgs.sapo.pt/3/flags/226.png","group":"B","endDate":"2012-07-02","beginDate":"2012-06-08","id":"7165","alias":"GER"}
    for team in jsonData["ListTeams"]:
        
        targetList.write("t_"+team["id"])
        targetList.write(":")
        targetList.write(team["name"])
        targetList.write(",")
        targetList.write(team["officialName"])
        targetList.write(",")
        targetList.write(team["alias"])
        targetList.write(";;;\n")        
        
    f = codecs.open("../Resources/euroTargets.txt","w","utf-8")
    
    f.write(unicode(targetList.getvalue()))
    f.close()   
        
def printMessages(messages):
    
    for message in messages:
    
        print message
    
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
    
def processTweets(targetsFile,sentiTokensFile,exceptSentiTokens,multiWordsFile,tweets):
    
    """ 
        Processes a list of tweets:
        1. Identify target
        2. If target is one of the politicians infer the comment's polarity
        
        politiciansFile -> path to the politicians list file
        sentiTokensFile -> path to the sentiTokens list file
        exceptSentiTokens -> path to the list of sentiTokens that cannot lose their accents without
                             causing ambiguity for ex: más -> mas
         tweets -> list of tweets
    """
    
    print "Loading resources...\nTargets: " + targetsFile
        
    targets = None#getFromCache(WIN_PERSONS_CACHE)
    
    if targets != None:
        print "Target list found on cache!"
    else:
        targets = Persons.loadPoliticians(targetsFile)
        putInCache(targets, WIN_PERSONS_CACHE) 
    
    print "SentiTokens: " + sentiTokensFile + "\nExceptTokens: " +  exceptSentiTokens
    
    sentiTokens = None#getFromCache(WIN_SENTI_CACHE)  
    
    if sentiTokens != None:
        print "SentiTokens found on cache!"
    else:
        sentiTokens = SentiTokens.loadSentiTokens(sentiTokensFile,exceptSentiTokens)
       
        putInCache(sentiTokens, WIN_SENTI_CACHE)
    
    print "Multiword Tokenizer: " + multiWordsFile
    
    multiWordTokenizer = None#getFromCache(WIN_MULTIWORD_CACHE)
    
    if multiWordTokenizer != None:
        print "Multiword Tokenizer found on cache"
    else:
        multiWordTokenizer = MultiWordHandler(multiWordsFile)
        multiWordTokenizer.addMultiWords(Persons.getMultiWords(targets))
        multiWordTokenizer.addMultiWords(SentiTokens.getMultiWords(sentiTokens))
        putInCache(multiWordTokenizer, WIN_MULTIWORD_CACHE)
    
    print  "Inferring polarity..."
    
    naive = Naive(targets,sentiTokens)
    rules = Rules(targets,sentiTokens)   
    
    analyzedTweets = []
    rejectedTweets = []
    
    for tweet in tweets:
        
        t0 = datetime.now()
        
        rulesScore,rulesInfo = rules.getRulesScore(tweet,True)
        cluesScore,clueInfo = rules.getCluesScore(tweet,True)        
        sentiScore,sentiInfo = naive.getSentiScore(tweet,True)
        
        tweetScore = int(sentiScore) + int(rulesScore) + int(cluesScore)
        
        if tweetScore > 0:
            tweet.polarity = 1
        elif tweetScore < 0:
            tweet.polarity = -1
        else:
            tweet.polarity = 0
        
        tweet.metadata = sentiInfo+";"+clueInfo+";"+rulesInfo 
        
        if tweet.polarity == 0:
            
            regex = ur'(\W|^)sentiTokens:(.*?);(\W|$)'            
            
            match = re.search(regex,tweet.metadata).group(2)
            
            if len(match.strip(' ')) == 0:

                rejectedTweets.append(tweet)
            else:
                analyzedTweets.append(tweet)
        else:
            analyzedTweets.append(tweet)
        
        t1 = datetime.now()
        
        print tweet.id + " ("+ str(t1-t0) + ")"
        
    logClassifiedTweets(rejectedTweets, "./rejectedTweets.csv")    
    
    return analyzedTweets            


def processTweets_old(targetsFile,sentiTokensFile,exceptSentiTokens,multiWordsFile,tweets):
    
    """ 
        Processes a list of tweets:
        1. Identify target
        2. If target is one of the politicians infer the comment's polarity
        
        politiciansFile -> path to the politicians list file
        sentiTokensFile -> path to the sentiTokens list file
        exceptSentiTokens -> path to the list of sentiTokens that cannot lose their accents without
                             causing ambiguity for ex: más -> mas
         tweets -> list of tweets
    """
    
    print "hell yeah!"
    print "Loading resources...\nTargets: " + targetsFile
        
    targets = getFromCache(PERSONS_CACHE)
    
    if targets != None:
        print "Target list found on cache!"
    else:
        targets = Persons.loadPoliticians(targetsFile)
        putInCache(targets, PERSONS_CACHE) 
    
    print "SentiTokens: " + sentiTokensFile + "\nExceptTokens: " +  exceptSentiTokens
    
    sentiTokens = getFromCache(SENTI_CACHE)  
    
    if sentiTokens != None:
        print "SentiTokens found on cache!"
    else:
        sentiTokens = SentiTokens.loadSentiTokens(sentiTokensFile,exceptSentiTokens)
        putInCache(sentiTokens, SENTI_CACHE)
    
    print "Multiword Tokenizer: " + multiWordsFile
    
    multiWordTokenizer = getFromCache(MULTIWORD_CACHE)
    
    if multiWordTokenizer != None:
        print "Multiword Tokenizer found on cache"
    else:
        multiWordTokenizer = MultiWordHandler(multiWordsFile)
        multiWordTokenizer.addMultiWords(Persons.getMultiWords(targets))
        multiWordTokenizer.addMultiWords(SentiTokens.getMultiWords(sentiTokens))
        putInCache(multiWordTokenizer, MULTIWORD_CACHE)
    
    print  "Inferring polarity..."
    
    naive = Naive(targets,sentiTokens)
    rules = Rules(targets,sentiTokens)   
    
    analyzedTweets = []
    rejectedTweets = []
    
    for tweet in tweets:
        
        t0 = datetime.now()
        
        #print "antes"
        
        tweetsWithTarget = naive.inferTarget(tweet)
        
        if tweetsWithTarget != None :
            
            #a tweet can have multiple targets (in that case the message is replicated)
            for tweet in tweetsWithTarget:       
        
                #try to classify with rules...
                analyzedTweet = rules.inferPolarity(tweet,False)
                print "depois"
                #if not possible use the naive classifier
                if analyzedTweet.polarity == 0:
                    analyzedTweet = naive.inferPolarity(analyzedTweet,False)
                
                if analyzedTweet.polarity == 0:
                    
                    regex = ur'(\W|^)sentiTokens:(.*?);(\W|$)'            
                    
                    match = re.search(regex,analyzedTweet.metadata).group(2)
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
    
    listOfTweets = getNewTweets2(beginDate,endDate)
    processedTweets = processTweets_old(targetsFile,sentiTokensFile,exceptSentiTokens,multiWordsFile,listOfTweets)
    
    logFilename = logFolder + "tweets"+str(beginDate.month)+str(beginDate.day)+str(endDate.day)+".csv"
    logClassifiedTweets(processedTweets,logFilename)
            
    if post:
        #post statistcs for the charts
        postResults(processedTweets)
    
if __name__ == '__main__':   
    
    #Default values
    proxy = None
    post = False
    beginDate = datetime.today() - timedelta(1)
    endDate = datetime.today()     
    targetsFile = "../Resources/politicians.txt"
    sentiTokensFile = "../Resources/SentiLex-flex-PT03.txt"    
    exceptSentiTokens = "../Resources/SentiLexAccentExcpt.txt"
    multiWordsFile = "../Resources/multiwords.txt"
    logFolder = "../Results/"
    singleSentence = None
    webOutput = False
    
    
    #Get command line parameters
    for param in sys.argv[1:]:
        
        if param.startswith("-pr="):
            proxy = param.replace("-pr=","")
        elif param.startswith("-bd="):
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
        elif param.startswith("-rt="):
            realTime = datetime.strptime(param.replace("-rt=",""), '%Y-%m-%d_%H:%M')
        elif param.startswith("-rt"):
            realTime = "lastHour"
        elif param.startswith("-ss="):                     
            singleSentence = unicode(param.replace("-ss=","").decode("utf-8"))
        elif param.startswith("-ssw="):                     
            singleSentence = unicode(param.replace("-ssw=","").decode("utf-8"))
            webOutput = True
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
    
    
    #evaluate(targetsFile, sentiTokensFile, exceptSentiTokens, multiWordsFile, "../gold_standard_PT-Turquia2.csv", "./silvioTestNew.csv")
    #genFeatures(targetsFile, sentiTokensFile, exceptSentiTokens, multiWordsFile, "../gold_standard_PT-Turquia2.csv", "./silvioFeatss.arff")
    
    main(targetsFile,sentiTokensFile,exceptSentiTokens,multiWordsFile,logFolder,beginDate,endDate,post)
    print "Done!"
    
