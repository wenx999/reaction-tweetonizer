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
from Opinion import Opinion

class Naive:
 
    def __init__(self,persons,sentiTokens):
    
        self.persons = persons        
        self.sentiTokens = sentiTokens    
        
        buff = StringIO.StringIO()
        buff.write(u'')
        
        regexTemplate = ur"(?:\W{0}(?:\W|$))|"
        
        # Build a regex for identifying targets
        for person in self.persons:            
            
            for name in person.names:
                                    
                    #buff.write(u"\W?" + name + u"\W?|")
                    buff.write(regexTemplate.format(name.replace(".","\.")))
            
            for nickName in person.nicknames:
                    
                    #buff.write(u"\W??" + nickName + u"\W?|")
                    buff.write(regexTemplate.format(nickName.replace(".","\.")))
                    
            for ergo in person.ergos:
                
                    #buff.write(u"\W??" + ergo + u"\W??|")
                    buff.write(regexTemplate.format(ergo))
                    

        self.targetsRegex = buff.getvalue().strip('|')
        
        print self.targetsRegex 
        
        buff = StringIO.StringIO()
                 
        # Build a regex for identifying sentiment tokens
        for sentiToken in sentiTokens:
            
            for token in sentiToken.getTokens():
                
                buff.write(regexTemplate.format(token))  
        
        self.sentiTokensRegex = buff.getvalue().strip('|')
    
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

    def inferPolarity(self,opinion,useProcessedSentence):        
        
        """ 
            Tries to identify the polarity of a sentence
            Params: opinion -> Opinion object
                    useProcessedSentence -> True to use the tagged (and tokenized) version of the sentence
            Returns: tuple(inferred polarity, algorithm metadata)
        """
        info = opinion.metadata + "; " + u'sentiTokens:'       
        specialChars = u' “”\"@)(!#;&:\\@/-_,?.«»\' ' 
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
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
        
        buff =  StringIO.StringIO()
        
        for multiWord in listOfMultiWords:
            
            if multiWord not in self.multiWordsRegex and multiWord not in buff.getvalue(): 
                buff.write(self.regexTemplate.format(multiWord))
            
                #add a normalized (no accents) version
                if multiWord != Utils.normalize(multiWord):
                    buff.write(self.regexTemplate.format(Utils.normalize(multiWord)))
        
        if len(self.multiWordsRegex) == 0:
            self.multiWordsRegex = buff.getvalue().strip('|')
        else:
            self.multiWordsRegex += "|" + buff.getvalue().strip('|')
      
        buff.close()

