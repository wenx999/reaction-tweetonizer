# -*- coding: UTF-8 -*-
'''
Created on Apr 12, 2011

@author: samir
'''

import re
from Opinion import Opinion
import Utils 
import Persons
import SentiTokens

class Naive:
    
    persons = None 
    sentiTokens = None
    targetsRegex = ""
    
    def __init__(self,persons,sentiTokens):
    
        self.persons = persons        
        self.sentiTokens = sentiTokens    
        
        for person in self.persons:            
            
            for name in person.names:
                    
                    self.targetsRegex += ".?" +name + ".?|"                   
            
            for name in person.nicknames:
                    
                    self.targetsRegex += ".?" +name + ".?|"
                    
            for name in person.ergos:
                    
                    self.targetsRegex += ".?" +name + ".?|"

        self.targetsRegex = self.targetsRegex.strip('|')
    
    def inferTarget(self,opinion):
        
        """ 
            Tries to identify mentions of the targets in a message
            Params: opinion -> Opinion object
            Returns: tuple(inferred target, algorithm metadata)
        """
        
        info = u"Targets: "
        specialChars = u' “”\"@)(!#;&:\\@/-_,?.«»\' ' 
        sentence = opinion.sentence.lower()
        
        #Find matches
        matches = re.findall(self.targetsRegex,sentence)
                 
        if matches != None and len(matches) > 0:
       
            targets = []
            
            for match in matches:
                
                mention = match.rstrip(specialChars).lstrip(specialChars)
                target = self.replaceNameWithTarget(mention)
                
                if target != None:
                
                    info += mention + ","
                    targets.append((target,mention))
                    
            if len(targets) > 0:
                
                results = []
                info = info.strip(',')
            
                for target in targets:
                    
                    results.append(opinion.clone(target=target[0],mention=target[1],metadata=info))
                    
                return results
            else:
                return None
                     
                
    def replaceNameWithTarget(self,name):       
                
        for person in self.persons:
            
            if person.isMatch(name):
                
                return person.id
        
        return None

    def inferPolarity(self,opinion):        
        
        """ 
            Tries to identify the polarity of a sentence
            Params: opinion -> Opinion object
            Returns: tuple(inferred polarity, algorithm metadata)
        """
        
        info = opinion.metadata + "; " + u'sentiTokens:'
        
        tokens = opinion.sentence.lower().split(' ')
        score = 0
        
        for token in tokens:
            
            for adj in self.sentiTokens:
            
                if adj.isMatch(token): 
                   
                    score += int(adj.polarity)
                    
                    info += token + "(" + adj.polarity + ") "
        
        info += '; score:' + unicode(score) + ";"        
        
        polarity = None
        
        if score > 0:
            polarity = 1
        
        elif score < 0:
            polarity = -1
        else:
            polarity = 0
            
        return opinion.clone(polarity=polarity,metadata=info)                
    
    def classify(self,opinion):
        
        """
            Encapsulates the classification of a message:
            1. Infer target
            2. If target is identified infer polarity
            
            Params: opinion -> Opinion object
            Returns: A new Opinion object with target and polarity assigned. 
                     The metadata field is filled with the results of the algorithms
        """
        
        resTarget = self.inferTarget(opinion)
        
        if resTarget != None:
            
            info = u""
            info += resTarget[1]
            
            resPolarity = self.inferPolarity(opinion)
            
            info += resPolarity[1]
                        
            return Opinion(opinion.id,
                          opinion.sentence, 
                          resTarget[0], 
                          opinion.mention, 
                          resPolarity[0], 
                          opinion.irony,
                          info,
                          opinion.date)
        else:
            return None

