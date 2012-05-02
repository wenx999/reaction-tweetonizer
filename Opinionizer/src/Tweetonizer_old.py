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
#import urllib2
#import urllib
import simplejson
from Opinion import Opinion
import codecs
#import twitter
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

access_key_prod = "300277144-taeETTFSRiQLUvOc667Y84PnobK0lley8jtC4zJg"
access_secret_prod = "tDms9BFzHAwhVmVoPbIpwdVblPHrAdxEsYJCzw4q1k"

def usage(commandName):
    
    print "usage: " + commandName + " [-pt (post to twitter and stats)|-ptr (post to twitter but randomize posts)|-pts (post stats only)] [-pr=proxy] [-pol=politicians file] [-sent=sentiment tokens file] [-excpt=exception sentiment tokens file] [-mw=multiwords file] [-bd=begin date (yyyy-mm-dd)] [-ed=end date (yyyy-mm-dd)] [-ss=single sentence] [-ssw=single sentence and web output] [-log=log file] [-excpt=ex"

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
            
            f.write("\""+str(tweet.id) + "\"|" + tweet.user + "|\"" + target  + "\"|\"" + mention + "\"|" + str(tweet.polarity ) + "|\"" + metadata +  "\"|\"" + sentence + "\"|\"" + taggedSentence + "\"\n")
    
    f.close()

def postResults(stats,proxy,date):
    
        print "1"

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
    
    print "1"

def printMessages(messages):
    
    for message in messages:
    
        print message
 
def tweetResults(tweets,acessKey,acessSecrect,randomizeTweets,proxy):    

    print "1"

    
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
    
    print "Loading resources...\nPoliticians: " + politiciansFile   
    politicians = Persons.loadPoliticians(politiciansFile)
    
    print "SentiTokens: " + sentiTokensFile + "\nExceptTokens: " +  exceptSentiTokens
    sentiTokens = SentiTokens.loadSentiTokens(sentiTokensFile,exceptSentiTokens)
    
    print "Multiword Tokenizer " + multiWordsFile    
    multiWordTokenizer = MultiWordHandler(multiWordsFile)
    multiWordTokenizer.addMultiWords(Persons.getMultiWords(politicians))
    multiWordTokenizer.addMultiWords(SentiTokens.getMultiWords(sentiTokens))
    
    naive = Naive(politicians,sentiTokens)    
    
    targetedTweets = {}    
    classifiedTweets = {}
    
    #Process tweets...
    #First step: infer targets and create a dictionary {target,listOfTweets}    
    print "Identifying targets..."
     
    for tweet in tweets:        
        
        tweetsWithTarget = naive.inferTarget(tweet)
        
        if tweetsWithTarget != None :
            
            #a tweet can have multiple targets (in that case the message is replicated)
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
            
            #try to classify with rules...
            classifiedTweet = rules.inferPolarity(tweet,True)
            
            #if not possible use the naive classifier
            if classifiedTweet.polarity == 0:
                classifiedTweet = naive.inferPolarity(classifiedTweet,True)
            
            classifiedTweets[target].append(classifiedTweet)
            
    return classifiedTweets

def processSingleSentence(politiciansFile,sentiTokensFile,exceptSentiTokens,sentence,webOutput):
            
    print "<br>Loading resources...<br>Politicians: " + politiciansFile    
    politicians = Persons.loadPoliticians(politiciansFile)
    
    print "<br>SentiTokens: " + sentiTokensFile + "<br>ExceptTokens: " +  exceptSentiTokens
    sentiTokens = SentiTokens.loadSentiTokens(sentiTokensFile,exceptSentiTokens)
    
    naive = Naive(politicians,sentiTokens)
    
    singleSentence = Opinion(1, sentence=sentence)
    targets = naive.inferTarget(singleSentence)
    results = []
    
    print "<br>Inferring targets...<br>"
        
    if targets != None:    
        
        print "<br>Inferring polarity...<br>"
        
        for target in targets:
            
            rules = Rules(politicians,sentiTokens)
            results.append(rules.inferPolarity(target, False))
    else:
        print "<br>No targets were identified...<br>"
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
           
def main(politiciansFile,sentiTokensFile,exceptSentiTokens,multiWordsFile,logFolder,beginDate,endDate,postTwitter,postStats,randomizeTweets,proxy,):       
    
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
            
    else:
        printMessages(formatedStats)
    
    logFilename = logFolder + "tweets"+str(beginDate.month)+str(beginDate.day)+str(endDate.day)+".csv"
    logClassifiedTweets(classifiedTweets.itervalues(),logFilename)

if __name__ == '__main__':   
    
    #Default values
    proxy = None
    postTwitter = False
    postStats = False
    randomizeTweets = False
    beginDate = datetime.today() - timedelta(1)
    endDate = datetime.today()     
    politiciansFile = "../Resources/politicians.txt"
    sentiTokensFile = "../Resources/sentiTokens-2011-05-30.txt"    
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
            postTwitter = True
            randomizeTweets = True
        elif param == "-pt":
            postTwitter = True
            postStats = True        
        elif param == "-pts":            
            postStats = True
        else:            
            print "Error! " + param
            usage(sys.argv[0])
            sys.exit(-1)
    
    if singleSentence == None:
        
        print "Go!"
        #Set the processing time frame between 19h16 of the previous day 19h15 of the current day
        beginDate = beginDate.replace(hour=19,minute=1,second=0,microsecond=0)
        endDate = endDate.replace(hour=19,minute=0,second=0,microsecond=0)
        
        main(politiciansFile,sentiTokensFile,exceptSentiTokens,multiWordsFile,logFolder,beginDate,endDate,postTwitter,postStats,randomizeTweets,proxy)
        print "Done!"
    else:
        processSingleSentence(politiciansFile, sentiTokensFile, exceptSentiTokens, singleSentence,webOutput)
                
    
