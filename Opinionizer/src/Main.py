# -*- coding: UTF-8 -*-
'''
Created on Apr 11, 2011

@author: samir
'''

import Persons
import Evaluator
import SentiTokens
import SentiCorpus
import Opinionizers

def benchmark():    
     
    goldStandard = SentiCorpus.read("../Data/sentiCorpusGoldStandard.xml")
    candidate = SentiCorpus.read("../Data/sentiCorpusComments.xml")    
    politicians = Persons.loadPoliticians("../Resources/politicians.txt")
    #adjectives = SentiTokens.loadSentiTokens("../Resources/sentiTokens.txt")
    adjectives = SentiTokens.loadSentiTokens("../Resources/SentiLex-Npred-flex.txt")
    
    processor = Opinionizers.Naive(politicians,adjectives)
    results = {}
    
    for opinion in candidate.itervalues():
        
        res = processor.classify(opinion)
        
        if res != None:
            results[opinion.id] = res
        
    evaluator = Evaluator.Evaluator(goldStandard,results)
    evaluator.writeReport("../Results/sentiCorpusBenchmark3.xml")

if __name__ == "__main__":
    
    print "Go"
    
    benchmark()
    
    print "Done"