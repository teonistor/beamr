'''
Slide lexer defines tokens used on all but the first level of the input document
(inside slides and inside all subsequent nested hierarchical nodes).
Some document tokens are reused.

Created on 1 Feb 2018

@author:     Teodor G Nistor

@copyright:  2018 Teodor G Nistor

@license:    MIT License
'''
from __future__ import unicode_literals
from ply import lex
from beamr.lexers.generic import t_error  # Used internally by lex() @UnusedImport
from beamr.lexers.document import t_COMMENT, t_RAW, t_MACRO, _argLineno  # Used internally by lex() @UnusedImport
import beamr

tokens = (
       'COMMENT',
       'AUTORAW',
       'ESCAPE',
       'ART',
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
    r'\\[a-zA-Z]+\*?(\{.*?\}|<.*?>|\[.*?\])*(?=[^\]}>]|$)' # e.g. \color{blue}
    t.value = beamr.interpreters.Text(t.value, **_argLineno(t.lexer, t.value))
    return t

def t_ESCAPE(t):
    r'\\[^0-9A-Za-z\s\\]' # e.g. \# Inspired from https://github.com/Khan/simple-markdown/blob/master/simple-markdown.js
    t.value = beamr.interpreters.Escape(t.value, **_argLineno(t.lexer, t.value))
    return t

def t_ART(t):
    r'-->|<->|<--|\|->|<-\||==>|<=>|<==|:\.\.|\.\.\.|:::|\\{2,3}' # e.g. -->, <=>, ...
    t.value = beamr.interpreters.AsciiArt(t.value, **_argLineno(t.lexer, t.value))
    return t

# For historical reasons called stretch; square bracket constructs were initially only for stretching and alignment, but that evolved
def t_STRETCH(t):
    r'\[(?P<STRETCH_FLAG_S>[<>_^:+*~.=!|@]{1,3})((?P<STRETCH_TXT>.*?[^\\])(?P<STRETCH_FLAG_F>(?P=STRETCH_FLAG_S)|[<>]))??\]'
    gd = t.lexer.lexmatch.groupdict()
    t.value = beamr.interpreters.Stretch(
        flagS=gd['STRETCH_FLAG_S'],
        flagF=gd['STRETCH_FLAG_F'],
        txt=gd['STRETCH_TXT'],
        **_argLineno(t.lexer, t.value))
    return t

def t_EMPH(t):
    r'(?P<EMPH_FLAG>[*_]{1,2})(?P<EMPH_TXT>[\S](.*?[^\s\\])?)(?P=EMPH_FLAG)' # e.g. *Bold text*, ~Strikethrough text~
    gd = t.lexer.lexmatch.groupdict()
    t.value = beamr.interpreters.Emph(
        flag=gd['EMPH_FLAG'],
        txt=gd['EMPH_TXT'],
        **_argLineno(t.lexer, t.value))
    return t

def t_CITATION(t):
    r'\[--(?P<CITE_TXT>.+?)(:(?P<CITE_OPTS>.+?))?\]' # e.g. [--einstein:p.241]
    gd = t.lexer.lexmatch.groupdict()
    t.value = beamr.interpreters.Citation(
        gd['CITE_TXT'], opts=gd['CITE_OPTS'], **_argLineno(t.lexer, t.value))
    return t

def t_FOOTNOTE(t):
    r'\[-((?P<FN_LABEL>.*?):)?(?P<FN_TXT>.*?)-\](?P<FN_OVRL>\<.*?\>)?' # e.g. [-24:See attached docs-]
    gd = t.lexer.lexmatch.groupdict()
    t.value = beamr.interpreters.Footnote(
        label=gd['FN_LABEL'],
        text=gd['FN_TXT'],
        overlay=gd['FN_OVRL'],
        **_argLineno(t.lexer, t.value))
    return t

def t_URL(t):
    r'\[(?P<URL_TEXT>\[.+?\])?(?P<URL_TARGET>.+?)\]' # e.g. [https://www.example.com/], [[example]https://www.example.com/]
    gd = t.lexer.lexmatch.groupdict()
    t.value = beamr.interpreters.Url(gd['URL_TARGET'], text=gd['URL_TEXT'], **_argLineno(t.lexer, t.value))
    return t
    
# e.g.:
# - One
# *. Two
# -,+ Three
def t_LISTITEM(t):
    r'\n(?P<LI_INDENT> *)(\*|-)(|\.|,|=)(|\+) .*(\n((?P=LI_INDENT) .*| *))*(?=\n|$)'
    t.value = beamr.interpreters.ListItem(txt=t.value, **_argLineno(t.lexer, t.value))
    return t

# e.g.:
# |1.5
#   Column content
# |20%
#   Column content
def t_COLUMN(t):
    r'\n(?P<COL_INDENT> *)\| *((?P<COL_WNUM>\d*\.?\d+)(?P<COL_WUNIT>%)?)? *(?P<COL_ALIGN>[_^])? *(?P<COL_OVRL>\<.*\>)?(?P<COL_CONTENT>(\n((?P=COL_INDENT) .*| *))+)(?=\n|$)'
    gd = t.lexer.lexmatch.groupdict()
    t.value = beamr.interpreters.Column(
        widthNum=gd['COL_WNUM'],
        widthUnit=gd['COL_WUNIT'],
        align=gd['COL_ALIGN'],
        overlay=gd['COL_OVRL'],
        content=gd['COL_CONTENT'],
        **_argLineno(t.lexer, t.value))
    return t

def t_IMGENV(t):
    r'~{[\s\S]*?}(\<.*\>)?'
    t.value = beamr.interpreters.ImageEnv(t.value, **_argLineno(t.lexer, t.value))
    return t

def t_PLUSENV(t):
    r'\n(?P<PLUS_INDENT> *)\[(?P<PLUS_TXT>[\s\S]+?\n)(?P=PLUS_INDENT)\]'
    t.value = beamr.interpreters.PlusEnv(
        t.lexer.lexmatch.group('PLUS_TXT'),
        **_argLineno(t.lexer, t.value))
    return t

def t_TABENV(t):
    r'={[\s\S]+?(?<!\\)}'
#     _trackLineNo(t.lexer, t.value, False)
#     t.value = beamr.interpreters.TableEnv(t.value[2:-1].replace(r'\}','}'))
#     return t

def t_ORGTABLE(t):
    r'\n(?P<ORGTAB_INDENT> *)\|.*(\n(?P=ORGTAB_INDENT)\|.*)+'
    t.value = beamr.interpreters.OrgTable(txt=t.value, **_argLineno(t.lexer, t.value))
    return t

def t_VERBATIM(t):
    r'\n(?P<VBTM_INDENT> *){{(?P<VBTM_HEAD>.*)\n(?P<VBTM_BODY>[\s\S]+?)\n(?P=VBTM_INDENT)}}'
    gd = t.lexer.lexmatch.groupdict()
    t.value = beamr.interpreters.VerbatimEnv(
        head=gd['VBTM_HEAD'].strip(), txt=gd['VBTM_BODY'], **_argLineno(t.lexer, t.value))
    return t

def t_BOX(t):
    r'\n(?P<BOX_INDENT> *)\((?P<BOX_KIND>\*|!|\?)(?P<BOX_TITLE>.*)(?P<BOX_CONTENT>[\s\S]+?)\n(?P=BOX_INDENT)\)(?P<BOX_OVRL>\<.*?\>)?'
    gd = t.lexer.lexmatch.groupdict()
    t.value = beamr.interpreters.Box(
        kind=gd['BOX_KIND'].strip(),
        title=gd['BOX_TITLE'],
        content=gd['BOX_CONTENT'],
        overlay=gd['BOX_OVRL'],
        **_argLineno(t.lexer, t.value))
    return t

def t_ANTIESCAPE(t):
    r'[^0-9A-Za-z\u00c0-\uffff\s]'
    t.value = beamr.interpreters.Antiescape(t.value, **_argLineno(t.lexer, t.value))
    return t

def t_TEXT(t):
    r'[\s\S]+?(?=[^0-9A-Za-z\u00c0-\uffff\s]|\n|$)' # Inspired loosely from https://github.com/Khan/simple-markdown/blob/master/simple-markdown.js
    t.value = beamr.interpreters.Text(t.value, **_argLineno(t.lexer, t.value))
    return t

lexer = lex.lex(debug=beamr.debug.verbose, reflags=0)
