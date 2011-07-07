'''
Created on Jul 7, 2011

@author: samir
'''

import csv
import numpy as np

class TwitometroCorpus():
    
    CORPUS_FILENAME = "/home/samir/workspace/Opinionizer/src/tweets_corpus.csv"
    GOLD_STANDARD_FILENAME = "/home/samir/workspace/Opinionizer/src/tweets_gold.csv"
    
    def __init__(self):
        
        self.trainingSet = None
        self.trainingSetLabels = None
        self.testSet = None
        
        self.trainingSet,self.trainingSetLabels = self.readGoldenStandard()
        self.testSet = self.readCorpus() 
       
       
    def readCorpus(self):
       
        corpus = csv.reader(open(TwitometroCorpus.CORPUS_FILENAME,"r"),delimiter='|')
        
        featureMatrix = []
        
        for tweet in corpus:
            
            featureSet = []
            
            for feature in tweet:
                featureSet.append(int(feature))
            
            featureMatrix.append(featureSet)

        return np.vstack(featureMatrix)
         
    def readGoldenStandard(self):
       
        corpus = csv.reader(open(TwitometroCorpus.GOLD_STANDARD_FILENAME,"r"),delimiter='|')        
        
        featureMatrix = []
        labelValues = []
        
        for tweet in corpus:
            
            featureSet = []
            
            for feature in tweet[0:-1]:
                featureSet.append(int(feature))
            
            featureMatrix.append(featureSet)
            labelValues.append([tweet[-1]])

        return np.vstack(featureMatrix),np.vstack(labelValues)    
        
if __name__ == '__main__':
    
    print "GO"
    
    c = TwitometroCorpus()
    
    print c.testSet
    print c.trainingSet
    #print c.trainingSetLabels
        
    print "Done!"        