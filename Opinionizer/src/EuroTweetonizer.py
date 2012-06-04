# -*- coding: UTF-8 -*-

'''
Created on Apr 21, 2011

@author: samir
'''

from datetime import datetime,timedelta
import time
import Persons 
import SentiTokens
from Opinionizers import Naive,Rules,MultiWordHandler
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

def logClassifiedTweets(tweetsByTarget,path):
    
    """ Writes a log (csv file) of the classified tweets """
    
    print "Writting log of analyzed tweets: " + path
     
    f = codecs.open(path,"w","utf-8")
    
    #Column headers
    f.write("ID|USER|TARGET|MENTION|POLARITY|INFO|MESSAGE|TAGGED\n")    
    
    for listOfTweets in tweetsByTarget:
        
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

def postResults(stats,proxy,date):
        
    """ Posts the statistics via a webservice 
        
        Params: stats -> list of tuples(target,nTweets,nPositives,nNeutrals,nNegatives)
                proxy -> proxy url 
                date  -> results of date
    """
    print "\nPosting daily stats...\n"
    
    username = "ome_user"
    password = "ome_pass"
    topLevelUrl = "http://robinson.fe.up.pt/cgi-bin/OpinionMiningElections/post_daily_results.pl"
    postResultsUrl =  "http://robinson.fe.up.pt/cgi-bin/OpinionMiningElections/post_daily_results.pl?target={0}&source=twitter&pos={1}&neg={2}&neu={3}&version=baseline&date={4}"   
    
    password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
    password_mgr.add_password(None, topLevelUrl, username, password)
    authHandler = urllib2.HTTPBasicAuthHandler(password_mgr)
    
    opener = None
    
    if proxy != None:
        proxyHandler = urllib2.ProxyHandler({'http': proxy})        
        opener = urllib2.build_opener(proxyHandler,authHandler)
    else:
        opener = urllib2.build_opener(authHandler)
    
    for target in stats:
        
        normalizedTargetName = urllib.quote(Utils.normalize(unicode(target[TARGET])))
        normalizedDate =  urllib.quote(date.strftime('%Y-%m-%d'))
        print "posting results to: " + postResultsUrl.format(normalizedTargetName,target[POSITIVES],target[NEGATIVES],target[NEUTRALS],normalizedDate)
        response = opener.open(postResultsUrl.format(normalizedTargetName,target[POSITIVES],target[NEGATIVES],target[NEUTRALS],normalizedDate))
        time.sleep(5)
        
        print response.readlines()

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

def getNewTweets(beginDate,endDate,proxy):
    
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
    requestTweets = "http://pattie.fe.up.pt/solr/portugal/select?q=created_at:[{0}%20TO%20{1}]&indent=on&wt=json&rows={2}&fl=text,id,created_at,user_id"
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

def printMessages(messages):
    
    for message in messages:
    
        print message
 
