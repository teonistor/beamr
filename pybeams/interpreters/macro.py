'''
Created on 1 Feb 2018

@author: Teodor Gherasim Nistor
'''

from pybeams.debug import warn
from pybeams.interpreters.textual import Text


class Macro(Text):
    
    def __init__(self, name, *param):
        
        # Check all known macros
        if name=='gm':
            pass
        
        # UNknown macro
        else:
            warn('Unknown macro:', name)
            # TODO set upper to an empty text so it doesn't err