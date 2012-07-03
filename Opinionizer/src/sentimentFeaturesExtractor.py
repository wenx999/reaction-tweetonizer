# -*- coding: UTF-8 -*-

import EuroOpinionizers
from Opinion import Opinion
import csv
import codecs
import Persons
import SentiTokens
import os
import glob
import cStringIO
import re
import Preprocessor
import pickle

SENTI_CACHE = "../cache/sentiTokens.cache"
PERSONS_CACHE = "../cache/persons.cache"
MULTIWORD_CACHE = "../cache/multiwords.cache"

ARFF_HEADERS = """

@relation twitometro

@ATTRIBUTE ID NUMERIC
@ATTRIBUTE hasNickName NUMERIC
@ATTRIBUTE hasInterjectionWithTarget NUMERIC
@ATTRIBUTE hasInterjection NUMERIC
@ATTRIBUTE hasLol NUMERIC
@ATTRIBUTE hasHehe NUMERIC
@ATTRIBUTE hasHeavyPunctuation NUMERIC
@ATTRIBUTE hasSmiley NUMERIC
@ATTRIBUTE hasQuotedSentiment NUMERIC
@ATTRIBUTE rule27 NUMERIC
@ATTRIBUTE rule4 NUMERIC
@ATTRIBUTE rule3 NUMERIC
@ATTRIBUTE rule2 NUMERIC
@ATTRIBUTE rule1 NUMERIC
@ATTRIBUTE rule12 NUMERIC
@ATTRIBUTE rule11 NUMERIC
@ATTRIBUTE rule14 NUMERIC
@ATTRIBUTE rule5 NUMERIC
@ATTRIBUTE rule13 NUMERIC
@ATTRIBUTE rule16 NUMERIC
@ATTRIBUTE rule15 NUMERIC
@ATTRIBUTE rule17 NUMERIC
@ATTRIBUTE rule18 NUMERIC
@ATTRIBUTE rule19 NUMERIC
@ATTRIBUTE rule6 NUMERIC
@ATTRIBUTE rule8 NUMERIC
@ATTRIBUTE rule7 NUMERIC
@ATTRIBUTE rule30 NUMERIC
@ATTRIBUTE rule29 NUMERIC
@ATTRIBUTE rule28 NUMERIC
@ATTRIBUTE rule37 NUMERIC
@ATTRIBUTE rule38 NUMERIC
@ATTRIBUTE rule39 NUMERIC
@ATTRIBUTE rule40 NUMERIC        
@ATTRIBUTE rule10 NUMERIC
@ATTRIBUTE rule9 NUMERIC
@ATTRIBUTE rule20 NUMERIC
@ATTRIBUTE rule21 NUMERIC
@ATTRIBUTE rule23 NUMERIC
@ATTRIBUTE rule22 NUMERIC
@ATTRIBUTE rule25 NUMERIC
@ATTRIBUTE rule24 NUMERIC
@ATTRIBUTE rule26 NUMERIC
@ATTRIBUTE rule32 NUMERIC
@ATTRIBUTE rule31 NUMERIC
@ATTRIBUTE rule34 NUMERIC
@ATTRIBUTE rule35 NUMERIC
@ATTRIBUTE rule33 NUMERIC
@ATTRIBUTE rule41  NUMERIC
@ATTRIBUTE naiveClassification {-1,0,1}
@ATTRIBUTE naiveSentiScore NUMERIC 
@ATTRIBUTE isNewsSource {0,1}
@ATTRIBUTE polarity? {-1,0,1}

@data

"""

TWEETS = "../SentiXXX.csv"
GOLD_STANDARD = "../SentiTuites-goldstandard-2012.csv"
GOLD_STANDARD_TEST = "../SentiTuites-goldstandard-2012-test.csv"
SOURCE_PATH = "../Results/"
DESTINY_PATH = "../Results/Features/"

"""
ID = 1
TARGET = 3 
MENTION = 4
SENTIMENT_POLARITY = 5 
TEXT = 6
"""

ID = 0
TARGET = 2 
MENTION = 3
SENTIMENT_POLARITY = 4 
TEXT = 6

