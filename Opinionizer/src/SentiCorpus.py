'''
Created on Apr 8, 2011

@author: samir
'''

import MySQLdb
import xml.dom.minidom
from Opinion import Opinion


resultsFolder = "./GoldenStandard/"

GET_COMMENTS_BY_TARGET = "SELECT id_news,id_com,id_sentence, target,iro_lit,polarity,sentence,rel_ident,mencao \
                    FROM `anotacoes_comentarios_debates` \
                    WHERE  target = \'{0}\' \
                    ORDER BY id_news, id_com, id_sentence"
                    
GET_ALL_COMMENTS = "SELECT id_news,id_com,id_sentence, target,iro_lit,polarity,sentence,rel_ident,mencao \
                    FROM `anotacoes_comentarios_debates` \
                    WHERE  target IN ('socrates','louca','portas','jeronimo') \
                    ORDER BY id_news, id_com, id_sentence"                    

ID_NEWS = 0
COMMENT_ID = 1
SENTENCE_ID = 2
TARGET = 3
IRO_LIT = 4
POLARITY = 5
SENTENCE = 6
REL_IDENT = 7
MENTION = 8


def getGoldStandardByTarget(target):
    
    """ 1. Query the SentiCorpus database for all comments of a given target
        2. Build and return an hashtable of annotated comments
    """
    comments = {}
    db = MySQLdb.connect(host="agatha",user="publico",passwd="publ1c0",db="senticorpus",use_unicode=False)

    c = db.cursor()
    c.execute(GET_COMMENTS_BY_TARGET.format(target))    
    
    result = c.fetchall()    

    for r in result:        
        
        commentId = str(r[ID_NEWS]) + "-" + str(r[COMMENT_ID]) + "-" + str(r[SENTENCE_ID])
                
        comment = Opinion(commentId,
                          unicode(r[SENTENCE]),                          
                          unicode(r[TARGET]),
                          unicode(r[MENTION]),
                          r[POLARITY],
                          r[IRO_LIT],                          
                          unicode(r[REL_IDENT]) )
        
        comments[commentId] = comment
        
        
    db.close()    
    
    return comments

def getGoldStandardAllTargets():
    
    """ 1. Query the SentiCorpus database for all comments of a given target
        2. Build and return an hashtable of annotated comments
    """
    comments = {}
    db = MySQLdb.connect(host="agatha",user="publico",passwd="publ1c0",db="senticorpus",use_unicode=False)

    c = db.cursor()
    c.execute(GET_ALL_COMMENTS)    
    
    result = c.fetchall()    

    for r in result:        
        
        commentId = str(r[ID_NEWS]) + "-" + str(r[COMMENT_ID]) + "-" + str(r[SENTENCE_ID])
                
        comment = Opinion(commentId,
                          unicode(r[SENTENCE]),                          
                          unicode(r[TARGET]),
                          unicode(r[MENTION]),
                          r[POLARITY],
                          r[IRO_LIT],                          
                          unicode(r[REL_IDENT]) )
        
        comments[commentId] = comment
        
        
    db.close()    
    
    return comments

def getAllComments():    
    
    comments = {}
    db = MySQLdb.connect(host="agatha",user="publico",passwd="publ1c0",db="senticorpus",use_unicode=False)

    c = db.cursor()
    c.execute(GET_ALL_COMMENTS)    
    
    result = c.fetchall()    

    for r in result:        
        
        commentId = str(r[ID_NEWS]) + "-" + str(r[COMMENT_ID]) + "-" + str(r[SENTENCE_ID])
                
        comment = Opinion(commentId,unicode(r[SENTENCE]))                          
                                  
        comments[commentId] = comment        
        
    db.close()    
    
    return comments

    
def refreshGoldStandardsByTarget():    
    
    targets = ['socrates','louca','portas','jeronimo']
    
    for target in targets:
        
        opinions = getGoldStandardByTarget(target)
        write(opinions, resultsFolder+target+".xml")
        
def refreshGoldStandard():    
    
    opinions = getGoldStandardAllTargets()
    write(opinions, "sentiCorpusGoldStandard.xml")

def refreshComments():
    
    opinions = getAllComments()
    write(opinions, "sentiCorpusComments.xml")

def read(path):
    
    listOfOpinions = {}
    
    xmlDocument = xml.dom.minidom.parse(path)    
    
    for opinion in xmlDocument.getElementsByTagName("Opinion"):        
        
        listOfOpinions[opinion.getAttribute("id")] = Opinion(opinion.getAttribute("id"),
                                                             unicode(opinion.firstChild.data.strip(' ,\n').rstrip(' ,\n')),
                                                             unicode(opinion.getAttribute("target")),
                                                             unicode(opinion.getAttribute("mention")),
                                                             opinion.getAttribute("polarity"),
                                                             opinion.getAttribute("irony"))
    
    return listOfOpinions
    
def write(opinions,path):
    
    doc = xml.dom.minidom.Document()
    
    root = doc.createElement("Opinionizer")
    doc.appendChild(root)
    
    for opinion in opinions.itervalues():
        
        comment = doc.createElement("Opinion")
        comment.setAttribute("id",str(opinion.id))
        
        if opinion.target != None:
            comment.setAttribute("target",opinion.target)
            
        if opinion.mention != None:            
            comment.setAttribute("mention",opinion.mention)
            
        if opinion.polarity != None:    
            comment.setAttribute("polarity",str(opinion.polarity))
        
        if opinion.irony != None:    
            comment.setAttribute("irony",opinion.irony)           
         
        commentText = doc.createTextNode(opinion.sentence)
        
        comment.appendChild(commentText)
        root.appendChild(comment)
        
    doc.writexml( open(path, 'w'),
            indent="  ",
            addindent="  ",
            newl='\n',
            encoding="utf-8")
    
    doc.unlink()         
   
if __name__ == "__main__":        
    
    print "Go"
    
    refreshGoldStandard()
    
    print "Done"