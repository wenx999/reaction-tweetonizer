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
import sys
import urllib
import simplejson
from datetime import datetime,timedelta
import Preprocessor
import Persons
import SentiTokens
import csv
import operator

def testCSVReader():
    
    fileName = "../../titulos.csv"
    csvfile = open(fileName, "rb")
    dialect = csv.Sniffer().sniff(csvfile.read(1024))
    csvfile.seek(0)
    reader = csv.reader(csvfile, dialect)
    
    for line in reader:
        
        print line
        
        


def countSentiTokens(inputFile,outputFile):
        
    f = codecs.open(inputFile, "r", "utf-8")
    
    text = f.read().split('\n')
    
    tokens = {}
    
    for token in text:
        
        normToken = token.lower()
        
        if normToken not in tokens:
            tokens[normToken] = 1
        else:
            tokens[normToken] += 1
            
    writeResults(tokens,outputFile)
    
def writeResults(tokens,filename):       
    
    f = codecs.open(filename, "w", "utf-8")
    
    sortedTokens = sorted(tokens.iteritems(), key=operator.itemgetter(1),reverse=True)
    
    for s in sortedTokens:
        f.write(s[0])
        f.write(",")
        f.write(str(s[1]))
        f.write("\n")
    
    f.close()

def testFindSenti():
    
    s1 = "Targets: coentrão; sentiTokens:; score:0;"
    s2 = "Targets: coentrão; sentiTokens:falha(-1) culpa(0) ; score:-1;"
    
    regex = ur'(\W|^)sentiTokens:(.*?);(\W|$)'
         
    match = re.search(regex,s1).group(2)
    
    print "S1: ", match, " ", len(match.strip(' '))
   
    match = re.search(regex,s2).group(2)
    
    print "S2: ", match, " ", len(match.strip(' ')) 


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

def newGetTweets(beginDate,endDate,proxy):
    
    """
    Gets tweets from a service for a certain period
    Params: begin date 
    end date
    proxy
    
    Returns: list of Opinion instances
    """
    
    print "Getting new tweets..."
    
    username = "twitter_crawl_user"
    password = "twitter_crawl_pass"
    top_level_url = "http://pattie.fe.up.pt/solr/portugal/select"
    requestTweets = "http://pattie.fe.up.pt/solr/portugal/select?q=created_at:[{0}%20TO%20{1}]&indent=on&wt=json"
    #requestTweets = "http://pattie.fe.up.pt/solr/portugal/select?q=created_at:[2012-05-25T13:00:00Z%20TO%202012-05-25T15:00:00Z]&indent=on&wt=json"
    
    #Password manager because the service requires authentication
    password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
    password_mgr.add_password(None, top_level_url, username, password)
    auth_handler = urllib2.HTTPBasicAuthHandler(password_mgr)
    opener = None
    
  
    
    if proxy != None:
        proxy_handler = urllib2.ProxyHandler({'http': proxy})        
        opener = urllib2.build_opener(auth_handler,proxy_handler)       
    else:
        #opener = urllib2.build_opener(auth_handler)
        opener = urllib2.build_opener()
    
    if beginDate.strftime('%Y') == "1900":
       
        print "Getting Tweets from STDIN ..."
        twitterData = sys.stdin;
        
    else:
        """
        print "Requesting: " + requestTweets.format(beginDate.strftime('%Y-%m-%dT%H:%M:%Sz'),
                                                    endDate.strftime('%Y-%m-%dT%H:%M:%Sz'))
        twitterData = opener.open(requestTweets.format(beginDate.strftime('%Y-%m-%dT%H:%M:%Sz'),
                                                       endDate.strftime('%Y-%m-%dT%H:%M:%Sz')));
                                                       
        """
        
        print "Requesting: " + requestTweets.format(urllib.quote(beginDate.strftime('%Y-%m-%dT%H:%M:%SZ')),
                                                    urllib.quote(endDate.strftime('%Y-%m-%dT%H:%M:%SZ')))
        twitterData = opener.open(requestTweets.format(urllib.quote(beginDate.strftime('%Y-%m-%dT%H:%M:%SZ')),
                                                       urllib.quote(endDate.strftime('%Y-%m-%dT%H:%M:%SZ'))));
        
    #Read the JSON response
    jsonTwitter = simplejson.loads(unicode(twitterData.read().decode("utf-8")))
    
    print jsonTwitter["response"]
    
    politicians = getPoliticians()
    sentiTokens = getSentiTokens()
       
    multiWordTokenizer = getMultiWordsTokenizer(politicians, sentiTokens)
                                
    listOfTweets = []
    
    #Build a dictionary
    for tweet in jsonTwitter["response"]["docs"]:
    
        id = str(tweet["user_id"]) + "_" + str(tweet["id"])
        userId = unicode(tweet["user_id"])
        #print userId
        
        date =  datetime.strptime(tweet["created_at"], '%Y-%m-%dT%H:%M:%Sz')
        
        taggedSentence = multiWordTokenizer.tokenizeMultiWords(unicode(tweet["text"]))
        taggedSentence = Preprocessor.removeURLs(taggedSentence)
        taggedSentence = Preprocessor.removeUsernames(taggedSentence)  
        
        listOfTweets.append(Opinionizers.Opinion(tweet["id"],unicode(tweet["text"]),user=userId,date=date,processedSentence = taggedSentence))
    
    print len(listOfTweets), " tweets loaded\n"  
   
    return listOfTweets

