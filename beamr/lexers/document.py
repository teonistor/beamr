'''
Created on 1 Feb 2018

@author: Teodor Gherasim Nistor
'''
from ply import lex
from beamr.lexers.generic import t_error  # Used internally by lex() @UnusedImport
import beamr.interpreters
import beamr.debug as dbg

tokens = ('COMMENT', 'RAW', 'HEADING', 'SLIDE', 'SCISSOR', 'YAML', 'TEXT')

def t_COMMENT(t):
    r'#.*(?=(\n|$))'
    t.value = beamr.interpreters.Comment(t.value)
    return t

def t_RAW(t):
    r'\n(?P<RAW_INDENT> *)&{(?P<RAW_TXT>[\s\S]+?)\n(?P=RAW_INDENT)}'
    _trackLineNo(t.lexer, t.value)
    gd = t.lexer.lexmatch.groupdict()
    t.value = beamr.interpreters.Text(gd['RAW_TXT'] + '\n\n')
    return t

def t_HEADING(t):
    r'\n.+\n[_~=-]{4,}(?=\n)'
    t.lexer.lineno += 2
    t.value = beamr.interpreters.Heading(t.value)
    return t

def t_SLIDE(t):
    r'\n\[(?P<SLD_OPTS>\S*) ?(?P<SLD_TITLE>.*)(?P<SLD_CONTENT>[\s\S]*?)\n\]'
    _trackLineNo(t.lexer, t.value, False)
    gd = t.lexer.lexmatch.groupdict()
    t.value = beamr.interpreters.Slide(
        gd['SLD_TITLE'], gd['SLD_OPTS'], gd['SLD_CONTENT'])
    return t

def t_SCISSOR(t):
    r'(8<|>8){.+?}'
    t.value = beamr.interpreters.ScissorEnv(t.value[3:-1])
    return t

def t_YAML(t):
    r'\n---\n[\s\S]*?(\n\.\.\.|$)'
    _trackLineNo(t.lexer, t.value)
    t.value = beamr.interpreters.Config(t.value)
    return t

def t_TEXT(t):
    r'[\s\S]+?(?=(\n|\[|#|$|>|8|&))'
    _trackLineNo(t.lexer, t.value)
    return t

lexer = lex.lex(debug=dbg.verbose, reflags=0)

def _trackLineNo(lexer, text, autoadvance=True):
    if autoadvance:
        lexer.lineno += text.count('\n')
    else:
        lexer.nextlineno = lexer.lineno + text.count('\n')
#     print 'Change lineno from', lexer.prevlineno, 'to', lexer.lineno
