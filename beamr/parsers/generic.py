'''
Functionality common to all parsers
Created on 1 Feb 2018

@author:     Teodor G Nistor

@copyright:  2018 Teodor G Nistor

@license:    MIT License
'''
from beamr.debug import warn

def p_nil(p): # An empty production
    'nil :'
    pass

def p_error(t): # Parsing error
    try:
        warn("Syntax error at token value", t.value)
    except:
        warn("Syntax error at", t)
