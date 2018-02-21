'''
Created on 1 Feb 2018

@author: Teodor Gherasim Nistor
'''
from ply import lex
from pybeams.lexers.generic import t_error  # @UnusedImport
import pybeams.interpreters
import pybeams.debug as dbg

tokens = ('YAML', 'HEADING', 'COMMENT', 'SLIDE')

def t_COMMENT(t):
    r'#[\s\S]*?(\n|$)'
    t.value = pybeams.interpreters.Comment(t.value)
    return t

def t_HEADING(t):
    r'(^|\n).+\n[_~=-]{4,}\n'
    t.value = pybeams.interpreters.Heading(t.value)
    return t

def t_SLIDE(t):
    r'(^\[|\n\[)[\s\S]+?\n\]'
    t.value = pybeams.interpreters.Slide(t.value)
    return t

# Rather, potential YAML. Parsing will be attempted, but may fail
t_YAML = r'[\s\S]+?(?=(\n|\[|#|$))'

lexer = lex.lex(debug=dbg.verbose, reflags=0)
