# -*- coding: UTF-8 -*-
'''
Created on Apr 12, 2011

@author: samir
'''

import re
import Utils 
import Persons
import SentiTokens
import codecs
import StringIO
import contextRestrictions

class Naive:
 
    def __init__(self,persons,sentiTokens):
    
        self.persons = persons        
        self.sentiTokens = sentiTokens    
        
        buffer = StringIO.StringIO()
        buffer.write(u'')
        
        regexTemplate = ur"(?:\W{0}(?:\W|$))|"
        
        # Build a regex for identifying targets
        for person in self.persons:            
            
            for name in person.names:
                                    
                    #buffer.write(u"\W?" + name + u"\W?|")
                    buffer.write(regexTemplate.format(name))
            
            for nickName in person.nicknames:
                    
                    #buffer.write(u"\W??" + nickName + u"\W?|")
                    buffer.write(regexTemplate.format(nickName))
                    
            for ergo in person.ergos:
                
                    #buffer.write(u"\W??" + ergo + u"\W??|")
                    buffer.write(regexTemplate.format(ergo))
                    

        self.targetsRegex = buffer.getvalue().strip('|')
        
        buffer = StringIO.StringIO()
                 
        # Build a regex for identifying sentiment tokens
        for sentiToken in sentiTokens:
            
            for token in sentiToken.getTokens():
                
                buffer.write(regexTemplate.format(token))  
        
        self.sentiTokensRegex = buffer.getvalue().strip('|')
    
    def isFalsePositive(self,mention,sentence):
        
        """
            Determines if a mention is a false positive
            by looking for the context (ahead and behind)
        """
        
        tokens = re.findall(u'\w+',sentence,re.U)
        nMention = unicode(mention)
        
        try:
            if nMention in contextRestrictions.left_context:
        
                badTokens = contextRestrictions.left_context[nMention]
                
                if tokens[tokens.index(nMention)-1] in badTokens:
                    print "Discarded (left) " + nMention + " in " + "**" + sentence.replace('\n',' ') + "**"
                    return True
            
            if mention in contextRestrictions.right_context:
                
                badTokens = contextRestrictions.right_context[nMention]             
                
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
        specialChars = u' “”\"@)(!#;&:\\@/-_,?.«»\'~ ' 
        sentence = opinion.sentence.lower()
        
        #Find matches
        matches = re.findall(self.targetsRegex,sentence)
                 
        if matches != None and len(matches) > 0:
       
            targets = {}
            
            for match in matches:
                
                mention = match.rstrip(specialChars).lstrip(specialChars)                
                
                target = self.getTargetByMention(mention)
                
                if target != None and not self.isFalsePositive(mention, sentence):                    
                    
                    if mention not in info:
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
                     
                
    def getTargetByMention(self,mention):       
        
        """
            Returns the target name by mention
        """
        
        for person in self.persons:
            
            if person.isMatch(mention):
                
                return person.id
        
        return None

    def inferPolarity(self,opinion,useTaggedSentence):        
        
        """ 
            Tries to identify the polarity of a sentence
            Params: opinion -> Opinion object
                    useTaggedSentence -> True to use the tagged (and tokenized) version of the sentence
            Returns: tuple(inferred polarity, algorithm metadata)
        """
        
        info = opinion.metadata + "; " + u'sentiTokens:'       
        specialChars = u' “”\"@)(!#;&:\\@/-_,?.«»\' ' 
        
        if useTaggedSentence:
            sentence = opinion.taggedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
            
        score = 0
        
        #Find matches
        matches = re.findall(self.sentiTokensRegex ,sentence)
        
        foundTokens = {}
                 
        if matches != None and len(matches) > 0:     
            
            for match in matches:
                
                token = match.rstrip(specialChars).lstrip(specialChars)
                
                for adj in self.sentiTokens:
            
                    if adj.isMatch(token): 
                        
                        #store found tokens in a dictionary to avoid duplicate tokens
                        foundTokens[token] = adj.polarity 
                        
            #register found tokens and sum scores of polarities                        
            for token, polarity in foundTokens.items():
                
                score += int(polarity)                        
                info += token + "(" + polarity + ") " 
        
        info += '; score:' + unicode(score) + ";"        
        
        polarity = None
        
        if score > 0:
            polarity = 1
        
        elif score < 0:
            polarity = -1
        else:
            polarity = 0
            
        return opinion.clone(polarity=polarity,metadata=info)

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
    
    
    def __init__(self,persons,sentiTokens):
    
        self.persons = self.buildPersonsDict(persons)        
        self.sentiTokens = sentiTokens
        self.quantRegex = self.getRegexFromList(self.QUANT)
        self.vcopRegex = self.getRegexFromList(self.VCOP)
        self.nclasRegex = self.getRegexFromList(self.NCLAS)
        self.vsupRegex = self.getRegexFromList(self.VSUP)
        self.populateSentiRegexes(sentiTokens)
    
    def getRegexFromList(self,list):
        
        """
            Builds a regex from a list of words 
        """
        
        regex = ur''
        
        buffer = StringIO.StringIO()
        
        for token in list:
            
            buffer.write(token)
            buffer.write("|")
        
        regex += buffer.getvalue().strip('|')
        buffer.close()
        
        return regex 
        
    
    def buildPersonsDict(self,personsList):
        
        personsDict= {}
        
        for person in personsList:
            
            for mention in person.mentions():
                
                personsDict[mention] = person
            
        return personsDict
    
    def populateSentiRegexes(self,sentiTokens):
        
        partialRegex = StringIO.StringIO()
        positiveRegex = StringIO.StringIO()
        negativeRegex = StringIO.StringIO()
        neutralRegex = StringIO.StringIO()
        
        for sentiToken in sentiTokens:
            
            for token in sentiToken.getTokens():
            
                partialRegex.write(token)
                partialRegex.write("|")    
            
            if sentiToken.polarity == str(1):                                
                positiveRegex.write(partialRegex.getvalue())
                
            elif sentiToken.polarity == str(0):                
                neutralRegex.write(partialRegex.getvalue())
                
            elif sentiToken.polarity == str(-1):                                  
                negativeRegex.write(partialRegex.getvalue())
                
            partialRegex = StringIO.StringIO()         
        
        self.posSentiRegex = positiveRegex.getvalue().strip('|')
        self.neutSentiRegex = neutralRegex.getvalue().strip('|')              
        self.negSentiRegex = negativeRegex.getvalue().strip('|')
        
        #close all buffers        
        partialRegex.close()
        positiveRegex.close()
        negativeRegex.close()
        neutralRegex.close()
        
    def inferPolarity(self,opinion,useTaggedSentence):
        
        for rule in self.setOfRules:
            
            result = rule(self,opinion,useTaggedSentence)
            
            if result != None:
             
                info = opinion.metadata + ";" + result[1]
                return opinion.clone(polarity=result[0],metadata=info)
            
        return opinion.clone(polarity=0)
    
    def hasNickName(self,opinion,useTaggedSentence):
        
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
    
    def hasLol(self,opinion,useTaggedSentence):
        
        info = "LOL: "        
        regex = r'(l+o+l+(o+)?)+'
        
        if useTaggedSentence:
            sentence = opinion.taggedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        match = re.search(regex,sentence)
    
        if match != None:
            
            info += match.group()
            
            return (-1,info)
        else:
            return None
   
    def hasSmiley(self,opinion,useTaggedSentence): 
        
        info = "Smiley: "        
        regex = r'([\W ])[:;xX8]-?([\)\(psd])+'
        
        if useTaggedSentence:
            sentence = opinion.taggedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        match = re.search(regex,sentence)
    
        if match != None:
            
            info += match.group().upper()
            
            return (-1,info)            
        else:
            return None
       
    def hasHehe(self,opinion,useTaggedSentence): 
        
        info = "Haha: "        
        regex = r'(h[e|a|i]+){2,}|(h[e|a|i] ?){2,}|([a|e]h ?){2,}'
        
        if useTaggedSentence:
            sentence = opinion.taggedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        match = re.search(regex,sentence)
    
        if match != None:
            
            info += match.group()
                        
            return (-1,info)    
            
        else:
            return None
        
    def hasHeavyPunctuation(self,opinion,useTaggedSentence): 
        
        info = "Heavy Punctuation: "        
        regex = r'.?([!?]{2,})+'
        
        if useTaggedSentence:
            sentence = opinion.taggedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        match = re.search(regex,sentence)
    
        if match != None:
            
            info += match.group()
                        
            return (-1,info)        
            
        else:
            return None
        
    def hasInterjection(self,opinion,useTaggedSentence): 
        
        """
        
        ai 
        é pá
        é pah
        eh pah
        filho da p%$& (arranjar um mecanismo para dar conta destes caracteres especiais, que normalmente ocorrem em substituição do palavrão)
        Whaaaat
        viva
        nhoc, nhoc, nhoc
        que seca
        isso é conversa
        desculpem lá
        vai-te catar
        estamos feitos        
        UAU
        Hum
        Oh Yeah
        Apre!
        Livra!        
        Uh!
        Abaixo! *
        Fora!
        Rua!
        Safa! 
        Basta! *
        
        """
        
        info = "Interjection: "
        regex = ur'(m+e+r+d+a+|f+o+d+a+-*s+e*|(es)?t[áa] fdd|que no+jo+|credo|lindo|(oh)?meu deus|([\W ])ui+[\W ])!*'
        #regex = ur'(m+e+r+d+a+|f+o+d+a+-*s+e*|(es)?t[áa] fdd|que no+jo+|credo|lindo|(oh)?meu deus|([\W ])ui+[\W ]|ba+sta+|abaixo|)!*'
               
        if useTaggedSentence:
            sentence = opinion.taggedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        match = re.search(regex,sentence)
    
        if match != None:
            
            info += match.group()
            
            return (-1,info) 
            
        else:
            return None
    
    def hasInterjectionWithTarget(self,opinion,useTaggedSentence): 
        
        info = u"Interjection with target: "        
        target = opinion.mention.lower()
        regexTargetLeft = ur'{0} nunca mais|{0} jamais'.format(target)
        regexTargetRight = ur'oh {0}|obrigado {0}|senhor {0}|anti-{0}'.format(target)
        
        if useTaggedSentence:
            sentence = opinion.taggedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
    
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
    
    def rule1(self,opinion,useTaggedSentence):
        
        """ Ex: não é uma pessoa honesta """
        
        info = u'Regra \"não [VCOP] um|uma [NCLAS] [AJD+] ? Neg\"-> '        
        regex = ur'.?não ({0}) (um|uma) ({1}) ({2}).?'.format(self.vcopRegex,self.nclasRegex,self.posSentiRegex)
        
        if useTaggedSentence:
            sentence = opinion.taggedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return None
        
    def rule2(self,opinion,useTaggedSentence):
        
        """ Ex: não é um tipo autoritário """
        
        info = u'Regra \"não [VCOP] um [NCLAS] [AJD-] ? Pos"\"-> '        
        regex = ur'.?não ({0}) (um|uma) ({1}) ({2}).?'.format(self.vcopRegex,self.nclasRegex,self.negSentiRegex)
        
        if useTaggedSentence:
            sentence = opinion.taggedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (1,info) 
            
        else:
            return None
    
    def rule3(self,opinion,useTaggedSentence):
        
        """ Ex: não é um bom político """
        
        info = u'Regra \"não [VCOP] um [AJD+] [NCLAS] ?Neg\""-> '        
        regex = ur'.?não ({0}) (um|uma) ({1}) ({2}).?'.format(self.vcopRegex,self.posSentiRegex,self.nclasRegex)
        
        if useTaggedSentence:
            sentence = opinion.taggedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return None
    
    def rule4(self,opinion,useTaggedSentence):
        
        """ Ex: não é um mau político """
        
        info = u'Regra \"não [VCOP] um [AJD-] [NCLAS] ?Pos\""-> '        
        regex = ur'.?não ({0}) (um|uma) ({1}) ({2}).?'.format(self.vcopRegex,self.negSentiRegex,self.nclasRegex)
        
        if useTaggedSentence:
            sentence = opinion.taggedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (1,info) 
            
        else:
            return None
    
    def rule5(self,opinion,useTaggedSentence):
        
        """ Ex: não é um idiota """
        
        info = u'Regra \"não [VCOP] um [AJD-] ? Pos\""-> '        
        regex = ur'.?não ({0}) (um|uma) ({1}).?'.format(self.vcopRegex,self.negSentiRegex)
        
        if useTaggedSentence:
            sentence = opinion.taggedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (1,info) 
            
        else:
            return None
    
    def rule6(self,opinion,useTaggedSentence):
        
        """ Ex: não é um embuste """
        
        info = u'Regra \"não [VCOP] um [N-] ? Pos\""-> '        
        regex = ur'.?não ({0}) (um|uma) ({1}).?'.format(self.vcopRegex,self.negSentiRegex)
        
        if useTaggedSentence:
            sentence = opinion.taggedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (1,info) 
            
        else:
            return None
    
    def rule7(self,opinion,useTaggedSentence):
        
        """ Ex: não foi nada sincero """
        
        info = u'Regra \"não [VCOP] [QUANT] [Adj+] ? Neg\""-> '        
        regex = ur'.?não ({0}) ({1}) ({2}).?'.format(self.vcopRegex,self.quantRegex,self.posSentiRegex)
        
        if useTaggedSentence:
            sentence = opinion.taggedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return None
    
    def rule8(self,opinion,useTaggedSentence):
        
        """ Ex: não é nada parvo """
        
        info = u'Regra \"não [VCOP] [QUANT] [Adj-] ? Pos\""-> '        
        regex = ur'.?não ({0}) ({1}) ({2}).?'.format(self.vcopRegex,self.quantRegex,self.negSentiRegex)
        
        if useTaggedSentence:
            sentence = opinion.taggedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (1,info) 
            
        else:
            return None
    
    def rule9(self,opinion,useTaggedSentence):
        
        """ Ex: não foi coerente """
        
        info = u'Regra \"não [VCOP] [Adj+] ? Neg\""-> '        
        regex = ur'.?não ({0}) ({1}).?'.format(self.vcopRegex,self.posSentiRegex)
        
        if useTaggedSentence:
            sentence = opinion.taggedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return None
        
    def rule10(self,opinion,useTaggedSentence):
        
        """ Ex: não é mentiroso """
        
        info = u'Regra \"não [VCOP] [Adj-] ? Pos\""-> '        
        regex = ur'.?não ({0}) ({1}).?'.format(self.vcopRegex,self.negSentiRegex)
        
        if useTaggedSentence:
            sentence = opinion.taggedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (1,info) 
            
        else:
            return None
    
    def rule11(self,opinion,useTaggedSentence):
        
        """ Ex: não demonstrou um forte empenho """
        
        info = u'Regra \"não [VSUP] (um+uma) [ADJ+|0] [N+] ? Neg\""-> '        
        regex = ur'.?não ({0}) (um|uma) ({1}|{2}) ({3}).?'.format(self.vsupRegex,self.posSentiRegex,self.neutSentiRegex,self.posSentiRegex)
        
        if useTaggedSentence:
            sentence = opinion.taggedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return None
    
    def rule12(self,opinion,useTaggedSentence):
        
        """ Ex: não mostrou falta de coragem """
        
        info = u'Regra \"não [VSUP] falta de [N+] ? Pos\""-> '        
        regex = ur'.?não ({0}) falta de ({1}).?'.format(self.vsupRegex,self.posSentiRegex)
        
        if useTaggedSentence:
            sentence = opinion.taggedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (1,info) 
            
        else:
            return None
    
    def rule13(self,opinion,useTaggedSentence):
        
        """ Ex:  é um político desonesto """
        
        info = u'Regra \"[VCOP] um [NCLAS] [AJD-] ? Neg\""-> '        
        regex = ur'.?({0}) um ({1}) ({2}).?'.format(self.vcopRegex,self.nclasRegex,self.negSentiRegex)
        
        if useTaggedSentence:
            sentence = opinion.taggedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return None
    
    def rule14(self,opinion,useTaggedSentence):
        
        """ Ex:  é um tipo honesto """
        
        info = u'Regra \"[VCOP] um [NCLAS] [AJD+] ? Pos\""-> '        
        regex = ur'.?({0}) um ({1}) ({2}).?'.format(self.vcopRegex,self.nclasRegex,self.posSentiRegex)
        
        if useTaggedSentence:
            sentence = opinion.taggedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (1,info) 
            
        else:
            return None
    
    def rule15(self,opinion,useTaggedSentence):
        
        """ Ex:  é um mau político """
        
        info = u'Regra \"[VCOP] um [AJD-] [NCLAS] ?Neg\""-> '        
        regex = ur'.?({0}) um ({1}) ({2}).?'.format(self.vcopRegex,self.negSentiRegex,self.nclasRegex)
        
        if useTaggedSentence:
            sentence = opinion.taggedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return None
    
    def rule16(self,opinion,useTaggedSentence):
        
        """ Ex:  é um bom político """
        
        info = u'Regra \"[VCOP] um [AJD+] [NCLAS] ?Pos\""-> '        
        regex = ur'.?({0}) um ({1}) ({2}).?'.format(self.vcopRegex,self.posSentiRegex,self.nclasRegex)
        
        if useTaggedSentence:
            sentence = opinion.taggedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (1,info) 
            
        else:
            return None
    
    def rule17(self,opinion,useTaggedSentence):
        
        """ Ex: é um perfeito idiota """
        
        info = u'Regra \"[VCOP] um [AJD+] [AJD-] ? Neg\""-> '        
        regex = ur'.?({0}) um ({1}) ({2}).?'.format(self.vcopRegex,self.posSentiRegex,self.negSentiRegex)
        
        if useTaggedSentence:
            sentence = opinion.taggedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return None
    
    def rule18(self,opinion,useTaggedSentence):
        
        """ Ex: é um verdadeiro desastre """
        
        info = u'Regra \"[VCOP] um [AJD+] [N-] ? Neg\""-> '        
        regex = ur'.?({0}) um ({1}) ({2}).?'.format(self.vcopRegex,self.posSentiRegex,self.negSentiRegex)
        
        if useTaggedSentence:
            sentence = opinion.taggedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return None
    
    def rule19(self,opinion,useTaggedSentence):
        
        """ Ex: é um mau perdedor """
        
        info = u'Regra \"[VCOP] um [AJD-] [AJD-] ? Neg\""-> '        
        regex = ur'.?({0}) um ({1}) ({2}).?'.format(self.vcopRegex,self.negSentiRegex,self.negSentiRegex)
        
        if useTaggedSentence:
            sentence = opinion.taggedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return None
    
    def rule20(self,opinion,useTaggedSentence):
        
        """ Ex: é um idiota """
        
        info = u'Regra \"[VCOP] um [AJD-] ? Neg\""-> '        
        regex = ur'.?({0}) um ({1}).?'.format(self.vcopRegex,self.negSentiRegex)
        
        if useTaggedSentence:
            sentence = opinion.taggedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return None
    
    def rule21(self,opinion,useTaggedSentence):
        
        """ Ex: é um embuste """
        
        info = u'Regra \"[VCOP] um [N-] ? Neg\""-> '        
        regex = ur'.?({0}) um ({1}).?'.format(self.vcopRegex,self.negSentiRegex)
        
        if useTaggedSentence:
            sentence = opinion.taggedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return None
    
    def rule22(self,opinion,useTaggedSentence):
        
        """ Ex: é muito parvo """
        
        info = u'Regra \"[VCOP] [QUANT] [Adj-] ? Pos\""-> '        
        regex = ur'.?({0}) ({1}) ({2}).?'.format(self.vcopRegex,self.quantRegex,self.negSentiRegex)
        
        if useTaggedSentence:
            sentence = opinion.taggedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return None
    
    def rule23(self,opinion,useTaggedSentence):
        
        """ Ex: foi extremamente sincero """
        
        info = u'Regra \"[VCOP] [QUANT] [Adj+] ? Pos\""-> '        
        regex = ur'.?({0}) ({1}) ({2}).?'.format(self.vcopRegex,self.quantRegex,self.posSentiRegex)
        
        if useTaggedSentence:
            sentence = opinion.taggedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (1,info) 
            
        else:
            return None    
    
    def rule24(self,opinion,useTaggedSentence):
        
        """ Ex: é mentiroso """
        
        info = u'Regra \"[VCOP] [Adj-] ? Neg\""-> '        
        regex = ur'.?({0}) ({1}).?'.format(self.vcopRegex,self.negSentiRegex)
        
        if useTaggedSentence:
            sentence = opinion.taggedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return None
    
    def rule25(self,opinion,useTaggedSentence):
        
        """ Ex: foi coerente """
        
        info = u'Regra \"[VCOP] [Adj+] ? Pos\""-> '        
        regex = ur'.?({0}) ({1}).?'.format(self.vcopRegex,self.posSentiRegex)
        
        if useTaggedSentence:
            sentence = opinion.taggedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (1,info) 
            
        else:
            return None        
    
    def rule26(self,opinion,useTaggedSentence):
        
        """ Ex: o idiota do Sócrates """
        
        target = opinion.mention.lower()
        
        info = u'Regra \"o [ADJ] do TARGET ? Neg\""-> '        
        regex = ur'.?o ({0}) do {1}.?'.format(self.negSentiRegex,target)
        
        if useTaggedSentence:
            sentence = opinion.taggedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return None  
    
    def rule27(self,opinion,useTaggedSentence):
        
        """ Ex: revelou uma enorme falta de respeito """
        
        info = u'Regra \"[VSUP] (um+uma) [ADJ+|0] falta de [N+] ? Neg\""-> '        
        regex = ur'.?({0}) (um|uma) ({1}|{2}) falta de ({3}).?'.format(self.vsupRegex,self.posSentiRegex,self.neutSentiRegex,self.posSentiRegex)
        
        if useTaggedSentence:
            sentence = opinion.taggedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return None
    
    def rule28(self,opinion,useTaggedSentence):
        
        """ Ex: tem falta de coragem """
        
        info = u'Regra \"[VSUP] falta de [N+] ? Neg\""-> '        
        regex = ur'.?({0}) falta de ({1}).?'.format(self.vsupRegex,self.posSentiRegex)
        
        if useTaggedSentence:
            sentence = opinion.taggedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return None
        
    def rule29(self,opinion,useTaggedSentence):
        
        """ Ex: demonstrou uma enorme arrogância """
        
        info = u'Regra \"[VSUP] (um+uma+0) [ADJ+|0] [N-] ? Neg\""-> '        
        regex = ur'.?({0}) (um|uma) ({1}|{2}) ({3}).?'.format(self.vsupRegex,self.posSentiRegex,self.neutSentiRegex,self.negSentiRegex)
        
        if useTaggedSentence:
            sentence = opinion.taggedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return None
    
    def rule30(self,opinion,useTaggedSentence):
        
        """ Ex: demonstrou uma enorme coragem """
        
        info = u'Regra \"[VSUP] (um+uma+0) [ADJ+|0] [N-] ? Neg\""-> '        
        regex = ur'.?({0}) (um|uma) ({1}|{2}) ({3}).?'.format(self.vsupRegex,self.posSentiRegex,self.neutSentiRegex,self.posSentiRegex)
        
        if useTaggedSentence:
            sentence = opinion.taggedSentence.lower()
        else:
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

