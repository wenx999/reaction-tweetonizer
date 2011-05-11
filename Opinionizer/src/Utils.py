# -*- coding: UTF-8 -*-

'''
Created on Apr 13, 2011

@author: samir
'''

import unicodedata

def normalize(s):
    
    """ Replace unicode chars with their ascii approximation
        ex: ç -> c
            ã,á,â -> a
    """
    
    return (''.join((c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'))).replace('-',' ')

if __name__ == '__main__':
    
    st = u"acção-se"
    
    print "Normalize ", st,"->",normalize(st)