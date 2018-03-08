'''
Created on 1 Feb 2018

@author: Teodor Gherasim Nistor
'''
from beamr.debug import debug, warn
from beamr.lexers import docLexer, slideLexer
from beamr.parsers import docParser, slideParser
from beamr.interpreters import Config, VerbatimEnv

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

    docClassCmd = (r'\documentclass[%s]{%s}', r'\documentclass{%s}')
    packageCmd = (r'\usepackage[%s]{%s}', r'\usepackage{%s}')
    titlePageCmd = '\\frame{\\titlepage}\n'
    begin = '\n\\begin{document}\n'
    end = '\\end{document}\n'

    # TODO title gizmos e.g. \title[This will be in footer]{This will be on title slide} Also, [\insertframenumber/\inserttotalframenumber]
    preambleCmds = {'theme'    : '\\usetheme{%s}\n',
                    'scheme'   : '\\usecolortheme{%s}\n',
                    'title'    : '\\title{%s}\n',
                    'author'   : '\\author{%s}\n',
                    'institute': '\\institute{%s}\n',
                    'date'     : '\\date{%s}\n'}

    def __init__(self, txt):
        if txt.find('\t') > -1:
            txt = txt.replace('\t','    ')
            warn("Input file has tabs, which will be considered 4 spaces; but please don't use tabs!")
        super(Document, self).__init__(docParser.parse(txt, docLexer), after=self.end)

        # Collect all kinds of configuration
        Config.resolve()
        debug('Final config', Config.effectiveConfig)

        # Post-factum list, column, and verbatim environment resolution
        ListItem.resolve(self.children)
        Column.resolve(self.children)
        VerbatimEnv.resolve()

        # Document class and package commands
        packageDef = self.splitCmd(self.docClassCmd, Config.getRaw('docclass'))
        for pkg in Config.effectiveConfig['packages']:
            packageDef += self.splitCmd(self.packageCmd, pkg)
        packageDef += '\n'

        # Outer preamble commands
        outerPreamble = ''
        for k in self.preambleCmds:
            if k in Config.effectiveConfig:
                outerPreamble += self.preambleCmds[k] % Config.getRaw(k)

        # Inner preamble commands
        innerPreamble = VerbatimEnv.preambleDefs
        if Config.effectiveConfig.get('titlepage', 'no') in ['yes', 'y', 'true', True]:
            innerPreamble += self.titlePageCmd

        self.before = packageDef + outerPreamble + self.begin + innerPreamble

    @staticmethod
    def splitCmd(cmdTemplate, content):
        i = content.rfind(',')
        if i > -1:
            return cmdTemplate[0] % (content[:i], content[i+1:]) + '\n'
        else:
            return cmdTemplate[1] % content + '\n'


class Slide(Hierarchy):

    parsingQ = []

    before = '\\begin{frame}%s{%s}\n'
    after = '\n\\end{frame}\n'

    def __init__(self, txt):
        headBegin = txt.find('[')
        headEnd = txt.find('\n', headBegin)
        headSplit = (txt.find(' ', headBegin) + 1) or headEnd # If there is a blank, title begins after it; otherwise stop at end of line and title will be the empty string.

# TODO THERE IS A BUG HERE WHEN SLIDE OPEN JUST BY [ ALONE

        # Add breaks or shrink if applicable
        opts = txt[headBegin+1 : headSplit].strip()
        if len(opts) > 0:
            if opts[0] == '.':
                if opts == '...':
                    opts = '[allowframebreaks]'
                else:
                    try:
                        float(opts[1:])
                        opts = '[shrink=%s]' % opts[1:]
                    except:
                        warn('Slide title: Invalid shrink specifier:', opts[1:])
                        opts = ''
            else:
                warn('Slide title: Invalid slide option:', opts)
                opts = ''

        super(Slide, self).__init__(slideParser.parse(txt[headEnd:-1], slideLexer),
                         self.before % (opts, txt[headSplit:headEnd]),
                         self.after)

        # Hierarchical children will have added themselves to the parsing queue which we process now
        while len(self.parsingQ) > 0:
            self.parsingQ.pop()()


