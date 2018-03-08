'''
Created on 1 Feb 2018

@author: Teodor Gherasim Nistor
'''
from ply import lex
from beamr.lexers.generic import t_error  # Used internally by lex() @UnusedImport
import beamr.interpreters
import beamr.debug as dbg

tokens = ('COMMENT', 'HEADING', 'SLIDE', 'SCISSOR', 'YAML', 'TEXT')

def t_COMMENT(t):
    r'#[\s\S]*?(\n|$)'
    t.value = beamr.interpreters.Comment(t.value)
    return t

def t_HEADING(t):
    r'(^|\n).+\n[_~=-]{4,}\n'
    t.value = beamr.interpreters.Heading(t.value)
    return t

def t_SLIDE(t):
    r'(^\[|\n\[)[\s\S]+?\n\]'
    t.value = beamr.interpreters.Slide(t.value)
    return t

def t_SCISSOR(t):
    r'(8<|>8){[\s\S]+?}'
    t.value = beamr.interpreters.ScissorEnv(t.value[3:-1])
    return t

def t_YAML(t):
    r'(^|\n)---\n[\s\S]*?(\n\.\.\.|$)'
    t.value = beamr.interpreters.Config(t.value)
    return t

# Rather, potential YAML. Parsing will be attempted, but may fail
t_TEXT = r'[\s\S]+?(?=(\n|\[|#|$|>|8))'

lexer = lex.lex(debug=dbg.verbose, reflags=0)
