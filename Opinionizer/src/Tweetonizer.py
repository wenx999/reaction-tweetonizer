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
import operator
import xml.dom.minidom
import urllib2
import urllib
import simplejson
from Opinion import Opinion
import csv
import codecs
import twitter
import os
import sys
import Utils
import random

TARGET = 0
N_TWEETS = 1
POSITIVES = 2
NEUTRALS = 3
NEGATIVES = 4

access_key_test = "284707222-ZRvtSilVFXGcEYT8AZ04STWP9q7VXofN3L3Ufx2s"
access_secret_test = "1PkYjXaJWzSyd0K6Z4g5Wsg6NZ9iVNNOxI277ELrbqA"

""" OBSOLETE 

def writeResults(tweetsByTarget):
    
    resultsFolder = "./OpinionizedTweets/"
    
    for target,tweets in tweetsByTarget.items():        
                
        doc = xml.dom.minidom.Document()
        
        root = doc.createElement("Opinionizer")
        root.setAttribute("target", target)
        root.setAttribute("numberOfTweets", str(len(tweets)))
        doc.appendChild(root)       
        
        tweets.sort(key=operator.attrgetter("date"),reverse=True)
        
        currentDate = None
        currentNode = None
        
        for opinion in tweets: 
            
            if opinion.date != currentDate:
                currentDate = opinion.date
                currentNode = doc.createElement("Tweets")
                currentNode.setAttribute("date",str(opinion.date))
                root.appendChild(currentNode)                
            
            comment = doc.createElement("tweet")
            comment.setAttribute("id",str(opinion.id))
            
            if opinion.target != None:
                comment.setAttribute("target",opinion.target)          

            if opinion.polarity != None:    
                comment.setAttribute("polarity",str(opinion.polarity))
             
            commentText = doc.createTextNode(opinion.sentence)
            
            comment.appendChild(commentText)
            currentNode.appendChild(comment)
        
        doc.writexml( open(resultsFolder+target, 'w'),
                indent="  ",
                addindent="  ",
                newl='\n',
                encoding="utf-8")
    
        doc.unlink()
        
def getTweetsCSV():
    
    USER_ID = 0
    STATUS_ID = 1
    CREATED_AT = 2
    TWEET = 3
    
    listOfTweets = {}
    
    reader = csv.reader(codecs.open("tweets.csv","r","utf-8"), delimiter=',')  
    
    for tweet in reader:
        
        try:
            id = tweet[USER_ID] + "_" + tweet[STATUS_ID]
            date =  datetime.strptime(tweet[CREATED_AT].split(' ')[0], '%Y-%m-%d')
            
            listOfTweets[id] = Opinion(id,unicode(tweet[TWEET]),date=date)
        except IndexError:
            continue
        
    return listOfTweets        

 OBSOLETE """

def usage(commandName):
    
    print "usage: " + commandName + " [-pt (post to twitter)|-ptr (post to twitter but randomize posts)] [-pr=proxy] [-pol=politicians file] [-sent=sentiment tokens file] [-excpt=exception sentiment tokens file] [-mw=multiwords file] [-bd=begin date (yyyy-mm-dd)] [-ed=end date (yyyy-mm-dd)] [-ss=single sentence] [-ssw=single sentence and web output]"

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
            taggedSentence = tweet.taggedSentence.replace("|","\\").replace("\n"," ").replace("\t"," ").replace("\r"," ")
            
            f.write(tweet.id + "|" + tweet.user + "|\"" + target  + "\"|\"" + mention + "\"|" + str(tweet.polarity ) + "|\"" + metadata +  "\"|\"" + sentence + "\"|\"" + taggedSentence + "\"\n")
    
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
    
    username = "twitter_crawl_user"
    password = "twitter_crawl_pass"
    top_level_url = "http://robinson.fe.up.pt/cgi-bin/twitter_crawl/get_tweets.pl"
    requestTweets = "http://robinson.fe.up.pt/cgi-bin/twitter_crawl/get_tweets.pl?begin_date={0}&end_date={1}&format=JSON&limit=all"
    #requestTweets = "http://robinson.fe.up.pt/cgi-bin/twitter_crawl/get_tweets.pl?begin_date=2011-04-10&end_date=2011-04-12%2001:00:00&format=JSON"
    
    #Password manager because the service requires authentication
    password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
    password_mgr.add_password(None, top_level_url, username, password)
    auth_handler = urllib2.HTTPBasicAuthHandler(password_mgr)
    opener = None
    
    if proxy != None:
    
        proxy_handler = urllib2.ProxyHandler({'http': proxy})        
        opener = urllib2.build_opener(auth_handler,proxy_handler)       
    else:
        opener = urllib2.build_opener(auth_handler)
    
    print "Requesting: " + requestTweets.format(urllib.quote(beginDate.strftime('%Y-%m-%d %H:%M')),
                                                urllib.quote(endDate.strftime('%Y-%m-%d %H:%M')))
    
    twitterData = opener.open(requestTweets.format(urllib.quote(beginDate.strftime('%Y-%m-%d %H:%M')),
                                                   urllib.quote(endDate.strftime('%Y-%m-%d %H:%M'))))
    
    #Read the JSON response
    jsonTwitter = simplejson.loads(unicode(twitterData.read().decode("utf-8")))  
    listOfTweets = []
    
    #Build a dictionary
    for tweet in jsonTwitter["tweets"]:
        
        id = tweet["user_id"] + "_" + tweet["status_id"]
        userId = unicode(tweet["user_id"])
        #print userId
        
        date =  datetime.strptime(tweet["created_at"].split(' ')[0], '%Y-%m-%d')
        
        listOfTweets.append(Opinion(tweet["status_id"],unicode(tweet["text"]),user=userId,date=date))
     
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

