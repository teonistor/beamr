'''
Created on 1 Feb 2018

@author: Teodor Gherasim Nistor
'''
from pybeams.debug import warn

def t_error(t):
    warn ('Skip lexing error..', t)
    t.lexer.skip(1)
