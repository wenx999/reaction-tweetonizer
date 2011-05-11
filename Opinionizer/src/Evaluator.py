# -*- coding: UTF-8 -*-

'''
Created on Apr 8, 2011

@author: samir
'''

import xml.dom.minidom
from Opinion import Opinion
from datetime import datetime

class Evaluator:

    goldStandard = None
    candidate = None
    
    correctTarget = {}
    incorrectTarget = {}
    missingTarget = {}
    
    correctNegatives = {}
    correctPositives = {}
    correctNeutrals = {}    
    wrongNegatives = {}
    wrongPositives = {}
    wrongNeutrals = {}
    
    def __init__(self, goldStandard, candidate):
    
        self.goldStandard = goldStandard
        self.candidate = candidate
    
        for id,opinion in self.candidate.items():
        
            try:
                
                #----------------- TARGET -----------------------
                if self.goldStandard[id].target == opinion.target:
                
                    self.correctTarget[id] = self.goldStandard[id]
                else:
                    self.incorrectTarget[id] = self.goldStandard[id]
                
                #----------------- POLARITY -----------------------
                
                if int(self.goldStandard[id].polarity) == -1:
                    
                    if int(opinion.polarity) == -1:
            
                        self.correctNegatives[id] = self.goldStandard[id]  
                    else:
                        self.wrongNegatives[id] = self.goldStandard[id]
                
                elif int(self.goldStandard[id].polarity) == 0:
                    
                    if int(opinion.polarity) == -0:
            
                        self.correctNeutrals[id] = self.goldStandard[id]  
                    else:
                        self.wrongNeutrals[id] = self.goldStandard[id]
                    
                elif int(self.goldStandard[id].polarity) == 1: 
                    
                    if int(opinion.polarity) == 1:
            
                        self.correctPositives[id] = self.goldStandard[id]  
                    else:
                        self.wrongPositives[id] = self.goldStandard[id]
                        
            except KeyError:
                self.incorrectTarget[id] = opinion
                
            except ValueError:
                print "Erro a analisar!"
                print "Candidate: " + opinion.tostring()
                print "----------------------------"
                print "Gold Standard: " + self.goldStandard[opinion.id].tostring()    
                    
        for id in set(self.goldStandard) - set(self.correctTarget):                    
            self.missingTarget[id] = self.goldStandard[id] 
        
    
    def targetPrecision(self):
        
        return float(len(self.correctTarget))/float(len(self.candidate))*100
        
    def targetRecall(self):
        
        return float(len(self.correctTarget))/float(len(self.goldStandard))*100
    
    def positivePolarityPrecision(self):
        
        return float(len(self.correctPositives)) / float(len(self.correctPositives) + len(self.wrongPositives))*100
    
    def negativePolarityPrecision(self):
        
        return float(len(self.correctNegatives)) / float(len(self.correctNegatives) + len(self.wrongNegatives))*100
    
    def neutralPolarityPrecision(self):
        
        return float(len(self.correctNeutrals)) / float(len(self.correctNeutrals) + len(self.wrongNeutrals))*100
  

    def totalPolarityPrecision(self):
        
        return float(len(self.correctNeutrals) + \
                     len(self.correctNegatives) + \
                     len(self.correctPositives))  / \
               float(len(self.correctNeutrals) + \
                     len(self.correctNegatives) + \
                     len(self.correctPositives) + \
                     len(self.wrongNegatives) + \
                     len(self.wrongPositives) + \
                     len(self.wrongNeutrals) )*100
  
    def writeReport(self,path):
              
        doc = xml.dom.minidom.Document()
    
        root = doc.createElement("OpinionizerResults")
        root.setAttribute("date", str(datetime.now()))
        root.setAttribute("nOfComments", str(len(self.goldStandard)))
        doc.appendChild(root)
        
        #-------Target Results-------        
        targetResultsNode = doc.createElement("TargetResults")        
        targetResultsNode.setAttribute("precision", str(self.targetPrecision()))
        targetResultsNode.setAttribute("recall", str(self.targetRecall()))
        root.appendChild(targetResultsNode)
        
        #Target missing matches
        #---------------------------------------------------------------------------------
        missingMatchesNode = doc.createElement("MissingMatches")
        missingMatchesNode.setAttribute("freq", str(len(self.missingTarget)))
        targetResultsNode.appendChild(missingMatchesNode) 
         
        for opinion in self.missingTarget.itervalues():
            
            commentNode = doc.createElement("Opinion")
            commentNode.setAttribute("id",str(opinion.id))
            
            if opinion.target != None:
                commentNode.setAttribute("target",opinion.target)
                
            if opinion.mention != None:            
                commentNode.setAttribute("mention",opinion.mention)
                
            if opinion.polarity != None:    
                commentNode.setAttribute("polarity",str(opinion.polarity))
            
            if opinion.irony != None:    
                commentNode.setAttribute("irony",opinion.irony)
             
            commentTextNode = doc.createTextNode(opinion.sentence)
            
            commentNode.appendChild(commentTextNode)
            missingMatchesNode.appendChild(commentNode)                

        #Target incorrect matches
        #---------------------------------------------------------------------------------
        incorrectTargetNode = doc.createElement("IncorrectMatches")
        incorrectTargetNode.setAttribute("freq", str(len(self.incorrectTarget)))
        targetResultsNode.appendChild(incorrectTargetNode)
        
        for opinion in self.incorrectTarget.itervalues():
            
            commentNode = doc.createElement("Opinion")
            commentNode.setAttribute("id",str(opinion.id))
            
            if opinion.target != None:
                commentNode.setAttribute("target",opinion.target)
            
            if self.candidate[opinion.id].target != None:
                commentNode.setAttribute("inferredTarget",self.candidate[opinion.id].target)
                
            if opinion.mention != None:            
                commentNode.setAttribute("mention",opinion.mention)
                
            if opinion.polarity != None:    
                commentNode.setAttribute("polarity",str(opinion.polarity))
            
            if opinion.irony != None:    
                commentNode.setAttribute("irony",opinion.irony)
            
            if self.candidate[opinion.id].metadata != None:    
                commentNode.setAttribute("metadata",self.candidate[opinion.id].metadata)
             
            commentTextNode = doc.createTextNode(opinion.sentence)
            
            commentNode.appendChild(commentTextNode)
            incorrectTargetNode.appendChild(commentNode)   
            
        #-------Polarity results-------
        polarityResultsNode = doc.createElement("PolarityResults")     
        polarityResultsNode.setAttribute("precision", str(self.totalPolarityPrecision())) 
        root.appendChild(polarityResultsNode)
        
        #Positives
        #---------------------------------------------------------------------------------
        positivePolarityNode = doc.createElement("Positives")             
        positivePolarityNode.setAttribute("precision", str(self.positivePolarityPrecision()))        
        polarityResultsNode.appendChild(positivePolarityNode)
        
        wrongPositivesNode = doc.createElement("IncorrectMatches")
        wrongPositivesNode.setAttribute("freq", str(len(self.wrongPositives)))
        
        for opinion in self.wrongPositives.itervalues():
            
            commentNode = doc.createElement("Opinion")
            commentNode.setAttribute("id",str(opinion.id))
            
            if opinion.target != None:
                commentNode.setAttribute("target",opinion.target)
                
            if opinion.mention != None:            
                commentNode.setAttribute("mention",opinion.mention)
                
            if opinion.polarity != None:    
                commentNode.setAttribute("polarity",str(opinion.polarity))
           
            if self.candidate[opinion.id].polarity:
                commentNode.setAttribute("inferredPolarity",str(self.candidate[opinion.id].polarity))
            
            if opinion.irony != None:    
                commentNode.setAttribute("irony",opinion.irony)
             
            if self.candidate[opinion.id].metadata != None:    
                commentNode.setAttribute("metadata",self.candidate[opinion.id].metadata)          
            
            commentTextNode = doc.createTextNode(opinion.sentence)
            
            commentNode.appendChild(commentTextNode)
            wrongPositivesNode.appendChild(commentNode)
        
        positivePolarityNode.appendChild(wrongPositivesNode)
        
        #Neutrals
        #---------------------------------------------------------------------------------
        neutralPolarityNode = doc.createElement("Neutrals")             
        neutralPolarityNode.setAttribute("precision", str(self.neutralPolarityPrecision()))        
        polarityResultsNode.appendChild(neutralPolarityNode)
        
        wrongNeutralsNode = doc.createElement("IncorrectMatches")
        wrongNeutralsNode.setAttribute("freq", str(len(self.wrongNeutrals)))
        
        for opinion in self.wrongNeutrals.itervalues():
            
            commentNode = doc.createElement("Opinion")
            commentNode.setAttribute("id",str(opinion.id))
            
            if opinion.target != None:
                commentNode.setAttribute("target",opinion.target)
                
            if opinion.mention != None:            
                commentNode.setAttribute("mention",opinion.mention)
                
            if opinion.polarity != None:    
                commentNode.setAttribute("polarity",str(opinion.polarity))
           
            if self.candidate[opinion.id].polarity:
                commentNode.setAttribute("inferredPolarity",str(self.candidate[opinion.id].polarity))
            
            if opinion.irony != None:    
                commentNode.setAttribute("irony",opinion.irony)   
                            
            if self.candidate[opinion.id].metadata != None:    
                commentNode.setAttribute("metadata",self.candidate[opinion.id].metadata)            
            
            commentTextNode = doc.createTextNode(opinion.sentence)
            
            commentNode.appendChild(commentTextNode)
            wrongNeutralsNode.appendChild(commentNode)
        
        neutralPolarityNode.appendChild(wrongNeutralsNode)
        
        #Negatives
        #---------------------------------------------------------------------------------
        negativePolarityNode = doc.createElement("Negative")             
        negativePolarityNode.setAttribute("precision", str(self.negativePolarityPrecision()))
        polarityResultsNode.appendChild(negativePolarityNode)
        
        wrongNegativesNode = doc.createElement("IncorrectMatches")
        wrongNegativesNode.setAttribute("freq", str(len(self.wrongNegatives)))
        
        for opinion in self.wrongNegatives.itervalues():
            
            commentNode = doc.createElement("Opinion")
            commentNode.setAttribute("id",str(opinion.id))
            
            if opinion.target != None:
                commentNode.setAttribute("target",opinion.target)
                
            if opinion.mention != None:            
                commentNode.setAttribute("mention",opinion.mention)
                
            if opinion.polarity != None:    
                commentNode.setAttribute("polarity",str(opinion.polarity))
           
            if self.candidate[opinion.id].polarity:
                commentNode.setAttribute("inferredPolarity",str(self.candidate[opinion.id].polarity))
            
            if opinion.irony != None:    
                commentNode.setAttribute("irony",opinion.irony)   
                            
            if self.candidate[opinion.id].metadata != None:    
                commentNode.setAttribute("metadata",self.candidate[opinion.id].metadata)            
            
            commentTextNode = doc.createTextNode(opinion.sentence)
            
            commentNode.appendChild(commentTextNode)
            wrongNegativesNode.appendChild(commentNode)
        
        negativePolarityNode.appendChild(wrongNegativesNode)
        
        doc.writexml( open(path, 'w'),
                indent="  ",
                addindent="  ",
                newl='\n',
                encoding="utf-8")
        
        doc.unlink()
        
