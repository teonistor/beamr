'''
Created on 1 Feb 2018

@author: Teodor Gherasim Nistor
'''
from beamr.debug import warn

def t_error(t):
    warn ('Skip lexing error..', t, 'at line', t.lexer.lineno)
    t.lexer.skip(1)
