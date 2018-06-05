'''
Document nodes which can contain nested nodes.
Created on 1 Feb 2018

@author:     Teodor G Nistor

@copyright:  2018 Teodor G Nistor

@license:    MIT License
'''
from beamr.debug import debug, warn, err
from beamr.lexers import docLexer, slideLexer
from beamr.parsers import docParser, slideParser
from beamr.interpreters import Config, VerbatimEnv
from beamr.interpreters.textual import _fullmatch_greedy, PlusEnv
from collections import deque
import re

class Hierarchy(object):

    parsingQ = deque()

    def __init__(self, lexer, lineno, nextlineno, **kw):
        'Assign empty contents, enqueue lateInit for later execution, then move lexer line number'
        self.genericInit(lineno, nextlineno)

        def innerFunc():
            self.lateInit(lineno=lineno, nextlineno=nextlineno, **kw)

        self.enQ(innerFunc)
        lexer.lineno = nextlineno

    def genericInit(self, lineno, nextlineno):
        'Assign empty contents and generate opoening and closing comments'
        self.children = []
        self.before = ''
        self.after = ''
        self.inter = ''

        explainRng = '%s from lines %d-%d' % (
                self.__class__.__name__,
                lineno, nextlineno
            )
        self.explainBefore = '%%%%%%%%%% Begin ' + explainRng + ' %%%%%%%%%%\n'
        self.explainAfter  = '%%%%%%%%%% End '   + explainRng + ' %%%%%%%%%%\n'

    def lateInit(self, **kw):
        'Dummy late initialisation for an empty hierarchy. To be overridden by subclasses'
        pass

    def __str__(self):
        '''Stringify hierarchy by recursively stringifying children and
        concatenating results with before, after, inter appropriately'''
        s = self.before
        for c in self.children:
            s += str(c) + self.inter
        s += self.after
        return s

    @classmethod
    def enQ(cls, f):
        'Enqueue a zero-argument function into the parsing queue'
        cls.parsingQ.appendleft(f)

    @classmethod
    def processQ(cls):
        'Pop functions from the parsing queue one by one and execute them'
        while len(cls.parsingQ) > 0:
            cls.parsingQ.pop()()


