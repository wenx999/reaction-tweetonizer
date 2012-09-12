# -*- coding: UTF-8 -*-

import re
import unicodedata

def normalize(s):
    
    """ Replace unicode chars with their ascii approximation
        ex: ç -> c
            ã,á,â -> a
    """
    
    return (''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))).replace('-',' ')

def removeURLs(sentence):
    
    regex = "(.?http://.+?)( |$)|(.?www\..+?)( |$)"
    
    return re.sub(regex," <URL> ",sentence)

def removeStopWords(sentence):
    
    stopwords = [" a ","1","2","3","4","5","6","7","8","9","0"
" à ",
" aí ",
" « ",
" » "
" acusa ",
" agora ",
" ainda ",
" ao ",
" aos ",
" aqui ",
" as ",
" assim ",
" até ",
" be ",
" bem ",
" bit ",
" c ",
" co ",
" com ",
" cm ",
" cá "
" como ",
" cont ",
" contra ",
" d ",
" da ",
" do "
" dá ",
" dão "
" dar ",
" das ",
" dos "
" de ",
" deck ",
" depois ",
" dia ",
" disse ",
" diz ",
" dizer ",
" dlvr ",
" do ",
" dos ",
" dd ",
" e ",
" é ",
" ele ",
" eleições ",
" em ",
" entre ",
" era ",
" eram ",
" esta ",
" está ",
" este ",
" essa ",
" esse ",
" eu ",
" eu ",
" fala ",
" falar ",
" faz ",
" fazer ",
" fb ",
" fez ",
" foi ",
" frente ",
" g ",
" gl ",
" goo ",
" h ",
" há ",
" i ",
" isso ",
" isto ",
" it ",
" j ",
" já ",
" k ",
" l ",
" lá ",
" lhe ",
" ly ",
" m ",
" mais ",
" mas ",
" me ",
" mesmo ",
" mil ",
" muito ",
" n ",
" na ",
" nada ",
" não ",
" nas ",
" nem ",
" no ",
" nos ",
" novas ",
" o ",
" ontem ",
" oportunidades ",
" os ",
" ou ",
" ow ",
" p ",
" país ",
" para ",
" pela ",
" pelo ",
" pode ",
" por ",
" porque ",
" portugal ",
" programa ",
" ps ",
" pt ",
" q ",
" quando ",
" que ",
" quem ",
" quer ",
" rt ",
" s ",
" sabe ",
" são ",
" se ",
" sem ",
" ser ",
" seu ",
" seu ",
" só ",
" sobre ",
" sua ",
" t ",
" te ",
" também ",
" tem ",
" ter ",
" tudo ",
" tvi ",
" um ",
" uma ",
" vai ",
" ver ",
" vez ",
" vs ",
" www ",
]
    newSentence = sentence
    
    for word in stopwords:
        newSentence = newSentence.replace(word," ")
        
    return newSentence



def removeUsernames(sentence):
    
    regex = ".?@.+?( |$)"
    return re.sub(regex," <USER> ", sentence)

def separateSpecialSymbols(sentence):
    
    symbols = [",","!",":",";",".","-","_","+","*","@","£","#","$","\"","%","&","(",")","/","<",">","[","]","^","{","}","|","'","~","?"]
    
    newSentence = sentence
    
    for s in symbols:
        newSentence = newSentence.replace(s," "+s+" ")
        
    return newSentence
    
if __name__ == '__main__':
    
    #print removeURLs("http://silvio.com/silvio na boa http://tinyurl.pt mesmo http://www.cnn.com/news.pl?format=1&newsId=2 ... www.susto.pt/ideas.php?e=100")
    print removeUsernames("Sabes que afinal @silvio é mesmo @sandra na boa @jonas")
    