def processTweets(politiciansFile,sentiTokensFile,exceptSentiTokens,multiWordsFile,tweets):
    
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
    
    print "Loading resources...\nPoliticians: " + politiciansFile + "\nSentiTokens: " + sentiTokensFile + "\nExceptTokens: " +  exceptSentiTokens
    politicians = Persons.loadPoliticians(politiciansFile)
    sentiTokens = SentiTokens.loadSentiTokens(sentiTokensFile,exceptSentiTokens)
    naive = Naive(politicians,sentiTokens)    
    multiWordTokenizer = MultiWordHandler(multiWordsFile)
    multiWordTokenizer.addMultiWords(Persons.getMultiWords(politicians))
    multiWordTokenizer.addMultiWords(SentiTokens.getMultiWords(sentiTokens))
    
    targetedTweets = {}    
    classifiedTweets = {}
    
    #Process tweets...
    #First step: infer targets and create a dictionary {target,listOfTweets}    
    print "Identifying targets..."
     
    for tweet in tweets:        
        
        tweetsWithTarget = naive.inferTarget(tweet)
        
        if tweetsWithTarget != None :
            
            for tweet in tweetsWithTarget:
            
                if tweet.target not in targetedTweets:                    
                
                    targetedTweets[tweet.target] = []
                
                tweet.taggedSentence = multiWordTokenizer.tokenizeMultiWords(tweet.sentence)  
                targetedTweets[tweet.target].append(tweet)
    
    print  len(targetedTweets), " targets Identified! Inferring polarity..."
    
    rules = Rules(politicians,sentiTokens)
    
    #Second step infer polarity 
    for target,tweets in targetedTweets.items():
        
        for tweet in tweets: 
            
            if target not in classifiedTweets:
                classifiedTweets[target]  = []
            
            classifiedTweet = rules.inferPolarity(tweet,True)
            
            if classifiedTweet.polarity == 0:
                classifiedTweet = naive.inferPolarity(classifiedTweet,True)
            
            classifiedTweets[target].append(classifiedTweet)
            
    return classifiedTweets

def processSingleSentence(politiciansFile,sentiTokensFile,exceptSentiTokens,sentence,webOutput):
        
    politicians = Persons.loadPoliticians(politiciansFile)
    sentiTokens = SentiTokens.loadSentiTokens(sentiTokensFile,exceptSentiTokens)
    naive = Naive(politicians,sentiTokens)
    
    singleSentence = Opinion(1, sentence=sentence)
    targets = naive.inferTarget(singleSentence)
    results = []
    
    if targets != None:    
        for target in targets:
            
            rules = Rules(politicians,sentiTokens)
            results.append(rules.inferPolarity(target))
    
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
           
def main(politiciansFile,sentiTokensFile,exceptSentiTokens,multiWordsFile,logFolder,beginDate,endDate,post,randomizeTweets,proxy,):       
    
    listOfTweets = getNewTweets(beginDate,endDate,proxy)
    classifiedTweets = processTweets(politiciansFile,sentiTokensFile,exceptSentiTokens,multiWordsFile,listOfTweets)
               
    stats = getStats(classifiedTweets)    
    formatedStats = formatStats(stats,len(listOfTweets),beginDate,endDate)
    
    if post:
        #If randomize tweets is enabled, assume this is a test run so posts will be done in
        #the tests account
        if randomizeTweets:        
            tweetResults(formatedStats,access_key_test,access_secret_test,randomizeTweets,proxy)
        else:
            #post results in the production account and post statistcs for the charts
            tweetResults(formatedStats,access_key_test,access_secret_test,randomizeTweets,proxy)        
            postResults(stats,proxy,endDate)
    else:
        printMessages(formatedStats)
    
    logFilename = logFolder + "tweets"+str(beginDate.month)+str(beginDate.day)+str(endDate.day)+".csv"
    logClassifiedTweets(classifiedTweets.itervalues(),logFilename)

if __name__ == '__main__':   
    
    #Default values
    proxy = None
    post = False
    randomizeTweets = False
    beginDate = datetime.today() - timedelta(1)
    endDate = datetime.today()     
    politiciansFile = "../Resources/politicians.txt"
    sentiTokensFile = "../Resources/sentitokens-2011-05-13.txt"
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
        elif param.startswith("-ss="):                     
            singleSentence = unicode(param.replace("-ss=","").decode("utf-8"))
        elif param.startswith("-ssw="):                     
            singleSentence = unicode(param.replace("-ssw=","").decode("utf-8"))
            webOutput = True
        elif param == "-ptr":
            print "Warning: Tweets will be randomized!"
            post = True
            randomizeTweets = True
        elif param == "-pt":
            post = True        
        else:            
            print "Error! " + param
            usage(sys.argv[0])
            sys.exit(-1)
    
    if singleSentence == None:
        
        print "Go!"
        #Set the processing time frame between 19h16 of the previous day 19h15 of the current day
        beginDate = beginDate.replace(hour=19,minute=1,second=0,microsecond=0)
        endDate = endDate.replace(hour=19,minute=0,second=0,microsecond=0)
        
        main(politiciansFile,sentiTokensFile,exceptSentiTokens,multiWordsFile,logFolder,beginDate,endDate,post,randomizeTweets,proxy)
        print "Done!"
    else:
        processSingleSentence(politiciansFile, sentiTokensFile, exceptSentiTokens, singleSentence,webOutput)
                
    