class Document(Hierarchy):
    'Root of document hierarchy'

    def __init__(self, txt, name=None):

        # Hack to simplify some lexer regexs
        txt = '\n' + txt
        docLexer.lineno = 0

        # Replace tabs with 4 spaces and warn about them
        i = txt.find('\t')
        if i > -1:
            txt = txt.replace('\t','    ')
            warn("Use of tabs is not recommended (will be considered 4 spaces)",
                 range=txt.count('\n', 0, i))
        self.children = docParser.parse(txt, docLexer)

        # Collect all kinds of configuration
        Config.resolve()
        debug('Final config', Config.effectiveConfig)

        # Post-factum macro, list, column, and verbatim environment resolution
        Hierarchy.processQ()
        Macro.resolve()
        ListItem.resolve(self.children)
        Column.resolve(self.children)
        VerbatimEnv.resolve()

        # Document class and package commands
        packageDef = '\n'.join(Config.getRaw('docclassPre'))
        packageDef += PlusEnv.docclassPre
        packageDef += self.splitCmd(Config.getRaw('~docclass'), Config.getRaw('docclass'))
        packageDef += '\n'.join(Config.getRaw('packageDefPre'))
        for pkg in Config.effectiveConfig['packages']:
            packageDef += self.splitCmd(Config.getRaw('~package'), pkg)
        packageDef += '\n'

        # Outer preamble commands
        outerPreamble = '\n'.join(Config.getRaw('outerPreamblePre'))
        outerPreamble += PlusEnv.outerPreamblePre
        titleNonBlank = False

        for cmd in ['theme', 'scheme']:
            cmdVal = Config.getRaw(cmd)
            if cmdVal:
                outerPreamble += Config.get('~'+cmd)(cmdVal)
        for cmd in ['author', 'institute']:
            cmdVal = Config.getRaw(cmd)
            if cmdVal:
                cmdVal = self.parseStrImmediate(cmdVal)
                titleNonBlank = True
                outerPreamble += Config.get('~'+cmd)(cmdVal)

        # Figure out what date to specify
        dateVal = Config.getRaw('date')
        if not dateVal:
            outerPreamble += Config.get('~date')('') # Date not specified therefore we must clear it in Beamer
        elif dateVal not in ['today', 'auto']:
            outerPreamble += Config.get('~date')(dateVal) # Date specified but not 'default' therefore we must specify it in Beamer

        # Figure out what title and footer to specify
        titleVal = self.parseStrImmediate(Config.getRaw('title') or '')
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

        outerPreamble += PlusEnv.outerPreamblePost
        outerPreamble += '\n'.join(Config.getRaw('outerPreamblePost'))

        # Inner preamble commands
        innerPreamble = '\n'.join(Config.getRaw('innerPreamblePre'))
        innerPreamble += VerbatimEnv.preambleDefs
        titlePage = Config.getRaw('titlePage')
        if titlePage and titleNonBlank or titlePage == 'force':
            innerPreamble += Config.getRaw('~titlePage')
        if Config.getRaw('toc') == True:
            innerPreamble += Config.get('~tocPage')(Config.getRaw('tocTitle'))
        innerPreamble += '\n'.join(Config.getRaw('innerPreamblePost'))

        # Outro commands
        outro = '\n'.join(Config.getRaw('outroPre'))

        bib = Config.getRaw('bib')
        bibFile = Config.getRaw('bibFile')
        if bib:
            if not bibFile:
                bibFile = (name or 'local') + '.bib'
            with open(bibFile, 'w') as bf:
                bf.write('\n'.join(bib))
        if bibFile:
            outro += Config.get('~bibPage')((Config.getRaw('bibTitle'),
                               Config.getRaw('bibStyle'),
                               bibFile))

        outro += '\n'.join(Config.getRaw('outroPost'))

        # Remember these blocks of code for use later in __str__()
        self.before = packageDef + outerPreamble + Config.getRaw('~docBegin') + innerPreamble
        self.after = outro + Config.getRaw('~docEnd')
        self.inter = ''

    @staticmethod
    def splitCmd(cmdTemplate, content):
        '''
        Chose from an optionful and optionless version of a command
        e.g. \foo{content} vs \foo[opts]{content}
        :param cmdTemplate: Tuple of optionful and optionless versions
        :param content: Comma-separated list of options, the last (possibly only) one being the content
        '''
        i = content.rfind(',')
        if i > -1:
            return cmdTemplate[0] % (content[:i], content[i+1:]) + '\n'
        else:
            return cmdTemplate[1] % content + '\n'

    @staticmethod
    def parseStrImmediate(s):
        '''
        Expedite the lex-parse-interpret cycle of a substring, using the
        slide parser; return the stringified resulting tree
        :param s: Substring to be parsed
        '''
        slideLexer.lineno = 1
        arr = slideParser.parse(s, slideLexer)
        Hierarchy.processQ()
        return ''.join(map(lambda x: str(x), arr))