if __name__ == "__main__":
  
    a = Opinion(1,u"O portas não sabe nadar",u"portas",u"name",-1,"iro")
    b = Opinion(2,u"O cavaco não dá cavaco",u"cavaco",u"name",0,"iro")
    c = Opinion(3,u"O socrates não nada",u"socrates",u"name",1,"iro")
    d = Opinion(4,u"O louca sabe pouco",u"louca",u"name",0,"iro")
    e = Opinion(5,u"O jeronimo é antigo",u"jeronimo",u"name",0,"iro")
    
    gold = {1:a,2:b,3:c,4:d,5:e}
    
    candidate = {1:a,2:b,3:d}
    
    eval = Evaluator(gold,candidate)
    
    p = eval.targetPrecision()
    print "target precision: ",p
   
    p = eval.targetRecall()
    print "target recall: ",p
    
    p = eval.positivePolarityPrecision()
    print "positive polarity precision: ",p
    
    p = eval.neutralPolarityPrecision()
    print "neutral polarity precision: ",p
    
    p = eval.negativePolarityPrecision()
    print "negative polarity precision: ",p
    
    print "--------------MISSING MATCHES--------------------"
    
    for o in eval.missingTarget.itervalues():
    
        print o.tostring()
        print "***********"
    
    #eval.writeReport("report.xml")
    