def generateFeatures(isGoldStandard, sourceFile, destinyFile):
    
    #corpus = csv.reader(codecs.open(sourceFile,"r","utf-8"),delimiter='|')
    corpus = codecs.open(sourceFile,"r","utf-8")
     
    politicians = getPoliticians()
    sentiTokens = getSentiTokens()
    
    rulesClassifier = EuroOpinionizers.Rules(politicians,sentiTokens)     
    naiveClassifier = EuroOpinionizers.Naive(politicians,sentiTokens)    
    multiWordTokenizer = getMultiWordsTokenizer(politicians, sentiTokens)
    listOfTweets = []
    
    i=0
    
    for line in corpus:
        
        tweet = line.replace("\"","\'").split('|')
        
        #skip the first line
        if tweet[0] != 'PERIOD':
            
            
            sentence = ''
            
            for block in tweet[TEXT:]:
                sentence = sentence + block
                           
            tokenizedSentence = multiWordTokenizer.tokenizeMultiWords(sentence)
            tokenizedSentence =  Preprocessor.removeURLs(tokenizedSentence)
            tokenizedSentence = Preprocessor.removeUsernames(tokenizedSentence)
            
            o = Opinion(id = tweet[ID],
                        sentence = unicode(sentence),
                        processedSentence = unicode(tokenizedSentence),
                        target = unicode(tweet[TARGET]),
                        mention = unicode(tweet[MENTION]),
                        polarity = int(tweet[SENTIMENT_POLARITY]))
            
         
            
            listOfTweets.append(o)
    
            i = i+1
        """          
        if i!=0 and i%20 == 0:
            
            break
        """
        
    print "tweets loaded..."
    
    featuresFile = open(destinyFile,"w") 
    featuresFile.write(ARFF_HEADERS)
    unknownSentiFile = codecs.open("./unknownSentiment.csv","w","utf-8")
        
    featurama = cStringIO.StringIO()
    unknownSentiment = cStringIO.StringIO()
    
    
    i = 0
    
    tmp = cStringIO.StringIO()
    
    for tweet in listOfTweets:
        
        print tweet.id
        
        #used to verify if an instance matches any rule and\or has any sentiToken
        #if after processing this var still has value 0 then we don't add it to 
        #the training set...
        sentiCounter = 0
        
        tmp = cStringIO.StringIO()
        #featurama.write(str(tweet.id)+ ",")
        tmp.write(str(tweet.id)+ ",")
                 
        featureSet = rulesClassifier.generateFeatureSet(tweet,True)
                
        for feature in featureSet:
            #featurama.write(str(feature) + ",")
            tmp.write(str(feature) + ",")
            sentiCounter += feature
               
        naiveClassification = naiveClassifier.inferPolarity(tweet,True)
        #featurama.write(str(naiveClassification.polarity) + ",")
        tmp.write(str(naiveClassification.polarity) + ",")
        sentiCounter+= naiveClassification.polarity
                        
        pos = naiveClassification.metadata.find("score:")
        score = naiveClassification.metadata[pos+6:].replace(";","")
        #featurama.write(str(score) + ",")
        tmp.write(str(score) + ",")        
        sentiCounter+= int(score)
        
        isNews = isNewsSource(tweet.sentence)
        #featurama.write(str(isNews) + ",")
        tmp.write(str(isNews) + ",")
        sentiCounter+= isNews
        
        if sentiCounter != 0:
            if isGoldStandard:
                    
                featurama.write(tmp.getvalue()+str(tweet.polarity)+"\n")
            
            else:
                featurama.write(tmp.getvalue()+"?\n")
        
            i+=1
        else:
            unknownSentiment.write(str(tweet.id)+"|"+str(tweet.polarity)+"|"+tweet.sentence+"\n")
            
        
    featuresFile.write(featurama.getvalue())
    featuresFile.close()
    unknownSentiFile.write(unknownSentiment.getvalue())
    unknownSentiFile.close()

def isNewsSource(sentence):
    
    newsSourceList = u"jn|diarionoticias|publico|público|expresso|antena 1|destak|destakes|dn|economico|iportugal|iradar|portugal diario|sol|tsf|ultimas|noticiasrtp|rtp|tvi|sic|sicn|diárioeconómico|ionline|sábado|sabado|visao|visão|lusa_noticias|expressoonline"
        
    info = u'Regra \"news source!\""-> '        
    regex = ur'(\W|^)#({0})|@({0})|\(({0})\)|\[({0})\](\W|$)'.format(newsSourceList)
    lsentence = sentence.lower()
     
    match = re.search(regex,lsentence)
    
    if match != None: 
        
        return 1 
        
    else:
        return 0