class Rules:

    
    QUANT_LIST = [u'muito',u'mto',u'muita',u'mta', u'mt', u'muitíssimo',u'muitíssima', u'pouco',u'pouca', u'pouquíssimo',u'pouquíssima',
             u'bastante',u'completamente', u'imensamente', u'estupidamente', u'demasiado', 
             u'profundamente', u'perfeitamente', u'relativamente', u'simplesmente', 
             u'verdadeiramente', u'inteiramente', u'realmente', 
             u'sempre', u'smp', u'sp', u'mais', u'bem', u'altamente', u'extremamente', u'mesmo',u'mm',u'msm', 
             u'particularmente', u'igualmente', u'especialmente', u'quase', u'tão',
             u'absolutamente', u'potencialmente', u'aparentemente', u'exactamente', u'nada',u'nd',
             ]

    VCOP_LIST = [u'é', u'foi', u'era', u'será',
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
    
    NCLAS_LIST = [u'pessoa',  u'homem',  u'rapaz',  u'jovem',  u'gajo',  u'tipo',  u'fulano',
             u'jogador',  u'atleta',  u'futebolista', u'seleção',  u'selecção',  u'equipa',  
             u'onze inicial',  u'onze', u'treinador',  u'mister',  u'técnico',  u'selecionador',  
             u'seleccionador',  u'capitão', u'árbitro',  u'bandeirinha',  u'fiscal de linha',  
             u'juiz', u'ala',  u'ala direito',  u'ala esquerdo',  u'médio',  u'médio defensivo', 
             u'médio ofensivo',  u'atacante',  u'avançado',  u'avançado central', 
             u'central',  u'defesa',  u'defesa direito',  u'defesa esquerdo',
             u'ponta de lança',  u'guarda redes',  u'guarda-redes',  u'lateral', 
             u'lateral direito',  u'lateral esquerdo',  u'extremo',  u'médio',  u'trinco',
             u'político',u'politico' 
            ]
    
    VSUP_LIST = [u'aparenta', u'aparentou', u'aparentava', u'aparentará',
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
    
    NEG_LIST = [u'não',u'nao',u'ñ',u'n']
    
    def __init__(self,persons,sentiTokens):
    
        self.persons = self.buildPersonsDict(persons)                
        self.sentiTokens = sentiTokens
        self.quant = self.getRegexFromList(self.QUANT_LIST)
        self.vcop = self.getRegexFromList(self.VCOP_LIST)
        self.nclas = self.getRegexFromList(self.NCLAS_LIST)
        self.vsup = self.getRegexFromList(self.VSUP_LIST)
        self.neg = self.getRegexFromList(self.NEG_LIST)
        self.populateSentiRegexes(sentiTokens)
            
    def getRegexFromList(self,wordList):
        
        """
            Builds a regex from a list of words 
        """
        
        regex = ur''
        
        buff = StringIO.StringIO()
        
        for token in wordList:
            
            buff.write(token)
            buff.write("|")
        
        regex += buff.getvalue().strip('|')
        buff.close()
        
        return regex 
        
    
    def buildPersonsDict(self,personsList):
        
        personsDict= {}
        
        for person in personsList:
            
            for mention in person.mentions():
                
                personsDict[mention] = person
            
        return personsDict
    
    def populateSentiRegexes_old(self,sentiTokens):
        
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
    
    def populateSentiRegexes(self,sentiTokens):
        
        ADJECTIVE = "adj"
        NOUN = "n"
        IDIOMATIC_EXPR = "idiom"
        VERB = "v"
    
        partialRegex = StringIO.StringIO()
    
        nounsPosRegex = StringIO.StringIO()
        nounsNegRegex = StringIO.StringIO()
        nounsNeutRegex = StringIO.StringIO()
        
        adjsPosRegex = StringIO.StringIO()
        adjsNegRegex = StringIO.StringIO()
        adjsNeutRegex = StringIO.StringIO()
        
        idiomPosRegex = StringIO.StringIO()
        idiomNegRegex = StringIO.StringIO()
        idiomNeutRegex = StringIO.StringIO()
        
        verbPosRegex = StringIO.StringIO()
        verbNegRegex = StringIO.StringIO()
        verbNeutRegex = StringIO.StringIO()
        
        for sentiToken in sentiTokens:
            
            for token in sentiToken.getTokens():
            
                partialRegex.write(token)
                partialRegex.write("|")    
            
            if sentiToken.polarity == str(1):
                
                if sentiToken.pos == ADJECTIVE:                                
                    adjsPosRegex.write(partialRegex.getvalue())
                
                elif sentiToken.pos == NOUN:
                    nounsPosRegex.write(partialRegex.getvalue())
                
                elif sentiToken.pos == IDIOMATIC_EXPR:
                    idiomPosRegex.write(partialRegex.getvalue())
                
                elif sentiToken.pos == VERB:
                    verbPosRegex.write(partialRegex.getvalue())
                
            elif sentiToken.polarity == str(0):  
                              
                if sentiToken.pos == ADJECTIVE:                                
                    adjsNeutRegex.write(partialRegex.getvalue())
                
                elif sentiToken.pos == NOUN:
                    nounsNeutRegex.write(partialRegex.getvalue())
                
                elif sentiToken.pos == IDIOMATIC_EXPR:
                    idiomNeutRegex.write(partialRegex.getvalue())
                
                elif sentiToken.pos == VERB:
                    verbNeutRegex.write(partialRegex.getvalue())
                
            elif sentiToken.polarity == str(-1):                                  
                
                if sentiToken.pos == ADJECTIVE:                                
                    adjsNegRegex.write(partialRegex.getvalue())
                
                elif sentiToken.pos == NOUN:
                    nounsNegRegex.write(partialRegex.getvalue())
                
                elif sentiToken.pos == IDIOMATIC_EXPR:
                    idiomNegRegex.write(partialRegex.getvalue())
                
                elif sentiToken.pos == VERB:
                    verbNegRegex.write(partialRegex.getvalue())
                
            partialRegex = StringIO.StringIO()         
        
        #Assign the generated regexes (the vars have the same name but we
        #are assigning the local vars to class properties)        
        self.nounsPosRegex = nounsPosRegex.getvalue().strip('|')
        self.nounsNegRegex = nounsNegRegex.getvalue().strip('|')
        self.nounsNeutRegex = nounsNeutRegex.getvalue().strip('|')        
        self.adjsPosRegex = adjsPosRegex.getvalue().strip('|')
        self.adjsNegRegex = adjsNegRegex.getvalue().strip('|')
        self.adjsNeutRegex = adjsNeutRegex.getvalue().strip('|')        
        self.idiomPosRegex = idiomPosRegex.getvalue().strip('|')
        self.idiomNegRegex = idiomNegRegex.getvalue().strip('|')
        self.idiomNeutRegex = idiomNeutRegex.getvalue().strip('|')        
        self.verbPosRegex = verbPosRegex.getvalue().strip('|')
        self.verbNegRegex = verbNegRegex.getvalue().strip('|')
        self.verbNeutRegex = verbNeutRegex.getvalue().strip('|')
        
        #close all buffers        
        partialRegex.close()
        nounsPosRegex.close()
        nounsNegRegex.close()
        nounsNeutRegex.close()        
        adjsPosRegex.close()
        adjsNegRegex.close()
        adjsNeutRegex.close()        
        idiomPosRegex.close()
        idiomNegRegex.close()
        idiomNeutRegex.close()        
        verbPosRegex.close()
        verbNegRegex.close()
        verbNeutRegex.close()
            
    def inferPolarity(self,opinion,useProcessedSentence):
        
        for rule in self.setOfRules:

            result = rule(self,opinion,useProcessedSentence)
            
            if result != None:
             
                info = opinion.metadata + ";" + result[1]
                return opinion.clone(polarity=result[0],metadata=info)
        
        return opinion.clone(polarity=0)

    def generateFeatureSet(self,opinion,useProcessedSentence):
        
        featureSet = []
        
        for rule in self.setOfRules:
            
            result = rule(self,opinion,useProcessedSentence)
            
            if result != None:
             
                featureSet.append(result[0])
            else:
                featureSet.append(0)
                
        return featureSet
    
    def hasNickName(self,opinion,useProcessedSentence):
        
        info = "Nickname: "
        
        mention = opinion.mention.lower()
        
        try:
            person = self.persons[mention]
            
            if person.isNickname(mention):
                
                info += mention
                return (-1,info)
            else:
                return None
        except KeyError:
            
            return None
    
    def hasLol(self,opinion,useProcessedSentence):
        
        info = "LOL: "        
        regex = r'(\W|^)(l+o+l+(o+)?)+(\W|$)'
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        match = re.search(regex,sentence)
    
        if match != None:
            
            info += match.group()
            
            return (-1,info)
        else:
            return None
   
    def hasSmiley(self,opinion,useProcessedSentence): 
        
        info = "Smiley: "        
        regex = r'(\W|^)([\W ])[:;xX8]-?([\)\(psd])+.?'
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        match = re.search(regex,sentence)
    
        if match != None:
            
            info += match.group().upper()
            
            return (-1,info)            
        else:
            return None
       
    def hasHehe(self,opinion,useProcessedSentence): 
        
        info = "Haha: "        
        regex = r'(\W|^)(h[e|a|i]+){2,}|(h[e|a|i] ?){2,}|([a|e]h ?){2,}(\W|$)'
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        match = re.search(regex,sentence)
    
        if match != None:
            
            info += match.group()
                        
            return (-1,info)    
            
        else:
            return None
    
    def hasQuotedSentiment(self,opinion,useProcessedSentence): 
        
        info = "Quoted sentiment: "        
        regex = ur'(\W|^)\".*({0}|{1}).*\"(\W|$)'.format(self.adjsPosRegex,self.nounsPosRegex)
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        match = re.search(regex,sentence)
    
        if match != None:
            
            info += match.group()
                        
            return (-1,info)    
            
        else:
            return None
        
    def hasHeavyPunctuation(self,opinion,useProcessedSentence): 
        
        info = "Heavy Punctuation: "        
        regex = r'(\W|^)([!?]{2,})+.?'
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        match = re.search(regex,sentence)
    
        if match != None:
            
            info += match.group()
                        
            return (-1,info)        
            
        else:
            return None
        
    def hasInterjection(self,opinion,useProcessedSentence):
                
        info = "Interjection: "        
        regex = ur'(\W|^)(m+e+r+d+a+|f+o+d+a+-*s+e*|(es)?t[áa] fdd|que no+jo+|cre+do+|li+ndo+|(oh)?meu deus|u+i+|li+vra+|a+ba+i+xo+!|fo+ra+!|ru+a+!|safa!|cruzes!|passou-se!|basta!|fo+go+!|estamos feitos)!*(\W|$)'        
               
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        match = re.search(regex,sentence)
    
        if match != None:
            
            info += match.group()
            
            return (-1,info) 
            
        else:
            return None
    
    def hasInterjectionWithTarget(self,opinion,useProcessedSentence): 
        
        info = u"Interjection with target: "        
        target = opinion.mention.lower()
        regexTargetLeft = ur'(\W|^){0} (nunca mais|jamais)(\W|$)'.format(target)
        regexTargetRight = ur'(\W|^)(oh|obrigado|senhor|anti-|este|esse){0}(\W|$)'.format(target)
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
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
    
    
    
    def rule1(self,opinion,useProcessedSentence):
        
        "(\W|^){0}(\W|$)"
        
        """ Ex: não é uma pessoa honesta """
        
        info = u'Regra \"[NEG] [VCOP] um/uma [NCLAS] [AJD+] ? Neg\"-> '        
        regex = ur'(\W|^)({0}) ({1}) (um|uma) ({2}) ({3})(\W|$)'.format(self.neg,self.vcop,self.nclas,self.adjsPosRegex)
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        if sentence.find(u"um") == -1 or sentence.find(u"não") == -1:
            
            return (0,'')
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return (0,'')
        
    def rule2(self,opinion,useProcessedSentence):
        
        """ Ex: não é um tipo autoritário """
        
        info = u'Regra \"[NEG] [VCOP] um [NCLAS] [AJD-] ? Pos"\"-> '        
        regex = ur'(\W|^)({0}) ({1}) (um|uma) ({2}) ({3})(\W|$)'.format(self.neg,self.vcop,self.nclas,self.adjsNegRegex)
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        if sentence.find(u"um") == -1 or sentence.find(u"não") == -1:
            
            return (0,'')
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (1,info) 
            
        else:
            return (0,'')
    
    def rule3(self,opinion,useProcessedSentence):
        
        """ Ex: não é um bom político """
        
        info = u'Regra \"[NEG] [VCOP] um [AJD+] [NCLAS] ?Neg\""-> '        
        regex = ur'(\W|^)({0}) ({1}) (um|uma) ({2}) ({3})(\W|$)'.format(self.neg,self.vcop,self.adjsPosRegex,self.nclas)
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return (0,'')
    
    def rule4(self,opinion,useProcessedSentence):
        
        """ Ex: não é um mau político """
        
        info = u'Regra \"[NEG] [VCOP] um [AJD-] [NCLAS] ?Pos\""-> '        
        regex = ur'(\W|^)({0}) ({1}) (um|uma) ({2}) ({3})(\W|$)'.format(self.neg,self.vcop,self.adjsNegRegex,self.nclas)
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        if sentence.find(u"um") == -1 or sentence.find(u"não") == -1:
            
            return (0,'')
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (1,info) 
            
        else:
            return (0,'')
    
    def rule5(self,opinion,useProcessedSentence):
        
        """ Ex: não é um idiota """
        
        info = u'Regra \"[NEG] [VCOP] um [AJD-] ? Pos\""-> '        
        regex = ur'(\W|^)({0}) ({1}) (um|uma) ({2})(\W|$)'.format(self.neg,self.vcop,self.adjsNegRegex)
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        if sentence.find(u"um") == -1 or sentence.find(u"não") == -1:
            
            return (0,'')
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (1,info) 
            
        else:
            return (0,'')
    
    def rule6(self,opinion,useProcessedSentence):
        
        """ Ex: não é um embuste """
        
        info = u'Regra \"[NEG] [VCOP] um [N-] ? Pos\""-> '        
        regex = ur'(\W|^)({0}) ({1}) (um|uma) ({2})(\W|$)'.format(self.neg,self.vcop,self.nounsNegRegex)
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        if sentence.find(u"um") == -1 or sentence.find(u"não") == -1:
            
            return (0,'')
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (1,info) 
            
        else:
            return (0,'')
    
    def rule7(self,opinion,useProcessedSentence):
        
        """ Ex: não foi nada sincero """
        
        info = u'Regra \"[NEG] [VCOP] [QUANT] [Adj+] ? Neg\""-> '        
        regex = ur'(\W|^)({0}) ({1}) ({2}) ({3})(\W|$)'.format(self.neg,self.vcop,self.quant,self.adjsPosRegex)
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        if sentence.find(u"não") == -1:
            
            return (0,'')
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return (0,'')
    
    def rule8(self,opinion,useProcessedSentence):
        
        """ Ex: não é nada parvo """
        
        info = u'Regra \"[NEG] [VCOP] [QUANT] [Adj-] ? Pos\""-> '        
        regex = ur'(\W|^)({0}) ({1}) ({2}) ({3})(\W|$)'.format(self.neg,self.vcop,self.quant,self.adjsNegRegex)
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        if sentence.find(u"não") == -1:
            
            return (0,'')
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (1,info) 
            
        else:
            return (0,'')
    
    def rule9(self,opinion,useProcessedSentence):
        
        """ Ex: não foi coerente """
        
        info = u'Regra \"[NEG] [VCOP] [Adj+] ? Neg\""-> '        
        regex = ur'(\W|^)({0}) ({1}) ({2})(\W|$)'.format(self.neg,self.vcop,self.adjsPosRegex)
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        if sentence.find(u"não") == -1:
            
            return (0,'')
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return (0,'')
        
    def rule10(self,opinion,useProcessedSentence):
        
        """ Ex: não é mentiroso """
        
        info = u'Regra \"[NEG] [VCOP] [Adj-] ? Pos\""-> '        
        regex = ur'(\W|^)({0}) ({1}) ({2})(\W|$)'.format(self.neg,self.vcop,self.adjsNegRegex)
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        if sentence.find(u"não") == -1:
            
            return (0,'')
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (1,info) 
            
        else:
            return (0,'')
    
    def rule11(self,opinion,useProcessedSentence):
        
        """ Ex: não demonstrou um forte empenho """
        
        info = u'Regra \"[NEG] [VSUP] (um+uma) [ADJ+/0] [N+] ? Neg\""-> '        
        regex = ur'(\W|^)({0}) ({1}) (um|uma) ({2}|{3}) ({4})(\W|$)'.format(self.neg,self.vsup,self.adjsPosRegex,self.adjsNeutRegex,self.nounsPosRegex)
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        if sentence.find(u"um") == -1 and sentence.find(u"não") == -1:
            
            return (0,'')
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return (0,'')
    
    def rule12(self,opinion,useProcessedSentence):
        
        """ Ex: não mostrou falta de coragem """
        
        info = u'Regra \"[NEG] [VSUP] falta de [N+] ? Pos\""-> '        
        regex = ur'(\W|^)({0}) ({1}) falta de ({2})(\W|$)'.format(self.neg,self.vsup,self.nounsPosRegex)
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        if sentence.find(u"falta") == -1:
            
            return (0,'')
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (1,info) 
            
        else:
            return (0,'')
    
    def rule13(self,opinion,useProcessedSentence):
        
        """ Ex:  é um político desonesto """
        
        info = u'Regra \"[VCOP] um [NCLAS] [AJD-] ? Neg\""-> '        
        regex = ur'(\W|^)({0}) um ({1}) ({2})(\W|$)'.format(self.vcop,self.nclas,self.adjsNegRegex)
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        if sentence.find(u"um") == -1:
            
            return (0,'')
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return (0,'')
    
    def rule14(self,opinion,useProcessedSentence):
        
        """ Ex:  é um tipo honesto """
        
        info = u'Regra \"[VCOP] um [NCLAS] [AJD+] ? Pos\""-> '        
        regex = ur'(\W|^)({0}) um ({1}) ({2})(\W|$)'.format(self.vcop,self.nclas,self.adjsPosRegex)
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        if sentence.find(u"um") == -1:
            
            return (0,'')
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (1,info) 
            
        else:
            return (0,'')
    
    def rule15(self,opinion,useProcessedSentence):
        
        """ Ex:  é um mau político """
        
        info = u'Regra \"[VCOP] um [AJD-] [NCLAS] ?Neg\""-> '        
        regex = ur'(\W|^)({0}) um ({1}) ({2})(\W|$)'.format(self.vcop,self.adjsNegRegex,self.nclas)
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        if sentence.find(u"um") == -1:
            
            return (0,'')
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return (0,'')
    
    def rule16(self,opinion,useProcessedSentence):
        
        """ Ex:  é um bom político """
        
        info = u'Regra \"[VCOP] um [AJD+] [NCLAS] ?Pos\""-> '        
        regex = ur'(\W|^)({0}) um ({1}) ({2})(\W|$)'.format(self.vcop,self.adjsPosRegex,self.nclas)
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        if sentence.find(u"um") == -1:
            
            return (0,'')
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (1,info) 
            
        else:
            return (0,'')
    
    def rule17(self,opinion,useProcessedSentence):
        
        """ Ex: é um perfeito idiota """
        
        info = u'Regra \"[VCOP] um [AJD+] [AJD-] ? Neg\""-> '        
        regex = ur'(\W|^)({0}) um ({1}) ({2})(\W|$)'.format(self.vcop,self.adjsPosRegex,self.adjsNegRegex)
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        if sentence.find(u"um") == -1:
            
            return (0,'')
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return (0,'')
    
    def rule18(self,opinion,useProcessedSentence):
        
        """ Ex: é um verdadeiro desastre """
        
        info = u'Regra \"[VCOP] um [AJD+] [N-] ? Neg\""-> '        
        regex = ur'(\W|^)({0}) um ({1}) ({2})(\W|$)'.format(self.vcop,self.adjsPosRegex,self.nounsNegRegex)
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        if sentence.find(u"um") == -1:
            
            return (0,'')
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return (0,'')
    
    def rule19(self,opinion,useProcessedSentence):
        
        """ Ex: é um mau perdedor """
        
        info = u'Regra \"[VCOP] um [AJD-] [AJD-] ? Neg\""-> '        
        regex = ur'(\W|^)({0}) um ({1}) ({2})(\W|$)'.format(self.vcop,self.adjsNegRegex,self.adjsNegRegex)
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        if sentence.find(u"um") == -1:
            
            return (0,'')
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return (0,'')
    
    def rule20(self,opinion,useProcessedSentence):
        
        """ Ex: é um idiota """
        
        info = u'Regra \"[VCOP] um [AJD-] ? Neg\""-> '        
        regex = ur'(\W|^)({0}) um ({1})(\W|$)'.format(self.vcop,self.adjsNegRegex)
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        if sentence.find(u"um") == -1:
            
            return (0,'')
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return (0,'')
    
    def rule21(self,opinion,useProcessedSentence):
        
        """ Ex: é um embuste """
        
        info = u'Regra \"[VCOP] um [N-] ? Neg\""-> '        
        regex = ur'(\W|^)({0}) um ({1})(\W|$)'.format(self.vcop,self.nounsNegRegex)
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        if sentence.find(u"um") == -1:
            
            return (0,'')
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return (0,'')
    
    def rule22(self,opinion,useProcessedSentence):
        
        """ Ex: é muito parvo """
        
        info = u'Regra \"[VCOP] [QUANT] [Adj-] ? Pos\""-> '        
        regex = ur'(\W|^)({0}) ({1}) ({2})(\W|$)'.format(self.vcop,self.quant,self.adjsNegRegex)
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return (0,'')
    
    def rule23(self,opinion,useProcessedSentence):
        
        """ Ex: foi extremamente sincero """
        
        info = u'Regra \"[VCOP] [QUANT] [Adj+] ? Pos\""-> '        
        regex = ur'(\W|^)({0}) ({1}) ({2})(\W|$)'.format(self.vcop,self.quant,self.adjsPosRegex)
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (1,info) 
            
        else:
            return (0,'')    
    
    def rule24(self,opinion,useProcessedSentence):
        
        """ Ex: é mentiroso """
        
        info = u'Regra \"[VCOP] [Adj-] ? Neg\""-> '        
        regex = ur'(\W|^)({0}) ({1})(\W|$)'.format(self.vcop,self.adjsNegRegex)
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return (0,'')
    
    def rule25(self,opinion,useProcessedSentence):
        
        """ Ex: foi coerente """
        
        info = u'Regra \"[VCOP] [Adj+] ? Pos\""-> '        
        regex = ur'(\W|^)({0}) ({1})(\W|$)'.format(self.vcop,self.adjsPosRegex)
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (1,info) 
            
        else:
            return (0,'')        
    
    def rule26(self,opinion,useProcessedSentence):
        
        """ Ex: o idiota do Sócrates """
        
        target = opinion.mention.lower()
        
        info = u'Regra \"o [ADJ-] do TARGET ? Neg\""-> '        
        regex = ur'(\W|^)o ({0}) do {1}(\W|$)'.format(self.adjsNegRegex,target)
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        if sentence.find(u"do") == -1:
            
            return (0,'')
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return (0,'')  
        
    def rule29(self,opinion,useProcessedSentence):
        
        """ Ex: demonstrou uma enorme arrogância """
        
        info = u'Regra \"[VSUP] (um+uma+0) [ADJ+/0] [N-] ? Neg\""-> '        
        regex = ur'(\W|^)({0}) (um|uma) ({1}|{2}) ({3})(\W|$)'.format(self.vsup,self.adjsPosRegex,self.adjsNeutRegex,self.nounsNegRegex)
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        if sentence.find(u"um") == -1:
            
            return (0,'')
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return (0,'')
    
    def rule30(self,opinion,useProcessedSentence):
        
        """ Ex: demonstrou (uma|0) alta coragem """
        
        info = u'Regra \"[VSUP] (um+uma+0) [ADJ+/0] [N+] ? Neg\""-> '        
        regex = ur'(\W|^)({0}) ((um|uma) )?({1}|{2}) ({3})(\W|$)'.format(self.vsup,self.adjsPosRegex,self.adjsNeutRegex,self.nounsPosRegex)
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (1,info) 
            
        else:
            return (0,'')
    
    def rule31(self,opinion,useProcessedSentence):
            
        """ Ex: não engana OU não agiu de má-fé """
        
        info = u'Regra \"[NEG]\nunca [V-]\[IDIOM-] ? Pos\""-> '        
        regex = ur'(\W|^)(({0})|nunca) ({1}|{2})(\W|$)'.format(self.neg,self.idiomNegRegex,self.verbNegRegex)
    
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        if sentence.find(u"não") == -1 and sentence.find(u"nunca") == -1: 
            
            return (0,'')
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (1,info) 
            
        else:
            return (0,'')

    def rule32(self,opinion,useProcessedSentence):
        
        """ Ex: não está a mentir """
        
        info = u'Regra \"[NEG]/nunca [VCOP] a [V-] ? Pos\""-> '        
        regex = ur'(\W|^)(({0})|nunca) ({1}) a ({2})(\W|$)'.format(self.neg,self.vcop,self.verbNegRegex)
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        if sentence.find(u"não") == -1 and sentence.find(u"nunca") == -1: 
            
            return (0,'')
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (1,info) 
            
        else:
            return (0,'')



    def rule33(self,opinion,useProcessedSentence):
        
        """ Ex: não brilhou OU não agiu da boa-fé """
        
        info = u'Regra \"[NEG]/nunca [V+]/[IDIOM+] ? Neg\""-> '        
        regex = ur'(\W|^)(({0})|nunca) ({1}|{2})(\W|$)'.format(self.neg,self.verbPosRegex,self.idiomPosRegex)
              
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        if sentence.find(u"não") == -1 and sentence.find(u"nunca") == -1: 
            
            return (0,'')
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return (0,'')


    def rule34(self,opinion,useProcessedSentence):
        
        """ Ex: não se atrapalhou OU não se espetou ao comprido """
        
        info = u'Regra \"[NEG]/nunca se [V-]/[IDIOM-] ? Pos\""-> '        
        regex = ur'(\W|^)(({0})|nunca) se ({1}|{2})(\W|$)'.format(self.neg,self.verbNegRegex,self.idiomNegRegex)
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        if sentence.find(u"não") == -1 and sentence.find(u"nunca") == -1: 
            
            return (0,'')
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (1,info) 
            
        else:
            return (0,'')


    def rule35(self,opinion,useProcessedSentence):
        
        """ Ex: não|nunca se sacrificar OU não se saiu bem"""
        
        info = u'Regra \"[NEG]/nunca se [V+]/[IDIOM+] ? Neg\""-> '        
        regex = ur'(\W|^)(({0})|nunca) se ({1}|{2})(\W|$)'.format(self.neg,self.verbPosRegex,self.idiomPosRegex)
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        if sentence.find(u"não") == -1 and sentence.find(u"nunca") == -1: 
            
            return (0,'')
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return (0,'')

    def rule37(self,opinion,useProcessedSentence):
        
        """ Ex: não ter (muita|0) contestação """
        
        info = u'Regra \"[NEG] [VSUP] [QUANT/0] [N-] ? Pos\""-> '
        regex = ur'(\W|^)({0}) ({1}) (({2}) )?({3})(\W|$)'.format(self.neg,self.vsup,self.quant,self.nounsNegRegex)
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        if sentence.find(u"não") == -1: 
            
            return (0,'')
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (1,info) 
            
        else:
            return (0,'')        
   

    def rule38(self,opinion,useProcessedSentence):
        
        """ Ex: não ter (muito|0) talento """
        
        info = u'Regra \"[NEG] [VSUP] [QUANT/0] [N+] ? Neg\""-> '
        regex = ur'(\W|^)({0}) ({1}) (({2}) )?({3})(\W|$)'.format(self.neg,self.vsup,self.quant,self.nounsPosRegex)
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        if sentence.find(u"não") == -1: 
            
            return (0,'')
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return (0,'')       


    def rule39(self,opinion,useProcessedSentence):
        
        """ Ex: ter (muita|0) coragem"""
        
        info = u'Regra \"[VSUP] [QUANT/0] [N+] ? Pos\""-> ' 
        regex = ur'(\W|^)({0}) (({1}) )?({2})(\W|$)'.format(self.vsup,self.quant,self.nounsPosRegex)
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (1,info) 
            
        else:
            return (0,'') 
      

    def rule40(self,opinion,useProcessedSentence):
        
        """ Ex: ter (muito|0) medo"""
        
        info = u'Regra \"[VSUP] [QUANT/0] [N-] ? Neg\""-> '
        regex = ur'(\W|^)({0}) (({1}) )?({2})(\W|$)'.format(self.vsup,self.quant,self.nounsNegRegex)
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return (0,'')        


    def rule41(self,opinion,useProcessedSentence):
        
        """ Ex: excesso/falta de coragem"""
        
        info = u'Regra \"falta de [N+] ? Neg\""-> ' 
        regex = ur'(\W|^)(falta|excesso) de ({0})(\W|$)'.format(self.nounsPosRegex)
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        if sentence.find(u"falta") == -1 and sentence.find(u"excesso") == -1: 
            
            return (0,'')
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return (0,'')  

                
    setOfRules = [hasNickName,hasInterjectionWithTarget,hasInterjection,hasLol,hasHehe,hasHeavyPunctuation,
                  hasSmiley,hasQuotedSentiment,rule4,rule3,rule2,rule1,rule12,rule11,rule14,rule5,rule13,rule16,rule15,
                  rule17,rule18,rule19,rule6,rule8,rule7,rule30,rule29,rule37,rule38,rule39,rule40,        
                  rule10,rule9,rule20,rule21,rule23,rule22,rule25,rule24,rule26,rule32,rule31,rule34,rule35,rule33, rule41]                    
    
def testInterjectionTarget():
    
    sentenceNoMatch = u"O sócrates e passos coelho são bff"
    
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
    
    ruler = getTestRuler()
    
    for s in interjecTargetSentences:
    
        o = Opinion(1,s,u"socrates",u"sócrates",0,None,u"Manual",u"Manual",None)
        
        v = ruler.hasInterjectionWithTarget(o)
        
        print s, "->", v 
        print "------------------"

def testInterjection():
    
    sentenceNoMatch = u"O sócrates e passos coelho são bff"
   
    interjectionSentences = [sentenceNoMatch,                               
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
                               u"Uuuuuui O sócrates e passos coelho são bff!" ,
                               u"Vai Abaixo! O sócrates e passos coelho são bff!",
                               u"Vai Fora! O sócrates e passos coelho são bff!",
                               u"Para Rua! O sócrates e passos coelho são bff!",
                               u"Safa!  O sócrates e passos coelho são bff!",
                               u"Basta! O sócrates e passos coelho são bff!",
                               u"Cruzes! O sócrates e passos coelho são bff!",
                               u"Passou-se!  O sócrates e passos coelho são bff!",
                               u"Livra! O sócrates e passos coelho são bff!",
                               u"Estamos feitos! O sócrates e passos coelho são bff!",
                               u"Fogo! O sócrates e passos coelho são bff!"
                               
                               ]                          
                                                                        
    ruler = getTestRuler()
    
    for sentence in interjectionSentences:
    
        o = Opinion(1,sentence,u"socrates",u"sócrates",0,None,u"Manual",u"Manual",None)
        
        v = ruler.hasInterjection(o,False)        
        
        print sentence, "->", v 
        print "------------------"

def testLOL():
    
    sentenceNoMatch = u"O sócrates e passos coelho são bff"
    
    lolSentences = [sentenceNoMatch,
                    u"O sócrates e passos coelho são bff lol",
                    u"O sócrates e passos coelho são bff lololoooool",
                    u"O sócrates e passos coelho são bff lolo"
                   ] 
    
    ruler = getTestRuler()
    
    for sentence in lolSentences:
    
        o = Opinion(1,sentence,u"socrates",u"socras",0,None,u"Manual",u"Manual",None)
        
        v = ruler.hasLol(o)
        
        print sentence, "->", v 
        print "------------------"

def testQuotedSentiment():
    
    sentenceNoMatch = u"O sócrates e passos coelho são bff"
    
    quotedSentences = [sentenceNoMatch,
                        u"O sócrates e passos são \"bons\" politicos",
                        u"O sócrates é um \"gajo bem bonito\" acho eu"                   
                      ] 
    
    ruler = getTestRuler()
    
    for sentence in quotedSentences:
    
        o = Opinion(1,sentence,u"socrates",u"socras",0,None,u"Manual",u"Manual",None)
        
        v = ruler.hasQuotedSentiment(o,False)
        
        print sentence, "->", v 
        print "------------------"

def testHaha():
    
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
    
    ruler = getTestRuler()
    
    for sentence in heheSentences:
    
        o = Opinion(1,sentence,u"socrates",u"socras",0,None,u"Manual",u"Manual",None)
        
        v = ruler.hasHehe(o)
        
        print sentence, "->", v 
        print "------------------"

def testSmiley():
    
    sentenceNoMatch = u"O sócrates e passos coelho são bff"
    
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
    
    ruler = getTestRuler()
    
    for s in smileySentences:
    
        o = Opinion(1,s,u"socrates",u"socras",0,None,u"Manual",u"Manual",None)
        
        v = ruler.hasSmiley(o)
        
        
        print s, "->", v 
        print "------------------"

def testHeavyPunct():
     
    sentenceNoMatch = u"O sócrates e passos coelho são bff"
    
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
    ruler = getTestRuler()
    
    for sentence in heavyPunctSentences:
    
        o = Opinion(1,sentence,u"socrates",u"socras",0,None,u"Manual",u"Manual",None)
        
        v = ruler.hasHeavyPunctuation(o)
        
        print sentence, "->", v 
        print "------------------"

def testSintaticRules():
    
    ruler = getTestRuler()
    
    sentenceNoMatch = u"O sócrates e passos coelho são bff"    
    
    s1 = [ruler.rule1,[sentenceNoMatch,0],[u" o sócrates não é uma pessoa honesta ",-1],[u"o sócrates não é uma pessoa honesta",-1]]
    s2 = [ruler.rule2,[sentenceNoMatch,0],[u" o sócrates não é um tipo autoritário ",1],[u"o sócrates não é um tipo autoritário",1]]
    s3 = [ruler.rule3,[sentenceNoMatch,0],[u" o sócrates não é um bom político ",-1]]
    s4 = [ruler.rule4,[sentenceNoMatch,0],[u" o sócrates não é um mau político ",1]]
    s5 = [ruler.rule5,[sentenceNoMatch,0],[u" o sócrates não é um idiota ",1]]
    s6 = [ruler.rule6,[sentenceNoMatch,0],[u" o sócrates não é um embuste ",1]] 
    s7 = [ruler.rule7,[sentenceNoMatch,0],[u" o sócrates não foi nada sincero ",-1]]
    s8 = [ruler.rule8,[sentenceNoMatch,0],[u" o sócrates não é nada parvo ",1]]
    s9 = [ruler.rule9,[sentenceNoMatch,0],[u" o sócrates não foi coerente ",-1]]
    s10 = [ruler.rule10,[sentenceNoMatch,0],[u" o sócrates não é mentiroso ",1]]
    s11 = [ruler.rule11,[sentenceNoMatch,0],[u" o sócrates não demonstrou um forte empenho ",-1]]
    s12 = [ruler.rule12,[sentenceNoMatch,0],[u" o sócrates não mostrou falta de coragem ",1]]
    s13 = [ruler.rule13,[sentenceNoMatch,0],[u" o sócrates é um político desonesto ",-1]]
    s14 = [ruler.rule14,[sentenceNoMatch,0],[u" o sócrates é um tipo honesto ",1]]
    s15 = [ruler.rule15,[sentenceNoMatch,0],[u" o sócrates é um mau político ",-1]]
    s16 = [ruler.rule16,[sentenceNoMatch,0],[u" o sócrates é um bom político ",1]]
    s17 = [ruler.rule17,[sentenceNoMatch,0],[u" o sócrates é um perfeito idiota ",-1]]
    s18 = [ruler.rule18,[sentenceNoMatch,0],[u" o sócrates é um verdadeiro desastre ",-1]]
    s19 = [ruler.rule19,[sentenceNoMatch,0],[u" o sócrates é um mau perdedor ",-1]]
    s20 = [ruler.rule20,[sentenceNoMatch,0],[u" o sócrates é um idiota ",-1]]
    s21 = [ruler.rule21,[sentenceNoMatch,0],[u" o sócrates é um embuste ",-1]]
    s22 = [ruler.rule22,[sentenceNoMatch,0],[u" o sócrates é muito parvo ",-1]]
    s23 = [ruler.rule23,[sentenceNoMatch,0],[u" o sócrates foi extremamente sincero ",1]]
    s24 = [ruler.rule24,[sentenceNoMatch,0],[u" o sócrates é mentiroso ",-1]]
    s25 = [ruler.rule25,[sentenceNoMatch,0],[u" o sócrates foi coerente ",1]]
    s26 = [ruler.rule26,[sentenceNoMatch,0],[u" o idiota do sócrates ",-1]]
    #s27 = [ruler.rule27,[sentenceNoMatch,0],[u" o sócrates revelou uma enorme falta de respeito ",-1]]
    #s28 = [ruler.rule28,[sentenceNoMatch,0],[u" o sócrates tem falta de coragem ",-1]]
    s29 = [ruler.rule29,[sentenceNoMatch,0],[u" o sócrates demonstrou uma enorme arrogância ",-1]]
    s30 = [ruler.rule30,[sentenceNoMatch,0],[u" o sócrates demonstrou uma alta coragem ",1],[u" o sócrates demonstrou alta coragem ",1],[u" o sócrates demonstrou um alto empenho ",1]]    
    s31 = [ruler.rule31,[sentenceNoMatch,0],[u" o sócrates não engana ",1],[u" o sócrates não agiu de má-fé ",1]]
    s32 = [ruler.rule32,[sentenceNoMatch,0],[u" o sócrates não está a papaguear ",1]]
    s33 = [ruler.rule33,[sentenceNoMatch,0],[u" o sócrates não brilhou ",-1],[u" o sócrates não agiu de boa-fé ",-1]]
    s34 = [ruler.rule34,[sentenceNoMatch,0],[u" o sócrates não se atrapalhou ",1],[u" o sócrates não espetou-se ao comprido ",1]]
    s35 = [ruler.rule35,[sentenceNoMatch,0],[u" o sócrates não se sacrificou ",-1],[u" o sócrates não saiu-se bem ",-1]]
    s37 = [ruler.rule37,[sentenceNoMatch,0],[u" o sócrates não tem muita susceptibilidade ",1],[u" o sócrates não tem susceptibilidade ",1]]
    s38 = [ruler.rule38,[sentenceNoMatch,0],[u" o sócrates não tem muito talento ",-1],[u" o sócrates não tem talento ",-1]]
    s39 = [ruler.rule39,[sentenceNoMatch,0],[u" o sócrates tem muita coragem ",1],[u" o sócrates tem coragem ",1]]   
    s40 = [ruler.rule40,[sentenceNoMatch,0],[u" o sócrates tem muito medo ",-1],[u" o sócrates tem medo ",-1]]
    s41 = [ruler.rule41,[sentenceNoMatch,0],[u" o sócrates tem falta de coragem ",-1],[u" o sócrates tem falta de alegria ",-1],[u" o sócrates tem excesso de confiança ",-1]]
    
    testCases = [s30]
    
    testCases = [s1,
             s2,
             s3,
             s4,
             s5,
             s6,
             s7,
             s8,
             s9,
             s10,
             s11,
             s12,
             s13,
             s14,
             s15,
             s16,
             s17,
             s18,
             s19,
             s20,
             s21,
             s22,
             s23,
             s24,
             s25,
             s26,
             s29,
             s30,
             s31,
             s32,
             s33,
             s34,
             s35,
             s37,
             s38,
             s39,
             s40,
             s41]
    
    failures = []
    
    for test in testCases:
        
        rule = test[0]
        
        for t in test[1:]:
            
            o = Opinion(1,t[0],u"socrates",u"sócrates",0,None,u"Manual",u"Manual",None)
            res = rule(o,False)
            
            if res[0] != t[1]:
                failures.append((rule,unicode(t[0]),t[1],res[0]))
    
    
    if len(failures) > 0:
        
        print str(len(failures))," errors\n"
        
        for ff in failures:
            print ff[0]," :: ", ff[1]
            print "expect:", str(ff[2])," got:", str(ff[3])
            print "\n--------------------\n"
    else:
        print "All ok!"
    
def getTestRuler():

    politiciansFile = "../Resources/politicians.txt"
    sentiTokensFile = "../Resources/SentiLex-flex-PT02.txt"
    exceptTokensFile = "../Resources/SentiLexAccentExcpt.txt"
    
    politicians = Persons.loadPoliticians(politiciansFile)
    sentiTokens = SentiTokens.loadSentiTokens(sentiTokensFile,exceptTokensFile)
    
    return Rules(politicians,sentiTokens)    

def getMultiWordsHandler():
    
    politiciansFile = "../Resources/politicians.txt"
    sentiTokensFile = "../Resources/SentiLex-flex-PT02.txt"
    exceptTokensFile = "../Resources/SentiLexAccentExcpt.txt"
    multiWordsFile = "../Resources/multiwords.txt"
    
    politicians = Persons.loadPoliticians(politiciansFile)
    sentiTokens = SentiTokens.loadSentiTokens(sentiTokensFile,exceptTokensFile)
        
    multiWordTokenizer = MultiWordHandler(multiWordsFile)
    multiWordTokenizer.addMultiWords(Persons.getMultiWords(politicians))
    multiWordTokenizer.addMultiWords(SentiTokens.getMultiWords(sentiTokens))    
    
    return multiWordTokenizer

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
    
    testSintaticRules()
    
    print "Done!"
