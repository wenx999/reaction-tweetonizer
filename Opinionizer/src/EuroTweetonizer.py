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

access_key_test = "284707222-ZRvtSilVFXGcEYT8AZ04STWP9q7VXofN3L3Ufx2s"
access_secret_test = "1PkYjXaJWzSyd0K6Z4g5Wsg6NZ9iVNNOxI277ELrbqA"

access_key_prod = "300277144-taeETTFSRiQLUvOc667Y84PnobK0lley8jtC4zJg"
access_secret_prod = "tDms9BFzHAwhVmVoPbIpwdVblPHrAdxEsYJCzw4q1k"

def usage(commandName):
    
    print "usage: " + commandName + " [-pt (post to twitter and stats)|-ptr (post to twitter but randomize posts)|-pts (post stats only)|-pf (post to file)] [-pr=proxy] [-pol=politicians file] [-sent=sentiment tokens file] [-excpt=exception sentiment tokens file] [-mw=multiwords file] [-bd=begin date (yyyy-mm-dd)] [-ed=end date (yyyy-mm-dd)] [-rt=end date (yyyy-mm-dd hh:mm)|-rt (last hour)] [-ss=single sentence] [-ssw=single sentence and web output] [-log=log file] [-excpt=ex"

def logClassifiedTweets(listOfTweets,path):
    
    """ Writes a log (csv file) of the classified tweets """
    
    print "Writting log of analyzed tweets: " + path
     
    f = codecs.open(path,"w","utf-8")
    
    #Column headers
    f.write("ID|USER|TARGET|MENTION|POLARITY|INFO|MESSAGE|TAGGED\n")    
        
    for tweet in listOfTweets:            
                    
        target = tweet.target.replace("\n"," ")
        mention = tweet.mention.replace("\n"," ")
        metadata = tweet.metadata.replace("\n"," ")
        sentence = tweet.sentence.replace("|","\\").replace("\n"," ").replace("\t"," ").replace("\r"," ")
        processedSentence = tweet.processedSentence.replace("|","\\").replace("\n"," ").replace("\t"," ").replace("\r"," ")
        
        f.write("\""+str(tweet.id) + "\"|" + tweet.user + "|\"" + target  + "\"|\"" + mention + "\"|" + str(tweet.polarity ) + "|\"" + metadata +  "\"|\"" + sentence + "\"|\"" + processedSentence + "\"\n")
    
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
    requestTweets = "http://voxx.sapo.pt/cgi-bin/Euro2012/get_tweets.pl?flag=extra_fields&numTweets=1000&beginDate={0}&endDate={1}"

    opener = urllib2.build_opener()   
    
    if beginDate.strftime('%Y') == "1900":
       
        print "Getting Tweets from STDIN ..."
        twitterData = sys.stdin;
        
    else:        
        request = requestTweets.format(urllib.quote(beginDate.strftime('%Y-%m-%dT%H:%M:%SZ')),
                                       urllib.quote(endDate.strftime('%Y-%m-%dT%H:%M:%SZ')))
                 
        print "Requesting: " + request
        
        twitterData = opener.open(request)
        
    #Read the JSON response
    jsonTwitter = simplejson.loads(unicode(twitterData.read().decode("utf-8")))  
                                
    listOfTweets = []
    
    for tweet in jsonTwitter["lastTweets"]:
                
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
        
    print len(listOfTweets), " tweets loaded\n"  
   
    return listOfTweets


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
        targetList.write(team["aliasShort"])
        targetList.write(",")
        targetList.write(team["alias"])
        targetList.write(";;;\n")        
        
    f = codecs.open("../Resources/players.txt","w","utf-8")
    
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
        
    targets = None #getFromCache(PERSONS_CACHE)
    
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
        
        #try to classify with rules...
        analyzedTweet = rules.inferPolarity(tweet,True)
        
        #if not possible use the naive classifier
        if analyzedTweet.polarity == 0:
            analyzedTweet = naive.inferPolarity(analyzedTweet,True)
        
        if analyzedTweet.polarity == 0:
            
            regex = ur'(\W|^)sentiTokens:(.*?);(\W|$)'            
            
            match = re.search(regex,analyzedTweet.metadata).group(2)
            
            if len(match.strip(' ')) == 0:

                rejectedTweets.append(analyzedTweet)
            else:
                analyzedTweets.append(analyzedTweet)
        
    logClassifiedTweets(rejectedTweets, "./rejectedTweets.csv")    
    return analyzedTweets    
           
def main(targetsFile,sentiTokensFile,exceptSentiTokens,multiWordsFile,logFolder,beginDate,endDate,post):       
    
    listOfTweets = getNewTweets(beginDate,endDate)
    processedTweets = processTweets(targetsFile,sentiTokensFile,exceptSentiTokens,multiWordsFile,listOfTweets)
    
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
    targetsFile = "../Resources/players.txt"
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
            beginDate = datetime.strptime(param.replace("-bd=",""), '%Y-%m-%d') 
        elif param.startswith("-ed="):             
            endDate = datetime.strptime(param.replace("-ed=",""), '%Y-%m-%d')
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
    beginDate = beginDate.replace(hour=19,minute=1,second=0,microsecond=0)
    endDate = endDate.replace(hour=19,minute=0,second=0,microsecond=0)
    
    post = True
    main(targetsFile,sentiTokensFile,exceptSentiTokens,multiWordsFile,logFolder,beginDate,endDate,post)
    print "Done!"