def logTweets_old(listOfTweets,path):
    
    f = codecs.open(path,"w","utf-8")
    
    #Column headers
    f.write("ID|USER|TARGET|MENTION|POLARITY|INFO|MESSAGE|PROCESSED\n")
    
    for tweet in listOfTweets:            
                        
            target = tweet.target.replace("\n"," ").replace("\"","").replace("'","")
            mention = tweet.mention.replace("\n"," ").replace("\"","").replace("'","")
            metadata = tweet.metadata.replace("\n"," ").replace("'","")
            sentence = tweet.sentence.replace("|","\\").replace("\n"," ").replace("\t"," ").replace("\r"," ").replace("'","")
            processedSentence = tweet.processedSentence.replace("|","\\").replace("\n"," ").replace("\t"," ").replace("\r"," ").replace("'","")
            
            f.write("\""+str(tweet.id) + "\"|" + tweet.user + "|\"" + target  + "\"|\"" + mention + "\"|" + str(tweet.polarity ) + "|\"" + metadata +  "\"|\"" + sentence + "\"|\"" + processedSentence + "\"\n")
    
    f.close()

def logTweets(listOfTweets,path):
    
    f = codecs.open(path,"w","utf-8")
    
    #Column headers
    f.write("ID|USER|TARGET|MENTION|POLARITY|INFO|MESSAGE|PROCESSED\n")
    
    for tweet in listOfTweets:            
                        
            target = tweet.target.replace("\n"," ").replace("\"","").replace("'","")
            mention = tweet.mention.replace("\n"," ").replace("\"","").replace("'","")
            metadata = tweet.metadata.replace("\n"," ").replace("'","")
            sentence = tweet.sentence.replace("|","\\").replace("\n"," ").replace("\t"," ").replace("\r"," ").replace("'","")
            processedSentence = tweet.processedSentence.replace("|","\\").replace("\n"," ").replace("\t"," ").replace("\r"," ").replace("'","")
            
            f.write(str(tweet.id) + "|" + tweet.user + "|" + target  + "|" + mention + "|" + str(tweet.polarity ) + "|" + metadata +  "|" + sentence + "|" + processedSentence + "\n")
    
    f.close()

def testOldProcessWithDiagnostics(sourceFile):
    
    results = {"numOf-1":0,"correct-1":0,"numOf0":0,"correct0":0,"numOf1":0,"correct1":0}
    
    #corpus = csv.reader(codecs.open(sourceFile,"r","utf-8"),delimiter='|')
    corpus = codecs.open(sourceFile,"r","utf-8")
    
    listOfTweets = []
    i=0
    
    politicians = getFromCache(PERSONS_CACHE) #getPoliticians()
    sentiTokens = getFromCache(SENTI_CACHE) #getSentiTokens()
    
    rulesClassifier = EuroOpinionizers.Rules(politicians,sentiTokens)     
    naiveClassifier = EuroOpinionizers.Naive(politicians,sentiTokens)    
    multiWordTokenizer = getFromCache(MULTIWORD_CACHE) #getMultiWordsTokenizer(politicians, sentiTokens)
    
    print "loading tweets..."
    
    for line in corpus:
        
        tweet = line.split('|')
        
        #skip the first line
        if tweet[0] != 'ID':
            
            #print tweet
            """
            fullSentence = ''
            
            
            #in some cases the message spawns across several fields so we are concatenating them...
            for block in tweet[TEXT:]:
                fullSentence = fullSentence + block
            """
            
            fullSentence = tweet[TEXT]    
            tokenizedSentence = multiWordTokenizer.tokenizeMultiWords(unicode(fullSentence))
            tokenizedSentence =  Preprocessor.removeURLs(tokenizedSentence)
            tokenizedSentence = Preprocessor.removeUsernames(tokenizedSentence)            
            
            o = Opinion(id = tweet[ID],
                        user = u"Teste",
                        sentence = unicode(fullSentence),
                        processedSentence = unicode(tokenizedSentence),
                        target = unicode(tweet[TARGET]),
                        mention = unicode(tweet[MENTION]),
                        polarity = int(tweet[SENTIMENT_POLARITY]))            
            listOfTweets.append(o)
    
            i = i+1            
            """
            if i!=0 and i%10 == 0:
                
                break
            """
            
    print "tweets loaded..."
    
    falseNeg = []
    falsePos = []
    falseNeut = []
    totalList = []
              
    for tweet in listOfTweets:
        
        rulesTweet = rulesClassifier.inferPolarity(tweet,True)
        naiveTweet = naiveClassifier.inferPolarity(tweet,True)
        
        regex = ur"score:(.*);"
        sentiScore = re.search(regex, naiveTweet.metadata).group(1)
        tweetScore = int(sentiScore) + int(rulesTweet.polarity)
        
        if tweetScore > 0:
            tweet.polarity = 1
        elif tweetScore < 0:
            tweet.polarity = -1
        else:
            tweet.polarity = 0
        
        tweet.metadata = rulesTweet.metadata + ";" + naiveTweet.metadata
        
        totalList.append(tweet)
        
        """
        if tweet.polarity == -1:
            results["numOf-1"] += 1
            if tweet.polarity == classifiedTweet.polarity:
                results["correct-1"] +=1
            else:
                matchedRules = rulesDiagnosticHelper(rulesClassifier.generateFeatureSet(tweet,True))
                classifiedTweet.metadata += " " + matchedRules
                falseNeg.append(classifiedTweet)
                
        elif tweet.polarity == 0:
            results["numOf0"] += 1
            if tweet.polarity == classifiedTweet.polarity:
                results["correct0"] +=1
            else:            
                matchedRules = rulesDiagnosticHelper(rulesClassifier.generateFeatureSet(tweet,True))
                classifiedTweet.metadata += " " + matchedRules
                falseNeut.append(classifiedTweet)
                
        if tweet.polarity == 1:
            results["numOf1"] += 1
            if tweet.polarity == classifiedTweet.polarity:
                results["correct1"] +=1
            else:
                matchedRules = rulesDiagnosticHelper(rulesClassifier.generateFeatureSet(tweet,True))
                classifiedTweet.metadata += " " + matchedRules
                falsePos.append(classifiedTweet)
    
    logTweets(falseNeg,"./falseNegs.csv")
    logTweets(falseNeut,"./falseNeut.csv")
    logTweets(falsePos,"./falsePos.csv")
    """
    logTweets(totalList,"./newProcess.csv")
    
    """
    g = open("results.txt","w")
    
    for k,v in results.items():
        
        g.write(k+":"+str(v)+"\n")
    
    g.close()    
                
    print results
    """
    
