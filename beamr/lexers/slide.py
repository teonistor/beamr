'''
Created on 1 Feb 2018

@author: Teodor Gherasim Nistor
'''
from ply import lex
from beamr.lexers.generic import t_error  # Used internally by lex() @UnusedImport
from beamr.lexers.document import t_COMMENT  # Used internally by lex() @UnusedImport
import beamr

tokens = (
       'COMMENT',
       'ESCAPE',
       'STRETCH1',
       'STRETCH2',
       'EMPH',
       'CITATION',
       'FOOTNOTE',
       'URL',
       'LISTITEM',
       'COLUMN',
       'IMGENV',
       'PLUSENV',
       'TABENV',
       'VERBATIM',
       'MACRO',
       'BOX',
       'ANTIESCAPE',
       'TEXT',
       )


def t_ESCAPE(t):
    r'\\[^0-9A-Za-z\s]' # e.g. \# # Almost copy-paste from https://github.com/Khan/simple-markdown/blob/master/simple-markdown.js
    t.value = beamr.interpreters.Escape(t.value)
    return t

def t_STRETCH1(t):
    r'\[[<>_^:+]\]' # e.g. [+] # TODO Tailor to those actually used
    t.value = beamr.interpreters.Stretch(t.value[1])
    return t

def t_STRETCH2(t):
    r'\[[<>_v^].+?[<>_v^]\]' # e.g. [< Stretched text >]
    t.value = beamr.interpreters.Stretch(t.value[1]+t.value[-2], t.value[2:-2])
    return t

def t_EMPH(t):
    r'(?P<EMPH_FLAG>[*_~]{1,2})(?P<EMPH_TXT>[\S](.*?[\S])?)(?P=EMPH_FLAG)' # e.g. *Bold text*, ~Strikethrough text~
    global lexer
    gd = lexer.lexmatch.groupdict()
    t.value = beamr.interpreters.Emph(
        gd['EMPH_FLAG'], gd['EMPH_TXT'])
    return t

def t_CITATION(t):
    r'\[--.+?\]' # e.g. [fn:See attached docs]
    t.value = beamr.interpreters.Citation(t.value[3:-1])
    return t

def t_FOOTNOTE(t):
    r'\[-.+?-\]' # e.g. [fn:See attached docs]
    t.value = beamr.interpreters.Footnote(t.value[2:-2])
    return t

def t_URL(t):
    r'\[.+?\]' # e.g. [https://www.example.com/]
    t.value = beamr.interpreters.Url(t.value[1:-1])
    return t
    
# e.g.:
# - One
# *. Two
# -,+ Three
def t_LISTITEM(t):
    r'(^|\n)(?P<LI_INDENT> *)(\*|-)(|\.|,|=)(|\+) .*(\n((?P=LI_INDENT) .*| *))*(?=\n|$)'
    t.value = beamr.interpreters.ListItem(t.value)
    return t

# e.g.:
# |1.5
#   Column content
# |20%
#   Column content
def t_COLUMN(t):
    r'(^|\n)(?P<COL_INDENT> *)\|(\d*\.?\d+(%|)|) *(\n((?P=COL_INDENT) .*| *))+(?=\n|$)'
    t.value = beamr.interpreters.Column(t.value)
    return t

def t_IMGENV(t):
    r'~{[\s\S]*?}'
    t.value = beamr.interpreters.ImageEnv(t.value)
    return t

def t_PLUSENV(t):
    r'(^|\n)(?P<PLUS_INDENT> *)\[[\s\S]+\n(?P=PLUS_INDENT)\]'
    t.value = beamr.interpreters.PlusEnv(t.value)
    return t

def t_TABENV(t):
    r'={[\s\S]+?}'
    t.value = beamr.interpreters.TableEnv(t.value)
    return t

def t_VERBATIM(t):
    r'(^|\n)(?P<VBTM_INDENT> *){{(?P<VBTM_HEAD>.*)\n(?P<VBTM_BODY>[\s\S]+)\n(?P=VBTM_INDENT)}}'
    global lexer
    gd = lexer.lexmatch.groupdict()
    t.value = beamr.interpreters.VerbatimEnv(
        gd['VBTM_HEAD'].strip(), gd['VBTM_BODY'])
    return t

def t_MACRO(t):
    r'%{[\s\S]+?}'
    t.value = beamr.interpreters.Macro(t.value)
    return t

def t_BOX(t):
    r'(^|\n)(?P<BOX_INDENT> *)\((\*|!)[\s\S]+?\n(?P=BOX_INDENT)\)'
    t.value = beamr.interpreters.Box(t.value)
    return t

def t_ANTIESCAPE(t):
    r'[%&]'
    t.value = beamr.interpreters.Text('\\' + t.value)
    return t

def t_TEXT(t):
    r'[\s\S]+?(?=[^0-9A-Za-z\s]|\n|$)' # Inspired loosely from https://github.com/Khan/simple-markdown/blob/master/simple-markdown.js
    t.value = beamr.interpreters.Text(t.value)
    return t

lexer = lex.lex(debug=beamr.debug.verbose, reflags=0)
