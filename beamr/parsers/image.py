'''
Created on 15 Feb 2018

@author: Teodor Gherasim Nistor
'''
import beamr.debug as debug
from beamr.parsers.generic import p_nil  # Used internally by yacc() @UnusedImport
from ply import yacc
from beamr.lexers.image import tokens  # Used internally by yacc() @UnusedImport

start = 'main'

def p_main(t):
    '''main : files shape align dims'''
    t[0] = (t[1], t[2], t[3], t[4])
        
def p_elem(t):
    '''files : files FILE
             | files QFILE
             | FILE
             | QFILE
             | files LF QFILE
             | files LF FILE'''
    if len(t) == 2:
        t[0] = [[t[1]]]
    elif len(t) == 3:
        t[0] = t[1]
        t[0][-1].append(t[2])
    else:
        t[0] = t[1]
        t[0].append([t[3]])


def p_shape(t):
    '''shape : VBAR
             | HBAR
             | PLUS
             | HASH
             | BIGO
             | nil'''
    t[0] = t[1]

def p_align(t):
    '''align : LEFT
             | RIGHT
             | UP
             | DOWN
             | nil'''
    t[0] = t[1]


# Lambda hack below caused by excesive caffeination
def p_dims_dim(t):
    '''dims : dim X dim
            | dim
            | X dim'''
    if len(t) == 2:
        t[0] = (_optional_format(t[1], 'width'),
                None)
    elif len(t) == 3:
        t[0] = (None,
                _optional_format(t[2], 'height'))
    else:
        t[0] = (_optional_format(t[1], 'width'),
                _optional_format(t[3], 'height'))

def p_dims_nil(t):
    '''dims : nil'''
    t[0] = (None, None)


def p_dim(p):
    '''dim : NUM UNIT
           | NUM'''
    fl = float(p[1])
    unit = p[2] if len(p) == 3 else None
    if not unit:
        if fl > 1.0:
            fl *= 0.01
        p[0] = (fl, r'\text%s', True)
    elif unit == '%':
        p[0] = (fl*0.01, r'\text%s', True)
    else:
        p[0] = (fl, unit, False)


def p_error(p):
    # TODO instead of discarding bad tokens, consider them file names, or pieces thereof, and return to lexer in a sensible fashion
    # BUT currently this fixes empty lines in image environment automagically so...
    if p:
        debug.warn('Syntax error in Image environment at "', p.value, '". Images or parameters may be missing from output.')
        global parser
        parser.errok()
    else:
        debug.warn('Syntax error at the end of Image environment.')

def _optional_format(a, b):
    if a[2]:
        return (a[0], a[1] % b)
    else:
        return (a[0], a[1])

parser = yacc.yacc(tabmodule='image_parsetab', debugfile='image_parsedbg', debug=not debug.quiet)
