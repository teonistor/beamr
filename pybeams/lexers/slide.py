'''
Created on 1 Feb 2018

@author: Teodor Gherasim Nistor
'''
from ply import lex
from pybeams.lexers.generic import t_error  # @UnusedImport
from pybeams.lexers.document import t_COMMENT  # @UnusedImport
import pybeams.debug as debug
import pybeams

tokens = (
       'COMMENT',
       'ESCAPE',
       'STRETCH',
       'EMPH',
       'NOTE',
       'URL',
       'LISTITEM',
       'COLUMN',
       'IMGENV',
       'PLUSENV',
       'TABENV',
       'SCIENV',
       'VERBATIM',
       'MACRO',
       'BOX',
       'TEXT',
       )


def t_ESCAPE(t):
    r'\\[^0-9A-Za-z\s]' # e.g. \# # Almost copy-paste from https://github.com/Khan/simple-markdown/blob/master/simple-markdown.js
    t.value = pybeams.interpreters.Escape(t.value)
    return t

def t_STRETCH(t):
    r'\[[<>v^].+?[<>v^]\]' # e.g. [< Stretched text >]
    t.value = pybeams.interpreters.Stretch(t.value)
    return t

def t_EMPH(t):
    r'(?P<EMPH_MARK>\*{1,4}).+?(?P=EMPH_MARK)' # e.g. *Bold text*, **Red text** - allow config
    # TODO perhaps this regex isn't the best approach..?
    t.value = pybeams.interpreters.Emph(t.value)
    return t

def t_NOTE(t):
    r'\[(fn|en|sn):.+?\]' # e.g. [fn:See attached docs]
    t.value = pybeams.interpreters.Note(t.value)
    return t

def t_URL(t):
    r'\[.+?\]' # e.g. [https://www.example.com/]
    t.value = pybeams.interpreters.Url(t.value)
    return t
    
# e.g.:
# - One
# *. Two
def t_LISTITEM(t):
    r'(^|\n)(?P<LI_INDENT> *)(\*|-)(|\.|,|=)(|\+) .*(\n((?P=LI_INDENT) .*| *))*(?=\n|$)'
    # TODO this regex puts list items separated by empty line in separate lists, but those separated by lines with blanks in the same list - confusing?
    t.value = pybeams.interpreters.ListItem(t.value)
    return t

# e.g.:
# |1.5
#   Column content
# |20%
#   Column content
def t_COLUMN(t):
    r'(^|\n)(?P<COL_INDENT> *)\|(\d*\.?\d+(%|)|) *(\n((?P=COL_INDENT) .*| *))+(?=\n|$)'
    t.value = pybeams.interpreters.Column(t.value)
    return t

def t_IMGENV(t):
    r'~{[\s\S]*?}'
    t.value = pybeams.interpreters.ImageEnv(t.value)
    return t

def t_PLUSENV(t):
    r'(^|\n)(?P<PLUS_INDENT> *)\[[\s\S]+\n(?P=PLUS_INDENT)\]'
    t.value = pybeams.interpreters.PlusEnv(t.value)
    return t

def t_TABENV(t):
    r'={[\s\S]+?}'
    t.value = pybeams.interpreters.TableEnv(t.value)
    return t

def t_SCIENV(t):
    r'(8<|>8){[\s\S]+?}'
    t.value = pybeams.interpreters.ScissorEnv(t.value)
    return t

def t_VERBATIM(t):
    r'(^|\n)(?P<VBTM_INDENT> *){{[\s\S]+\n(?P=VBTM_INDENT)}}'
    t.value = pybeams.interpreters.VerbatimEnv(t.value)
    return t

def t_MACRO(t):
    r'%{[\s\S]+?}'
    t.value = pybeams.interpreters.Macro(t.value)
    return t

def t_BOX(t):
    r'(^|\n)(?P<BOX_INDENT> *)\((\*|!)[\s\S]+?\n(?P=BOX_INDENT)\)'
    t.value = pybeams.interpreters.Box(t.value)
    return t

def t_TEXT(t):
    r'[\s\S]+?(?=[^0-9A-Za-z\s\u00c0-\uffff]|\n|$)' # Almost copy-paste from https://github.com/Khan/simple-markdown/blob/master/simple-markdown.js
    t.value = pybeams.interpreters.Text(t.value)
    return t

lexer = lex.lex(debug=debug.verbose, reflags=0)