class ListItem(Hierarchy):

    enumCounters = ['i', 'ii', 'iii', 'iv']
    enumCounterCmd = '\\setcounter{enum%s}{%d}\n'
    counterValues = [0,0,0,0]

    begins = ['\\begin{itemize}\n', '\\begin{enumerate}\n', '\\begin{description}\n']
    specs = ['', '<alert@+>', '<+->', '<+-|alert@+>']
    markers = [r'\item%s %s', r'\item%s %s', r'\item%s[%s] ']
    ends = ['\\end{itemize}\n', '\\end{enumerate}\n', '\\end{description}\n']
    
    
    def __init__(self, txt):
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
            
            super(ListItem, self).__init__(slideParser.parse(content, slideLexer),
                     '%s' + self.markers[self.kind] % (self.specs[self.emph + self.uncover], describee),
                     '\n')

        Slide.parsingQ.insert(0, innerFunc)
    
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

    begin = '\\begin{columns}\n'
    end = '\\end{columns}'
    marker = '\\column{%.3f\\textwidth}\n'

    def __init__(self, txt):
        txt = txt.strip()

        debug('Txt picked up by col:', txt)
        i = txt.find('\n') # Guaranteed >0 by regex
        head = txt[1:i].strip()
        txt = txt[i+1:]

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
            super(Column, self).__init__(slideParser.parse(txt, slideLexer), after='\n')
        Slide.parsingQ.insert(0, innerFunc)

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
                currentColumnSet[0].before = cls.begin
                currentColumnSet[-1].after += cls.end

                if totalSpace < 0.0: # Anti-stupid
                    warn('Fixed column widths exceed 100%.', totalSpace, 'remaining, setting to 0.')
                    totalSpace = 0.0

                # Generate column markers
                for col in currentColumnSet:

                    # If width unspecified, allocate space unclaimed by fixed-percentage columns
                    if col.unspecified:
                        col.percentage = totalSpace / unspecifiedCount

                    col.before += cls.marker % (col.percentage if col.percentage > 0.0
                                                else col.units / totalUnits * totalSpace)

                # Reset counters and set
                currentColumnSet = []
                totalSpace = 1.0
                totalUnits = 0.0
                unspecifiedCount = 0

            # Recurse
            if isinstance(elem, Hierarchy):
                cls.resolve(elem.children)


class Box(Hierarchy):

    # TODO anything config-able?
    # TODO other types of box (affects regex)

    begin = '\\begin{%sblock}{%s}\n'
    end = '\\end{%sblock}\n'

    def __init__(self, txt):
        txt = txt.strip()[:-1]

        # Isolate head (marker & title) from content
        i = txt.find('\n') # Guaranteed >0 by regex definition
        head = txt[:i].strip()
        txt = txt[i+1:]

        # Find box kind based on marker
        kind = ''
        if head[1] == '!':
            kind = 'alert'

        # Isolate title (if any)
        head = head[2:]

        # Enqueue function below to be called when all current parsing has finished
        def innerFunc():
            super(Box, self).__init__(slideParser.parse(txt, slideLexer),
                                      self.begin % (kind, head),
                                      self.end % kind)

        Slide.parsingQ.insert(0, innerFunc)


class Emph(Hierarchy):
    def __init__(self, flag, txt):
        self.flag = flag
        def innerFunc():
            super(Emph, self).__init__(slideParser.parse(txt, slideLexer))
        Slide.parsingQ.insert(0, innerFunc)

    def __str__(self):
        return Config.get('emph', self.flag)(super(Emph, self).__str__())


class Stretch(Hierarchy):
    def __init__(self, flag, txt=''):
        self.flag = flag
        def innerFunc():
            super(Stretch, self).__init__(slideParser.parse(txt, slideLexer) if txt else [])
        Slide.parsingQ.insert(0, innerFunc)

    def __str__(self):
        return Config.get('stretch', self.flag)(super(Stretch, self).__str__())


class Footnote(Hierarchy):
    def __init__(self, txt):
        def innerFunc():
            super(Footnote, self).__init__(slideParser.parse(txt, slideLexer),
                                            r'\footnote[frame]{', '}')
        Slide.parsingQ.insert(0, innerFunc)