class Slide(Hierarchy):

    def __init__(self, title, opts, plain, align, bg, bgUp, content, lexer, lineno, nextlineno):
        '''
        Parse slide title and contents, remember other attributes, advance lexer line number
        :param title: Slide title
        :param opts: Break/shrink option
        :param plain: Decoration removal option
        :param align: Vertical alignment option
        :param bg: Background image path
        :param bgUp: Background stretch opton
        :param content: Slide content
        :param lexer: Lexer instance used
        :param lineno: Line number at the beginning of slide
        :param nextlineno: Line number at the end of slide
        '''
        self.opts = opts
        self.plain = plain
        self.align = align
        self.bg = bg
        self.bgUp = bgUp
        self.lineno = lineno + 1 # Slide regex starts with \n
        self.genericInit(self.lineno, nextlineno)
        lexer.lineno = nextlineno

        slideLexer.lineno = lineno + 1
        self.title = slideParser.parse(title, slideLexer)
        if bg:
            slideLexer.lineno += 1 # Background specification takes up one more line if present
        self.children = slideParser.parse(content, slideLexer)

        # Hierarchical children of this slide will have added themselves to the parsing queue which we process now
        Hierarchy.processQ()

    def __str__(self):
        'Stringify slide tree'
        title = ''.join(map(lambda x: str(x), self.title))

        # Figure out necessary options and put them here:
        outerOpts = []
        innerOpts = []

        # Clear decorations?
        if self.plain:
            outerOpts.append(Config.getRaw('~sldOptsOut', 'plain'))
            innerOpts.append(Config.getRaw('~sldOptsIn', 'plain'))

        # Top/bottom alignment?
        if self.align:
            innerOpts.append(Config.getRaw('~sldOptsIn', 'align' + self.align))

        # Auto break or shrink?
        if len(self.opts) > 0:
            if self.opts[0] == '.':
                if self.opts == '...':
                    innerOpts.append(Config.getRaw('~sldOptsIn', 'break'))
                elif len(self.opts) == 1:
                    innerOpts.append(Config.getRaw('~sldOptsIn', 'shrinkA'))
                else:
                    try:
                        float(self.opts[1:])
                        innerOpts.append(Config.get('~sldOptsIn', 'shrink')(self.opts[1:]))
                    except:
                        warn('Slide title: Invalid shrink specifier:', self.opts[1:], range=self.lineno)
                        innerOpts.append(Config.getRaw('~sldOptsIn', 'shrinkA'))
            else:
                warn('Slide title: Invalid option:', self.opts, range=self.lineno)

        # Background?
        if self.bg:
            outerOpts.append(Config.get('~sldOptsOut',
                             'bgH' if self.bgUp else 'bgW')(
                             self.bg.strip()))

        # Flatten options
        outerOpts = '' .join(outerOpts)
        innerOpts = ','.join(innerOpts)

        # Add explanatory comments
        self.before = self.explainBefore + (
            Config.get('~sldBeginOpts')((outerOpts, innerOpts, title))
            if innerOpts else
            Config.get('~sldBegin')((outerOpts, title)))
        self.after  = Config.getRaw('~sldEnd') + self.explainAfter

        # Return Hierarchy-built string
        return super(Slide, self).__str__()


