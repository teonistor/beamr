'''
Created on 1 Feb 2018

@author: Teodor Gherasim Nistor
'''
from pybeams.parsers.generic import p_nil, p_error  # @UnusedImport
from pybeams.lexers.document import tokens  # @UnusedImport
from ply import yacc
import pybeams
import pybeams.debug as debug

start = 'main'

def p_main(t): # TODO solve shift-reduce in yamlconcat. Currently defaults to desired action, but.
    '''main : main yamlconcat
            | main HEADING
            | main SLIDE
            | main COMMENT
            | nil'''
    if len(t) > 2:
        t[0] = t[1]
        t[0].append(t[2])
    else:
        t[0] = []

# Workaround to create a single Config from concatenated bits of potential YAML sitting next to each other
def p_yamlconcat(t):
    'yamlconcat : yamlconcatinner'
    t[0] = pybeams.interpreters.Config(t[1])
        
def p_yamlconcatinner(t):
    '''yamlconcatinner : yamlconcatinner YAML
                       | YAML'''
    if len(t) > 2:
        t[0] = t[1] + t[2]
    else:
        t[0] = t[1]

parser = yacc.yacc(tabmodule='document_parsetab', debugfile='document_parsedbg', debug=not debug.quiet)
