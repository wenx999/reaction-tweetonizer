import Opinionizers
from Opinion import Opinion
import csv
import codecs
import Persons
import SentiTokens

TWEETS = "/home/samir/TwitometroCorpus/teste.csv"
GOLD_STANDARD = "/home/samir/TwitometroCorpus/tweets_GoldStandard_teste.csv"

ID = 0
TARGET = 2 
MENTION = 3
SENTIMENT_POLARITY = 4 
TEXT = 6

def generateFeatures(isGoldStandard, sourceFile, destinyFile):
    
    corpus = csv.reader(codecs.open(sourceFile,"r","utf-8"),delimiter='|')
    
    listOfTweets = []
    
    for tweet in corpus:
        
        # sentence, target=u'', mention=u'', polarity=u'', irony=u'',metadata=u'',user=None,date=None,taggedSentence=None)
        
        o = Opinion(id = tweet[ID],
                    sentence = unicode(tweet[TEXT]),
                    target = unicode(tweet[TARGET]),
                    mention = unicode(tweet[MENTION]),
                    polarity = int(tweet[SENTIMENT_POLARITY]))
        
        listOfTweets.append(o)
         
    rulesClassifier = getRulesClassifier()
    naiveClassifier = getNaiveClassifier()
    
    featuresFile = csv.writer(open(destinyFile,"w"),delimiter='|') 
    
    for t in listOfTweets:
        
        featureSet = rulesClassifier.generateFeatureSet(t)
        featureSet.append(naiveClassifier.inferPolarity(t,False).polarity)
        
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


if __name__ == '__main__':
    
    print "GO"
    
    generateFeatures(True,GOLD_STANDARD,"tweets_gold.csv")
    generateFeatures(False,TWEETS,"tweets_corpus.csv")
    
    print "Done!"