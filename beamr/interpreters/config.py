'''
Created on 6 Feb 2018

@author: Teodor Gherasim Nistor
'''
import yaml
import subprocess
import os
import re
from beamr.debug import warn, err


class Config(object):

    # Location of user config file
    userConfigPath = os.path.expanduser('~/.beamrrc')

    # Template for creating a fresh new user config file
    userConfigTemplate = '''---
### Beamr configuration file. Please include user settings between the 3 dashes and the 3 dots. ###
editor: %s

...
'''

    # Template for wrapping the dump of this config in user config file
    userConfigDumpTemplate = '''
---
### Default configuration dumped from beamr.interpreters.config ###
# You can safely remove parts which you don't wish to alter #

%s
...
'''

    # Initial config; will be updated throughout
    effectiveConfig = {

        # Whether to perform additional safety checks (easily toggled from command line)
        'safe'      :  True,

        # Whether a title page should be generated
        'titlePage' :  True,

        # Document properties for use in title page
        'title'     :  None,
        'footer'    :  None,
        'author'    :  None,
        'institute' :  None,
        'date'      :  None,

        # Whether to create a table of contents in various places and what title to give it
        'toc'       :  False,
        'sectionToc':  False,
        'headerToc' :  False,
        'tocTitle'  : 'Contents',

        # Arrangement themes and color schemes
        'theme'     : 'Copenhagen',
        'scheme'    : 'beaver',

        # Bibliography file, title for bibliography slide
        'bib'     :  None,
        'bibTitle': 'Bibliography',

        # Document class and used packages configuration
        'docclass': 'beamer',
        'packages': [
                'utf8,inputenc',
                'T1,fontenc',
                'pdfpages',
                'upquote',
                'normalem,ulem',
                'tabularx',
            ],

        # Paths where to search for images in the ~{ } construct
        'graphicspath': [
               # Graphics path resolution: pdflatex automatically looks in the directory where it was called, but should it also look in the directory of the input file?
            ],

        # Image file extensions for use in the ~{ } construct
        # Empty extension is necessary when file name is already given with extension.
        'imgexts': [
                '', '.png', '.pdf', '.jpg', '.mps', '.jpeg', '.jbig2', '.jb2',
                    '.PNG', '.PDF', '.JPG', '.JPEG', '.JBIG2', '.JB2' # As per https://tex.stackexchange.com/a/72939 - Sept 2017
            ],

        # Characters whose escaped/unescaped normal LaTeX use cases are to be swapped
        'antiescape': '&%',

        # Inline emphasis, e.g. *bold*, __underlined__ etc
        'emph': {
                '*': r'\textbf{%s}',
                '_': r'\textit{%s}',
                '~': r'\sout{%s}',
                '**': r'\alert{%s}',
                '__': r'\underline{%s}',
            },

        # Square bracket constructs, e.g. [>], [<Stretched text>] etc
        'stretch': {
                '<>':  '\\centering\\noindent\\resizebox{0.9\\textwidth}{!}{%s}',
                '><':  '\\begin{center}\n%s\n\\end{center}',
                '<<':  '\\begin{flushleft}\n%s\n\\end{flushleft}',
                '>>':  '\\begin{flushright}\n%s\n\\end{flushright}',
                '+' : r'\pause %s',
                '>' : r'\hfill %s',
                '^^': r'\vspace{-%s}',
                '..': r'{\footnotesize %s}',
                ':' : r'\vspace{5mm}%s'
            },

        # Environment to use for verbatim
        'verbatim': 'listings',

        # User-configurable custom LaTeX code insertion points
        'packageDefPre'    : '',
        'outerPreamblePre' : '',
        'outerPreamblePost': '',
        'innerPreamblePre' : '',
        'innerPreamblePost': '',
        'outroPre'         : '',
        'outroPost'        : '',

        # Command sets used internally by listings/minted
        '~vbtmCmds': {
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
            'insertion': r'\codeSnippet%s '
            },

        # TBC ascii arrow art et al
        '~asciiArt': {},

        # Commands for package preamble
        '~docclass': [r'\documentclass[%s]{%s}', r'\documentclass{%s}'],
        '~package' : [r'\usepackage[%s]{%s}', r'\usepackage{%s}'],

        # Commands for outer preamble
        '~theme'        :  '\\usetheme{%s}\n',
        '~scheme'       :  '\\usecolortheme{%s}\n',
        '~author'       :  '\\author{%s}\n',
        '~institute'    :  '\\institute{%s}\n',
        '~date'         :  '\\date{%s}\n',
        '~title'        :  '\\title[%s]{%s}\n',
        '~footerCounter': r' \insertframenumber/\inserttotalframenumber\ ',
        '~sectionToc'   : r'\AtBeginSection[]{\frametitle{%s}\tableofcontents[currentsection,currentsubsection,hideothersubsections,sectionstyle=show/shaded,subsectionstyle=show/show/shaded]}' + '\n',
        '~headerNoToc'  :  '\\setbeamertemplate{headline}{}\n',

        # Commands for inner preamble
        '~titlePage':  '\\frame{\\titlepage}\n',
        '~tocPage'  : r'\frame{\frametitle{%s}\tableofcontents}' + '\n',

        # Commands for outro
        '~bibPage'  : r'\frame{\frametitle{%s}\bibliographystyle{plain}\bibliography{%s}}' + '\n',

        # Document wrapper commands
        '~docBegin' :  '\n\\begin{document}\n',
        '~docEnd'   :  '\n\\end{document}\n',

        # Slide wrapper commands
        '~sldBeginNormal'    : '\\begin{frame}{%s}\n',
        '~sldBeginBreak'     : '\\begin{frame}[allowframebreaks]{%s}\n',
        '~sldBeginShrink'    : '\\begin{frame}[shrink=%s]{%s}\n',
        '~sldBeginShrinkAuto': '\\begin{frame}[shrink]{%s}\n',
        '~sldEnd'            : '\n\\end{frame}\n',

        # Column wrapper commands
        '~colBegin'  : '\\begin{columns}\n',
        '~colEnd'    : '\\end{columns}',
        '~colMarker' : '\\column{%.3f\\textwidth}\n',

        # Box wrapper commands
        '~boxBegin'  : {
                '*'   :  '\\begin{block}{%s}\n',
                '!'   :  '\\begin{alertblock}{%s}\n',
                '?'   :  '\\begin{exampleblock}{%s}\n'
            },
        '~boxEnd'    : {
                '*'   :  '\\end{block}\n',
                '!'   :  '\\end{alertblock}\n',
                '?'   :  '\\end{exampleblock}\n'
            },

        # Footnote commands
        '~fnSimple'   : r'\footnote[frame]{',
        '~fnLabel'    : r'\footnote[frame]{\label{fn:%s}',
        '~fnOnlyLabel': r'\textsuperscript{\ref{fn:%s}}',

        # Citation commands
        '~citeSimple' : r'\cite{%s}',
        '~citeOpts'   : r'\cite[%s]{%s}',

        # Comment command
        '~comment'    :  '%% %s\n',

        # URL command
        '~url'        :  r'\url{%s}',

        # Heading commands
        '~heading'   : [
                '\\section{ %s }\n',
                '\\subsection{ %s }\n',
                '\\subsubsection{ %s }\n'
            ],

        # "Scissor" operator commands
        '~scissorSimple': r'{\setbeamercolor{background canvas}{bg=}\includepdf{%s}}' + '\n',
        '~scissorPages' : r'{\setbeamercolor{background canvas}{bg=}\includepdf[pages={%s}]{%s}}' + '\n',

        # Only makes sense in user config, but placed here to avoid a spurious warning
        'editor': None
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
                        '\n' + cf.read()
                    )):
                    if stub:
                        configStubs.append(stub)
        except:
            pass

        # Update effective config above with all these
        for c in reversed(configStubs):
            cls.recursiveUpdate(cls.effectiveConfig, c, True)

    @classmethod
    def fromCmdline(cls, general, **special):
        if general:
            try:
                cls.recursiveUpdate(cls.cmdlineConfig, yaml.load(general))
            except Exception as e:
                warn(repr(e), 'when parsing config from command line')
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
    def editUserConfig(cls, editor, dump):
        if not os.path.isfile(cls.userConfigPath):
            if editor:
                with open(cls.userConfigPath, 'w') as cf:
                    cf.write(cls.userConfigTemplate % editor)
                    if dump:
                        cf.write(cls.dump())
                        dump = False
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
            except Exception as e:
                warn(repr(e))
            if not editor:
                err('Editor not given. Cannot edit.')
                return 3
        if dump:
            with open(cls.userConfigPath, 'a') as cf:
                cf.write(cls.dump())
        subprocess.call([editor, cls.userConfigPath])
        return 0

    @staticmethod
    def recursiveUpdate(target, source, checkExists=False):
        for k in source:

            # Key doesn't exists in target => add from source, warn if necessary
            if k not in target:
                if checkExists:
                    warn('Config: Adding previously unseen element', k)
                target[k] = source[k]

            # Key exists in target and is dict => recurse only if value in source is also dict
            elif isinstance(target[k], dict):
                if isinstance(source[k], dict):
                    Config.recursiveUpdate(target[k], source[k])
                else:
                    warn('Config: Skipping non-dict replacement for dict', k)

            # Key exists in target and is list => add/remove/ensure existence as per source, enforcing value in source to also be list
            elif isinstance(target[k], list):
                if not isinstance(source[k], list):
                    source[k] = [str(source[k])]
                for c in source[k]:
                    if c and c[0] == '+':
                        target[k].append(c[1:])
                    elif c and c[0] == '-' and c[1:] in target[k]:
                        target[k].remove(c[1:])
                    elif c not in target[k]:
                        target[k].append(c)

            # Key exists in target and is normal element => replace
            else:
                target[k] = source[k]

    @classmethod
    def dump(cls):
        return cls.userConfigDumpTemplate % yaml.dump(cls.effectiveConfig, default_flow_style=False)

    def __str__(self):
        return ''
