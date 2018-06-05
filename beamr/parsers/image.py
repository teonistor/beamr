'''
Image frame parser
Created on 15 Feb 2018

@author:     Teodor G Nistor

@copyright:  2018 Teodor G Nistor

@license:    MIT License
'''
import beamr.debug as debug
from beamr.parsers.generic import p_nil  # Used internally by yacc() @UnusedImport
from ply import yacc
from beamr.lexers.image import tokens  # Used internally by yacc() @UnusedImport

start = 'main'

def p_main(t):
    '''main : files shape dims'''
    t[0] = (t[1], t[2], t[3])

def p_files(t):
    '''files : files file
             | files DOT
             | file
             | DOT
             | files LF file
             | files LF DOT
    '''
    if len(t) == 2:
        t[0] = [[t[1]]] # First file
    elif len(t) == 3:
        t[0] = t[1]
        t[0][-1].append(t[2]) # Add file to inner list (most recent line)
    else:
        t[0] = t[1]
        t[0].append([t[3]]) # Add new line with one new file

def p_file(t):
    '''file : FILE
            | FILE OVRL
            | QFILE
            | QFILE OVRL'''
    if len(t) > 2:
        t[0] = (t[1], t[2]) # Overlay present
    else:
        t[0] = (t[1], None) # No overlay

def p_shape(t):
    '''shape : VBAR
             | HBAR
             | PLUS
             | nil'''
    t[0] = t[1]

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
    # Currently this fixes empty lines in image environment automagically, though instead of
    # discarding bad tokens one could try returning them as file names or something
    if p and p.value:
        debug.warn('Syntax error in Image Frame: invalid token', p.value, range=p.lexer.lineno)
        global parser
        parser.errok()
    else:
        debug.warn('Syntax error at the end of Image Frame', range=p.lexer.lineno)

def _optional_format(a, b):
    'Helper for transparently formatting relative dimensions'
    if a[2]:
        return (a[0], a[1] % b)
    else:
        return (a[0], a[1])

parser = yacc.yacc(tabmodule='image_parsetab', debugfile='image_parsedbg', debug=debug.quiet<2)