def tweetResults(tweets,acessKey,acessSecrect,randomizeTweets,proxy):       
    
    """
        Tweets the results in a twitter account
        
        Params: tweets -> list of tweet messages                
                accessKey -> for oAuth authentication
                accessSecret -> for oAuth authentication
                randomizeTweets -> True if tweets need to have a random substring to avoid posting duplicates
                proxy 
    """
    
    print "Posting results to twitter...\n"
    
    consumer_key = "sEwbkfgkFU4B7l5DBuRvXw"
    consumer_secret = "aUAKFq3qpB7NqeHh89AIJL85ZXHORlmZ7WIczLoxE"    
    
      
    if proxy != None:
        os.environ['HTTP_PROXY'] = proxy        
        proxy_handler = urllib2.ProxyHandler({'http': proxy})    
        opener = urllib2.build_opener(proxy_handler)
        urllib2.install_opener(opener)    
    

    api = twitter.Api(consumer_key=consumer_key,
                       consumer_secret=consumer_secret, access_token_key=acessKey, access_token_secret=acessSecrect)
    
    for tweetMessage in tweets:
        
        if randomizeTweets:            
            randomizedTweet = tweetMessage +  " <" + str(random.random())[3:7] + ">"
            print randomizedTweet, " ("+str(len(randomizedTweet))+")"
            api.PostUpdate(randomizedTweet)   
        else:
            print tweetMessage, " ("+str(len(tweetMessage))+")"
            api.PostUpdate(tweetMessage) 

    
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
    t0 = datetime.now()
    
    targets = getFromCache(PERSONS_CACHE)
    
    if targets != None:
        print "Target list found on cache!"
    else:
        targets = Persons.loadPoliticians(targetsFile)
        putInCache(targets, PERSONS_CACHE)
        
    Ttotal = datetime.now() - t0
    print "done (" + str(Ttotal) + ")" 
    
    print "SentiTokens: " + sentiTokensFile + "\nExceptTokens: " +  exceptSentiTokens
    t0 = datetime.now() 
    
    sentiTokens = getFromCache(SENTI_CACHE)  
    
    if sentiTokens != None:
        print "SentiTokens found on cache!"
    else:
        sentiTokens = SentiTokens.loadSentiTokens(sentiTokensFile,exceptSentiTokens)
        putInCache(sentiTokens, SENTI_CACHE)
        
    Ttotal = datetime.now() - t0
    print "done (" + str(Ttotal) + ")"
    
    print "Multiword Tokenizer " + multiWordsFile
    t0 = datetime.now()       
    
    multiWordTokenizer = getFromCache(MULTIWORD_CACHE)
    
    if multiWordTokenizer != None:
        print "Multiword Tokenizer found on cache"
    else:
        multiWordTokenizer = MultiWordHandler(multiWordsFile)
        multiWordTokenizer.addMultiWords(Persons.getMultiWords(targets))
        multiWordTokenizer.addMultiWords(SentiTokens.getMultiWords(sentiTokens))
        putInCache(multiWordTokenizer, MULTIWORD_CACHE)
            
    Ttotal = datetime.now() - t0
    print "done (" + str(Ttotal) + ")"
    
    #Process tweets...
    #First step: infer targets and create a dictionary {target,listOfTweets}    
    print "Identifying targets..."
    t0 = datetime.now()  
    
    naive = Naive(targets,sentiTokens)    
    
    targetedTweets = {}    
    classifiedTweets = {}
     
    for tweet in tweets:        
        
        tweetsWithTarget = naive.inferTarget(tweet)
        
        if tweetsWithTarget != None :
            
            #a tweet can have multiple targets (in that case the message is replicated)
            for tweet in tweetsWithTarget:
            
                if tweet.target not in targetedTweets:                    
                
                    targetedTweets[tweet.target] = []
                
                tweet.processedSentence = multiWordTokenizer.tokenizeMultiWords(tweet.sentence)
                tweet.processedSentence = Preprocessor.removeURLs(tweet.processedSentence)
                tweet.processedSentence = Preprocessor.removeUsernames(tweet.processedSentence)  
                targetedTweets[tweet.target].append(tweet)
    
    Ttotal = datetime.now() - t0
    print "done (" + str(Ttotal) + ")"
    
    print  len(targetedTweets), " targets Identified! Inferring polarity..."
    
    rules = Rules(targets,sentiTokens)
    
    #Second step infer polarity 
    for target,tweets in targetedTweets.items():
        
        for tweet in tweets: 
            
            if target not in classifiedTweets:
                classifiedTweets[target]  = []
            
            #try to classify with rules...
            classifiedTweet = rules.inferPolarity(tweet,True)
            
            #if not possible use the naive classifier
            if classifiedTweet.polarity == 0:
                classifiedTweet = naive.inferPolarity(classifiedTweet,True)
            
            classifiedTweets[target].append(classifiedTweet)
            
    return classifiedTweets

