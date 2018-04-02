'''
Created on 1 Feb 2018

@author: Teodor Gherasim Nistor
'''
from beamr.debug import debug, warn, err
from beamr.lexers import docLexer, slideLexer
from beamr.parsers import docParser, slideParser
from beamr.interpreters import Config, VerbatimEnv, TableEnv
import re

class Hierarchy(object):

    def __init__(self, children, before='', after='', inter=''):
        self.children = children
        self.before = before
        self.after = after
        self.inter = inter
        
    def __str__(self):
        s = self.before
        for c in self.children:
            s += str(c) + self.inter
        s += self.after
        return s
    
#     def debug(self):
#         debug(self.__class__)


class Document(Hierarchy):

    def __init__(self, txt):
        txt = '\n' + txt
        docLexer.lineno = 0

        i = txt.find('\t')
        if i > -1:
            txt = txt.replace('\t','    ')
            warn("Use of tabs is not recommended (will be considered 4 spaces)",
                 range=txt.count('\n', 0, i))
        super(Document, self).__init__(docParser.parse(txt, docLexer))

        # Collect all kinds of configuration
        Config.resolve()
        debug('Final config', Config.effectiveConfig)

        # Post-factum macro, list, column, and verbatim environment resolution
        Macro.resolve()
        ListItem.resolve(self.children)
        Column.resolve(self.children)
        VerbatimEnv.resolve()

        # Document class and package commands
        packageDef = self.splitCmd(Config.getRaw('~docclass'), Config.getRaw('docclass'))
        packageDef += Config.getRaw('packageDefPre')
        for pkg in Config.effectiveConfig['packages']:
            packageDef += self.splitCmd(Config.getRaw('~package'), pkg)
        packageDef += '\n'

        # Outer preamble commands
        outerPreamble = Config.getRaw('outerPreamblePre')
        titleNonBlank = False

        for cmd in ['theme', 'scheme']:
            cmdVal = Config.getRaw(cmd)
            if cmdVal:
                outerPreamble += Config.get('~'+cmd)(cmdVal)
        for cmd in ['author', 'institute']:
            cmdVal = Config.getRaw(cmd)
            if cmdVal:
                titleNonBlank = True
                outerPreamble += Config.get('~'+cmd)(cmdVal)

        # Figure out what date to specify
        dateVal = Config.getRaw('date')
        if not dateVal:
            outerPreamble += Config.get('~date')('') # Date not specified therefore we must clear it in Beamer
        elif dateVal not in ['default', 'auto']:
            outerPreamble += Config.get('~date')(dateVal) # Date specified but not 'default' therefore we must specify it in Beamer

        # Figure out what title and footer to specify
        titleVal = Config.getRaw('title') or ''
        footerVal = Config.getRaw('footer') or ''
        if footerVal == 'title':
            footerVal = titleVal
        elif footerVal == 'counter':
            footerVal = Config.getRaw('~footerCounter')
        elif footerVal == 'title counter':
            footerVal = titleVal + Config.getRaw('~footerCounter')
        elif footerVal == 'counter title':
            footerVal = Config.getRaw('~footerCounter') + titleVal
        outerPreamble += Config.get('~title')((footerVal, titleVal))

        if titleVal or dateVal:
            titleNonBlank = True

        # Add graphics paths
        gpaths = ''
        for p in Config.getRaw('graphicspath'):
            if p:
                if p[-1] != '/':
                    p += '/'
                gpaths += '{' + p + '}'
        if gpaths:
            outerPreamble += Config.get('~graphicspath')(gpaths)

        # Place tables of contents where necessary
        if Config.getRaw('sectionToc') == True:
            outerPreamble += Config.get('~sectionToc')(Config.getRaw('tocTitle'))
        if not Config.getRaw('headerToc'):
            outerPreamble += Config.getRaw('~headerNoToc')

        outerPreamble += Config.getRaw('outerPreamblePost')

        # Inner preamble commands
        innerPreamble = Config.getRaw('innerPreamblePre')
        innerPreamble += VerbatimEnv.preambleDefs
        titlePage = Config.getRaw('titlePage')
        if titlePage and titleNonBlank or titlePage == 'force':
            innerPreamble += Config.getRaw('~titlePage')
        if Config.getRaw('toc') == True:
            innerPreamble += Config.get('~tocPage')(Config.getRaw('tocTitle'))
        innerPreamble += Config.getRaw('innerPreamblePost')

        # Outro commands
        outro = Config.getRaw('outroPre')

        bib = Config.getRaw('bib')
        bibCmd = Config.getRaw('~bibPage')
        if bib and bibCmd:
            outro += bibCmd % (Config.getRaw('bibTitle'),
                               Config.getRaw('bibStyle'),
                               bib)

        outro += Config.getRaw('outroPost')

        self.before = packageDef + outerPreamble + Config.getRaw('~docBegin') + innerPreamble
        self.after = outro + Config.getRaw('~docEnd')

    @staticmethod
    def splitCmd(cmdTemplate, content):
        i = content.rfind(',')
        if i > -1:
            return cmdTemplate[0] % (content[:i], content[i+1:]) + '\n'
        else:
            return cmdTemplate[1] % content + '\n'