class Rules:
    
    modifiers = ['muito', 'muitíssimo', 'pouco', 'pouquíssimo', 'bastante',
                 'completamente', 'imensamente', 'estupidamente', 'demasiado', 
                 'profundamente', 'perfeitamente', 'relativamente', 'simplesmente', 
                 'verdadeiramente', 'inteiramente', 'realmente', 
                 'sempre', 'mais', 'bem', 'altamente', 'extremamente', 'mesmo', 
                 'particularmente', 'igualmente', 'especialmente', 'quase', 'tão',
                 'absolutamente', 'potencialmente', 'aparentemente', 'exactamente', 'nada'
                 ]

    copulative_verbs = ['é', 'foi', 'era', 'será',
                        'está', 'esteve', 'estava', 'estará',
                        'continua', 'continuou', 'continuava', 'continuará',
                        'permanece', 'permaneceu', 'permanecia', 'permanecerá',
                        'fica', 'ficou', 'ficava', 'ficará',
                        'anda', 'andou', 'andava', 'andará',
                        'encontra-se', 'encontrou-se', 'encontrava-se', 'encontrar-se-á',
                        'sente-se', 'sentiu-se', 'sentia-se', 'sentir-se-á',
                        'mostra-se', 'mostrou-se', 'mostrava-se', 'mostrar-se-á',
                        'revela-se', 'revelou-se', 'revelava-se', 'revelar-se-á',
                        'torna-se', 'tornou-se', 'tornava-se', 'tornar-se-á',
                        'vive', 'viveu', 'vivia', 'viverá'
                       ]
            
    ser = ['é', 'foi', 'era', 'será']

    human_referents = ['gajo', 'gaja', 
                      'mulher', 'homem', 
                       'fulano','fulana',
                       'tipa',
                       'indivíduo','indivídua', 
                       'rapaz', 'rapariga',
                       'pessoa', 'jovem'
                      ]
    
    indirect_human_referents = ['ele', 'ela', 'você']
    
    persons = None 
    sentiTokens = None
    
    def __init__(self,persons,sentiTokens):
    
        self.persons = self.buildPersonsDict(persons)        
        self.sentiTokens = sentiTokens
    
    def buildPersonsDict(self,personsList):
        
        personsDict= {}
        
        for person in personsList:
            
            for mention in person.mentions():
                
                personsDict[mention] = person
            
        return personsDict
    
    def inferPolarity(self,opinion):
        
        for rule in self.negativeRules:
            
            result = rule(self,opinion)
            
            found = result[0]
            
            if found: 
                
                return opinion.clone(polarity=-1,metadata=result[1])
            
        return opinion.clone(polarity=0)
        
    def hasNickName(self,opinion):
        
        info = "Nickname: "
        
        mention = opinion.mention.lower()
        person = self.persons[mention]
        
        if person != None:
            
            if person.isNickname(mention):
                
                info += mention
                return (True,info)
            else:
                return (False,None)
        else:
            return (False,None)
    
    def hasLol(self,opinion):
        
        info = "LOL: "
        
        regex = r'(l+o+l+(o+)?)+'
        sentence = opinion.sentence.lower()
        
        match = re.findall(regex,sentence)
    
        if match != None and len(match) > 0:
            
            for m in match:
                
                for v in m:
                
                    info += v + ","
            
            info = info.strip(',')
            
            return (True,info)
        else:
            return (False,None)
   
    def hasSmiley2(self,opinion): 
        
        info = "Smiley: "
        
        regex = r'[:;8xX]{1}-?[DPpSs)(\\/]+'
        sentence = opinion.sentence.lower()
        
        match = re.search(regex,sentence)
    
        if match != None: 
                    
            #info += match
            print "match >",match.group()
            info = info.strip(',')
            
            return (True,info)            
        else:
            return (False,None)
   
   
    def hasSmiley(self,opinion): 
        
        info = "Smiley: "
        
        regex = r'[:;8xX]{1}-?[DPpSs)(\\/]+'
        sentence = opinion.sentence.lower()
        
        match = re.findall(regex,sentence)
    
        if match != None and len(match) > 0:            
           
            for m in match:
                
                for v in m:
                    
                        info += v + ","
            
            info = info.strip(',')
            
            return (True,info)            
        else:
            return (False,None)
   
    def hasHehe(self,opinion): 
        
        info = "Haha: "
        
        regex = r'([h|e|a|i]+ *)+'
        sentence = opinion.sentence.lower()
        
        match = re.findall(regex,sentence)
    
        if match != None and len(match) > 0:
                      
            for m in match:
                
                for v in m:
                
                    info += v + ","
            
            info = info.strip(',')
            
            return (True,info)    
            
        else:
            return (False,None)
        
    def hasHeavyPunctuation(self,opinion): 
        
        info = "Heavy Punctuation: "
        
        regex = r'.*([!?]{2,})+'
        sentence = opinion.sentence.lower()
        
        match = re.findall(regex,sentence)
    
        if match != None and len(match) > 0:
            
            for m in match:
                
                for v in m:
                
                    info += v + ","
            
            info = info.strip(',')
            
            return (True,info)        
            
        else:
            return (False,None)
        
    def hasInterjection(self,opinion): 
        
        info = "Interjection: "
        
        #Está a falhar para o está|tá (acentuados)
        regex = r'(m+e+r+d+a+|f+o+d+a+-*s+e*|(es)?t[áa] fdd|que no+jo+|credo|lindo|(oh)?meu deus)!*'
               
        sentence = opinion.sentence.lower()
        
        match = re.findall(regex,sentence)
    
        if match != None and len(match) > 0:            
            
            for m in match:
                
                for v in m:
                
                    info += v + ","
            
            info = info.strip(',')
            
            return (True,info) 
            
        else:
            return (False,None)
    
    def hasInterjectionWithTarget(self): 
                
        #target = opinion.mention.lower()
        #sentence = opinion.sentence.lower()
                
        #regexTargetLeft = r'{0} nunca mais|{0} jamais'.format(target)
        #regexTargetRight = r'oh {0}|obrigado {0}|senhor {0}|anti-{0}'.format(target)
        
        regexTargetLeft = r'{0} nunca mais|{0} jamais'.format("silvio")
        regexTargetRight = r'oh {0}|obrigado {0}|senhor {0}|anti-{0}'.format("silvio")
        
        print "La sentença ", sentence
        match = re.findall(regexTargetLeft,sentence)
    
        if match != None and len(match) > 0:
                
            return True
        else:
            match = re.findall(regexTargetRight,sentence)
            
            if match != None and len(match) > 0:
                    
                return True
            else:
                return False
            
    negativeRules = [hasNickName,hasLol,hasHehe,hasHeavyPunctuation,hasInterjection]
    