def processSingleSentence(politiciansFile,sentiTokensFile,exceptSentiTokens,sentence,webOutput):
            
    print "Loading resources..."
    print "Politicians: " + politiciansFile    
    politicians = Persons.loadPoliticians(politiciansFile)
    
    print "SentiTokens: " + sentiTokensFile 
    print "ExceptTokens: " +  exceptSentiTokens
    sentiTokens = SentiTokens.loadSentiTokens(sentiTokensFile,exceptSentiTokens)
    
    naive = Naive(politicians,sentiTokens)
    
    singleSentence = Opinion(1, sentence=sentence)
    
    print "Inferring targets..."
    targets = naive.inferTarget(singleSentence)
            
    results = []
        
    if targets != None:    
        
        print "Inferring polarity..."
        
        for target in targets:
            
            rules = Rules(politicians,sentiTokens)
            
            #if not possible to classify with rules use the naive classifier
            classifiedTweet = rules.inferPolarity(target, False)
            
            if classifiedTweet.polarity == 0:
                classifiedTweet = naive.inferPolarity(classifiedTweet,True)
            
            results.append(classifiedTweet)
    else:
        print "No targets were identified..."
    if webOutput:
        return printResultsWeb(results,sentence)
    else:
        return printResultsConsole(results)

def printResultsConsole(results):
    
    for r in results:
        
        print r.tostring()
        print "---------------"
        
def printResultsWeb(results,sentence):
    
    html = u"<h1>FACTOS - Ferramenta de Análise Computacional de Tweets com Opinião e Sentimento</h1> \
            <h2>Frase: {0}</h2> \
            <h3>Alvos: <br> {1}</h3> \
            <h3>Polaridade: {2}</h3>"
    
    htmlNoTargets = u"<h1>FACTOS - Ferramenta de Análise Computacional de Tweets com Opinião e Sentimento</h1> \
            <h2>Frase: {0}</h2> \
            <h3>Não foram encontrados alvos</h3>"
    
    if results == None or len(results) == 0:
        
        print htmlNoTargets.format(sentence).encode("utf-8")
    
    else:
        
        targets = u""
        
        for r in results:
            
            targets += "<p>"+ r.target + " > " + r.mention + "</p>"
        
        print html.format(sentence,targets, str(results[0].polarity)).encode("utf-8")       
           