class Slide(Hierarchy):

    parsingQ = []

    def __init__(self, title, opts, content):
        docLexer.lineno += 1
        nextlineno = docLexer.nextlineno
        before = Config.get('~sldBeginNormal')(title)

        # Add breaks or shrink if applicable
        if len(opts) > 0:
            if opts[0] == '.':
                if opts == '...':
                    before = Config.get('~sldBeginBreak')(title)
                elif len(opts) == 1:
                    before = Config.get('~sldBeginShrinkAuto')(title)
                else:
                    try:
                        float(opts[1:])
                        before = Config.get('~sldBeginShrink')((opts[1:], title))
                    except:
                        warn('Slide title: Invalid shrink specifier:', opts[1:], range=docLexer.lineno)
                        before = Config.get('~sldBeginShrinkAuto')(title)
            else:
                warn('Slide title: Invalid option:', opts, range=docLexer.lineno)

        slideLexer.lineno = docLexer.lineno
        super(Slide, self).__init__(slideParser.parse(content, slideLexer),
                         before,
                         Config.getRaw('~sldEnd'))

        # Hierarchical children will have added themselves to the parsing queue which we process now
        self.processQ()

        docLexer.lineno = nextlineno

    @classmethod
    def processQ(cls):
        while len(cls.parsingQ) > 0:
            cls.parsingQ.pop()()


class ListItem(Hierarchy):

    enumCounters = ['i', 'ii', 'iii', 'iv']
    enumCounterCmd = '\\setcounter{enum%s}{%d}\n'
    counterValues = [0,0,0,0]

    begins = ['\\begin{itemize}\n', '\\begin{enumerate}\n', '\\begin{description}\n']
    specs = ['', '<alert@+>', '<+->', '<+-|alert@+>']
    markers = [r'\item%s %s', r'\item%s %s', r'\item%s[%s] ']
    ends = ['\\end{itemize}\n', '\\end{enumerate}\n', '\\end{description}\n']
    
    
    def __init__(self, txt):
        lineno = slideLexer.lineno + 1
        nextlineno = slideLexer.nextlineno
        txt = txt.strip()

        def innerFunc():
            i = txt.find(' ') # Definitely >0 by way of definition of the list item regex
            marker = txt[:i]
            describee = ''
            content = txt[i+1:]

            self.emph = 1 if marker.find('*') > -1 else 0
            self.uncover = 2 if marker.find('+') > -1 else 0

            self.kind = 0 # Unordered list
            self.resume = False

            debug('List marker', marker, range=lineno)

            if marker.find('.') > -1:
                self.kind = 1 # Ordered list
    
            elif marker.find(',') > -1:
                self.kind = 1 # Ordered list, resume numbering
                self.resume = True

            elif marker.find('=') > -1:
                self.kind = 2 # Description list. Isolate describee
                j = content.find('=')
                if j == -1:
                    j = content.find(' ')
    
                if j == -1:
                    describee = content
                    content = ' '
                else:
                    describee = content[:j]
                    content = content[j+1:]
            
            slideLexer.lineno = lineno
            super(ListItem, self).__init__(slideParser.parse(content, slideLexer),
                     '%s' + self.markers[self.kind] % (self.specs[self.emph + self.uncover], describee),
                     '\n')

        Slide.parsingQ.insert(0, innerFunc)
        slideLexer.lineno = nextlineno
    
    @classmethod
    def resolve(cls, docList, depth=0):
        maxIndex = len(docList) - 1

        # Anti-stupid
        if depth > 3:
            warn('Nested lists to depth greater than 4')
            depth = 3

        for i,l in enumerate(docList):

            # Deal with list items
            if isinstance(l, cls):

                # Begin list before current item if previous item doesn't exist, is not a list item, or is a list item of a different kind
                if i == 0 or (docList[i-1].kind != l.kind if isinstance(docList[i-1], cls) else True):
                    l.before = cls.begins[l.kind] + l.before

                    # If this is an enumeration item which doesn't resume the counter, reset counter for current depth to 0
                    if l.kind == 1 and not l.resume:
                        cls.counterValues[depth] = 0

                # End list after current item if next item doesn't exist, is not a list item, or is a list item of a different kind
                if i == maxIndex or (docList[i+1].kind != l.kind if isinstance(docList[i+1], cls) else True):
                    l.after += cls.ends[l.kind]

                # Resume counters for enumerations that require it
                l.before %= cls.enumCounterCmd % (cls.enumCounters[depth], cls.counterValues[depth]) if l.resume else ''

                # Increment counter for current level if enumeration
                if l.kind == 1:
                    cls.counterValues[depth] += 1

                # Recurse to children, which are now one level deeper
                cls.resolve(l.children, depth+1)

            # Deal with non-list hierarchies
            elif isinstance(l, Hierarchy):
                cls.resolve(l.children, depth)


