'''
Created on 6 Feb 2018

@author: Teodor Gherasim Nistor
'''
import yaml
import subprocess
import os
import re
from beamr.debug import warn, err

# TODO could move class methods and effective config to module level
# TODO prevent the user from too easily breaking the config - is there another way except littering try/except everywhere config is used??
# TODO is there a case for overriding lists completely? nb. Can be done by setting to non-list then to fresh list later in the yaml

class Config(object):

    userConfigPath = os.path.expanduser('~/.beamrrc')
    userConfigTemplate = '''---
# Beam configuration file. Please include user settings between the 3 dashes and the 3 dots.
editor: %s

...
'''

    # Initial config
    effectiveConfig = {
        'docclass': 'beamer', # Obvs
        'packages': [
                'utf8,inputenc',
                'T1,fontenc',
                'pdfpages',
                #'hidelinks,hyperref', # Clashes with beamer...?
                'upquote',
                'normalem,ulem',
                # TODO give example for setting a font
                # tikz? natbib? etc??
                
            ],

        'graphicspath': [
               # Graphics path resolution: pdflatex automatically looks in the directory where it was called, but should it also look in the directory of the input file?
            ],

        # Arrangement themes and color schemes
        'theme': 'Copenhagen',
        'scheme': 'beaver',

        # Image file extensions. Empty extension is necessary when file name is already given with extension.
        'imgexts': [
                '', '.png', '.pdf', '.jpg', '.mps', '.jpeg', '.jbig2', '.jb2',
                    '.PNG', '.PDF', '.JPG', '.JPEG', '.JBIG2', '.JB2' # As per https://tex.stackexchange.com/a/72939 - Sept 2017
            ],

        # TODO Whether to perform additional safety checks
        'safe': True,

        # pdflatex executable path
        'pdflatex': 'pdflatex',

        # Environment to use for verbatim
        'verbatim': 'listings',

        # Command sets used internally by listings/minted
        'vbtmCmds': {
            'packageNames': ['listings', 'minted'],
            'once': {
                'listings': r'\definecolor{codegreen}{rgb}{0.1,0.4,0.1}\definecolor{codegray}{rgb}{0.5,0.5,0.5}\definecolor{codepurple}{rgb}{0.4,0,0.7}\lstdefinestyle{defostyle}{commentstyle=\color{codegreen},keywordstyle=\color{blue},numberstyle=\tiny\color{codegray},stringstyle=\color{codepurple},basicstyle=\footnotesize\ttfamily,breakatwhitespace=false,breaklines=true,captionpos=b,keepspaces=true,numbers=left,numbersep=5pt,showspaces=false,showstringspaces=false,showtabs=false,tabsize=3}',
                'minted': ''
                },
            'foreach': {
                'minted':
'''\\defverbatim[colored]%s{
  \\begin{minted}[xleftmargin=20pt,linenos]{%s}
%s
  \\end{minted}
}
''',
                'listings':
'''\\defverbatim[colored]%s{
  \\begin{lstlisting}[language=%s,style=defostyle]
%s
  \\end{lstlisting}
}
'''
                },
            'foreachNoLang': {
                'minted':
'''\\defverbatim[colored]%s{
  \\begin{minted}[xleftmargin=20pt,linenos]{text}
%s
  \\end{minted}
}
''',
                'listings':
'''\\defverbatim[colored]%s{
  \\begin{lstlisting}[style=defostyle]
%s
  \\end{lstlisting}
}
'''
                },
#             'langCheck': {
#                 'minted': '''''''',
#                 },
            'insertion': r'\codeSnippet%s '
            },

        # Inline emphasis, e.g. *bold*. ~strikethrough~
        'emph': {
                '*': r'\textbf{%s}',
                '_': r'\textit{%s}',
                '~': r'\sout{%s}',
                '**': r'\alert{%s}',
                '__': r'\underline{%s}',
            },

        # Square bracket constructs, e.g. [>], [<Stretched text>] etc
        'stretch': {
                '<>': lambda s: '\\centering\\noindent\\resizebox{0.9\\textwidth}{!}{%s}' % s,
                '><': lambda s: '\\begin{center}\n%s\n\\end{center}' % s,
                '<<': lambda s: '\\begin{flushleft}\n%s\n\\end{flushleft}' % s,
                '>>': lambda s: '\\begin{flushright}\n%s\n\\end{flushright}' % s,
                '+' : lambda s: r'\pause ',  # @UnusedVariable
                '>' : lambda s: r'\hfill ',  # @UnusedVariable
                '^^': lambda s: r'\vspace{-%s}' % s, # TODO check number, add default unit (mm)
                'vv': lambda s: r'\vspace{%s}' % s, # TODO check number, add default unit (mm)
                '__': lambda s: r'{\footnotesize %s}' % s,
                ':' : lambda s: r''
            },

        # Bibliography file
        'bib': None,
    }

    # Config instances left to process from document
    docConfig = []

    # Store command-line config for updating after document config has been loaded
    cmdlineConfig = {}

    def __init__(self, txt):
        self.parsedConfig = yaml.load_all(txt)
        self.__class__.docConfig.append(self)

    @classmethod
    def resolve(cls):
        configStubs = [cls.cmdlineConfig] # Config from command line

        # Config from input file
        while len(cls.docConfig):
            try:
                for stub in cls.docConfig.pop(0).parsedConfig:
                    configStubs.append(stub)
            except: # If there was bad Yaml
                pass

        # Config from user config file
        try:
            with open(cls.userConfigPath, 'r') as cf:
                for stub in yaml.load_all(re.sub( # Get rid of text outside Yaml markers
                        r'(^|\n\.\.\.)[\s\S]*?($|\n---)',
                        '\n---',
                        cf.read()
                    )):
                    if stub:
                        configStubs.append(stub)
        except:
            pass

        # Update effective config above with all these
        for c in reversed(configStubs):
            cls.recursiveUpdate(cls.effectiveConfig, c)

    @classmethod
    def fromCmdline(cls, general, **special):
        try:
            cls.recursiveUpdate(cls.cmdlineConfig, yaml.load(general))
        except:
            pass
        cls.recursiveUpdate(cls.cmdlineConfig, special)

    @classmethod
    def getRaw(cls, *arg):
        try:
            d = cls.effectiveConfig
            for i in range(len(arg)):
                d = d[arg[i]]
            return d
        except Exception as e:
            warn('Could not get raw configuration for', arg, 'due to', repr(e))
            return None

    @classmethod
    def get(cls, *arg, **kw):
        try:
            d = cls.effectiveConfig
            for i in range(len(arg)):
                d = d[arg[i]]
            if callable(d):
                return d
            return lambda s: d % s
        except Exception as e:
            warn('Could not get configuration for', arg, 'due to', repr(e))
            return kw['default'] if 'default' in kw else lambda s: s

    @classmethod
    def editUserConfig(cls, editor):
        if not os.path.isfile(cls.userConfigPath):
            if editor:
                with open(cls.userConfigPath, 'w') as cf:
                    cf.write(cls.userConfigTemplate % editor)
            else:
                err('Editor not given. Cannot edit.')
                return 2
        elif not editor:
            try:
                with open(cls.userConfigPath, 'r') as cf:
                    for d in yaml.load_all(cf):
                        if 'editor' in d:
                            editor = d['editor']
                            break
            except:
                pass
            if not editor:
                err('Editor not given. Cannot edit.')
                return 3
        subprocess.call([editor, cls.userConfigPath])
        return 0

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
        return ''

