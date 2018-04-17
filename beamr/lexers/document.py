'''
Document lexer defines tokens used at the root of the input file
Created on 1 Feb 2018

@author:     Teodor G Nistor

@copyright:  2018 Teodor G Nistor

@license:    MIT License
'''
from ply import lex
from beamr.lexers.generic import t_error  # Used internally by lex() @UnusedImport
import beamr.interpreters
import beamr.debug as dbg

tokens = ('COMMENT', 'RAW', 'HEADING', 'SLIDE', 'SCISSOR', 'MACRO', 'YAML', 'TEXT')

def t_COMMENT(t):
    r'#.*(?=(\n|$))'
    t.value = beamr.interpreters.Comment(t.value, **_argLineno(t.lexer, t.value))
    return t

def t_RAW(t):
    r'\n(?P<RAW_INDENT> *)&{(?P<RAW_TXT>[\s\S]+?)\n(?P=RAW_INDENT)}'
    gd = t.lexer.lexmatch.groupdict()
    t.value = beamr.interpreters.Text(gd['RAW_TXT'] + '\n\n', **_argLineno(t.lexer, t.value))
    return t

def t_HEADING(t):
    r'\n.+\n[_~=-]{4,}(?=\n)'
    t.value = beamr.interpreters.Heading(t.value, **_argLineno(t.lexer, t.value))
    return t

def t_SLIDE(t):
    r'\n\[(?P<SLD_PLAIN>\/)?(?P<SLD_ALIGN>[_^])?(?P<SLD_OPTS>\S*) ?(?P<SLD_TITLE>.*)(\n~(?P<SLD_BG>[^\n|]*)(?P<SLD_BGUP>\|)?)?(?P<SLD_CONTENT>[\s\S]*?)\n\]'
    gd = t.lexer.lexmatch.groupdict()
    t.value = beamr.interpreters.Slide(
        title=gd['SLD_TITLE'],
        opts=gd['SLD_OPTS'],
        plain=gd['SLD_PLAIN'],
        align=gd['SLD_ALIGN'],
        bg=gd['SLD_BG'],
        bgUp=gd['SLD_BGUP'],
        content=gd['SLD_CONTENT'],
        **_argLineno(t.lexer, t.value))
    return t

def t_SCISSOR(t):
    r'(8<|>8){.+?}'
    t.value = beamr.interpreters.ScissorEnv(t.value[3:-1], **_argLineno(t.lexer, t.value))
    return t

def t_MACRO(t):
    r'%{[\s\S]+?}'
    t.value = beamr.interpreters.Macro(txt = t.value[2:-1], **_argLineno(t.lexer, t.value))
    return t

def t_YAML(t):
    r'\n---(?=\n)[\s\S]*?(\n\.\.\.|$)'
    t.value = beamr.interpreters.Config(t.value, **_argLineno(t.lexer, t.value))
    return t

def t_TEXT(t):
    r'[\s\S]+?(?=(\n|\[|#|$|>|8|&|%))'
    t.lexer.lineno += t.value.count('\n')
    return t

lexer = lex.lex(debug=dbg.verbose, reflags=0)

def _argLineno(lexer, text):
    '''
    Return a dictionary of the lexer in use, line number at the moment, and line number
    post evaluation of text (useful for passing to interpreter constructors)
    :param lexer: Current lexer instance in use
    :param text: Text being evaluated
    '''
    lineno = lexer.lineno
    nextlineno = lineno + text.count('\n')
    return {'lexer': lexer,
            'lineno': lineno,
            'nextlineno': nextlineno}
