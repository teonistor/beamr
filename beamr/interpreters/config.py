'''
Config class is instantiated upon reading Yaml blocks.
On the class level lives a large configuration dictionary, central to the flexible
design of the tool, as well as helpers given config stubs from elsewhere.

Created on 6 Feb 2018

@author:     Teodor G Nistor

@copyright:  2018 Teodor G Nistor

@license:    MIT License
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

        # Bibliography file, contents, style; title for bibliography slide
        'bibFile'   :  None,
        'bib'       :  [],
        'bibStyle'  : 'plain',
        'bibTitle'  : 'Bibliography',

        # Document class and used packages configuration
        'docclass': 'xcolor={table,rgb,usenames,svgnames},beamer',
        'packages': [
                'utf8,inputenc',
                'T1,fontenc',
                'pdfpages',
                'upquote',
                'normalem,ulem',
                'tikz',
                'tabularx',
                'dcolumn'
            ],

        # Paths where to search for images in the ~{ } construct
        'graphicspath': [
                ''
            ],

        # Image file extensions for use in the ~{ } construct
        # Empty extension is necessary when file name is already given with extension.
        'imgexts': [
                '', '.png', '.pdf', '.jpg', '.mps', '.jpeg', '.jbig2', '.jb2',
                    '.PNG', '.PDF', '.JPG', '.JPEG', '.JBIG2', '.JB2', '.eps' # As per https://tex.stackexchange.com/a/72939 - Sept 2017
            ],

        # Characters whose escaped/unescaped normal LaTeX use cases are to be swapped
        'antiescape': '&%',

        # Inline emphasis, e.g. *bold*, __underlined__ etc
        'emph': {
                '*' : r'\textbf{%s}',
                '_' : r'\textit{%s}',
                '**': r'\alert{%s}',
                '__': r'\underline{%s}',
            },

        # Square bracket constructs, e.g. [>], [<Stretched text>] etc
        'stretch': {
                '<>':  '\\centering\\noindent\\resizebox{0.9\\textwidth}{!}{%s}',
                '><':  '\\begin{center}\n%s\n\\end{center}',
                '<<':  '\\begin{flushleft}\n%s\n\\end{flushleft}',
                '>>':  '\\begin{flushright}\n%s\n\\end{flushright}',
                '==': r'\texttt{%s}',
                '~~': r'\sout{%s}',
                '+' : r'\pause %s',
                '>' : r'\hfill %s',
                '^^': r'\vskip -%s ',
                '..': r'{\footnotesize %s}',
                ':' : r'\vskip 5mm %s'
            },

        # Environment to use for verbatim
        'verbatim'  : 'listings',

        # User macros will be placed here
        'macro'     : {},

        # Arguments for underlying PDF engines
        'pdfEngines': {
            'pdflatex': ['pdflatex'],
            'latexmk' : ['latexmk', '-pdf', '-f'],
            'all'     : ['-shell-escape', '-interaction=nonstopmode'],
            'test'    : ['latexmk', '--version']
        },

        # User-configurable custom LaTeX code insertion points
        'docclassPre'      : [],
        'packageDefPre'    : [],
        'outerPreamblePre' : [],
        'outerPreamblePost': [],
        'innerPreamblePre' : [],
        'innerPreamblePost': [],
        'outroPre'         : [],
        'outroPost'        : [],

        # Post-processing hook will, if required, contain arbitrary Python code to be executed on the final string
        'postProcess'      : [],

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

        # Ascii arrow and ellipsis art
        '~asciiArt': {
                '...'  : r'\ensuremath{\ldots}',
                ':::'  : r'\resizebox{!}{1em}{\ensuremath{\vdots}}',
                ':..'  : r'\resizebox{!}{1em}{\ensuremath{\ddots}}',
                '\\'*2 : r'\newline ',
                '\\'*3 : r'\textbackslash ',
                '-->'  : r'\ensuremath{\rightarrow}',
                '<->'  : r'\ensuremath{\leftrightarrow}',
                '<--'  : r'\ensuremath{\leftarrow}',
                '|->'  : r'\ensuremath{\mapsto}',
                '==>'  : r'\ensuremath{\Rightarrow}',
                '<=>'  : r'\ensuremath{\Leftrightarrow}',
                '<=='  : r'\ensuremath{\Leftarrow}'
            },

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

        # Command for graphics path
        '~graphicspath' :  '\\graphicspath{%s}\n',

        # Commands for inner preamble
        '~titlePage':  '\\frame{\\titlepage}\n',
        '~tocPage'  : r'\frame{\frametitle{%s}\tableofcontents}''\n',

        # Commands for outro
        '~bibPage'  : r'\frame{\frametitle{%s}\bibliographystyle{%s}\bibliography{%s}}''\n',

        # Document wrapper commands
        '~docBegin' :  '\n'r'\begin{document}''\n'r'\renewcommand*{\arraystretch}{1.25}''\n',
        '~docEnd'   :  '\n\\end{document}\n',

        # Slide wrapper commands
        '~sldBegin'       : r'{%s\begin{frame}{%s}',
        '~sldBeginOpts'   : r'{%s\begin{frame}[%s]{%s}',
        '~sldEnd'         : '\n\\end{frame}}\n',
        '~sldOptsOut' : {
                'plain'   : r'\setbeamertemplate{navigation symbols}{}',
                'bgW'     : r'\setbeamertemplate{background}{\includegraphics[width=\paperwidth]{%s}}',
                'bgH'     : r'\setbeamertemplate{background}{\includegraphics[height=\paperheight]{%s}}'
            },
        '~sldOptsIn'  : {
                'break'   :  'allowframebreaks',
                'plain'   :  'plain',
                'align^'  :  't',
                'align_'  :  'b',
                'shrink'  :  'shrink=%s',
                'shrinkA' :  'shrink',
            },

        # Column wrapper commands
        '~colBegin'   : '\\begin{columns}[c,totalwidth=\linewidth]\n',
        '~colBegin^'  : '\\begin{columns}[t,totalwidth=\linewidth]\n',
        '~colBegin_'  : '\\begin{columns}[b,totalwidth=\linewidth]\n',
        '~colEnd'     : '\\end{columns}',
        '~colMarker'  : '\\column{%.3f\\textwidth}%s\n',

        # Box wrapper commands
        '~boxBegin'  : {
                '*'   :  '\\begin{block}{%s}%s\n',
                '!'   :  '\\begin{alertblock}{%s}%s\n',
                '?'   :  '\\begin{exampleblock}{%s}%s\n'
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
        '~comment'    :  '%% Comment from line %d:%s\n',

        # URL command
        '~url'        :  r'\href{%s}{\color{blue}%s}',

        # Heading commands
        '~heading'   : [
                '\\section{ %s }\n',
                '\\subsection{ %s }\n',
                '\\subsubsection{ %s }\n'
            ],

        # Image frame commands:
        '~image'     : {
                'wh' : r'\includegraphics[width=%.3f%s,height=%.3f%s]{%s}',
                'w-' : r'\includegraphics[width=%.3f%s]{%s}',
                '-h' : r'\includegraphics[height=%.3f%s]{%s}',
                '--' : r'\includegraphics[%s]{%s}',
                'space'   : r'\hskip %.3f%s ',
                'overlay' : r'\alt%s{%s}{%s}'
            },

        # Org Table commands
        '~orgTable'  : {
                'align' : {
                    '<' :  'l',
                    '>' :  'r',
                    '^' :  'c',
                    '.' :  'D{.}{.}{-1}',
                    ',' :  'D{,}{,}{-1}',
                    '-' :  'X',
                },
                'begin'   : r'\begin{center}\begin{tabular}{%s}',
                'beginX'  : r'\begin{tabularx}{\textwidth}{%s}',
                'end'     : r'\end{tabular}\end{center}',
                'endX'    : r'\end{tabularx}',
                'multicol': r'\multicolumn{1}{c%s}{%s}',
                'hBar'    :  '\n\\hline',
            },

        # "Scissor" operator commands
        '~scissorSimple': r'{\setbeamercolor{background canvas}{bg=}\setbeamertemplate{navigation symbols}{}\includepdf{%s}}''\n',
        '~scissorPages' : r'{\setbeamercolor{background canvas}{bg=}\setbeamertemplate{navigation symbols}{}\includepdf[pages={%s}]{%s}}''\n',

        # Only makes sense in user config, but placed here to avoid a spurious warning
        'editor': None
    }

    # Config instances left to process from document
    docConfig = []

    # Config files to process from command line
    configFiles = []

    # Store command-line config for updating after document config has been loaded
    cmdlineConfig = {}

    def __init__(self, txt, lineno, nextlineno, lexer):
        ''' Set up a block of Yaml for parsing
        :param txt: Yaml contents
        '''
        self.parsedConfig = yaml.load_all(txt)
        self.rng = '%d-%d' % (lineno + 1, nextlineno)
        self.__class__.docConfig.append(self)
        lexer.lineno = nextlineno

    @classmethod
    def resolve(cls):
        '''Parse configuration stubs from all over and update effective
        configuration in the right order of precedence'''

        # Config from command line
        configStubs = [cls.cmdlineConfig]

        # Config from input file
        while len(cls.docConfig):
            thisConfig = cls.docConfig.pop(0)
            try:
                for stub in thisConfig.parsedConfig:
                    if isinstance(stub, dict):
                        configStubs.append(stub)
            except Exception as e: # If there was bad Yaml
                warn('Bad configuration block:', e, range=thisConfig.rng)

        # Config from user config file(s)
        for cf in reversed(cls.configFiles):
            cls.fromConfigFile(configStubs, cf, True)
        cls.fromConfigFile(configStubs, cls.userConfigPath, False)

        # Update effective config above with all these
        for c in reversed(configStubs):
            cls.recursiveUpdate(cls.effectiveConfig, c, True)

    @staticmethod
    def fromConfigFile(configStubs, filePath, fileShouldExist):
        try:
            with open(filePath, 'r') as cf:
                try:
                    for stub in yaml.load_all(re.sub( # Get rid of text outside Yaml markers
                            r'(^|\n\.\.\.)[\s\S]*?($|\n---)',
                            '\n---',
                            '\n' + cf.read()
                        )):
                        if isinstance(stub, dict):
                            configStubs.append(stub)
                except Exception as e: # If there was bad Yaml
                    warn('Malformatted configuration file ', filePath, ':', e)
        except Exception as e: # If file is nonexistent or unreadable
            if fileShouldExist:
                warn('Could not read configuration file ', filePath, ':', e)

    @classmethod
    def fromCmdline(cls, general, **special):
        '''
        Save some configuration coming from command line
        :param general: Configuration from -c argument
        :param special: -s/-u argument
        '''
        for gen in general:
            try:
                gen = yaml.load(gen)

                # Dictionary => Contents to update config with
                if (isinstance(gen, dict)):
                    cls.recursiveUpdate(cls.cmdlineConfig, gen)

                # String => File name to process later
                else:
                    cls.configFiles.append(gen)

            except Exception as e:
                warn(repr(e), 'when parsing config from command line')
        cls.recursiveUpdate(cls.cmdlineConfig, special)

    @classmethod
    def getRaw(cls, *arg):
        '''
        Return a certain piece of configuration. If not found, raise a warning and return None
        :param arg: Dictionary keys / list indexes to traverse to dig into the configuration'''
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
        '''
        Return a function which takes the formatting arguments of a code snippet from
        configuration and returns the formatted string
        If not found, raise a warning and return the identity function
        :param arg: Dictionary keys / list indexes to traverse to dig into the configuration
        :param kw: Provide named argument 'default' to override the identity function
                   returned when requested configuration is not found
        '''
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
        ''' Open user config file for editing. Create it / dump defaults as necessary.
        Called by cli as final action when -e argument given on terminal
        :param editor: <editor> command line argument
        :param dump: -d command line argument
        '''

        # No file -> need editor to know how to edit
        if not os.path.isfile(cls.userConfigPath):
            if editor:

                # Write bare template
                with open(cls.userConfigPath, 'w') as cf:
                    cf.write(cls.userConfigTemplate % editor)

                    # Dump defaults if asked for
                    if dump:
                        cf.write(cls.dump())
                        dump = False

            # No file, no editor -> cannot edit
            else:
                err('Editor not given. Cannot edit.')
                return 2

        # File but no editor -> find out editor from file
        elif not editor:
            try:
                with open(cls.userConfigPath, 'r') as cf:
                    for d in yaml.load_all(cf):
                        if 'editor' in d:
                            editor = d['editor']
                            break

            # Editor not in file -> cannot edit
            except Exception as e:
                warn(repr(e))
            if not editor:
                err('Editor not given. Cannot edit.')
                return 3

        # Dump defaults if asked for
        if dump:
            with open(cls.userConfigPath, 'a') as cf:
                cf.write(cls.dump())

        # Finally open editor
        subprocess.call([editor, cls.userConfigPath])
        return 0

    @staticmethod
    def recursiveUpdate(target, source, checkExists=False):
        '''
        Update a dictionary with another by merging subdictionaries
        and updating sublists based on +/- prefixes
        :param target: Dictionary to update
        :param source: Contents to update with
        :param checkExists: If true, raise a warning when a key in source doesn't
                            exist in target (false by default)
        '''
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
        'Return Yaml-formatted default configuration, wrapped in a user-friendly template'
        return cls.userConfigDumpTemplate % yaml.dump(cls.effectiveConfig, default_flow_style=False)

    def __str__(self):
        'Return the empty string (configuration doesn\'t appear in final document)'
        return ''
