'''
Generic functionality used by all lexers
Created on 1 Feb 2018

@author:     Teodor G Nistor

@copyright:  2018 Teodor G Nistor

@license:    MIT License
'''
from beamr.debug import warn

def t_error(t):
    warn ('Skip lexing error..', t, 'at line', t.lexer.lineno)
    t.lexer.skip(1)