if __name__ == '__main__':  
    
    politiciansFile = "../Resources/politicians.txt"
    sentiTokensFile = "../Resources/sentiTokens.txt"
    
    politicians = Persons.loadPoliticians(politiciansFile)
    sentiTokens = SentiTokens.loadSentiTokens(sentiTokensFile)
    
    ruler = Rules(politicians,sentiTokens)
    
    sentenceNoMatch = u"O sócrates e passos coelho são bff"
    
    """
    interjecTargetSentences = [sentenceNoMatch,
                               u"O sócrates nunca mais!",
                               u"O sócrates nunca!",
                               u"O sócrates jamais!",
                               u"Oh sócrates...",
                               u"Obrigado sócrates ...",
                               u"senhor sócrates ...",
                               u"anti-sócrates ..."
                               ]
    
    for sentence in interjecTargetSentences:
    
        #o = Opinion(1,sentence,u"socrates",u"sócrates",0,None,u"Manual",u"Manual",None)
        
        v = ruler.hasInterjectionWithTarget()
        
        #if not v:
        #    print sentence, "->", v 
        #    print "------------------"
    
    """
    """
    interjectionSentences = [sentenceNoMatch,
                               u"O sócrates e passos coelho são bff!",
                               u"Foda-se o sócrates e passos coelho são bff!",
                               u"Fooooda-se o sócrates e passos coelho são bff!",
                               u"Foooodaaaa-se o sócrates e passos coelho são bff!",
                               u"Foooodaaaase o sócrates e passos coelho são bff!",
                               u"Foooodaaaasssse o sócrates e passos coelho são bff!",
                               u"Foooodaaaa-seee o sócrates e passos coelho são bff!",
                               u"merda o sócrates e passos coelho são bff!",
                               u"meeeerda o sócrates e passos coelho são bff!",
                               u"meeeerdaaa o sócrates e passos coelho são bff!",
                               u"meeeerdaaa!! o sócrates e passos coelho são bff!",
                               u"meeeerddaaa!! o sócrates e passos coelho são bff!",
                               u"está fdd o sócrates e passos coelho são bff!",
                               u"esta fdd o sócrates e passos coelho são bff!",
                               u"ta fdd o sócrates e passos coelho são bff!",
                               u"tá fdd o sócrates e passos coelho são bff!",
                               u"que nojo o sócrates e passos coelho são bff!",
                               u"que nojo! o sócrates e passos coelho são bff!",
                               u"que noooojo o sócrates e passos coelho são bff!",
                               u"que noojoooo o sócrates e passos coelho são bff!",
                               u"que noojoooo!! o sócrates e passos coelho são bff!",
                               u"credo o sócrates e passos coelho são bff!",
                               u"lindo o sócrates e passos coelho são bff!",
                               u"lindo! O sócrates e passos coelho são bff!",
                               u"meu deus O sócrates e passos coelho são bff!",
                               u"meu deus! O sócrates e passos coelho são bff!",
                               u"oh meu deus O sócrates e passos coelho são bff!",
                               u"oh meu deus! O sócrates e passos coelho são bff!",                           
                           ]                              
    
    for sentence in interjectionSentences:
    
        o = Opinion(1,sentence,u"socrates",u"sócrates",0,None,u"Manual",u"Manual",None)
        
        v = ruler.hasInterjection(o)
        
        if not v:
            print sentence, "->", v 
            print "------------------"
        
    """
    
    """
    heavyPunctSentences = [sentenceNoMatch,
                           u"O sócrates e passos coelho são bff!",
                           u"O sócrates e passos coelho são bff?",                           
                           u"O sócrates e passos coelho são bff!!",
                           u"O sócrates e passos coelho são bff??",                           
                           u"O sócrates e passos coelho são bff!!!",
                           u"O sócrates e passos coelho são bff???",
                           u"O sócrates e passos coelho são bff!?!",
                           u"O sócrates e passos coelho são bff!?!!?",
                           u"O sócrates e passos coelho são bff?!!!?",
                           u"O sócrates e passos coelho são bff!??!"                           
                           ]                              
    
    for sentence in heavyPunctSentences:
    
        o = Opinion(1,sentence,u"socrates",u"socras",0,None,u"Manual",u"Manual",None)
        
        v = ruler.hasHeavyPunctuation(o)
        
        print sentence, "->", v 
        print "------------------"
    """
    
    """
    
    heheSentences = [sentenceNoMatch,
                     u"O sócrates e passos coelho são bff hehehehe",
                     u"O sócrates e passos coelho são bff ehehehehe",
                     u"O sócrates e passos coelho são bff he he he he",
                     u"O sócrates e passos coelho são bff eh eh eh eh",
                     u"O sócrates e passos coelho são bff ehe ehe ehe ehe",
                     u"O sócrates e passos coelho são bff heeeheeeheehe",
                     u"O sócrates e passos coelho são bff eheeeheeeheehe",
                     u"O sócrates e passos coelho são bff heee heee he he",                     
                     u"O sócrates e passos coelho são bff hahahaha",
                     u"O sócrates e passos coelho são bff ahahahaha",
                     u"O sócrates e passos coelho são bff ha ha ha ha",
                     u"O sócrates e passos coelho são bff ah ah ah ah",
                     u"O sócrates e passos coelho são bff ahahahah",
                     u"O sócrates e passos coelho são bff aha aha aha aha",
                     u"O sócrates e passos coelho são bff haaahaaahaaha",
                     u"O sócrates e passos coelho são bff ahaaahaaahaaha",
                     u"O sócrates e passos coelho são bff haaa haaa ha ha",                     
                     u"O sócrates e passos coelho são bff hihihihi",
                     u"O sócrates e passos coelho são bff ihihihihi",
                     u"O sócrates e passos coelho são bff hi hi hi hi",
                     u"O sócrates e passos coelho são bff ihi ihi ihi ihi",
                     u"O sócrates e passos coelho são bff hiiihiiihiihi",
                     u"O sócrates e passos coelho são bff ihiiihiiihiihi",
                     u"O sócrates e passos coelho são bff hiii hiii hi hi",
                     ]
    
    for sentence in heheSentences:
    
        o = Opinion(1,sentence,u"socrates",u"socras",0,None,u"Manual",u"Manual",None)
        
        v = ruler.hasHehe(o)
        
        print sentence, "->", v 
        print "------------------"
    """
    
    """
    lolSentences = [sentenceNoMatch,
                    u"O sócrates e passos coelho são bff lol",
                    u"O sócrates e passos coelho são bff lololoooool",
                    u"O sócrates e passos coelho são bff lolo"
                   ] 
    
    for sentence in lolSentences:
    
        o = Opinion(1,sentence,u"socrates",u"socras",0,None,u"Manual",u"Manual",None)
        
        v = ruler.hasLol(o)
        
        print sentence, "->", v 
        print "------------------"
    
    """    
    
    smileySentences = [sentenceNoMatch,
                       u"O sócrates e passos coelho são :)",
                       u"O sócrates e passos coelho são :))))",
                       u"O sócrates e passos coelho são :(",
                       u"O sócrates e passos coelho são :((",
                       u"O sócrates e passos coelho são :D",
                       u"O sócrates e passos coelho são :DDD",                 
                       u"O sócrates e passos coelho são :S",
                       u"O sócrates e passos coelho são :SSS",
                       u"O sócrates e passos coelho são :ss",
                       u"O sócrates e passos coelho são :s",
                       u"O sócrates e passos coelho são :P",
                       u"O sócrates e passos coelho são :PP",
                       u"O sócrates e passos coelho são :p",
                       u"O sócrates e passos coelho são :pp",
                       u"O sócrates e passos coelho são :\\",
                       u"O sócrates e passos coelho são :\\\\",
                       u"O sócrates e passos coelho são :/",
                       u"O sócrates e passos coelho são ://///",                                         
                       u"O sócrates e passos coelho são :-D",
                       u"O sócrates e passos coelho são :-DDD",
                       u"O sócrates e passos coelho são :-S",
                       u"O sócrates e passos coelho são :-SSS",
                       u"O sócrates e passos coelho são :-ss",
                       u"O sócrates e passos coelho são :-s",
                       u"O sócrates e passos coelho são :-\\",
                       u"O sócrates e passos coelho são :-\\\\", 
                       u"O sócrates e passos coelho são :-)",
                       u"O sócrates e passos coelho são :-))))",
                       u"O sócrates e passos coelho são :-(",
                       u"O sócrates e passos coelho são :-((",
                       u"O sócrates e passos coelho são :-/",
                       u"O sócrates e passos coelho são :-/////",    
                       u"O sócrates e passos coelho são :-P",
                       u"O sócrates e passos coelho são :-PP",
                       u"O sócrates e passos coelho são :-p",
                       u"O sócrates e passos coelho são :-pp", 
                       u"O sócrates e passos coelho são ;P",
                       u"O sócrates e passos coelho são ;PP",
                       u"O sócrates e passos coelho são ;p",
                       u"O sócrates e passos coelho são ;pp",
                       u"O sócrates e passos coelho são ;)",
                       u"O sócrates e passos coelho são ;))))",
                       u"O sócrates e passos coelho são ;(",
                       u"O sócrates e passos coelho são ;((",                       
                       u"O sócrates e passos coelho são ;/",
                       u"O sócrates e passos coelho são ;/////"                                        
                       u"O sócrates e passos coelho são ;D",
                       u"O sócrates e passos coelho são ;DDD",
                       u"O sócrates e passos coelho são ;S",
                       u"O sócrates e passos coelho são ;SSS",
                       u"O sócrates e passos coelho são ;ss",
                       u"O sócrates e passos coelho são ;s",
                       u"O sócrates e passos coelho são ;\\",
                       u"O sócrates e passos coelho são ;\\\\",
                       u"O sócrates e passos coelho são 8P",
                       u"O sócrates e passos coelho são 8PP",
                       u"O sócrates e passos coelho são 8p",
                       u"O sócrates e passos coelho são 8pp",
                       u"O sócrates e passos coelho são 8)",
                       u"O sócrates e passos coelho são 8))))",
                       u"O sócrates e passos coelho são 8D",
                       u"O sócrates e passos coelho são 8/",
                       u"O sócrates e passos coelho são 8(",
                       u"O sócrates e passos coelho são 8((",
                       u"O sócrates e passos coelho são 8DDD",     
                       u"O sócrates e passos coelho são 8S",
                       u"O sócrates e passos coelho são 8SSS",
                       u"O sócrates e passos coelho são 8ss",
                       u"O sócrates e passos coelho são 8s",
                       u"O sócrates e passos coelho são 8\\",
                       u"O sócrates e passos coelho são 8\\\\",
                       u"O sócrates e passos coelho são 8/////",
                       u"O sócrates e passos coelho são XD",
                       u"O sócrates e passos coelho são X-D"
                       u"O sócrates e passos coelho são xD",
                       u"O sócrates e passos coelho são x-D",
                      ]        
    
    
    for s in smileySentences:
    
        o = Opinion(1,s,u"socrates",u"socras",0,None,u"Manual",u"Manual",None)
        
        v = ruler.hasSmiley2(o)
        
        
        print s, "->", v 
        print "------------------"
    