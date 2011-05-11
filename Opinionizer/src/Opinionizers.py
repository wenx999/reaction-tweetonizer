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
    targetsRegex = u""
    sentiTokensRegex = u""
    
    def __init__(self,persons,sentiTokens):
    
        self.persons = persons        
        self.sentiTokens = sentiTokens    
        
        # Build a regex for identifying targets
        for person in self.persons:            
            
            for name in person.names:
                    
                    self.targetsRegex += ".?" +name + ".?|"                   
            
            for name in person.nicknames:
                    
                    self.targetsRegex += ".?" +name + ".?|"
                    
            for name in person.ergos:
                    
                    self.targetsRegex += ".?" +name + ".?|"

        self.targetsRegex = self.targetsRegex.strip('|')
                 
        # Build a regex for identifying sentiment tokens
        for sentiToken in sentiTokens:
            
            for token in sentiToken.getTokens():
                
                self.sentiTokensRegex += ".?" + token + ".?|"  
        
        self.sentiTokensRegex.strip('|')
    
    def isFalsePositive(self,mention,sentence):
        
        left_context = {u'portas': [u'as',u'nas',u'às',u'miguel',u'abriu',u'abriram',u'abre',u'abrem',u'numeral',u'mais']}
        right_context = {u'portas': [u'de',u'do',u'da',u'das',u'dos']}
        
        tokens = re.findall(u'\w+',sentence,re.U)
        nMention = unicode(mention)
        
        try:
            if nMention in left_context:
        
                badTokens = left_context[nMention]
                
                if tokens[tokens.index(nMention)-1] in badTokens:
                    print "Discarded (left) " + nMention + " in " + "**" + sentence.replace('\n',' ') + "**"
                    return True
            
            if mention in right_context:
                
                badTokens = right_context[nMention]             
                
                if tokens[tokens.index(nMention)+1] in badTokens:
                    print "Discarded (right) " + nMention + " in " + "**" +  sentence.replace('\n',' ') + "**"
                    return True
                
            return False
        except:            
            return False
            
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
       
            targets = {}
            
            for match in matches:
                
                mention = match.rstrip(specialChars).lstrip(specialChars)
                
                target = self.replaceNameWithTarget(mention)
                
                if target != None and not self.isFalsePositive(mention, sentence):                    
                
                    info += mention + ","
                    targets[target] = mention
                    
            if len(targets) > 0:
                
                results = []
                info = info.strip(',')
            
                for target,mention in targets.items():
                    
                    results.append(opinion.clone(target=target,mention=mention,metadata=info))
                    
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
        specialChars = u' “”\"@)(!#;&:\\@/-_,?.«»\' ' 
        sentence = opinion.sentence.lower()
        score = 0
        
        #Find matches
        matches = re.findall(self.sentiTokensRegex ,sentence)
                 
        if matches != None and len(matches) > 0:     
            
            for match in matches:
                
                token = match.rstrip(specialChars).lstrip(specialChars)
                
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
    
    QUANT = [u'muito', u'muitíssimo', u'pouco', u'pouquíssimo', u'bastante',
             u'completamente', u'imensamente', u'estupidamente', u'demasiado', 
             u'profundamente', u'perfeitamente', u'relativamente', u'simplesmente', 
             u'verdadeiramente', u'inteiramente', u'realmente', 
             u'sempre', u'mais', u'bem', u'altamente', u'extremamente', u'mesmo', 
             u'particularmente', u'igualmente', u'especialmente', u'quase', u'tão',
             u'absolutamente', u'potencialmente', u'aparentemente', u'exactamente', u'nada'
             ]

    VCOP = [u'é', u'foi', u'era', u'será',
            u'está', u'esteve', u'estava', u'estará',
            u'continua', u'continuou', u'continuava', u'continuará',
            u'permanece', u'permaneceu', u'permanecia', u'permanecerá',
            u'fica', u'ficou', u'ficava', u'ficará',
            u'anda', u'andou', u'andava', u'andará',
            u'encontra-se', u'encontrou-se', u'encontrava-se', u'encontrar-se-á',
            u'sente-se', u'sentiu-se', u'sentia-se', u'sentir-se-á',
            u'mostra-se', u'mostrou-se', u'mostrava-se', u'mostrar-se-á',
            u'revela-se', u'revelou-se',u'revelava-se', u'revelar-se-á',
            u'torna-se', u'tornou-se', u'tornava-se', u'tornar-se-á',
            u'vive', u'viveu', u'vivia', u'viverá'
           ]   
    
    NCLAS = [u'gajo', u'homem', u'senhor', u'fulano', u'tipo',
            u'indivíduo', u'rapaz', u'pessoa', u'figura', u'personagem', u'criatura',
            u'político', u'candidato', u'líder', u'adversário' 
            ]
    
    VSUP = [u'aparenta', u'aparentou', u'aparentava', u'aparentará',
            u'apresenta',u'apresentou', u'apresentava', u'apresentará',
            u'continua', u'continuou', u'continuava', u'continuará',
            u'demonstra', u'demonstrou', u'demonstrava', u'demonstrará',
            u'faz', u'fez', u'fazia', u'fará',
            u'mostra', u'mostrou', u'mostrava', u'mostrará',
            u'revela', u'revelou', u'revelava', u'revelará',
            u'sente', u'sentiu', u'sentia', u'sentirá',
            u'tem', u'teve', u'tinha', u'terá',
            u'transparece', u'transpareceu', u'transparecia', u'transparecerá',
            u'anda sob', u'andou sob', u'andava sob', u'andará sob', 
            u'anda com', u'andou com', u'andava com', u'andará com'
            u'entra em', u'entrou em', u'entrava em', u'entrará em',
            u'está com', u'esteve com', u'estava com',u'estará com',
            u'está em', 'uesteve em', u'estava em', u'estará em',
            u'está sob', u'esteve sob', u'estava sob', u'estará sob'
            u'fica com', u'ficou com', u'ficava com', u'ficará com'
            ]
    
    persons = None 
    sentiTokens = None
    quantRegex = u''
    vcopRegex = u''
    nclasRegex = u''
    vsupRegex = u''
    negSentiRegex = u''
    neutSentiRegex = u''
    posSentiRegex = u''
    
    def __init__(self,persons,sentiTokens):
    
        self.persons = self.buildPersonsDict(persons)        
        self.sentiTokens = sentiTokens
        self.quantRegex = self.getRegexFromList(self.QUANT)
        self.vcopRegex = self.getRegexFromList(self.VCOP)
        self.nclasRegex = self.getRegexFromList(self.NCLAS)
        self.vsupRegex = self.getRegexFromList(self.VSUP)
        self.populateSentiRegexes(sentiTokens)
    
    def getRegexFromList(self,list):
        
        regex = u''
        
        for token in list:
            
            regex += token+"|"
        
        return regex.strip('|')
        
    
    def buildPersonsDict(self,personsList):
        
        personsDict= {}
        
        for person in personsList:
            
            for mention in person.mentions():
                
                personsDict[mention] = person
            
        return personsDict
    
    def populateSentiRegexes(self,sentiTokens):
        
        partialRegex = u''
        positiveRegex = u''
        negativeRegex = u''
        neutralRegex = u''
        
        for sentiToken in sentiTokens:
            
            for token in sentiToken.getTokens():
            
                partialRegex += token + "|"    
            
            if sentiToken.polarity == str(1):                                
                positiveRegex += partialRegex
                
            elif sentiToken.polarity == str(0):                
                neutralRegex += partialRegex
                
            elif sentiToken.polarity == str(-1):                                  
                negativeRegex += partialRegex
                
            partialRegex = u''         
        
        self.posSentiRegex = positiveRegex.strip('|')
        self.neutSentiRegex = neutralRegex.strip('|')              
        self.negSentiRegex = negativeRegex.strip('|')
    
    def inferPolarity_old(self,opinion):
        
        for rule in self.negativeRules:
            
            result = rule(self,opinion)
            
            found = result[0]
            
            if found: 
                info = opinion.metadata + ";" + result[1]
                return opinion.clone(polarity=-1,metadata=info)
            
        return opinion.clone(polarity=0)
    
    def inferPolarity(self,opinion):
        
        for rule in self.setOfRules:
            
            result = rule(self,opinion)
            
            if result != None:
             
                info = opinion.metadata + ";" + result[1]
                return opinion.clone(polarity=result[0],metadata=info)
            
        return opinion.clone(polarity=0)
    
    def hasNickName(self,opinion):
        
        info = "Nickname: "
        
        mention = opinion.mention.lower()
        person = self.persons[mention]
        
        if person != None:
            
            if person.isNickname(mention):
                
                info += mention
                return (-1,info)
            else:
                return None
        else:
            return None
    
    def hasLol(self,opinion):
        
        info = "LOL: "
        
        regex = r'(l+o+l+(o+)?)+'
        sentence = opinion.sentence.lower()
        
        match = re.search(regex,sentence)
    
        if match != None:
            
            info += match.group()
            
            return (-1,info)
        else:
            return None
   
    def hasSmiley(self,opinion): 
        
        info = "Smiley: "
        
        regex = r'([\W ])[:;xX8]-?([\)\(psd])+'
        sentence = opinion.sentence.lower()
        
        match = re.search(regex,sentence)
    
        if match != None:
            
            info += match.group().upper()
            
            return (-1,info)            
        else:
            return None
       
    def hasHehe(self,opinion): 
        
        info = "Haha: "
        
        regex = r'(h[e|a|i]+){2,}|(h[e|a|i] ?){2,}|([a|e]h ?){2,}'
        sentence = opinion.sentence.lower()
        
        match = re.search(regex,sentence)
    
        if match != None:
            
            info += match.group()
                        
            return (-1,info)    
            
        else:
            return None
        
    def hasHeavyPunctuation(self,opinion): 
        
        info = "Heavy Punctuation: "
        
        regex = r'.?([!?]{2,})+'
        sentence = opinion.sentence.lower()
        
        match = re.search(regex,sentence)
    
        if match != None:
            
            info += match.group()
                        
            return (-1,info)        
            
        else:
            return None
        
    def hasInterjection(self,opinion): 
        
        info = "Interjection: "        
       
        regex = ur'(m+e+r+d+a+|f+o+d+a+-*s+e*|(es)?t[áa] fdd|que no+jo+|credo|lindo|(oh)?meu deus|([\W ])ui+[\W ])!*'
               
        sentence = opinion.sentence.lower()
        
        match = re.search(regex,sentence)
    
        if match != None:
            
            info += match.group()
            
            return (-1,info) 
            
        else:
            return None
    
    def hasInterjectionWithTarget(self,opinion): 
        
        info = u"Interjection with target: "        
        target = opinion.mention.lower()
        sentence = opinion.sentence.lower()
                
        regexTargetLeft = ur'{0} nunca mais|{0} jamais'.format(target)
        regexTargetRight = ur'oh {0}|obrigado {0}|senhor {0}|anti-{0}'.format(target)
    
        match = re.search(regexTargetLeft,sentence)
    
        if match != None:
            
            info += match.group()
            
            return (-1,info)
        else:
            match = re.match(regexTargetRight,sentence)           
            
            if match != None:
                
                for g in match.groups():
                    
                    info += g + ","
                
                info = info.strip(',')
                
                return (-1,info)
            else:
                return None
    
    def rule1(self,opinion):
        
        """ Ex: não é uma pessoa honesta """
        
        info = u'Regra \"não [VCOP] um|uma [NCLAS] [AJD+] ? Neg\"-> '        
        regex = ur'.?não ({0}) (um|uma) ({1}) ({2}).?'.format(self.vcopRegex,self.nclasRegex,self.posSentiRegex)
        sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return None
        
    def rule2(self,opinion):
        
        """ Ex: não é um tipo autoritário """
        
        info = u'Regra \"não [VCOP] um [NCLAS] [AJD-] ? Pos"\"-> '        
        regex = ur'.?não ({0}) (um|uma) ({1}) ({2}).?'.format(self.vcopRegex,self.nclasRegex,self.negSentiRegex)
        sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (1,info) 
            
        else:
            return None
    
    def rule3(self,opinion):
        
        """ Ex: não é um bom político """
        
        info = u'Regra \"não [VCOP] um [AJD+] [NCLAS] ?Neg\""-> '        
        regex = ur'.?não ({0}) (um|uma) ({1}) ({2}).?'.format(self.vcopRegex,self.posSentiRegex,self.nclasRegex)
        sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return None
    
    def rule4(self,opinion):
        
        """ Ex: não é um mau político """
        
        info = u'Regra \"não [VCOP] um [AJD-] [NCLAS] ?Pos\""-> '        
        regex = ur'.?não ({0}) (um|uma) ({1}) ({2}).?'.format(self.vcopRegex,self.negSentiRegex,self.nclasRegex)
        sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (1,info) 
            
        else:
            return None
    
    def rule5(self,opinion):
        
        """ Ex: não é um idiota """
        
        info = u'Regra \"não [VCOP] um [AJD-] ? Pos\""-> '        
        regex = ur'.?não ({0}) (um|uma) ({1}).?'.format(self.vcopRegex,self.negSentiRegex)
        sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (1,info) 
            
        else:
            return None
    
    def rule6(self,opinion):
        
        """ Ex: não é um embuste """
        
        info = u'Regra \"não [VCOP] um [N-] ? Pos\""-> '        
        regex = ur'.?não ({0}) (um|uma) ({1}).?'.format(self.vcopRegex,self.negSentiRegex)
        sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (1,info) 
            
        else:
            return None
    
    def rule7(self,opinion):
        
        """ Ex: não foi nada sincero """
        
        info = u'Regra \"não [VCOP] [QUANT] [Adj+] ? Neg\""-> '        
        regex = ur'.?não ({0}) ({1}) ({2}).?'.format(self.vcopRegex,self.quantRegex,self.posSentiRegex)
        
        sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return None
    
    def rule8(self,opinion):
        
        """ Ex: não é nada parvo """
        
        info = u'Regra \"não [VCOP] [QUANT] [Adj-] ? Pos\""-> '        
        regex = ur'.?não ({0}) ({1}) ({2}).?'.format(self.vcopRegex,self.quantRegex,self.negSentiRegex)
        
        sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (1,info) 
            
        else:
            return None
    
    def rule9(self,opinion):
        
        """ Ex: não foi coerente """
        
        info = u'Regra \"não [VCOP] [Adj+] ? Neg\""-> '        
        regex = ur'.?não ({0}) ({1}).?'.format(self.vcopRegex,self.posSentiRegex)
        
        sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return None
        
    def rule10(self,opinion):
        
        """ Ex: não é mentiroso """
        
        info = u'Regra \"não [VCOP] [Adj-] ? Pos\""-> '        
        regex = ur'.?não ({0}) ({1}).?'.format(self.vcopRegex,self.negSentiRegex)
        
        sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (1,info) 
            
        else:
            return None
    
    def rule11(self,opinion):
        
        """ Ex: não demonstrou um forte empenho """
        
        info = u'Regra \"não [VSUP] (um+uma) [ADJ+|0] [N+] ? Neg\""-> '        
        regex = ur'.?não ({0}) (um|uma) ({1}|{2}) ({3}).?'.format(self.vsupRegex,self.posSentiRegex,self.neutSentiRegex,self.posSentiRegex)
        
        sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return None
    
    def rule12(self,opinion):
        
        """ Ex: não mostrou falta de coragem """
        
        info = u'Regra \"não [VSUP] falta de [N+] ? Pos\""-> '        
        regex = ur'.?não ({0}) falta de ({1}).?'.format(self.vsupRegex,self.posSentiRegex)
        
        sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (1,info) 
            
        else:
            return None
    
    def rule13(self,opinion):
        
        """ Ex:  é um político desonesto """
        
        info = u'Regra \"[VCOP] um [NCLAS] [AJD-] ? Neg\""-> '        
        regex = ur'.?({0}) um ({1}) ({2}).?'.format(self.vcopRegex,self.nclasRegex,self.negSentiRegex)
        
        sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return None
    
    def rule14(self,opinion):
        
        """ Ex:  é um tipo honesto """
        
        info = u'Regra \"[VCOP] um [NCLAS] [AJD+] ? Pos\""-> '        
        regex = ur'.?({0}) um ({1}) ({2}).?'.format(self.vcopRegex,self.nclasRegex,self.posSentiRegex)
        
        sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (1,info) 
            
        else:
            return None
    
    def rule15(self,opinion):
        
        """ Ex:  é um mau político """
        
        info = u'Regra \"[VCOP] um [AJD-] [NCLAS] ?Neg\""-> '        
        regex = ur'.?({0}) um ({1}) ({2}).?'.format(self.vcopRegex,self.negSentiRegex,self.nclasRegex)
        
        sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return None
    
    def rule16(self,opinion):
        
        """ Ex:  é um bom político """
        
        info = u'Regra \"[VCOP] um [AJD+] [NCLAS] ?Pos\""-> '        
        regex = ur'.?({0}) um ({1}) ({2}).?'.format(self.vcopRegex,self.posSentiRegex,self.nclasRegex)
        
        sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (1,info) 
            
        else:
            return None
    
    def rule17(self,opinion):
        
        """ Ex: é um perfeito idiota """
        
        info = u'Regra \"[VCOP] um [AJD+] [AJD-] ? Neg\""-> '        
        regex = ur'.?({0}) um ({1}) ({2}).?'.format(self.vcopRegex,self.posSentiRegex,self.negSentiRegex)
        
        sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return None
    
    def rule18(self,opinion):
        
        """ Ex: é um verdadeiro desastre """
        
        info = u'Regra \"[VCOP] um [AJD+] [N-] ? Neg\""-> '        
        regex = ur'.?({0}) um ({1}) ({2}).?'.format(self.vcopRegex,self.posSentiRegex,self.negSentiRegex)
        
        sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return None
    
    def rule19(self,opinion):
        
        """ Ex: é um mau perdedor """
        
        info = u'Regra \"[VCOP] um [AJD-] [AJD-] ? Neg\""-> '        
        regex = ur'.?({0}) um ({1}) ({2}).?'.format(self.vcopRegex,self.negSentiRegex,self.negSentiRegex)
        
        sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return None
    
    def rule20(self,opinion):
        
        """ Ex: é um idiota """
        
        info = u'Regra \"[VCOP] um [AJD-] ? Neg\""-> '        
        regex = ur'.?({0}) um ({1}).?'.format(self.vcopRegex,self.negSentiRegex)
        
        sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return None
    
    def rule21(self,opinion):
        
        """ Ex: é um embuste """
        
        info = u'Regra \"[VCOP] um [N-] ? Neg\""-> '        
        regex = ur'.?({0}) um ({1}).?'.format(self.vcopRegex,self.negSentiRegex)
        
        sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return None
    
    def rule22(self,opinion):
        
        """ Ex: é muito parvo """
        
        info = u'Regra \"[VCOP] [QUANT] [Adj-] ? Pos\""-> '        
        regex = ur'.?({0}) ({1}) ({2}).?'.format(self.vcopRegex,self.quantRegex,self.negSentiRegex)
        
        sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return None
    
    def rule23(self,opinion):
        
        """ Ex: foi extremamente sincero """
        
        info = u'Regra \"[VCOP] [QUANT] [Adj+] ? Pos\""-> '        
        regex = ur'.?({0}) ({1}) ({2}).?'.format(self.vcopRegex,self.quantRegex,self.posSentiRegex)
        
        sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (1,info) 
            
        else:
            return None    
    
    def rule24(self,opinion):
        
        """ Ex: é mentiroso """
        
        info = u'Regra \"[VCOP] [Adj-] ? Neg\""-> '        
        regex = ur'.?({0}) ({1}).?'.format(self.vcopRegex,self.negSentiRegex)
        
        sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return None
    
    def rule25(self,opinion):
        
        """ Ex: foi coerente """
        
        info = u'Regra \"[VCOP] [Adj+] ? Pos\""-> '        
        regex = ur'.?({0}) ({1}).?'.format(self.vcopRegex,self.posSentiRegex)
        
        sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (1,info) 
            
        else:
            return None        
    
    def rule26(self,opinion):
        
        """ Ex: o idiota do Sócrates """
        
        target = opinion.mention.lower()
        
        info = u'Regra \"o [ADJ] do TARGET ? Neg\""-> '        
        regex = ur'.?o ({0}) do {1}.?'.format(self.negSentiRegex,target)
        
        sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return None  
    
    def rule27(self,opinion):
        
        """ Ex: revelou uma enorme falta de respeito """
        
        info = u'Regra \"[VSUP] (um+uma) [ADJ+|0] falta de [N+] ? Neg\""-> '        
        regex = ur'.?({0}) (um|uma) ({1}|{2}) falta de ({3}).?'.format(self.vsupRegex,self.posSentiRegex,self.neutSentiRegex,self.posSentiRegex)
        
        sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return None
    
    def rule28(self,opinion):
        
        """ Ex: tem falta de coragem """
        
        info = u'Regra \"[VSUP] falta de [N+] ? Neg\""-> '        
        regex = ur'.?({0}) falta de ({1}).?'.format(self.vsupRegex,self.posSentiRegex)
        
        sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return None
        
    def rule29(self,opinion):
        
        """ Ex: demonstrou uma enorme arrogância """
        
        info = u'Regra \"[VSUP] (um+uma+0) [ADJ+|0] [N-] ? Neg\""-> '        
        regex = ur'.?({0}) (um|uma) ({1}|{2}) ({3}).?'.format(self.vsupRegex,self.posSentiRegex,self.neutSentiRegex,self.negSentiRegex)
        
        sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return None
    
    def rule30(self,opinion):
        
        """ Ex: demonstrou uma enorme coragem """
        
        info = u'Regra \"[VSUP] (um+uma+0) [ADJ+|0] [N-] ? Neg\""-> '        
        regex = ur'.?({0}) (um|uma) ({1}|{2}) ({3}).?'.format(self.vsupRegex,self.posSentiRegex,self.neutSentiRegex,self.posSentiRegex)
        
        sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (1,info) 
            
        else:
            return None
    
    setOfRules = [hasNickName,hasInterjectionWithTarget,hasInterjection,hasLol,hasHehe,hasHeavyPunctuation,
                  hasSmiley,rule2,rule4,rule5,rule6,rule8,rule10,rule12,rule14,rule16,rule23,rule25,rule30,
                  rule1,rule3,rule7,rule9,rule11,rule13,rule15,rule17,rule18,rule19,rule20,rule21,rule22,
                  rule24,rule26,rule27,rule28,rule29]
    