class MultiWordHandler:
    
    """
        Handles the tokenization of multiwords from "x y" to "x_y"
        Builds a regex that finds multiwords in a sentence 
        Those multiwords are then concatenated with '_'
    """
    
    regexTemplate = ur"(?:\W{0}(?:\W|$))|"
    
    def __init__(self,multiWordsFilePath):
        
        self.multiWordsRegex = ur""
        
        f = codecs.open(multiWordsFilePath,"r","utf-8")
        multiWordsList = f.read().lower().split('\n')
        
        self.addMultiWords(multiWordsList)
        
    def tokenizeMultiWords(self,sentence):
        
        """
            Finds multiwords in a sentence and
            concatenates them with '_'
        
        """
        
        loweredSentence = sentence.lower()     
        newSentence = loweredSentence
        
        matches = re.findall(self.multiWordsRegex,loweredSentence)        
        
        for multiWord in matches:
                
            cleanTokens = multiWord.strip(' ').rstrip(' ')
            
            if cleanTokens != "":
            
                multiToken = cleanTokens.replace(" ","_")
                newSentence = newSentence.replace(cleanTokens,multiToken)                
            
        return newSentence  
    
    def addMultiWords(self,listOfMultiWords):
        
        """
            Updates the internal regex with a
            list of multiwords
        """
        
        buffer =  StringIO.StringIO()
        
        for multiWord in listOfMultiWords:
            
            if multiWord not in self.multiWordsRegex and multiWord not in buffer.getvalue(): 
                buffer.write(self.regexTemplate.format(multiWord))
            
                #add a normalized (no accents) version
                if multiWord != Utils.normalize(multiWord):
                    buffer.write(self.regexTemplate.format(Utils.normalize(multiWord)))
        
        if len(self.multiWordsRegex) == 0:
            self.multiWordsRegex = buffer.getvalue().strip('|')
        else:
            self.multiWordsRegex += "|" + buffer.getvalue().strip('|')
      
        buffer.close()
        
    
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
   
   
    """
   sentenceNoMatch = u"O sócrates e passos coelho são bff"
    
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

def testSintaticRules():
    
    sentenceNoMatch = u"O sócrates e passos coelho são bff"
    s1 = [sentenceNoMatch,u" o sócrates não é uma pessoa honesta "]
    s2 = [sentenceNoMatch,u" o sócrates não é um tipo autoritário "]
    s3 = [sentenceNoMatch,u" o sócrates não é um bom político "]
    s4 = [sentenceNoMatch,u" o sócrates não é um mau político "]
    s5 = [sentenceNoMatch,u" o sócrates não é um idiota "]
    s6 = [sentenceNoMatch,u" o sócrates não é um embuste "] 
    s7 = [sentenceNoMatch,u" o sócrates não foi nada sincero "]
    s8 = [sentenceNoMatch,u" o sócrates não é nada parvo "]
    s9 = [sentenceNoMatch,u" o sócrates não foi coerente "]
    s10 = [sentenceNoMatch,u" o sócrates não é mentiroso "]
    s11 = [sentenceNoMatch,u" o sócrates não demonstrou um forte empenho "]
    s12 = [sentenceNoMatch,u" o sócrates não mostrou falta de coragem "]
    s13 = [sentenceNoMatch,u" o sócrates é um político desonesto "]
    s14 = [sentenceNoMatch,u" o sócrates é um tipo honesto "]
    s15 = [sentenceNoMatch,u" o sócrates é um mau político "]
    s16 = [sentenceNoMatch,u" o sócrates é um bom político "]
    s17 = [sentenceNoMatch,u" o sócrates é um perfeito idiota "]
    s18 = [sentenceNoMatch,u" o sócrates é um verdadeiro desastre "]
    s19 = [sentenceNoMatch,u" o sócrates é um mau perdedor "]
    s20 = [sentenceNoMatch,u" o sócrates é um idiota "]
    s21 = [sentenceNoMatch,u" o sócrates é um embuste "]
    s22 = [sentenceNoMatch,u" o sócrates é muito parvo "]
    s23 = [sentenceNoMatch,u" o sócrates foi extremamente sincero "]
    s24 = [sentenceNoMatch,u" o sócrates é mentiroso "]
    s25 = [sentenceNoMatch,u" o sócrates foi coerente "]
    s26 = [sentenceNoMatch,u" o idiota do sócrates "]
    s27 = [sentenceNoMatch,u" o sócrates revelou uma enorme falta de respeito "]
    s28 = [sentenceNoMatch,u" o sócrates tem falta de coragem "]
    s29 = [sentenceNoMatch,u" o sócrates demonstrou uma enorme arrogância "]
    s30 = [sentenceNoMatch,u" o sócrates demonstrou uma enorme coragem "]

def testRules():
    
    politiciansFile = "../Resources/politicians.txt"
    sentiTokensFile = "../Resources/sentitokens-2011-05-13.txt"
    exceptTokensFile = "../Resources/SentiLexAccentExcpt.txt"
    
    politicians = Persons.loadPoliticians(politiciansFile)
    sentiTokens = SentiTokens.loadSentiTokens(sentiTokensFile,exceptTokensFile)
    
    ruler = Rules(politicians,sentiTokens)    

def testMultiWords():
    
        
    sentiTokensFile = "../Resources/sentiTokens.txt"
    exceptTokensFile = "../Resources/SentiLexAccentExcpt.txt"
        
    sentiTokens = SentiTokens.loadSentiTokens(sentiTokensFile,exceptTokensFile)
    tst = MultiWordHandler("../Resources/multiwords.txt")
    tst.addMultiWords(SentiTokens.getMultiWords(sentiTokens))
    
    #str = " Era uma vez um VSS Enterprise! que era do ,ministro do Fomento, e se transformou XiXi presidente cessante p"
    str = " Ele era um atrasado mental Era uma vez um VSS Enterprise! que era do ,ministro do Fomento, e se transformou XiXi presidente cessante p"
    
    print tst.tokenizeMultiWords(str)
    
      
if __name__ == '__main__':  
    
    print "Go!"
    
    testMultiWords()
    
    print "Done!"
   