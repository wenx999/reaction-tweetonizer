# -*- coding: UTF-8 -*-

import re

def removeURLs(sentence):
    
    regex = "(.?http://.+?)( |$)|(.?www\..+?)( |$)"
    
    return re.sub(regex," <URL> ",sentence)

def removeUsernames(sentence):
    
    regex = ".?@.+?( |$)"
    return re.sub(regex," <USER> ", sentence)
    
if __name__ == '__main__':
    
    #print removeURLs("http://silvio.com/silvio na boa http://tinyurl.pt mesmo http://www.cnn.com/news.pl?format=1&newsId=2 ... www.susto.pt/ideas.php?e=100")
    print removeUsernames("Sabes que afinal @silvio é mesmo @sandra na boa @jonas")
    