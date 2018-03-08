'''
Created on 15 Feb 2018

@author: Teodor Gherasim Nistor
'''
from ply import lex

import beamr.debug as dbg
from beamr.lexers.generic import t_error  # @UnusedImport


tokens = (
       'VBAR',
       'HBAR',
       'PLUS',
       'HASH',
       'BIGO',
       'LEFT',
       'RIGHT',
       'UP',
       'DOWN',
       'NUM',
       'UNIT',
       'X',
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

def t_HASH(t):
    r'#' # 
    return t

def t_BIGO(t):
    r'O(?= |$)' # Is only big-O symbol when followed by space or end of string
    return t

def t_LEFT(t):
    r'<' # 
    return t

def t_RIGHT(t):
    r'>' # 
    return t

def t_UP(t):
    r'\^' # 
    return t

def t_DOWN(t):
    r'v(?= |$)' # Is only down symbol when followed by space or end of string
    return t

def t_NUM(t):
    r'\d+(\.\d+)?' # 
    return t

def t_UNIT(t):
    r'cm|pt|em|%(?=x\d|$)' # Is only unit when followed by other measurement or end of string
    return t

def t_X(t):
    r'x(?=\d)' # Is only unit delimiter when followed by other measurement
    return t

def t_QFILE(t):
    r'".+?"'
    t.value = t.value[1:-1]
    return t

def t_FILE(t):
    r'[^ \n]+'
    return t

t_LF = r'\n'

lexer = lex.lex(debug=dbg.verbose, reflags=0)