def testSubjectivity(sourceFile):
    
    corpus = codecs.open(sourceFile,"r","utf-8")
    
    listOfTweets = []
    rejectList = []
    i=0
    
    politicians = getPoliticians()
    sentiTokens = getSentiTokens()
    
    #rulesClassifier = EuroOpinionizers.Rules(politicians,sentiTokens)     
    naiveClassifier = EuroOpinionizers.Naive(politicians,sentiTokens)    
    #multiWordTokenizer = getMultiWordsTokenizer(politicians, sentiTokens)
    
    print "loading tweets..."
    
    for line in corpus:
        
        tweet = line.replace("\"","\'").split('|')
        
        #skip the first line
        if tweet[0] != 'PERIOD':
            
            #print tweet
            
            fullSentence = ''
            
            #in some cases the message spawns across several fields so we are concatenating them...
            for block in tweet[TEXT:]:
                fullSentence = fullSentence + block
                
            tokenizedSentence = Preprocessor.separateSpecialSymbols(unicode(fullSentence)) #multiWordTokenizer.tokenizeMultiWords(unicode(fullSentence))
            #tokenizedSentence =  Preprocessor.removeURLs(tokenizedSentence)
            #tokenizedSentence = Preprocessor.removeUsernames(tokenizedSentence)            
            print tokenizedSentence
            
            o = Opinion(id = tweet[ID],
                        user = u"Teste",
                        sentence = unicode(fullSentence),
                        processedSentence = tokenizedSentence,
                        target = unicode(tweet[TARGET]),
                        mention = unicode(tweet[MENTION]),
                        polarity = int(tweet[SENTIMENT_POLARITY]))
            
            matches = re.findall(naiveClassifier.sentiTokensRegex ,tokenizedSentence) 
            
            if matches != None and len(matches) > 0:  
            
                listOfTweets.append(o)
                
            else:
                rejectList.append(o) 
            
            i = i+1
            
            """
            if i!=0 and i%30 == 0:
                
                break
            """
    
    logTweets(listOfTweets,"./listOfTweets.csv")
    logTweets(rejectList,"./rejectList.csv")

