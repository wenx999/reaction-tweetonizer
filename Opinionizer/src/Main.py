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
import codecs
import urllib
import simplejson

HTTP_PRXOXY = 'http://proxy.di.fc.ul.pt:3128'

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

def getNamesFromVoxx():
    
    voxxWhoIs = u'http://services.sapo.pt/InformationRetrieval/Verbetes/WhoIs?name={0}' 
    voxxPersonalitiesList = u'http://services.sapo.pt/InformationRetrieval/Verbetes/GetPersonalities?format=json' 
    
    persons = {}
    
    url = urllib.urlopen(voxxPersonalitiesList,proxies={'http': HTTP_PRXOXY})    
    data = unicode(url.read().decode("utf-8"))    
    url.close()

    voxxPersonalities = simplejson.loads(data)["listPersonalities"]            

    for voxxPersonName in voxxPersonalities.iterkeys():
        
        persons[voxxPersonName] = ''
        uniName = urllib.quote(voxxPersonName.encode("utf-8"))
        url = urllib.urlopen(voxxWhoIs.format(uniName),proxies={'http':HTTP_PRXOXY})        
        data = url.read()    
        url.close()

        voxxMoreNames = simplejson.loads(data)["verbetes"]        
        
        officialName = voxxMoreNames["officialName"]         
        persons[officialName] = ''
        
        for name in voxxMoreNames["alternativeNames"]:
            
            persons[name] = ''        
        
        for name in voxxMoreNames["jobs"].iterkeys():
            
            persons[name] = ''
        
    fx = codecs.open("../Results/voxxNames.txt","w","utf-8")
    
    for person in persons.iterkeys():
        
        if len(person.split(' ')) > 1:
            fx.write(person.encode("UTF-8")+"\n")
    
    fx.close()        


if __name__ == "__main__":
    
    print "Go"
    
    getNamesFromVoxx()
    
    print "Done"