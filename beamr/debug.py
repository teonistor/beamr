'''
Created on 13 Nov 2017

@author: Teodor Gherasim Nistor
'''
from __future__ import print_function
import sys

verbose = 0
quiet = 0
infname = '<stdin>'

def debug(*arg, **kw):
    if verbose:
        _print(arg, kw, 'DBG')

def warn(*arg, **kw):
    if quiet < 2:
        _print(arg, kw, 'WARN')

def err(*arg, **kw):
    if quiet < 3:
        _print(arg, kw, 'ERR')

def _print(arg, kw, pre=''):
    kw['file'] = sys.stderr
    if 'range' in kw:
        pre = '%s:%s: %s:' % (infname, kw['range'], pre)
        del kw['range']
    else:
        pre = '%s: %s:' % (infname, pre)
    print(pre, *arg, **kw)