def getPoliticians():
    
    politiciansFile = "../Resources/politicians.txt"
    politicians = Persons.loadPoliticians(politiciansFile)
    
    return politicians

def getSentiTokens():
    
    sentiTokensFile = "../Resources/sentiTokens-2011-05-30.txt"
    exceptTokensFile = "../Resources/SentiLexAccentExcpt.txt"
    
    sentiTokens = SentiTokens.loadSentiTokens(sentiTokensFile,exceptTokensFile)
    
    return sentiTokens

def getRulesClassifier(politicians, sentiTokens):
    
    return Opinionizers.Rules(politicians,sentiTokens)    

def getNaiveClassifier(politicians, sentiTokens):

    politiciansFile = "../Resources/politicians.txt"
    sentiTokensFile = "../Resources/sentiTokens-2011-05-30.txt"
    exceptTokensFile = "../Resources/SentiLexAccentExcpt.txt"
    
    politicians = Persons.loadPoliticians(politiciansFile)
    sentiTokens = SentiTokens.loadSentiTokens(sentiTokensFile,exceptTokensFile)
    
    return Opinionizers.Naive(politicians,sentiTokens)    

def getMultiWordsTokenizer(politicians,sentiTokens):
    
    multiWordsFile = "../Resources/multiwords.txt"
    print "Multiword Tokenizer " + multiWordsFile    
    
    multiWordTokenizer = Opinionizers.MultiWordHandler(multiWordsFile)
    multiWordTokenizer.addMultiWords(Persons.getMultiWords(politicians))
    multiWordTokenizer.addMultiWords(SentiTokens.getMultiWords(sentiTokens))

    return multiWordTokenizer

def isNewsSource(sentence):
    
    newsSourceList = "jn|diarionoticias|publico|público|expresso|antena 1|destak|destakes|dn|economico|iportugal|iradar|portugal diario|sol|tsf|ultimas|noticiasrtp|rtp|tvi|sic|sicn|diárioeconómico|ionline|sábado|sabado|visao|visão|lusa_noticias|expressoonline"
        
    info = u'Regra \"news source!\""-> '        
    regex = ur'(\W|^)#({0})|@({0})|\(({0})\)|\[({0})\](\W|$)'.format(newsSourceList)
    
    """
    if useTaggedSentence:
        sentence = opinion.processedSentence.lower()
    else:
        sentence = opinion.sentence.lower()
    
    
    if sentence.find(u"falta de") == -1:
        
        return None
    """
     
    match = re.search(regex,sentence)
    
    if match != None:
        
        info += match.group() 
        
        return (1,info) 
        
    else:
        return None

def a():
    
    for c in map(chr, range(256)):
         
        if not c.isalnum():
            print c


def separateSpecialSymbols(sentence):
    
    symbols = [",","!",":",";",".","-","_","+","*","@","£","#","$","\"","%","&","(",")","/","<",">","[","]","^","{","}","|","'","~","?"]
    
    newSentence = sentence
    
    for s in symbols:
        newSentence = newSentence.replace(s," "+s+" ")
        
    return newSentence
    
if __name__ == '__main__':
    
    print "GOOO!"
    
    
    countSentiTokens('./concord-intransitivos-positivos2.csv','./newPositives.csv')
    
    """
    print isNewsSource("aquelas manbos ")
    print isNewsSource("aquelas manbos #publico coiso")
    print isNewsSource("aquelas manbos @jn cenas")
    print isNewsSource("(diarionoticias) aquelas manbos cenas")
    print isNewsSource(" [publico] aquelas manbos cenas")
    
    
    a = newGetTweets(datetime(year=2011,month=1,day=1),datetime.now(),None)
    
    for b in a:
        print b.tostring() + "\n\n"
    """
    print "Done!"