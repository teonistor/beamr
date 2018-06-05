'''
Image frame lexer
Created on 15 Feb 2018

@author:     Teodor G Nistor

@copyright:  2018 Teodor G Nistor

@license:    MIT License
'''
from ply import lex

import beamr.debug as dbg
from beamr.lexers.generic import t_error  # @UnusedImport


tokens = (
       'VBAR',
       'HBAR',
       'PLUS',
#        'HASH',
#        'BIGO',
       'OVRL',
#        'LEFT',
#        'RIGHT',
#        'UP',
#        'DOWN',
       'NUM',
       'UNIT',
       'X',
       'DOT',
       'QFILE',
       'FILE',
       'LF'
       )

t_ignore = ' '

def t_VBAR(t):
    r'-'
    return t

def t_HBAR(t):
    r'\|'
    return t

def t_PLUS(t):
    r'\+'
    return t

def t_OVRL(t):
    r'<.*?>' # Beamer overlay, e.g. <2->
    return t

def t_NUM(t):
    r'\d+(\.\d+)?' # Number, optionally with decimal point e.g. 2, 3.7 but not 4. or .9
    return t

def t_UNIT(t):
    r'cm|pt|ex|mm|in|em|%(?=x\d|$)' # Is only unit when followed by other measurement or end of string
    return t

def t_X(t):
    r'x(?=\d)' # Is only unit delimiter when followed by other measurement
    return t

def t_DOT(t):
    r'\.'
    t.value = (None, None) # Placeholder for a gap in the grid => no file name, no overlay
    return t

def t_QFILE(t):
    r'".+?"'
    t.value = t.value[1:-1] # Strip the quotes from around the file name
    return t

def t_FILE(t):
    r'[^ \n<]+'
    return t

def t_LF(t):
    r'\n+'
    t.lexer.lineno += len(t.value)
    return t

lexer = lex.lex(debug=dbg.verbose, reflags=0)