def genFeatsWithSubjectivity(isGoldStandard,sourceFile, destinyFile):
    
    corpus = codecs.open(sourceFile,"r","utf-8")
     
    politicians = getPoliticians()
    sentiTokens = getSentiTokens()
    
    rulesClassifier = EuroOpinionizers.Rules(politicians,sentiTokens)     
    naiveClassifier = EuroOpinionizers.Naive(politicians,sentiTokens)    
    multiWordTokenizer = getMultiWordsTokenizer(politicians, sentiTokens)
    listOfTweets = []
    
    i=0
    
    for line in corpus:
        
        tweet = line.replace("\"","\'").split('|')
        
        #skip the first line
        if tweet[0] != 'PERIOD':            
            
            sentence = ''
            
            for block in tweet[TEXT:]:
                sentence = sentence + block
                           
            tokenizedSentence = multiWordTokenizer.tokenizeMultiWords(sentence)            
            tokenizedSentence = Preprocessor.removeURLs(tokenizedSentence)
            tokenizedSentence = Preprocessor.removeUsernames(tokenizedSentence)
            #tokenizedSentence =  separateSpecialSymbols(tokenizedSentence)
            
            o = Opinion(id = tweet[ID],
                        sentence = unicode(sentence),
                        processedSentence = unicode(tokenizedSentence),
                        target = unicode(tweet[TARGET]),
                        mention = unicode(tweet[MENTION]),
                        polarity = int(tweet[SENTIMENT_POLARITY]))
            
            listOfTweets.append(o)
    
            i = i+1
        """          
        if i!=0 and i%50 == 0:
            
            break
        """
        
        
    print "tweets loaded..."
    
    featuresFile = open(destinyFile,"w") 
    featuresFile.write(ARFF_HEADERS)
    unknownSentiFile = codecs.open("./unknownSentiment.csv","w","utf-8")
        
    featurama = cStringIO.StringIO()
    unknownSentiment = cStringIO.StringIO()    
    
    tmp = cStringIO.StringIO()
    
    for tweet in listOfTweets:
                
        #used to verify if an instance matches any rule and\or has any sentiToken
        #if after processing this var still has value 0 then we don't add it to 
        #the training set...
        sentiCounter = 0
        
        tmp = cStringIO.StringIO()
        tmp.write(str(tweet.id)+ ",")
                 
        featureSet = rulesClassifier.genConditionalFeatureSet(tweet,True)
                
        for feature in featureSet:
            tmp.write(str(feature) + ",")
            sentiCounter += feature
               
        naiveClassification = naiveClassifier.inferPolarity(tweet,True)
        tmp.write(str(naiveClassification.polarity) + ",")
        sentiCounter+= naiveClassification.polarity
                        
        pos = naiveClassification.metadata.find("score:")
        score = naiveClassification.metadata[pos+6:].replace(";","")
        tmp.write(str(score) + ",")        
        sentiCounter+= int(score)
        
        isNews = isNewsSource(tweet.sentence)    
    
        tmp.write(str(isNews) + ",")
        sentiCounter+= isNews
        
        if sentiCounter != 0:
            
            if isGoldStandard:
                    
                featurama.write(unicode(tmp.getvalue())+unicode(tweet.polarity))
            
            else:
                featurama.write(tmp.getvalue()+"?\n")
        else:
            unknownSentiment.write(str(tweet.id)+"|"+str(tweet.polarity)+"|"+tweet.sentence+"\n")
            
        
    featuresFile.write(featurama.getvalue())
    featuresFile.close()
    unknownSentiFile.write(unknownSentiment.getvalue())
    unknownSentiFile.close() 
    
    
def rulesDiagnosticHelper(rulesVector):
    
    setOfRules = ["hasNickName","hasInterjectionWithTarget","hasInterjection","hasLol","hasHehe","hasHeavyPunctuation",
    "hasSmiley","hasQuotedSentiment","rule27","rule4","rule3","rule2","rule1","rule12","rule11","rule14","rule5","rule13","rule16","rule15",
    "rule17","rule18","rule19","rule6","rule8","rule7","rule30","rule29","rule28","rule37","rule38","rule39","rule40",        
    "rule10","rule9","rule20","rule21","rule23","rule22","rule25","rule24","rule26","rule32","rule31","rule34","rule35","rule33", "rule41"]
     
    v = 0
    matchedRules = ';rules='
     
    while v < len(rulesVector):
        
        if rulesVector[v] != 0:
            matchedRules = matchedRules + "," + setOfRules[v]
            
        v += 1
    
    return matchedRules

