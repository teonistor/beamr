'''
Created on 13 Nov 2017

@author: Teodor Gherasim Nistor
'''
import sys

file = sys.stderr
verbose = False
quiet = False

def debug(*arg):
    if verbose:
        print('DBG:', *arg, file=file)

def warn(*arg):
    if not quiet:
        print('WARN:', *arg, file=file)

def err(*arg):
    print('ERR:', *arg, file=file)