def main(politiciansFile,sentiTokensFile,exceptSentiTokens,multiWordsFile,logFolder,beginDate,endDate,postTwitter,postStats,postFile,randomizeTweets,proxy,):       
    
    listOfTweets = getNewTweets(beginDate,endDate,proxy)
    classifiedTweets = processTweets(politiciansFile,sentiTokensFile,exceptSentiTokens,multiWordsFile,listOfTweets)
               
    stats = getStats(classifiedTweets)    
    formatedStats = formatStats(stats,len(listOfTweets),beginDate,endDate)
    
    if postTwitter:
        #If randomize tweets is enabled, assume this is a test run so posts will be done in
        #the tests account
        if randomizeTweets:        
            tweetResults(formatedStats,access_key_test,access_secret_test,randomizeTweets,proxy)
        else:
            #post results in the production account
            tweetResults(formatedStats,access_key_prod,access_secret_prod,randomizeTweets,proxy)
            
    if postStats:
        #post statistcs for the charts
        postResults(stats,proxy,endDate)
            
    elif postFile:
        logHourlyTweets(listOfTweets,logFolder+"hourTweets_"+beginDate.strftime('%Y-%m-%d_%H-%M')+".txt","hourTweets_"+(beginDate+timedelta(hours=1)).strftime('%Y-%m-%d_%H-%M')+".txt","hourTweets_"+(beginDate-timedelta(hours=1)).strftime('%Y-%m-%d_%H-%M')+".txt")
        logHourlyTweets(listOfTweets,logFolder+"hourTweets_lastHour.txt","hourTweets_"+(beginDate+timedelta(hours=1)).strftime('%Y-%m-%d_%H-%M')+".txt","hourTweets_"+(beginDate-timedelta(hours=1)).strftime('%Y-%m-%d_%H-%M')+".txt")

        for target in ["ppcoelho","jseguro","pportas","flouca","jsousa"]:
            try:
                logHourlyTweets(classifiedTweets[target],logFolder+"hourTweets_"+target+"_"+beginDate.strftime('%Y-%m-%d_%H-%M')+".txt","hourTweets_"+target+"_"+(beginDate+timedelta(hours=1)).strftime('%Y-%m-%d_%H-%M')+".txt","hourTweets_"+target+"_"+(beginDate-timedelta(hours=1)).strftime('%Y-%m-%d_%H-%M')+".txt")
                logHourlyTweets(classifiedTweets[target],logFolder+"hourTweets_"+target+"_lastHour.txt","hourTweets_"+target+"_"+(beginDate+timedelta(hours=1)).strftime('%Y-%m-%d_%H-%M')+".txt","hourTweets_"+target+"_"+(beginDate-timedelta(hours=1)).strftime('%Y-%m-%d_%H-%M')+".txt")
            except KeyError:
                logHourlyTweets([],logFolder+"hourTweets_"+target+"_"+beginDate.strftime('%Y-%m-%d_%H-%M')+".txt","hourTweets_"+target+"_"+(beginDate+timedelta(hours=1)).strftime('%Y-%m-%d_%H-%M')+".txt","hourTweets_"+target+"_"+(beginDate-timedelta(hours=1)).strftime('%Y-%m-%d_%H-%M')+".txt")
                logHourlyTweets([],logFolder+"hourTweets_"+target+"_lastHour.txt","hourTweets_"+target+"_"+(beginDate+timedelta(hours=1)).strftime('%Y-%m-%d_%H-%M')+".txt","hourTweets_"+target+"_"+(beginDate-timedelta(hours=1)).strftime('%Y-%m-%d_%H-%M')+".txt")
            
    else:
        printMessages(formatedStats)
    
    logFilename = logFolder + "tweets"+str(beginDate.month)+str(beginDate.day)+str(endDate.day)+".csv"
    logClassifiedTweets(classifiedTweets.itervalues(),logFilename)
    
if __name__ == '__main__':   
    

    #Default values
    proxy = None
    realTime = None
    postTwitter = False
    postStats = False
    postFile = False
    randomizeTweets = False
    beginDate = datetime.today() - timedelta(1)
    endDate = datetime.today()     
    politiciansFile = "../Resources/players.txt"
    sentiTokensFile = "../Resources/SentiLex-flex-PT02.txt"    
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
        elif param.startswith("-pol="):             
            politiciansFile = param.replace("-pol=","")
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
    
    if realTime == "lastHour":
        
        print "Go!"
        #Set the processing time frame to last hour of the current day
        endDate = endDate.replace(minute=0,second=0,microsecond=0)
        beginDate = endDate - timedelta(hours=1)
        
        main(politiciansFile,sentiTokensFile,exceptSentiTokens,multiWordsFile,logFolder,beginDate,endDate,postTwitter,postStats,postFile,randomizeTweets,proxy)
        print "Done!"
    
    elif realTime != None:
        
        print "Go!"
        #Set the processing time frame to 1 hour of the time given in rt
        endDate = realTime
        beginDate = endDate - timedelta(hours=1)
        
        main(politiciansFile,sentiTokensFile,exceptSentiTokens,multiWordsFile,logFolder,beginDate,endDate,postTwitter,postStats,postFile,randomizeTweets,proxy)
        print "Done!"
    
    elif singleSentence == None:
        
        print "Go!"
        #Set the processing time frame between 19h16 of the previous day 19h15 of the current day
        beginDate = beginDate.replace(hour=19,minute=1,second=0,microsecond=0)
        endDate = endDate.replace(hour=19,minute=0,second=0,microsecond=0)
        
        main(politiciansFile,sentiTokensFile,exceptSentiTokens,multiWordsFile,logFolder,beginDate,endDate,postTwitter,postStats,postFile,randomizeTweets,proxy)
        print "Done!"
    else:
        processSingleSentence(politiciansFile, sentiTokensFile, exceptSentiTokens, singleSentence,webOutput)