class Column(Hierarchy):

    def __init__(self, txt):
        lineno = slideLexer.lineno + 1
        nextlineno = slideLexer.nextlineno
        txt = txt.strip()

        debug('Txt picked up by col:', txt, range=lineno)
        i = txt.find('\n') # Guaranteed >0 by regex
        head = txt[1:i].strip()
        txt = txt[i:]

        # Identify width params
        self.percentage = self.units = 0.0
        self.unspecified = 0
        if len(head) == 0:
            self.unspecified = 1
        elif head[-1:] == '%':
            self.percentage = float(head[:-1]) * 0.01
        else:
            self.units = float(head)

        def innerFunc():
            slideLexer.lineno = lineno
            super(Column, self).__init__(slideParser.parse(txt, slideLexer), after='\n')
        Slide.parsingQ.insert(0, innerFunc)
        slideLexer.lineno = nextlineno

    @classmethod
    def resolve(cls, docList):
        currentColumnSet = []
        totalSpace = 1.0
        totalUnits = 0.0
        unspecifiedCount = 0

        # A dummy element at the end ensures the last column set is processed if the current docList ends with a column
        for elem in docList + [None]:

            # Column encountered. Add it to current set and adjust counters
            if isinstance(elem, Column):
                currentColumnSet.append(elem)
                totalSpace -= elem.percentage
                totalUnits += elem.units
                unspecifiedCount += elem.unspecified

            # Non-column encountered. If a nonempty set exists, process it now.
            elif len(currentColumnSet) > 0:

                # Begin and end column environment around first and last columns of current set.
                currentColumnSet[0].before = Config.getRaw('~colBegin')
                currentColumnSet[-1].after += Config.getRaw('~colEnd')

                if totalSpace < 0.0: # Anti-stupid
                    warn('Fixed column widths exceed 100%.', totalSpace, 'remaining, setting to 0.')
                    totalSpace = 0.0

                # Generate column markers
                for col in currentColumnSet:

                    # If width unspecified, allocate space unclaimed by fixed-percentage columns
                    if col.unspecified:
                        col.percentage = totalSpace / unspecifiedCount

                    col.before += Config.get('~colMarker')(col.percentage
                                                  if col.percentage > 0.0
                                                else col.units / totalUnits * totalSpace)

                # Reset counters and set
                currentColumnSet = []
                totalSpace = 1.0
                totalUnits = 0.0
                unspecifiedCount = 0

            # Recurse
            if isinstance(elem, Hierarchy):
                cls.resolve(elem.children)


class OrgTable(TableEnv):

    def __init__(self, txt):
        lineno = slideLexer.lineno
        nextlineno = slideLexer.nextlineno

        # Regular expression for separating table cells from a row (based on capturing groups)
        r = re.compile(r'\|(\|?) *([<>^.,-]?)((?:\\\||[^\|\n])*)')
        # Regular expression for detecting horizontal bar lines
        b = re.compile(r'\|{1,2}(-+(\+-)*)+\|{1,2}')

        # This will store the contents of cells
        arr = []
        # These will remember cell alignments and where to place margins
        aligns = ''
        vBars = ''
        hBars = []

        # Iterate through non-blank lines...
        i = 0
        for line in txt.splitlines():
            lineno += 1
            line = line.strip()
            if line:

                # Bar line. Mark horizontal bar
                if b.match(line):
                    hBars.append(i)

                # Contents line. Create a row in the matrix, split and process
                else:
                    arr.append([])
                    enumLine = [el for el in enumerate(r.findall(line))]

                    # Iterate over cells...
                    for j, (bar, align, text) in enumLine:

                        # First visit this far to the right. Note if vertical bar is needed
                        if len(vBars) <= j:
                            vBars += '|' if bar else ' '

                        # Not beyond right edge. Process contents
                        if j+1 < len(enumLine):

                            # First visit this far to the right. Note alignment, if any
                            if len(aligns) <= j:
                                aligns += align or 'A'

                            # Not first visit this far. Alignment symbol is actually part of the contents
                            else:
                                text = align + text

                            # Enqueue contents for parsing and addition to current matrix row
                            self.qHelper(arr[i], text.replace(r'\|', '|'), lineno)
                    i += 1

        # Store what we have processed for use by __str__() in TableEnv.
        # (arr contains only empty lists at this point, but they will be populated from the queue)
        super(OrgTable, self).remember(arr, aligns, vBars, hBars)
        slideLexer.lineno = nextlineno

    # Helper function to enqueue the processing of a cell's contents and
    # append the results to given table row
    @staticmethod
    def qHelper(arr, text, lineno):
        def innerFunc():
            slideLexer.lineno = lineno
            arr.append(Hierarchy(slideParser.parse(text, slideLexer)))
        Slide.parsingQ.insert(0, innerFunc)