class ListItem(Hierarchy):

    enumCounters = ['i', 'ii', 'iii', 'iv']
    enumCounterCmd = '\\setcounter{enum%s}{%d}\n'
    counterValues = [0,0,0,0]

    begins = ['\\begin{itemize}\n', '\\begin{enumerate}\n', '\\begin{description}\n']
    specs = ['', '<alert@+>', '<+->', '<+-|alert@+>']
    markers = [r'\item%s %s', r'\item%s %s', r'\item%s[%s] ']
    ends = ['\\end{itemize}\n', '\\end{enumerate}\n', '\\end{description}\n']


    def lateInit(self, txt, lineno, **kw):
        lineno += 1
        txt = txt.strip()

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
        self.children = slideParser.parse(content, slideLexer)
        self.before = '%s' + self.markers[self.kind] % (self.specs[self.emph + self.uncover], describee)
        self.after = '\n'

    @classmethod
    def resolve(cls, docList, depth=0):
        '''
        Traverse given hierarchy collection and join adjacent list items of
        compatible kinds. Recurse on hierarchies encountered.
        :param docList: List of children of a collection to traverse
        :param depth: Current nested list depth. Should not be >3
        '''
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
                    l.before = l.explainBefore + cls.begins[l.kind] + l.before

                    # If this is an enumeration item which doesn't resume the counter, reset counter for current depth to 0
                    if l.kind == 1 and not l.resume:
                        cls.counterValues[depth] = 0

                # End list after current item if next item doesn't exist, is not a list item, or is a list item of a different kind
                if i == maxIndex or (docList[i+1].kind != l.kind if isinstance(docList[i+1], cls) else True):
                    l.after += cls.ends[l.kind] + l.explainAfter

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

    def lateInit(self, widthNum, widthUnit, align, overlay, content, lineno, **kw):
        'Identify column width specification, parse contents'

        # Identify width params
        self.percentage = self.units = 0.0

        if widthUnit: # Can either be '%' or None by regex
            self.percentage = float(widthNum) * 0.01
        elif widthNum:
            self.units = float(widthNum)
        else:
            self.units = 1.0

        self.align = align or ''
        self.overlay = overlay or ''

        slideLexer.lineno = lineno
        self.children = slideParser.parse(content, slideLexer)
        self.after='\n'

    @classmethod
    def resolve(cls, docList):
        '''
        Traverse given hierarchy collection and join adjacent columns in column
        environments; idistribute relative widths. Recurse on hierarchies encountered.
        :param docList: List of children of a collection to traverse
        '''
        currentColumnSet = []
        totalSpace = 1.0
        totalUnits = 0.0

        # A dummy element at the end ensures the last column set is processed if the current docList ends with a column (hack)
        for elem in docList + [None]:

            # Column encountered. Add it to current set and adjust counters
            if isinstance(elem, Column):
                currentColumnSet.append(elem)
                totalSpace -= elem.percentage
                totalUnits += elem.units

            # Non-column encountered. If a nonempty set exists, process it now.
            elif len(currentColumnSet) > 0:

                # Begin and end column environment around first and last columns of current set.
                currentColumnSet[0].before = currentColumnSet[0].explainBefore + Config.getRaw('~colBegin' + currentColumnSet[0].align)
                currentColumnSet[-1].after += Config.getRaw('~colEnd') + currentColumnSet[-1].explainAfter

                if totalSpace < 0.0: # Anti-stupid
                    warn('Fixed column widths exceed 100%.', totalSpace, 'remaining, setting to 0.')
                    totalSpace = 0.0

                # Generate column markers
                for col in currentColumnSet:
                    p = totalSpace * col.units / totalUnits if col.units else col.percentage
                    col.before += Config.get('~colMarker')((p, col.overlay))

                # Reset counters and set
                currentColumnSet = []
                totalSpace = 1.0
                totalUnits = 0.0

            # Recurse
            if isinstance(elem, Hierarchy):
                cls.resolve(elem.children)


