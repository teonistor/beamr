'''
Created on 1 Feb 2018

@author: Teodor Gherasim Nistor
'''
from beamr.parsers.generic import p_nil, p_error  # Used internally by yacc() @UnusedImport
from beamr.lexers.document import tokens  # Used internally by yacc() @UnusedImport
from ply import yacc
import beamr.debug as debug

start = 'main'

def p_main_notext(t):
    '''main : main COMMENT
            | main HEADING
            | main SLIDE
            | main SCISSOR
            | main YAML
            | nil'''
    if len(t) > 2:
        t[0] = t[1]
        t[0].append(t[2])
    else:
        t[0] = []

def p_main_text(t):
    '''main : main TEXT'''
    t[0] = t[1]

parser = yacc.yacc(tabmodule='document_parsetab', debugfile='document_parsedbg', debug=not debug.quiet)
