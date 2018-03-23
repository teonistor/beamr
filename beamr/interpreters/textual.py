'''
Created on 6 Feb 2018

@author: Teodor Gherasim Nistor

'''
import os.path
import re
from beamr.lexers import docLexer, imageLexer, slideLexer
from beamr.parsers import imageParser
from beamr.debug import debug, warn


class Text(object):
    
    def __init__(self, txt):
        self.txt = txt

    def __str__(self):
        return self.txt
    
    def __repr__(self):
        return self.__str__()


class Comment(Text):
    def __init__(self, txt):
        debug('Comment ', txt, range=slideLexer.lineno)
        from beamr.interpreters import Config
        super(Comment, self).__init__(Config.get('~comment')(txt))


class Escape(Text):
    def __init__(self, txt):
        debug('Escape', txt, range=slideLexer.lineno)
        super(Escape, self).__init__(txt[1:])


class Antiescape(Text):
    def __str__(self):
        from beamr.interpreters.config import Config
        if self.txt in Config.getRaw('antiescape'):
            return '\\' + self.txt
        else:
            return self.txt


class Citation(Text):
    def __init__(self, txt, opts):
        self.txt = txt
        self.opts = opts
        self.lineno = slideLexer.lineno

    def __str__(self):
        from beamr.interpreters.config import Config
        if Config.getRaw('bib'):
            if self.opts:
                return Config.get('~citeOpts')((self.opts, self.txt))
            else:
                return Config.get('~citeSimple')(self.txt)
        else:
            warn('Citations used but no bibliography file given! Skipping.', range=self.lineno)
            return ''


class Url(Text):
    def __str__(self):
        from beamr.interpreters.config import Config
        return Config.get('~url')(self.txt)


class Heading(Text):
    usedMarkers = []

    def __init__(self, txt):
        super(Heading, self).__init__(txt)
        self.lineno = docLexer.lineno

    def __str__(self):
        txt = self.txt.strip().splitlines()
        marker = txt[1][0]
        
        try:
            i = Heading.usedMarkers.index(marker)
        except:
            i = len(Heading.usedMarkers)
            Heading.usedMarkers.append(marker)

        if i > 2: # Anti-stupid
            warn("Something's wrong with heading marker", marker, 'having index', i, range=self.lineno)
            i = 2
            
        from beamr.interpreters.config import Config
        debug('Heading level', i, marker, txt[0], range=self.lineno)
        return Config.get('~heading', i)(txt[0])


class ImageEnv(Text):
    # TODo cf \includepdf[pages=61,width=\paperwidth,height=\paperheight]{yourfile.pdf}

    markers = [r'\includegraphics[width=%.3f%s,height=%.3f%s]{%s}',
               r'\includegraphics[width=%.3f%s]{%s}',
               r'\includegraphics[height=%.3f%s]{%s}',
               r'\includegraphics[%s]{%s}']

    def __init__(self, txt):
        try:
            imageLexer.lineno=slideLexer.lineno
            files, shape, align, dims = imageParser.parse(txt[2:-1].strip(), imageLexer)
            debug(files, shape, align, dims)

        # Anti-stupid: Ignore an empty environment
        except:
            super(ImageEnv, self).__init__('')
            return

        def singleImage(dims, files=None, file=None, implicitDims=r'width=\textwidth'):
            if not file:
                file = files[0][0]
            if dims[0]:
                if dims[1]:
                    return self.markers[0] % (dims[0][0], dims[0][1], dims[1][0], dims[1][1], file)
                else:
                    return self.markers[1] % (dims[0][0], dims[0][1], file)
            else:
                if dims[1]:
                    return self.markers[2] % (dims[1][0], dims[1][1], file)
                else:
                    return self.markers[3] % (implicitDims, file)


        def vStrip(dims, files):
            # Flatten into a vertical list
            return smartGrid(dims, [[file] for line in files for file in line], False)

        def hStrip(dims, files):
            # Flatten into a horizontal list
            return smartGrid(dims, [[file for line in files for file in line]], True)

        def grid(dims, files, implicitFillWidth=True):
            x=0
            y=len(files)
            for line in files:
                if len(line) > x:
                    x = len(line)
            dims = ((dims[0][0] / x, dims[0][1]) if dims[0] else None,
                    (dims[1][0] / y, dims[1][1]) if dims[1] else None)
            if not (dims[0] or dims[1]):
                if implicitFillWidth:
                    dims = ((1.0/x, r'\textwidth'), None)
                else:
                    dims = (None, (1.0/y, r'\textheight'))

            s = ''
            for line in files:
                for file in line:
                    s += singleImage(dims, file=file)
                s += r'\\'
            return s

        def smartGrid(dims, files, implicitFillWidth=True):
            warn('Image Frame: PIL support not yet implemented, falling back to basic grid. Some images may be distorted.', range=slideLexer.lineno)
            return grid(dims, files, implicitFillWidth)

        shapes = {'|': vStrip,
                  '-': hStrip,
                  '+': grid,
                  '#': smartGrid}

        super(ImageEnv, self).__init__(shapes.get(shape, singleImage)(dims, files))
        slideLexer.lineno = slideLexer.nextlineno