class OrgTable(Hierarchy):

    # Regular expression for separating table cells from a row (based on capturing groups)
    r = re.compile(r'\|(\|?) *([<>^.,-]?)((?:\\\||[^\|\n])*)')
    # Regular expression for detecting horizontal bar lines
    b = re.compile(r'\|{1,2}(-+(\+-)*)+\|{1,2}')

    def lateInit(self, txt, lineno, **kw):

        # This will store the contents of cells
        self.arr = []
        # These will remember cell alignments and where to place margins
        self.aligns = ''
        self.vBars = ''
        self.hBars = []

        # Iterate through non-blank lines...
        i = 0
        for line in txt.splitlines():
            lineno += 1
            line = line.strip()
            if line:

                # Bar line. Mark horizontal bar
                if self.b.match(line):
                    self.hBars.append(i)

                # Contents line. Create a row in the matrix, split and process
                else:
                    self.arr.append([])
                    enumLine = [el for el in enumerate(self.r.findall(line))]

                    # Iterate over cells...
                    for j, (bar, align, text) in enumLine:

                        # First visit this far to the right. Note if vertical bar is needed
                        if len(self.vBars) <= j:
                            self.vBars += '|' if bar else ' '

                        # Not beyond right edge. Process contents
                        if j+1 < len(enumLine):

                            # First visit this far to the right. Note alignment, if any
                            if len(self.aligns) <= j:
                                self.aligns += align or 'A'

                            # Not first visit this far. Alignment symbol is actually part of the contents
                            else:
                                text = align + text

                            # Parse contents and add to current matrix row
                            slideLexer.lineno = lineno
                            self.arr[i].append(slideParser.parse(text.replace(r'\|', '|'), slideLexer))
                    i += 1

    def __str__(self):
        'Stringify table'

        # Stringify all children
        for arri in self.arr:
            for j in range(len(arri)):
                arri[j] = ''.join(map(lambda x: str(x), arri[j])).strip()

        # Regexs for identifying special types of cell contents
        rInteger = re.compile(r'-?\d+')
        rDecimalD = re.compile(r'-?\d*\.\d+')
        rDecimalC = re.compile(r'-?\d*,\d+')

        aligns = self.vBars[0]
        j = 0
        while j < len(self.aligns):
            thisAlign = self.aligns[j]

            # Decide automatic alignments
            if thisAlign == 'A':
                plain = integer = decimalD = decimalC = 0

                # Count cells of each kind on a column
                for arri in self.arr:
                    if j < len(arri):
                        if _fullmatch_greedy(rInteger, arri[j]):
                            integer += 1
                        elif _fullmatch_greedy(rDecimalD, arri[j]):
                            decimalD += 1
                        elif _fullmatch_greedy(rDecimalC, arri[j]):
                            decimalC += 1
                        else:
                            plain += 1

                # If majority is numeric, see which decimal character (if any) dominates
                if integer + decimalD + decimalC >= plain:
                    if decimalD or decimalC:
                        if decimalC > decimalD:
                            thisAlign = ','
                        else:
                            thisAlign = '.'
                    else:
                        # No decimal character. Simply right-align
                        thisAlign = '>'
                else:
                    # Not (sufficiently) numeric. Leave it left-aligned
                    thisAlign = '<'

            # Establish LaTeX code for this alignment (be it automatic or not)
            aligns += Config.getRaw('~orgTable', 'align', thisAlign) or 'l'

            # And add vertical bar spec
            j += 1
            aligns += self.vBars[j]

            # Fix headings: if using D column, cells not complying to decimal in use must centre-override alignment
            if thisAlign == '.':
                for arri in self.arr:
                    if j <= len(arri):
                        if not (_fullmatch_greedy(rDecimalD,arri[j-1]) or _fullmatch_greedy(rInteger,arri[j-1])):
                            arri[j-1] = Config.get('~orgTable', 'multicol')(
                                                  (aligns[-1], arri[j-1]))
            elif thisAlign == ',':
                for arri in self.arr:
                    if j <= len(arri):
                        if not (_fullmatch_greedy(rDecimalC,arri[j-1]) or _fullmatch_greedy(rInteger,arri[j-1])):
                            arri[j-1] = Config.get('~orgTable', 'multicol')(
                                                  (aligns[-1], arri[j-1]))

        debug('Aligns:', aligns, 'done')

        # Do we need tabularx or normal table?
        begin = 'begin'
        end   = 'end'
        if aligns.find('X') > -1:
            begin += 'X'
            end   += 'X'

        # Build LaTeX string
        s = self.explainBefore
        s += Config.get('~orgTable', begin)(aligns)
        hBar = Config.getRaw('~orgTable', 'hBar')

        for i in range(len(self.arr)):
            for j in range(self.hBars.count(i)):
                s += hBar
            s += '\n' + ' & '.join(self.arr[i]) + r' \\'

        # Don't forget horizontal bar spec after last line
        for j in range(self.hBars.count(len(self.arr))):
            s += hBar

        s += Config.getRaw('~orgTable', end)
        s += '\n' + self.explainAfter
        return s


