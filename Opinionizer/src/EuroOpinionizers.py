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
import Preprocessor
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

    def inferTarget2(self,opinion):
        
        """ 
            Tries to identify mentions of the targets in a message
            Params: opinion -> Opinion object
            Returns: tuple(inferred target, algorithm metadata)
        """
       
        info = u"Targets: "
        specialChars = u' “”\"@)(!#;&:\\@/-_,?.«»\'~ ' 
        sentence = Preprocessor.separateSpecialSymbols(opinion.sentence.lower()) 
        print sentence
        
        matches = []
        
        for person in self.persons:            
            
            for name in person.names:
                                   
                if sentence.find(" "+name+" ") != -1:
                    
                    matches.append(name)
            
            for nickName in person.nicknames:
                    
                if sentence.find(" "+nickName+" ") != -1:
                    
                    matches.append(nickName)
                    
            for ergo in person.ergos:
                
                if sentence.find(" "+ergo+" ") != -1:
                    
                    matches.append(ergo)                
            
        targets = {}
        
        for mention in matches:
            
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
            
            if result[0] != 0:
             
                info = opinion.metadata + ">>" + result[1]
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
    
    def genConditionalFeatureSet(self,opinion,useProcessedSentence):
        
        featureSet = []
        
        for rules in self.clusterOfRules:
            
            match = False
            
            for rule in rules:
                
                if not match:
                    result = rule(self,opinion,useProcessedSentence)
                
                    if result[0] != 0:
                        match = True
                        featureSet.append(result[0])
                    else:
                        featureSet.append(0)
                else:
                    print "rule already matched...", rule
                    featureSet.append(0)
                    
        return featureSet
    
    def hasPosInterjection(self,opinion,useProcessedSentence):         
                         
        info = "Positive Interjection: "        

        regex = ur'(\W|^)(g+o+l+o+|f+o+r[cç]+a+|b+r+a+v+o+|b+o+a+|l+i+n+d+o+|f+i+x+e+|m(ui)?to+ b[eo]+m+|co+ra+ge+m|v+i+v+a+|v+a+i+|v+a+m+o+s+( l[aá]+)?|bo+ra+ l[aá]+|e+spe+t[aá]+cu+lo+|u+a+u+|y+e+s+|l+o+v+e+|l+i+k+e+|n+i+c+e+|g+o+a+l+|t+h+a+n+k+s+|o+b+r+i+g+a+d+o+|sco+re+d?)!+(\W|$)'        
               
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        if sentence.find(u"!") == -1: 
            
            return (0,'')
        
        match = re.search(regex,sentence)
    
        if match != None:
            
            info += match.group()
            
            return (1,info) 
            
        else:
            return (0,'')

    def hasNegInterjection(self,opinion,useProcessedSentence):         
                         
        info = "Positive Interjection: "        
        regex = ur'(\W|^)(j[aá]+ fo+mo+s|que+ ma+u+|fo+sga-se|j[áa]+ che+ga+|so+co+rro+|u+i+|a+i+|o+h+|i+rr+a+|a+pre+|ra+i+o+s|mandem-no embora|sa+i da+[íi]+|tirem-no da[ií]|da+ss+|fo+ra+|m+e+r+d+a+|f+o+d+a+-*s+e*|(es)?t[áa] fdd|que no+jo+|cre+do+|(oh)?meu deus|u+i+|li+vra+|va+i+ a+ba+i+xo+|fo+ra+|(pa+ra+ a )?ru+a+|sa+fa+|cru+ze+s|pa+sso+u+-se|ba+sta+|fo+go+|esta+mo+s fe+i+to+s) ?!+(\W|$)'
                
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        if sentence.find(u"!") == -1: 
            
            return (0,'')
        
        match = re.search(regex,sentence)
    
        if match != None:
            
            info += match.group()
            
            return (-1,info) 
            
        else:
            return (0,'')
        
   
    def hasPosSmiley(self,opinion,useProcessedSentence): 
        
        info = "Smiley: "        
        regex = ur'(\W|^)[\=:x8]-?[\)d\]]+(\W|$)'
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        match = re.search(regex,sentence)
    
        if match != None:
            
            info += match.group().upper()
            
            return (1,info)            
        else:
            return (0,'') 
   
    def hasNegSmiley(self,opinion,useProcessedSentence): 
        
        info = "Smiley: "        
        regex = ur'(\W|^)[\=:x8]-?[\[\(s]+(\W|$)'
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        match = re.search(regex,sentence)
    
        if match != None:
            
            info += match.group().upper()
            
            return (-1,info)            
        else:
            return (0,'')
         
    def hasNegIdiomExpression(self,opinion,useProcessedSentence): 
        
        info = "[IDIOM-]"        
        regex = ur'(\W|^)({0})(\W|$)'.format(self.idiomNegRegex)
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        match = re.search(regex,sentence)
    
        if match != None:
            
            info += match.group().upper()
            
            return (-1,info)            
        else:
            return (0,'')  
        
    def hasPosIdiomExpression(self,opinion,useProcessedSentence): 
        
        info = "[IDIOM+]"        
        regex = ur'(\W|^)({0})(\W|$)'.format(self.idiomPosRegex)
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        match = re.search(regex,sentence)
    
        if match != None:
            
            info += match.group().upper()
            
            return (1,info)            
        else:
            return (0,'')
            
    def hasQuotedSentiment(self,opinion,useProcessedSentence): 
        
        info = "Quoted sentiment: "        
        regex = ur'(\W|^)\"\W?({0}|{1})\W\?"(\W|$)'.format(self.adjsPosRegex,self.nounsPosRegex)
        
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
        
    def hasHeavyPunctuation(self,opinion,useProcessedSentence): 
        
        info = "Heavy Punctuation: "        
        regex = r'(\W|^)(!+\?+)|(\?+!+)(\W|$)'
        
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
    
    def rule1(self,opinion,useProcessedSentence):
        
        """ Ex: não é uma pessoa honesta """
        
        info = u'Regra \"[NEG] [VCOP] um/uma [NCLAS] [AJD+] ? Neg\"-> '        
        regex = ur'(\W|^)({0}) ({1}) (um|uma) ({2}) ({3})(\W|$)'.format(self.neg,self.vcop,self.nclas,self.adjsPosRegex)
        
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
        
    def rule2(self,opinion,useProcessedSentence):
        
        """ Ex: não é um tipo autoritário """
        
        info = u'Regra \"[NEG] [VCOP] um [NCLAS] [AJD-] ? Pos"\"-> '        
        regex = ur'(\W|^)({0}) ({1}) (um|uma) ({2}) ({3})(\W|$)'.format(self.neg,self.vcop,self.nclas,self.adjsNegRegex)
        
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
    
    def rule3(self,opinion,useProcessedSentence):
        
        """ Ex: não é um bom político """
        
        info = u'Regra \"[NEG] [VCOP] um [AJD+] [NCLAS] ?Neg\""-> '        
        regex = ur'(\W|^)({0}) ({1}) (um|uma) ({2}) ({3})(\W|$)'.format(self.neg,self.vcop,self.adjsPosRegex,self.nclas)
        
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
    
    def rule4(self,opinion,useProcessedSentence):
        
        """ Ex: não é um mau político """
        
        info = u'Regra \"[NEG] [VCOP] um [AJD-] [NCLAS] ?Pos\""-> '        
        regex = ur'(\W|^)({0}) ({1}) (um|uma) ({2}) ({3})(\W|$)'.format(self.neg,self.vcop,self.adjsNegRegex,self.nclas)
        
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
    
    def rule5(self,opinion,useProcessedSentence):
        
        """ Ex: não é um idiota """
        
        info = u'Regra \"[NEG] [VCOP] um [AJD-] ? Pos\""-> '        
        regex = ur'(\W|^)({0}) ({1}) (um|uma) ({2})(\W|$)'.format(self.neg,self.vcop,self.adjsNegRegex)
        
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
    
    def rule6(self,opinion,useProcessedSentence):
        
        """ Ex: não é um embuste """
        
        info = u'Regra \"[NEG] [VCOP] um [N-] ? Pos\""-> '        
        regex = ur'(\W|^)({0}) ({1}) (um|uma) ({2})(\W|$)'.format(self.neg,self.vcop,self.nounsNegRegex)
        
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
    
    def rule7(self,opinion,useProcessedSentence):
        
        """ Ex: não foi nada sincero """
        
        info = u'Regra \"[NEG] [VCOP] [QUANT] [Adj+] ? Neg\""-> '        
        regex = ur'(\W|^)({0}) ({1}) ({2}) ({3})(\W|$)'.format(self.neg,self.vcop,self.quant,self.adjsPosRegex)
        
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
    
    def rule8(self,opinion,useProcessedSentence):
        
        """ Ex: não é nada parvo """
        
        info = u'Regra \"[NEG] [VCOP] [QUANT] [Adj-] ? Pos\""-> '        
        regex = ur'(\W|^)({0}) ({1}) ({2}) ({3})(\W|$)'.format(self.neg,self.vcop,self.quant,self.adjsNegRegex)
        
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
    
    def rule9(self,opinion,useProcessedSentence):
        
        """ Ex: não foi coerente """
        
        info = u'Regra \"[NEG] [VCOP] [Adj+] ? Neg\""-> '        
        regex = ur'(\W|^)({0}) ({1}) ({2})(\W|$)'.format(self.neg,self.vcop,self.adjsPosRegex)
        
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
        
    def rule10(self,opinion,useProcessedSentence):
        
        """ Ex: não é mentiroso """
        
        info = u'Regra \"[NEG] [VCOP] [Adj-] ? Pos\""-> '        
        regex = ur'(\W|^)({0}) ({1}) ({2})(\W|$)'.format(self.neg,self.vcop,self.adjsNegRegex)
        
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
    
    def rule11(self,opinion,useProcessedSentence):
        
        """ Ex: não demonstrou um forte empenho """
        
        info = u'Regra \"[NEG] [VSUP] (um+uma) [ADJ+/0] [N+] ? Neg\""-> '        
        regex = ur'(\W|^)({0}) ({1}) (um|uma) ({2}|{3}) ({4})(\W|$)'.format(self.neg,self.vsup,self.adjsPosRegex,self.adjsNeutRegex,self.nounsPosRegex)
        
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
    
    def rule12(self,opinion,useProcessedSentence):
        
        """ Ex: não mostrou falta de coragem """
        
        info = u'Regra \"[NEG] [VSUP] (falta|excesso) de [N+] ? Pos\""-> '        
        regex = ur'(\W|^)({0}) ({1}) (falta|excesso) de ({2})(\W|$)'.format(self.neg,self.vsup,self.nounsPosRegex)
        
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
        
        info = u'Regra \"[VCOP] um [AJD+|0] [AJD-] ? Neg\""-> '        
        regex = ur'(\W|^)({0}) um ({1}|{2}) ({3})(\W|$)'.format(self.vcop,self.adjsPosRegex,self.adjsNeutRegex,self.adjsNegRegex)
        
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
        
        info = u'Regra \"[VCOP] um [AJD+|0] [N-] ? Neg\""-> '        
        regex = ur'(\W|^)({0}) um ({1}|{2}) ({3})(\W|$)'.format(self.vcop,self.adjsPosRegex,self.adjsNeutRegex,self.nounsNegRegex)
        
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

    
        
    def rule42(self,opinion,useProcessedSentence):
        
        info= u'culpa|culpado é|foi do|o [TARGET]'
        regex = ur'(\W|^)(culpa|culpado) {0} (o|a|do|da)? {1}(\W|$)'.format(self.vcop,opinion.mention)
        
        if useProcessedSentence:
            sentence = opinion.processedSentence.lower()
        else:
            sentence = opinion.sentence.lower()
        
        if sentence.find(u"culpa") == -1 and sentence.find(u"culpado") == -1:
            
            return (0,'')
         
        match = re.search(regex,sentence)
        
        if match != None:
            
            info += match.group() 
            
            return (-1,info) 
            
        else:
            return (0,'')
    
    setOfRules = [hasPosInterjection,hasNegInterjection,hasPosSmiley,
                  hasNegSmiley,rule31,hasPosIdiomExpression,hasNegIdiomExpression,
                  rule33,rule1,rule14,rule2,
                  rule13,rule3,rule16,rule4,rule15,rule5,rule20,rule6,
                  rule21,rule7,rule23,rule8,rule22,rule9,rule25,rule10,
                  rule24,rule11,rule30,rule12,rule41,rule17,rule18,rule19,
                  rule26,rule29,rule32,rule34,rule35,rule37,rule40,                  
                  rule38,rule39,rule42,hasHeavyPunctuation,hasQuotedSentiment]
    
    clusterOfRules = [[hasHeavyPunctuation],
                      [hasPosIdiomExpression],[hasNegIdiomExpression],[hasNegSmiley],
                      [hasPosSmiley],[hasNegInterjection],[hasPosInterjection],
                      [hasQuotedSentiment],[rule26],[rule32],[rule31],[rule34],
                      [rule17],[rule12],[rule29],[rule18],[rule19],[rule35], 
                      [rule33],[rule41],[rule42],[rule1,rule14],[rule2,rule13],
                      [rule3,rule16],[rule4,rule15],[rule5,rule20],[rule6,rule21],
                      [rule7,rule23],[rule8,rule22],[rule9,rule25],[rule10,rule24],
                      [rule11,rule30],[rule37,rule40],[rule38,rule39]]
        
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
                               u"Foda-se!",
                               u"Fooooda-se!",
                               u"Foooodaaaa-se!",
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
        
        v = ruler.hasSmiley(o,False)
        
        
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
    
    s1 = [ruler.rule1,[sentenceNoMatch,0],[u" o sócrates não é uma pessoa honesta ",-1],[u"o sócrates não é uma pessoa honesta",-1],[u"o sócrates não é uma tipo honesto",-1]]
    s2 = [ruler.rule2,[sentenceNoMatch,0],[u" o sócrates não é um tipo autoritário ",1],[u"o sócrates não é uma tipo autoritário",1]]
    s3 = [ruler.rule3,[sentenceNoMatch,0],[u" o sócrates não é um bom político ",-1],[u" o sócrates ñ é um bom político ",-1]]
    s4 = [ruler.rule4,[sentenceNoMatch,0],[u" o sócrates não é um mau político ",1]]
    s5 = [ruler.rule5,[sentenceNoMatch,0],[u" o sócrates não é um idiota ",1],[u" o sócrates n é um idiota ",1]]
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
    s29 = [ruler.rule29,[sentenceNoMatch,0],[u" o sócrates demonstrou uma alta arrogância ",-1]]
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
    s42 = [ruler.rule42,[sentenceNoMatch,0],[u"a culpa foi do sócrates",-1],[u" o culpado é o sócrates",-1]]
    
    shasPosInterjection = [ruler.hasPosInterjection,[sentenceNoMatch,0],[u'força!',1],[u'fooorça!',1],[u'fooorçaaaaa!',1],[u'braaaavo!',1],
                                                    [u'brrraaaavoooo!',1],[u'bravoooooo!',1],[u'boa!',1],[u'boooaaaa!',1],[u'booooooa!',1],
                                                    [u'lindo!',1],[u'lindoooo!',1],[u'liiiinnndooooo!',1],[u'fixe!',1],[u'fixeeeee!',1],
                                                    [u'fiiiiiiixe!',1],[u'muito bem!',1],[u'muitoooo bem!',1],[u'muito bom!',1],
                                                    [u'mto bem!',1],[u'mtoooo beeeeeem!',1],[u'mto boooom!',1],
                                                    [u'coragem!',1],[u'coraaaaagem!',1],[u'cooooraagem!',1],
                                                    [u'viva!',1],[u'vivaaaaa!',1],[u'viiivaaaa!',1],
                                                    [u'vai!',1],[u'vaaaaai!',1],[u'vaaaiiiiii!',1],
                                                    [u'vamos!',1],[u'vaaaamooooos!',1],[u'vaaamos!',1],
                                                    [u'vamos lá!',1],[u'vamos laaaa!',1],[u'vaaaamos láááá!',1],
                                                    [u'bora lá!',1],[u'boooooraa lá!',1],[u'bora laaaa!',1],
                                                    [u'espetáculo!',1],[u'espetáááácuuuloo!',1],[u'espetaaaaculooo!',1],
                                                    [u'uau!',1],[u'uuuuauuuu!',1],[u'uaaaau!',1],
                                                    [u'yes!',1],[u'yeeeees!',1],[u'yessss!',1],
                                                    [u'love!',1],[u'looooove!',1],[u'loooooveeeee!',1],
                                                    [u'like!',1],[u'liiiiike!',1],[u'liiiiikeeee!',1],
                                                    [u'nice!',1],[u'niiiiiice!',1],[u'niceeeee!',1],
                                                    [u'goal!',1],[u'gooooooal!',1],[u'gooooaaaaal!',1],
                                                    [u'scored!',1],[u'scooooored!',1],[u'score!',1]]         

 
    shasNegInterjection = [ruler.hasNegInterjection,[sentenceNoMatch,0],                               
                                                   [u"Foda-se!",-1],
                                                   [u"Fooooda-se!",-1],
                                                   [u"Foooodaaaa-se!",-1],
                                                   [u"Foooodaaaase!",-1],
                                                   [u"Foooodaaaasssse!",-1],
                                                   [u"Foooodaaaa-seee!",-1],
                                                   [u"merda!",-1],
                                                   [u"meeeerda!",-1],
                                                   [u"meeeerdaaa!",-1],
                                                   [u"meeeerdaaa!!!",-1],
                                                   [u"meeeerddaaa!!!",-1],
                                                   [u"está fdd!",-1],
                                                   [u"esta fdd!",-1],
                                                   [u"ta fdd!",-1],
                                                   [u"tá fdd!",-1],
                                                   [u"que nojo!",-1],
                                                   [u"que nojo!!",-1],
                                                   [u"que noooojo!",-1],
                                                   [u"que noojoooo!",-1],
                                                   [u"que noojoooo!!!",-1],
                                                   [u"credo!",-1],                                                   
                                                   [u"meu deus!",-1],
                                                   [u"meu deus! !",-1],
                                                   [u"oh meu deus !",-1],
                                                   [u"oh meu deus! !",-1],
                                                   [u"Ui !",-1],
                                                   [u"Uuuuuui !" ,-1],
                                                   [u"Vai Abaixo!",-1],
                                                   [u"Vai Fora!",-1],
                                                   [u"rua!!!",-1],
                                                   [u"Para a Rua !",-1],
                                                   [u"Safa! ",-1],
                                                   [u"Basta!!",-1],
                                                   [u"Cruzes!!",-1],
                                                   [u"passou-se!  !",-1],
                                                   [u"Livra!!",-1],
                                                   [u"Estamos feitos!!",-1],
                                                   [u"Fogo!!",-1],
                                                    [u"já fomos!",-1],[u"jaaa fooomos!",-1],[u"jááá fomooos!",-1],
                                                    [u"que mau!",-1],[u"que mau",0],[u"quee maaau!",-1],
                                                    [u"foooosga-se!",-1],[u"fosga-se!",-1],[u"fosga-se",0],
                                                    [u"jáááá chega!",-1],[u"já cheeegaaa!",-1],[u"jaaaa chega!",-1],
                                                    [u"socorro!",-1],[u"socorro!",-1],[u"socorro!",-1],
                                                    [u"uuuui!",-1],[u"uuuuiiiii!",-1],[u"ui!",-1],
                                                    [u"aaaaaai!",-1],[u"aiiiiii!",-1],[u"ai!",-1],
                                                    [u"oh!",-1],[u"oooooooh!",-1],[u"oooohhhhhh!",-1],
                                                    [u"irra!",-1],[u"iiiirrrrraaaa!",-1],[u"iirraaaaa!",-1],
                                                    [u"apre!",-1],[u"aaaaaapre!",-1],[u"apreeee!",-1],
                                                    [u"raios!",-1],[u"raaaaios!",-1],[u"raaaiiiioooos!",-1],
                                                    [u"mandem-no embora!",-1],
                                                    [u"sai daí!",-1],[u"saaaaai daííí!",-1],[u"sai daaaaaiii!",-1],
                                                    [u"tirem-no daí!",-1],[u"tirem-no daí!",-1],[u"tirem-no daí!",-1],
                                                    [u"dass!",-1],[u"dasssss!",-1],[u"daaaassssss!",-1],
                                                    [u"fora!",-1],[u"foraaaaa!",-1],[u"fooooraaaaa!",-1]]
    
    
    
    sHasGoodSmiley = [ruler.hasPosSmiley,[sentenceNoMatch,0],
                                        [u"O sócrates e passos coelho são :) ",1],
                                        [u"O sócrates e passos coelho são :))))",1],                       
                                        [u"O sócrates e passos coelho são :D",1],
                                        [u"O sócrates e passos coelho são :DDD",1], 
                                        [u"O sócrates e passos coelho são :-D",1],
                                        [u"O sócrates e passos coelho são :-DDD",1],
                                        [u"O sócrates e passos coelho são 8)",1],
                                        [u"O sócrates e passos coelho são 8))))",1],
                                        [u"O sócrates e passos coelho são 8D",1],
                                        [u"O sócrates e passos coelho são 8DDD",1],
                                        [u"O sócrates e passos coelho são XD",1],
                                        [u"O sócrates e passos coelho são X-D",1],
                                        [u"O sócrates e passos coelho são xD",1],
                                        [u"O sócrates e passos coelho são x-D",1],
                                        [u"O sócrates e passos coelho são :-) sjajsa",1],
                                        [u"O sócrates e passos coelho são :-)))) dssd",1]]
    
    sHasBadSmiley = [ruler.hasNegSmiley,[sentenceNoMatch,0],   
                                        [u"O sócrates e passos coelho são :(  sasa",-1],
                                        [u"O sócrates e passos coelho são :((",-1], 
                                        [u"O sócrates e passos coelho são :S",-1],
                                        [u"O sócrates e passos coelho são :SSS ",-1],
                                        [u"O sócrates e passos coelho são :ss dewedwe",-1],
                                        [u"O sócrates e passos coelho são :s",-1],                                                                                    
                                        [u"O sócrates e passos coelho são :-S Kokdas",-1],
                                        [u"O sócrates e passos coelho são :-SSS",-1],
                                        [u"O sócrates e passos coelho são :-ss ",-1],
                                        [u"O sócrates e passos coelho são :-s ",-1],                                           
                                        [u"O sócrates e passos coelho são :-(",-1],
                                        [u"O sócrates e passos coelho são :-((",-1],
                                        [u"O sócrates e passos coelho são 8(",-1],
                                        [u"O sócrates e passos coelho são 8((",-1],
                                        [u"O sócrates e passos coelho são 8S",-1],
                                        [u"O sócrates e passos coelho são 8SSS",-1],
                                        [u"O sócrates e passos coelho são 8ss",-1],
                                        [u"O sócrates e passos coelho são 8s",-1]]
                    
    sHasPosIdiomExp = [ruler.hasPosIdiomExpression,[sentenceNoMatch,0],
                                                    [u"ele acertou na mosca",1],
                                                    [u"o gajo agarrou a oportunidade",1]]
    
    sHasNegIdiomExp = [ruler.hasNegIdiomExpression,[sentenceNoMatch,0],
                                                    [u"ele apanhou por tabela",-1],
                                                    [u"entregou o ouro ao bandido ",-1]]
                       
    
    shasHeavyPunctuation = [ruler.hasHeavyPunctuation,[sentenceNoMatch,0],
                             [u"O sócrates e passos coelho são bff!",0],
                           [u"O sócrates e passos coelho são bff?",0],                           
                           [u"O sócrates e passos coelho são bff!!",0],
                           [u"O sócrates e passos coelho são bff??",0],                           
                           [u"O sócrates e passos coelho são bff!!!",0],
                           [u"O sócrates e passos coelho são bff!?!?",-1],
                           [u"O sócrates e passos coelho são bff??!!",-1],
                           [u"O sócrates e passos coelho são bff??!?",-1],
                           [u"O sócrates e passos coelho são bff!?!",-1],
                           [u"O sócrates e passos coelho são bff!?!!?",-1],
                           [u"O sócrates e passos coelho são bff?!!!?",-1],
                           [u"O sócrates e passos coelho são bff!??!",-1]]
    
    testCases = [shasHeavyPunctuation]
    
    """
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
             s41,
             s42,
             shasPosInterjection,
             shasNegInterjection,
             sHasGoodSmiley,
             sHasBadSmiley,
             sHasPosIdiomExp,
             sHasNegIdiomExp,
             shasHeavyPunctuation]
        """
        
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

def getTestNaive():

    politiciansFile = "../Resources/players.txt"
    sentiTokensFile = "../Resources/SentiLex-flex-PT02.txt"
    exceptTokensFile = "../Resources/SentiLexAccentExcpt.txt"
    
    politicians = Persons.loadPoliticians(politiciansFile)
    sentiTokens = SentiTokens.loadSentiTokens(sentiTokensFile,exceptTokensFile)
    
    return Naive(politicians,sentiTokens)

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

def testInferTarget():
    
    a = u"aí vai Özil com a bola..."
    b = u"Ilkay Gündogan a fazer um grande lance"
    c = u"o que é que se passa entre o L. Schøne e Ricardo Quaresma??"
    d = u"quem é o Kjær!?!?!"
    e = u"alto corte de Laštůvka"
    
    naive = getTestNaive()
    
    o = Opinion(1,c,None,None,0,None,u"Manual",u"Manual",None)
    
    res = naive.inferTarget2(o)
    
    if len(res) > 0:
        
        for r in res:
            
            print r.tostring()
            print "\n\n" 
    else:
        print "Not fonud"
   

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
    
    testInferTarget()
    
    print "Done!"
