import Opinionizers
from Opinion import Opinion
import csv
import codecs
import Persons
import SentiTokens
import os
import glob


#TWEETS = "/home/samir/TwitometroCorpus/teste.csv"
#TWEETS = "/home/samir/corpusSoft.csv"
TWEETS = "/home/samir/tweetscorpus.csv"
GOLD_STANDARD = "/home/samir/TwitometroCorpus/tweets_GoldStandard_teste.csv"
SOURCE_PATH = "../Results/"
DESTINY_PATH = "../Results/Features/"

ID = 1
TARGET = 3 
MENTION = 4
SENTIMENT_POLARITY = 5 
TEXT = 7

def generateFeatures(isGoldStandard, sourceFile, destinyFile):
    
    corpus = csv.reader(codecs.open(sourceFile,"r","utf-8"),delimiter='|')
    
    listOfTweets = []
    
    for tweet in corpus:
        
        #skip the first line
        if tweet[0] != 'DATE':
        
            o = Opinion(id = tweet[ID],
                        sentence = unicode(tweet[TEXT]),
                        target = unicode(tweet[TARGET]),
                        mention = unicode(tweet[MENTION]),
                        polarity = int(tweet[SENTIMENT_POLARITY]))
            
            listOfTweets.append(o)
    
    print "tweets loaded..."
         
    rulesClassifier = getRulesClassifier()
    naiveClassifier = getNaiveClassifier()
    
    featuresFile = csv.writer(open(destinyFile,"w"),delimiter='|') 
    
    for t in listOfTweets:
                
        featureSet = rulesClassifier.generateFeatureSet(t)
        featureSet.append(naiveClassifier.inferPolarity(t,False).polarity)
        featureSet.insert(0, t.id)
        
        if isGoldStandard:
                
            featureSet.append(t.polarity)
        
        featuresFile.writerow(featureSet)
        
    
def getRulesClassifier():

    politiciansFile = "../Resources/politicians.txt"
    sentiTokensFile = "../Resources/sentiTokens-2011-05-30.txt"
    exceptTokensFile = "../Resources/SentiLexAccentExcpt.txt"
    
    politicians = Persons.loadPoliticians(politiciansFile)
    sentiTokens = SentiTokens.loadSentiTokens(sentiTokensFile,exceptTokensFile)
    
    return Opinionizers.Rules(politicians,sentiTokens)    

def getNaiveClassifier():

    politiciansFile = "../Resources/politicians.txt"
    sentiTokensFile = "../Resources/sentiTokens-2011-05-30.txt"
    exceptTokensFile = "../Resources/SentiLexAccentExcpt.txt"
    
    politicians = Persons.loadPoliticians(politiciansFile)
    sentiTokens = SentiTokens.loadSentiTokens(sentiTokensFile,exceptTokensFile)
    
    return Opinionizers.Naive(politicians,sentiTokens)    

def processFiles():
    
    for infile in glob.glob( os.path.join(SOURCE_PATH, '*.csv') ):

        baseFileName = os.path.basename(infile)
        
        print "processing ", baseFileName, "..."
        generateFeatures(False,infile,DESTINY_PATH+baseFileName.replace(".csv","")+"_feats.csv")        


if __name__ == '__main__':
    
    print "GO"
    
    #processFiles()
    #generateFeatures(True,GOLD_STANDARD,"tweets_gold.csv")
    generateFeatures(False,TWEETS,"tweets_corpusfeatures.csv")
    
    print "Done!"