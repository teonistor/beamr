'''
Logging utilities
Created on 13 Nov 2017

@author:     Teodor G Nistor

@copyright:  2018 Teodor G Nistor

@license:    MIT License
'''
from __future__ import print_function
import sys

# Default logging settings, likely to be changed from cli
verbose = 0
quiet = 0
infname = '<stdin>'

def debug(*arg, **kw):
    ''' Print a debugging message only if verbose level set
    :param arg: Iterable of things to print
    :param kw: 'range' and other printing options
    '''
    if verbose:
        _print(arg, kw, 'DBG')

def warn(*arg, **kw):
    ''' Print a warning message only if quiet level is at most 1
    :param arg: Iterable of things to print
    :param kw: 'range' and other printing options
    '''
    if quiet < 2:
        _print(arg, kw, 'WARN')

def err(*arg, **kw):
    ''' Print an error message only if quiet level is at most 2
    :param arg: Iterable of things to print
    :param kw: 'range' and other printing options
    '''
    if quiet < 3:
        _print(arg, kw, 'ERR')

def _print(arg, kw, pre=''):
    '''
    Print arg with a prefix of file, location, and message type
    :param arg: Iterable of things to print
    :param kw: Dictionary of printing options ('file' will be overriden with stderr)
               A line number/range should be given under key 'range'
    :param pre: Prefix denoting message type
    '''
    kw['file'] = sys.stderr
    if 'range' in kw:
        pre = '%s:%s: %s:' % (infname, kw['range'], pre)
        del kw['range']
    else:
        pre = '%s: %s:' % (infname, pre)
    print(pre, *arg, **kw)
