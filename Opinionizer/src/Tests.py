# -*- coding: UTF-8 -*-

'''
Created on Apr 27, 2011

@author: samir
'''

#import tweepy
#from nltk import word_tokenize, wordpunct_tokenize
import os
import urllib2
import re
import contextRestrictions
import MySQLdb
import codecs
import subprocess

def testSubprocess():    
    
    xmlStarlet = 'xmlstarlet sel -t -c "//entity[@id=\'{0}\']" *.xml ' 
    
    fi = open("./TAC_2010_KBP_Evaluation_Entity_Linking_Gold_Standard_Entities.txt","r")
    fo = open("./outuput.txt","w")
    
    data = ""
    
    for l in fi:
        
        entity = l.rstrip().strip()
        print "entity: ", entity
        
        p = subprocess.Popen(xmlStarlet.format(entity), shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)    
    
        for line in p.stdout.readlines():
            data += line
         
    print data
    
    fo.write(data)
    fo.close()
    fi.close()
    
    retval = p.wait()
    

def removeNilsFromTACGoldStandard():
    
    fi = open("/home/samir/TAC_2010_KBP_Evaluation_Entity_Linking_Gold_Standard_V1.1.txt","r")
    fo = open("/home/samir/TAC_2010_KBP_Evaluation_Entity_Linking_Gold_Standard_NoNils.txt","w")
    
    for l in fi:
        
        if "NIL" not in l:
            
            fo.write(l)

    fo.close()
    fi.close()

def splitEntityIDsFromTACGoldStandard():

    fi = open("/home/samir/TAC_2010_KBP_Evaluation_Entity_Linking_Gold_Standard_NoNils.txt","r")
    fo = open("/home/samir/TAC_2010_KBP_Evaluation_Entity_Linking_Gold_Standard_Entities.txt","w")    
    
    for l in fi:      
         
        print l.split(" ")[1].strip()
           
        fo.write(l.split(" ")[1].strip()+"\n")

    fo.close()
    fi.close()

    
def testDB():

    sql= """SELECT p.page_title 
            FROM  `en_redirect` r,  `en_page` p
            WHERE r.rd_title =  'Association_football'
            AND r.rd_from = p.page_id """
                
    comments = {}
    db = MySQLdb.connect(host="agatha.inesc-id.pt",user="publico",passwd="publ1c0",db="wikipedia",use_unicode=True)

    c = db.cursor()
    c.execute(sql)    
    
    result = c.fetchall()    

    for r in result:        
        
        print r
        print codecs.decode(r[0],"utf-8")
        #print unicode(r[0])
        #print r[0]        
        
    db.close()    
    
    return comments


def isFalsePositive(mention,sentence):
        
        left_context = {'portas': ['as','nas','às','miguel','abriu','abriram','abre','abrem','numeral','mais']}
        right_context = {'portas': ['de','do','da','das','dos']}
        
        tokens = re.findall(u'\w+',unicode(sentence),re.X)
        print tokens
        badTokens = []
        
        try:
            if mention in left_context:
                
                badTokens = left_context[mention]
                
                if tokens[tokens.index(mention)-1] in badTokens:
                    return True
            
            if mention in right_context:
    
                badTokens = right_context[mention]             
                
                if tokens[tokens.index(mention)+1] in badTokens:
                    return True
                
            return False
        except:
            print mention, " in ", sentence

def tokenizer2():
    
    regex = ur"(?:\W?macaquinho do chinês\W?)|(?:\W?nova iorque\W?)|(?:\W?big ben\W?)|(?:\W?qualquer coisa\W?)"
    
    str = u"Estava lá em plena ,nova iorque! Um macaquinho do chinês, tinha uma camisola do big ben ou qualquer coisa e não qualquer outra coisa"
    newSentence = str
    
    matches = re.findall(regex,str)
    print matches
    for match in matches:
            
            a = match.strip(' ').rstrip(' ')
            
            if a != "":
            
                r = a.replace(" ","_")
                newSentence = newSentence.replace(a,r)
            
            
    print str, " -> ", newSentence
    
def tokenizer():
    
    regex = ur"(?:\W?macaquinho do chinês\W?)|(?:\W?nova iorque\W?)|(?:\W?big ben\W?)|(?:\W?qualquer coisa\W?)"
    
    str = u"Estava lá em plena ,nova iorque! Um macaquinho do chinês, tinha uma camisola do big ben ou qualquer coisa e não qualquer outra coisa"
    newSentence = str
    
    matches = re.findall(regex,str)
    print matches
    for match in matches:
        
        for m in match:
            
            a = m.strip(' ').rstrip(' ')
            
            if a != "":
            
                r = a.replace(" ","_")
                newSentence = newSentence.replace(a,r)
            
            
    print str, " -> ", newSentence

def getConcordance(text,word,offset):
    
    tokens = re.findall(u'\w+',text,re.U)
    listOfIndexes  = list(find_all_in_list( tokens,word))
    print listOfIndexes   

    listOfConcordance = []
    
    for i in listOfIndexes:
        
        start = i - offset
        
        if start < 0:
            start = 0
        
        end = i + offset + 1
         
        if end > len(text):
            end = len(text)
        
        listOfConcordance.append(tokens[start:end])
    
    return listOfConcordance

def find_all_in_list(a_str, sub):
    
    start = 0
    
    while True:
         
        try:
            start = start + a_str[start:].index(sub)
        except ValueError:
            return
        yield start
        
        start+=1
    
        
def find_all(a_str, sub):
    
    start = 0
    
    while True:
    
        start = a_str.find(sub, start)
        if start == -1: return
        yield start
        start += len(sub)

def testConcordance():
    
    text = "O rato roeu a garrafa de rum do rei da russia. Uma vez brinquei com o rato mickey e com o pateta. Hummm aqui há rato. Fazer de mim rato sapato grande e vermelho"
    
    l = getConcordance(text,"rato",2)
    
    print l
            
if __name__ == '__main__':
    
    print "GOOO!"
    
    testConcordance()
    
    print "Done!"