def getFromCache(filename):
    
    obj = None
    
    try:
        f = open(filename, "r")    
        obj = pickle.load(f)
    except IOError:
        obj = None
        
    return obj
    
def getPoliticians():
    
    politiciansFile = "../Resources/politicians.txt"
    politicians = Persons.loadPoliticians(politiciansFile)
    
    return politicians

def getSentiTokens():
    
    sentiTokensFile = "../Resources/SentiLex-flex-PT03.txt"
    exceptTokensFile = "../Resources/SentiLexAccentExcpt.txt"
    
    sentiTokens = SentiTokens.loadSentiTokens(sentiTokensFile,exceptTokensFile)
    
    return sentiTokens
   
def getRulesClassifier(politicians, sentiTokens):
    
    return EuroOpinionizers.Rules(politicians,sentiTokens)    

def getNaiveClassifier(politicians, sentiTokens):
    
    return EuroOpinionizers.Naive(politicians,sentiTokens)    

def getMultiWordsTokenizer(politicians,sentiTokens):
    
    multiWordsFile = "../Resources/multiwords.txt"    
    
    multiWordTokenizer = EuroOpinionizers.MultiWordHandler(multiWordsFile)
    multiWordTokenizer.addMultiWords(Persons.getMultiWords(politicians))
    multiWordTokenizer.addMultiWords(SentiTokens.getMultiWords(sentiTokens))

    return multiWordTokenizer

def processFiles():
    
    for infile in glob.glob( os.path.join(SOURCE_PATH, '*.csv') ):

        baseFileName = os.path.basename(infile)
        
        print "processing ", baseFileName, "..."
        generateFeatures(False,infile,DESTINY_PATH+baseFileName.replace(".csv","")+"_feats.csv")        


def generateTextFeatures(sourceFile,destinyFile):
    
    corpus = codecs.open(sourceFile,"r","utf-8")
     
    politicians = getPoliticians()
    sentiTokens = getSentiTokens()
    
    #rulesClassifier = EuroOpinionizers.Rules(politicians,sentiTokens)     
    #naiveClassifier = EuroOpinionizers.Naive(politicians,sentiTokens)    
    multiWordTokenizer = getMultiWordsTokenizer(politicians, sentiTokens)
    listOfTweets = []
    
    i=0
    headers = """
    

@relation twitometro

@ATTRIBUTE ID NUMERIC 
@ATTRIBUTE tweet STRING
@ATTRIBUTE polarity? {-1,0,1}

@data
 
    """

    featuresFile = open(destinyFile,"w") 
    featuresFile.write(headers)
    
    for line in corpus:
        
        tweet = line.replace("\"","\'").split('|')
        
        #skip the first line
        if tweet[0] != 'PERIOD':            
            
            sentence = ''
            
            for block in tweet[TEXT:]:
                sentence = sentence + block
                           
            tokenizedSentence = multiWordTokenizer.tokenizeMultiWords(sentence)
            tokenizedSentence =  Preprocessor.removeURLs(tokenizedSentence)
            tokenizedSentence = Preprocessor.removeUsernames(tokenizedSentence)
            tokenizedSentence = tokenizedSentence.replace(tweet[MENTION]," <TARGET> ")
            tokenizedSentence = Preprocessor.removeStopWords(tokenizedSentence)
            tokenizedSentence = Preprocessor.separateSpecialSymbols(tokenizedSentence)
            tokenizedSentence = tokenizedSentence.replace("\n","") 
            tokenizedSentence = tokenizedSentence.replace(","," ")
            
            featuresFile.write(tweet[ID]+",\""+tokenizedSentence+"\","+tweet[SENTIMENT_POLARITY]+"\n")
            print sentence + " --> " + tokenizedSentence
            
            """
            o = Opinion(id = tweet[ID],
                        sentence = unicode(sentence),
                        processedSentence = unicode(tokenizedSentence),
                        target = unicode(tweet[TARGET]),
                        mention = unicode(tweet[MENTION]),
                        polarity = int(tweet[SENTIMENT_POLARITY]))
            
            listOfTweets.append(o)
            """
            
            i = i+1       
            
            """     
            if i!=0 and i%20 == 0:
            
                break
            """
            
    featuresFile.close()   


if __name__ == '__main__':
    
    testOldProcessWithDiagnostics("../Results/tweets623.csv")   
    
    print "Done!"