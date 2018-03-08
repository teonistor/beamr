'''
Created on 1 Feb 2018

@author: Teodor Gherasim Nistor
'''
import beamr.debug as debug
from beamr.parsers.generic import p_nil, p_error  # Used internally by yacc() @UnusedImport
from ply import yacc
from beamr.lexers.slide import tokens  # Used internally by yacc() @UnusedImport

start = 'main'

def p_main(t):
    '''main : main elem
            | nil'''
    if len(t) > 2:
        t[0] = t[1]
        t[0].append(t[2])
    else:
        t[0] = []
        
def p_elem(t):
    '''elem : COMMENT
            | ESCAPE
            | STRETCH1
            | STRETCH2
            | EMPH
            | CITATION
            | FOOTNOTE
            | URL
            | LISTITEM
            | COLUMN
            | IMGENV
            | PLUSENV
            | TABENV
            | VERBATIM
            | MACRO
            | BOX
            | ANTIESCAPE
            | TEXT'''
    t[0] = t[1]

parser = yacc.yacc(tabmodule='slide_parsetab', debugfile='slide_parsedbg', debug=not debug.quiet)