class Macro(Hierarchy):
    macros = []

    def __init__(self, txt):
        self.txt = txt.split()
        self.lineno = slideLexer.lineno
        nextlineno = slideLexer.nextlineno
        slideLexer.lineno = nextlineno
        self.rng = '%d-%d' % (self.lineno, nextlineno)

        self.macros.append(self)
        super(Macro, self).__init__([])

    @classmethod
    def resolve(cls):
        for macro in cls.macros:

            # Callback for user code to call if Beamr parsing is desired on macro result
            def beamr(s):
                slideLexer.lineno = macro.lineno
                super(Macro, macro).__init__(slideParser.parse(s, slideLexer))

                # Need to redo this manually as slide-side processing will have finished at this point
                Slide.processQ()

            # Callback for user code to call if macro results directly in LaTeX code
            def latex(s):
                super(Macro, macro).__init__([], s)

            # Run user code
            code = Config.getRaw('macro', macro.txt[0])
            if not code:
                warn('Unknown macro', macro.txt[0], range=macro.rng)

            try:
                exec(code, {'beamr': beamr, 'latex': latex, 'arg': macro.txt[1:], 'debug': debug})
            except Exception as e:
                err('An error occurred during macro', macro.txt[0],'execution:', e, range=macro.rng)
                debug('Macro', macro.txt[0],'error:', repr(e), range=macro.rng)


class Box(Hierarchy):

    def __init__(self, kind, title, content):
        lineno = slideLexer.lineno + 1
        nextlineno = slideLexer.nextlineno

        # Enqueue function below to be called when all current parsing has finished
        def innerFunc():
            slideLexer.lineno = lineno
            super(Box, self).__init__(slideParser.parse(content, slideLexer),
                                      Config.get('~boxBegin', kind)(title),
                                      Config.getRaw('~boxEnd', kind))

        Slide.parsingQ.insert(0, innerFunc)
        slideLexer.lineno = nextlineno


class Emph(Hierarchy):
    def __init__(self, flag, txt):
        self.flag = flag
        def innerFunc():
            super(Emph, self).__init__(slideParser.parse(txt, slideLexer))
        Slide.parsingQ.insert(0, innerFunc)

    def __str__(self):
        return Config.get('emph', self.flag)(super(Emph, self).__str__())


class Stretch(Hierarchy):
    def __init__(self, flagS, flagF, txt=''):
        self.flagS = flagS if flagS else ''
        self.flagF = flagF if flagF else ''
        def innerFunc():
            super(Stretch, self).__init__(slideParser.parse(txt, slideLexer) if txt else [])
        Slide.parsingQ.insert(0, innerFunc)

    def __str__(self):
        f = Config.get('stretch', self.flagS + self.flagF, default=None)
        if not f and self.flagS == self.flagF:
            f = Config.get('stretch', self.flagS, default=None)
            if not f:
                f = Config.get('emph', self.flagS)
        if f:
            return f(super(Stretch, self).__str__())
        return super(Stretch, self).__str__()


class Footnote(Hierarchy):

    def __init__(self, txt):
        i = txt.find(':')
        label = txt[0:i] if i > -1 else None
        txt = txt[i+1:]

        def innerFunc():
            if txt and label:
                super(Footnote, self).__init__(slideParser.parse(txt, slideLexer),
                                        Config.get('~fnLabel')(label),
                                         '}')
            elif txt:
                super(Footnote, self).__init__(slideParser.parse(txt, slideLexer),
                                        Config.getRaw('~fnSimple'),
                                        '}')
            elif label:
                super(Footnote, self).__init__([],
                                        Config.get('~fnOnlyLabel')(label))
            else:
                super(Footnote, self).__init__([])
        Slide.parsingQ.insert(0, innerFunc)