def testBasicRules():
    
    sentenceNoMatch = u"O sócrates e passos coelho são bff"
    
    """
    interjecTargetSentences = [sentenceNoMatch,
                               u"O socrates nunca mais!",
                               u"O socrates nunca!",
                               u"O socrates jamais!",
                               u"Oh socrates...",
                               u"Obrigado socrates ...",
                               u"senhor socrates ...",
                               u"anti-socrates ..."
                               u"O sócrates nunca mais!",
                               u"O sócrates nunca!",
                               u"O sócrates jamais!",
                               u"Oh sócrates...",
                               u"Obrigado sócrates ...",
                               u"senhor sócrates ...",
                               u"anti-sócrates ..."
                               ]
    
    for s in interjecTargetSentences:
    
        o = Opinion(1,s,u"socrates",u"sócrates",0,None,u"Manual",u"Manual",None)
        
        v = ruler.hasInterjectionWithTarget(o)
        
        print s, "->", v 
        print "------------------"

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
                               u"Ui O sócrates e passos coelho são bff!",
                               u"Uuuuuui O sócrates e passos coelho são bff!"                           
                           ]                              
    
    for sentence in interjectionSentences:
    
        o = Opinion(1,sentence,u"socrates",u"sócrates",0,None,u"Manual",u"Manual",None)
        
        v = ruler.hasInterjection(o)        
        
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
        
        v = ruler.hasSmiley(o)
        
        
        print s, "->", v 
        print "------------------"
    """
    
    """
    sA = [sentenceNoMatch,u" Uii o sócrates demonstrou uma enorme coragem ",
          u" O Rui! é fixe ",
          u" O ui! como é fixe ",
          u" O fui lá e uiii, como é fixe ",
          u" O fui lá e uiii muito bom!",
          u" O fui lá e não é mau, descuidei-me..."]
    
    for s in sA:
        o = Opinion(1,s,u"socrates",u"sócrates",0,None,u"Manual",u"Manual",None)
    
        v = ruler.hasInterjection(o)
    
        if v != None:
            print s, "->", v[0],v[1] 
        else:
            print s, "-> Fail"
    """
    
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
                       u"O sócrates e passos coelho são ;/////",                                        
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
                       u"O sócrates e passos coelho são X-D",
                       u"O sócrates e passos coelho são xD",
                       u"O sócrates e passos coelho são x-D"
                      ]        
    
    
    for s in smileySentences:
    
        o = Opinion(1,s,u"socrates",u"socras",0,None,u"Manual",u"Manual",None)
        
        v = ruler.hasSmiley(o)
        
        
        print s, "->", v 
        print "------------------"
   """ 
    
if __name__ == '__main__':  
    
    politiciansFile = "../Resources/politicians.txt"
    sentiTokensFile = "../Resources/sentiTokens.txt"
    exceptTokensFile = "../Resources/SentiLexAccentExcpt.txt"
    
    politicians = Persons.loadPoliticians(politiciansFile)
    sentiTokens = SentiTokens.loadSentiTokens(sentiTokensFile,exceptTokensFile)
    
    ruler = Rules(politicians,sentiTokens)    
    sentenceNoMatch = u"O sócrates e passos coelho são bff"
    
    #s1 = [sentenceNoMatch,u" o sócrates não é uma pessoa honesta "]
    #s2 = [sentenceNoMatch,u" o sócrates não é um tipo autoritário "]
    #s3 = [sentenceNoMatch,u" o sócrates não é um bom político "]
    #s4 = [sentenceNoMatch,u" o sócrates não é um mau político "]
    #s5 = [sentenceNoMatch,u" o sócrates não é um idiota "]
    #s6 = [sentenceNoMatch,u" o sócrates não é um embuste "] 
    #s7 = [sentenceNoMatch,u" o sócrates não foi nada sincero "]
    #s8 = [sentenceNoMatch,u" o sócrates não é nada parvo "]
    #s9 = [sentenceNoMatch,u" o sócrates não foi coerente "]
    #s10 = [sentenceNoMatch,u" o sócrates não é mentiroso "]
    #s11 = [sentenceNoMatch,u" o sócrates não demonstrou um forte empenho "]
    #s12 = [sentenceNoMatch,u" o sócrates não mostrou falta de coragem "]
    #s13 = [sentenceNoMatch,u" o sócrates é um político desonesto "]
    #s14 = [sentenceNoMatch,u" o sócrates é um tipo honesto "]
    #s15 = [sentenceNoMatch,u" o sócrates é um mau político "]
    #s16 = [sentenceNoMatch,u" o sócrates é um bom político "]
    #s17 = [sentenceNoMatch,u" o sócrates é um perfeito idiota "]
    #s18 = [sentenceNoMatch,u" o sócrates é um verdadeiro desastre "]
    #s19 = [sentenceNoMatch,u" o sócrates é um mau perdedor "]
    #s20 = [sentenceNoMatch,u" o sócrates é um idiota "]
    #s21 = [sentenceNoMatch,u" o sócrates é um embuste "]
    #s22 = [sentenceNoMatch,u" o sócrates é muito parvo "]
    #s23 = [sentenceNoMatch,u" o sócrates foi extremamente sincero "]
    #s24 = [sentenceNoMatch,u" o sócrates é mentiroso "]
    #s25 = [sentenceNoMatch,u" o sócrates foi coerente "]
    #s26 = [sentenceNoMatch,u" o idiota do sócrates "]
    #s27 = [sentenceNoMatch,u" o sócrates revelou uma enorme falta de respeito "]
    #s28 = [sentenceNoMatch,u" o sócrates tem falta de coragem "]
    #s29 = [sentenceNoMatch,u" o sócrates demonstrou uma enorme arrogância "]
    #s30 = [sentenceNoMatch,u" o sócrates demonstrou uma enorme coragem "]
    
    
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
   
   