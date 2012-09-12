'''
Created on Sep 10, 2012

@author: samir

'''

import codecs
import re
import StringIO
import Preprocessor

class MultiWordHelper:
    
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
                if multiWord != Preprocessor.normalize(multiWord):
                    buff.write(self.regexTemplate.format(Preprocessor.normalize(multiWord)))
        
        if len(self.multiWordsRegex) == 0:
            self.multiWordsRegex = buff.getvalue().strip('|')
        else:
            self.multiWordsRegex += "|" + buff.getvalue().strip('|')
      
        buff.close()