class PlusEnv(Text):

    def __init__(self, txt):
        # TODO
        warn('Plus integration not yet implemented', slideLexer.lineno+1)
        super(PlusEnv, self).__init__( 'Plus: ' + txt)
        slideLexer.lineno = slideLexer.nextlineno


class TableEnv(Text):

    begin = r'\begin{center}\begin{tabular}{%s}'
    beginX = r'\begin{tabularx}{\textwidth}{%s}'
    end = r'\end{tabular}\end{center}'
    endX = r'\end{tabularx}'
    hBar = '\n\\hline'

    def __init__(self, txt):
        # TODO
        self.remember([])
        slideLexer.lineno = slideLexer.nextlineno

    def remember(self, arr, aligns='', vBars='', hBars=None):
        self.arr = arr
        maxWidth = max(map(lambda a: len(a), arr))
        self.aligns = aligns or 'c' * maxWidth
        self.vBars = vBars or ' ' + '|' * (maxWidth-1) + ' '
        self.hBars = hBars or range(1, len(arr))

    def __str__(self):
        aligns = ''.join([self.vBars[i] + self.aligns[i] for i in range(len(self.aligns))]) + self.vBars[-1]
        debug('Aligns:', aligns, 'done')

        s = (self.begin if aligns.find('X') == -1 else self.beginX) % aligns
        for i in range(len(self.arr)):
            if i in self.hBars:
                s += self.hBar
            s += '\n' + ' & '.join(map(lambda a: str(a), self.arr[i])) + r' \\'
        if len(self.arr) in self.hBars:
            s += self.hBar
        s += (self.end if aligns.find('X') == -1 else self.endX) + '\n'
        return s


class ScissorEnv(Text):

    def __init__(self, txt):
        super(ScissorEnv, self).__init__(txt)
        self.lineno = docLexer.lineno

    def __str__(self):
        arr = self.txt.strip().split()
        if not len(arr):
            warn('Empty 8< command, omitting', range=self.lineno)
            return ''

        from beamr.interpreters.config import Config

        if not (os.path.isfile(arr[0]) or os.path.isfile(arr[0] + '.pdf')):
            if Config.getRaw('safe'):
                warn('File for 8< not found, omitting', range=self.lineno)
                return ''
            else:
                warn('File for 8< not found, proceeding unsafely', range=self.lineno)

        if len(arr) > 1:
            if len(arr) > 2:
                warn('Ignoring extraneous arguments in 8<', range=self.lineno)

            if re.fullmatch(r'\d+(-\d+)?(,\d+(-\d+)?)*', arr[1]):
                return Config.get('~scissorPages')((arr[1], arr[0]))

            else:
                warn('Ignoring malformed page range in 8<', range=self.lineno)

        return Config.get('~scissorSimple')(arr[0])


class VerbatimEnv(Text):
    
    count=0
    todo = []
    preambleDefs = ''

    def __init__(self, head, body):
        self.__class__.count += 1
        self.__class__.todo.append(self)

        # Document.classResulutionSet.add(__class__)
        # TODO

        # We can use Config here as this part of the dict is not supposed to ever change
        from beamr.interpreters import Config
        lettr = ''
        num = self.__class__.count
        while num:
            lettr += chr(64 + num%27)
            num //= 27
        self.insertCmd = Config.get('~vbtmCmds', 'insertion')(lettr)
        self.head = head
        self.body = body
        super(VerbatimEnv, self).__init__(self.insertCmd)

    @classmethod
    def resolve(cls):
        if cls.count:

            # Ensure proper package name is given
            from beamr.interpreters import Config
            package = Config.getRaw('verbatim')
            packageList = Config.getRaw('~vbtmCmds', 'packageNames')
            if package not in packageList:
                package = packageList[0]
                Config.effectiveConfig['verbatim'] = package
            Config.effectiveConfig['packages'].append(package)

            cls.preambleDefs = Config.getRaw('~vbtmCmds', 'once', package) + '\n'

            for f in cls.todo:
                if f.head:
                    cls.preambleDefs += Config.getRaw('~vbtmCmds', 'foreach', package) % (
                             f.insertCmd,
                             f.head,
                             f.body)
                else:
                    cls.preambleDefs += Config.getRaw('~vbtmCmds', 'foreachNoLang', package) % (
                             f.insertCmd,
                             f.body)