class Macro(Hierarchy):
    macros = []

    def lateInit(self, txt, lineno, nextlineno, **kw):
        txt = txt.split(None, 1)
        self.cmd = txt[0]
        self.txt = [txt[1]] + txt[1].split() if len(txt) > 1 else ['']
        self.lineno = lineno
        self.rng = '%d-%d' % (lineno, nextlineno)

        self.macros.append(self)

    @classmethod
    def resolve(cls):
        'Run Python snippet for every macro; parse results of those that return Beamr code'
        for macro in cls.macros:

            # Callback for user code to call if Beamr parsing is desired on macro result
            def beamr(s):
                slideLexer.lineno = macro.lineno
                macro.children = slideParser.parse(s, slideLexer)

            # Callback for user code to call if macro results directly in LaTeX code
            def latex(s):
                macro.before = s

            # Run user code
            code = Config.getRaw('macro', macro.cmd)
            if not code:
                warn('Unknown macro', macro.cmd, range=macro.rng)

            try:
                exec(code, {'beamr': beamr, 'latex': latex, 'arg': macro.txt, 'debug': debug})
            except Exception as e:
                err('An error occurred during macro', macro.cmd,'execution:', e, range=macro.rng)
                debug('Macro', macro.cmd,'error:', repr(e), range=macro.rng)

            # Need to redo this manually as slide-side processing will have finished at this point
            Hierarchy.processQ()


class Box(Hierarchy):

    def lateInit(self, kind, title, content, overlay, lineno, **kw):
        '''
        Initialise box
        :param kind: Symbol (one of ?!*) denoting box kind
        :param title: Box title (will be parsed)
        :param content: Box content (will be parsed)
        :param overlay: Beamer overlay command
        :param lineno: Line number at the beginning of box
        '''
        self.kind = kind

        slideLexer.lineno = lineno
        self.title = slideParser.parse(title, slideLexer)
        slideLexer.lineno = lineno + 1
        self.children = slideParser.parse(content, slideLexer)
        self.overlay = overlay or ''

    def __str__(self):
        'Stringify box'
        title = ''.join(map(lambda x: str(x), self.title))

        self.before = self.explainBefore + Config.get('~boxBegin', self.kind)((title, self.overlay))
        self.after = Config.getRaw('~boxEnd', self.kind) + self.explainAfter

        return super(Box, self).__str__()


class Emph(Hierarchy):
    def lateInit(self, flag, txt, lineno, **kw):
        '''
        Initialise emphasised text
        :param flag: Emphasis flag
        :param txt: Contents (will be parsed)
        :param lineno: Line number at the beginning
        '''
        slideLexer.lineno = lineno
        self.flag = flag
        self.children = slideParser.parse(txt, slideLexer)

    def __str__(self):
        return Config.get('emph', self.flag)(super(Emph, self).__str__())


class Stretch(Hierarchy):
    def lateInit(self, flagS, flagF, txt, lineno, **kw):
        '''
        Initialise square bracket construct
        :param flagS: Flag at the start of construct
        :param flagF: Flag at the end of construct
        :param txt: Contents (will be parsed)
        :param lineno: Line number at the beginning of construct
        '''
        self.flagS = flagS or ''
        self.flagF = flagF or ''

        slideLexer.lineno = lineno
        if txt:
            self.children = slideParser.parse(txt, slideLexer)

    def __str__(self):
        '''Stringify by looking for appropriate command first by concatenated
        flags, then by start flag, then by start flag in emph dictionary'''
        f = Config.get('stretch', self.flagS + self.flagF, default=None)
        if not f and self.flagS == self.flagF:
            f = Config.get('stretch', self.flagS, default=None)
            if not f:
                f = Config.get('emph', self.flagS)
        if f:
            return f(super(Stretch, self).__str__())
        return super(Stretch, self).__str__()


class Footnote(Hierarchy):
    def lateInit(self, label, text, overlay, lineno, **kw):
        self.label = label
        self.overlay = overlay or ''
        self.lineno = lineno

        if text:
            slideLexer.lineno = lineno
            self.children = slideParser.parse(text, slideLexer)

    def __str__(self):
        'Pick the right command based on whether the footnote has label, contents, or both'
        if self.children:
            if self.label:
                self.before = Config.get('~fnLabel')(self.label)
            else:
                self.before = Config.getRaw('~fnSimple')
            self.after = '}' + self.overlay
        elif self.label:
            self.before = Config.get('~fnOnlyLabel')(self.label)
            if self.overlay:
                warn('Ignoring overlay indicator on label-only footnote', range=self.lineno)

        return super(Footnote, self).__str__()
