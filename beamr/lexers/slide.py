'''
Created on 1 Feb 2018

@author: Teodor Gherasim Nistor
'''
from __future__ import unicode_literals
from ply import lex
from beamr.lexers.generic import t_error  # Used internally by lex() @UnusedImport
from beamr.lexers.document import t_COMMENT, t_RAW, _trackLineNo  # Used internally by lex() @UnusedImport
import beamr

tokens = (
       'COMMENT',
       'AUTORAW',
       'ESCAPE',
       'STRETCH',
       'EMPH',
       'CITATION',
       'FOOTNOTE',
       'URL',
       'LISTITEM',
       'COLUMN',
       'IMGENV',
       'PLUSENV',
       'TABENV',
       'ORGTABLE',
       'RAW',
       'VERBATIM',
       'MACRO',
       'BOX',
       'ANTIESCAPE',
       'TEXT',
       )


def t_AUTORAW(t):
    r'\\[a-zA-Z]+(\{.*?\}|<.*?>|\[.*?\])*(?=[\s\\]|$)'
    t.value = beamr.interpreters.Text(t.value)
    return t

def t_ESCAPE(t):
    r'\\[^0-9A-Za-z\s]' # e.g. \# Inspired from https://github.com/Khan/simple-markdown/blob/master/simple-markdown.js
    t.value = beamr.interpreters.Escape(t.value)
    return t

def t_STRETCH(t):
    r'\[(?P<STRETCH_FLAG_S>[<>_^:+*~.]{1,3})((?P<STRETCH_TXT>.*?[^\\])(?P<STRETCH_FLAG_F>(?P=STRETCH_FLAG_S)|[<>]))?\]'
    gd = t.lexer.lexmatch.groupdict()
    t.value = beamr.interpreters.Stretch(
        gd['STRETCH_FLAG_S'], gd['STRETCH_FLAG_F'], gd['STRETCH_TXT'])
    return t

def t_EMPH(t):
    r'(?P<EMPH_FLAG>[*_~]{1,2})(?P<EMPH_TXT>[\S](.*?[^\s\\])?)(?P=EMPH_FLAG)' # e.g. *Bold text*, ~Strikethrough text~
    gd = t.lexer.lexmatch.groupdict()
    t.value = beamr.interpreters.Emph(
        gd['EMPH_FLAG'], gd['EMPH_TXT'])
    return t

def t_CITATION(t):
    r'\[--(?P<CITE_TXT>.+?)(:(?P<CITE_OPTS>.+?))?\]' # e.g. [--einstein:p.241]
    gd = t.lexer.lexmatch.groupdict()
    t.value = beamr.interpreters.Citation(
        gd['CITE_TXT'], gd['CITE_OPTS'])
    return t

def t_FOOTNOTE(t):
    r'\[-.+?-\]' # e.g. [-24:See attached docs-]
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
    r'\n(?P<LI_INDENT> *)(\*|-)(|\.|,|=)(|\+) .*(\n((?P=LI_INDENT) .*| *))*(?=\n|$)'
    _trackLineNo(t.lexer, t.value, False)
    t.value = beamr.interpreters.ListItem(t.value)
    return t

# e.g.:
# |1.5
#   Column content
# |20%
#   Column content
def t_COLUMN(t):
    r'\n(?P<COL_INDENT> *)\|(\d*\.?\d+(%|)|) *(\n((?P=COL_INDENT) .*| *))+(?=\n|$)'
    _trackLineNo(t.lexer, t.value, False)
    t.value = beamr.interpreters.Column(t.value)
    return t

def t_IMGENV(t):
    r'~{[\s\S]*?}'
    _trackLineNo(t.lexer, t.value, False)
    t.value = beamr.interpreters.ImageEnv(t.value)
    return t

def t_PLUSENV(t):
    r'\n(?P<PLUS_INDENT> *)\[[\s\S]+?\n(?P=PLUS_INDENT)\]'
    _trackLineNo(t.lexer, t.value, False)
    t.value = beamr.interpreters.PlusEnv(t.value)
    return t

def t_TABENV(t):
    r'={[\s\S]+?(?<!\\)}'
    _trackLineNo(t.lexer, t.value, False)
    t.value = beamr.interpreters.TableEnv(t.value[2:-1].replace(r'\}','}'))
    return t

def t_ORGTABLE(t):
    r'\n(?P<ORGTAB_INDENT> *)\|.*(\n(?P=ORGTAB_INDENT)\|.*)+'
    _trackLineNo(t.lexer, t.value, False)
    t.value = beamr.interpreters.OrgTable(t.value)
    return t

def t_VERBATIM(t):
    r'\n(?P<VBTM_INDENT> *){{(?P<VBTM_HEAD>.*)\n(?P<VBTM_BODY>[\s\S]+?)\n(?P=VBTM_INDENT)}}'
    _trackLineNo(t.lexer, t.value)
    gd = t.lexer.lexmatch.groupdict()
    t.value = beamr.interpreters.VerbatimEnv(
        gd['VBTM_HEAD'].strip(), gd['VBTM_BODY'])
    return t

def t_MACRO(t):
    r'%{[\s\S]+?}'
    _trackLineNo(t.lexer, t.value, False)
    t.value = beamr.interpreters.Macro(t.value)
    return t

def t_BOX(t):
    r'\n(?P<BOX_INDENT> *)\((?P<BOX_KIND>\*|!|\?)(?P<BOX_TITLE>.+)(?P<BOX_CONTENT>[\s\S]+?)\n(?P=BOX_INDENT)\)'
    _trackLineNo(t.lexer, t.value, False)
    gd = t.lexer.lexmatch.groupdict()
    t.value = beamr.interpreters.Box(
        gd['BOX_KIND'].strip(), gd['BOX_TITLE'], gd['BOX_CONTENT'])
    return t

def t_ANTIESCAPE(t):
    r'[^0-9A-Za-z\u00c0-\uffff\s]'
    t.value = beamr.interpreters.Antiescape(t.value)
    return t

def t_TEXT(t):
    r'[\s\S]+?(?=[^0-9A-Za-z\u00c0-\uffff\s]|\n|$)' # Inspired loosely from https://github.com/Khan/simple-markdown/blob/master/simple-markdown.js
    _trackLineNo(t.lexer, t.value)
    t.value = beamr.interpreters.Text(t.value)
    return t

lexer = lex.lex(debug=beamr.debug.verbose, reflags=0)
