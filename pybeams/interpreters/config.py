'''
Created on 6 Feb 2018

@author: Teodor Gherasim Nistor
'''

import yaml

# TODO could move class methods and effective config to module level
# TODO prevent the user from too easily breaking the config - is there another way except littering try/except everywhere config is used??
# TODO is there a case for overriding lists completely? nb. Can be done by setting to non-list then to fresh list later in the yaml

class Config:
    
    # Initial config
    effectiveConfig = {
        'docclass': 'beamer', # Obvs
        'packages': [
                'utf8,inputenc',
                'T1,fontenc',
                #'hidelinks,hyperref', # Clashes with beamer...?
                'upquote',
                'listings'
                # TODO give example for setting a font
                # tikz? natbib? etc??
                
            ],
        
        'graphicspath': [
               # '/home/teo/Documents/Coursework1718/comp3200-p3p/pybeams/test/' # TODO
               # Graphics path resolution: pdflatex automatically looks in the directory where it was called, but should it also look in the directory of the input file?
            ],

        # Arrangement themes and color schemes
        'theme': 'Copenhagen',
        'scheme': 'beaver',

        # This is dict because elements thereof are meant to be overridden
        'emph': {
                1: r'\textbf{%s}',
                2: r'\textit{%s}',
                3: r'\emph{%s}',
                4: r'\emph{%s}'
            }
    }
    
    def __init__(self, txt):
        self.txt = txt
    
    @classmethod
    def resolve(cls, docList):
        i = 0
        while i < len(docList):
            if isinstance(docList[i], Config):
                try:
                    cls.recursiveUpdate(cls.effectiveConfig,
                                        yaml.load(docList.pop(i).txt))
                except:
                    i += 1
            else:
                i += 1
                
    @staticmethod
    def recursiveUpdate(target, content):
        for k in content:
            if k in target and isinstance(content[k], dict) and isinstance(target[k], dict):
                Config.recursiveUpdate(target[k], content[k])
            elif k in target and isinstance(content[k], list) and isinstance(target[k], list):
                target[k] += content[k]
            else:
                target[k] = content[k]
                
    def __str__(self):
        return self.txt

