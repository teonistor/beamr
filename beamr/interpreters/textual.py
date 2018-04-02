'''
Created on 6 Feb 2018

@author: Teodor Gherasim Nistor

'''
from __future__ import division
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
        if txt == r'\#':
            super(Escape, self).__init__(txt)
        else:
            super(Escape, self).__init__(txt[1:])


class AsciiArt(Text):
    def __str__(self):
        from beamr.interpreters import Config
        return Config.getRaw('~asciiArt', self.txt) or ''


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
    firstRun = True
    pilImage = None
    pilErr = None

    def __init__(self, txt):
        # First time setup
        if self.__class__.firstRun:
            self.__class__.firstRun = False
            try:
                from PIL import Image
                self.__class__.pilImage = Image
            except ImportError as e:
                self.__class__.pilErr = e

        # Remember line range for future warnings etc and update lexers accordingly
        self.lineno = '%d-%d' % (slideLexer.lineno, slideLexer.nextlineno)
        imageLexer.lineno = slideLexer.lineno
        slideLexer.lineno = slideLexer.nextlineno

        try:
            self.files, self.shape, self.align, self.dims = imageParser.parse(txt[2:-1].strip(), imageLexer)
            debug(self.files, self.shape, self.align, self.dims, range=self.lineno)

        # Anti-stupid: Ignore an empty environment
        except:
            self.files = None
            warn('Invalid image frame', range=self.lineno)

    # Helper method to check the validity of a file as best as possible under current configuration
    @classmethod
    def checkFile(cls, file):
        if cls.pilImage:
            try:
                cls.pilImage.open(file)
                return True
            except:
                return False
        cls.pilWarn()
        return os.path.isfile(file)

    # Helper method to recurst through file paths and extension until a file is found
    def resolveFile(self, file):
        if file:
            from beamr.interpreters import Config
            for path in Config.getRaw('graphicspath'):
                f = os.path.join(path, file)
                for ext in Config.getRaw('imgexts'):
                    fe = f + ext
                    if self.checkFile(fe):
                        return fe
            warn('Image Frame: Could not find file', file, range=self.lineno)
        return None

    # Get image dimensions, if known and obtainable
    @classmethod
    def getDims(cls, file):
        if file:
            if cls.pilImage:
                try:
                    return cls.pilImage.open(file).size
                except:
                    return None
            cls.pilWarn()
            return (1,1)
        return None

    # Warn only once about the absence of PIL package
    @classmethod
    def pilWarn(cls):
        if cls.pilErr:
            warn('Image Frame:', cls.pilErr, 'Falling back to basic grid. Some images may be distorted.')
            cls.pilErr = None

    def __str__(self):
        if not self.files:
            return ''

        from beamr.interpreters import Config

        # One image...
        def singleImage(dims, file, makeHspace=False, implicitDims=r'width=\textwidth'):
            if not file:
                if makeHspace and dims[0]:
                    return r'\hspace{%.3f%s}' % dims[0]
                else:
                    return ''

            if dims[0]:
                if dims[1]:
                    return Config.get('~image', 'wh')((dims[0][0], dims[0][1], dims[1][0], dims[1][1], file))
                else:
                    return Config.get('~image', 'w-')((dims[0][0], dims[0][1], file))
            else:
                if dims[1]:
                    return Config.get('~image', '-h')((dims[1][0], dims[1][1], file))
                else:
                    return Config.get('~image', '--')((implicitDims, file))

        # Multi image...

        def vStrip(dims, files):
            # Flatten into a vertical list
            return grid(dims, [[file] for line in files for file in line], False)

        def hStrip(dims, files):
            # Flatten into a horizontal list
            return grid(dims, [[file for line in files for file in line]], True)

        def grid(dims, files, implicitFillWidth=True):
            safe = Config.getRaw('safe')
            imageDims = []

            # Stage 1: Collect dimensions and from found files and calculate missing ones
            # as averages. Update file paths if safe.
            sumW = 0
            sumH = 0
            correctCount = 0
            incorrectQ = []

            for i in range(len(files)):
                imageDims.append([])
                for j in range(len(files[i])):
                    file = self.resolveFile(files[i][j])

                    if file:
                        w,h = self.getDims(file)
                        imageDims[i].append([w,h])
                        sumW += w
                        sumH += h
                        correctCount += 1
                    else:
                        imageDims[i].append(None)
                        incorrectQ.append((i,j))

                    if safe:
                        if file:
                            debug('Image frame:', files[i][j], 'resolved as', file, range=self.lineno)
                        files[i][j] = file

            if correctCount:
                incorrectDims = (sumW / correctCount, sumH / correctCount)

            elif safe:
                    warn('Invalid image frame (no valid files found)', range=self.lineno)
                    return ''
            else:
                incorrectDims = (1,1)

            for i,j in incorrectQ:
                imageDims[i][j] = [iDim for iDim in incorrectDims]

            # Stage 2: Scale images according to first per row, and rows according to first row
            sumW = sumH = 0
            for i in range(len(imageDims)):
                thisRowW = 0
                for j in range(len(imageDims[i])):
                    imageDims[i][j][0] *= imageDims[i][0][1] / imageDims[i][j][1]
                    imageDims[i][j][1]  = imageDims[i][0][1]
                    thisRowW += imageDims[i][j][0]
                if sumW:
                    for j in range(len(imageDims[i])):
                        imageDims[i][j][0] *= sumW / thisRowW
                        imageDims[i][j][1] *= sumW / thisRowW
                else:
                    sumW = thisRowW
                sumH += imageDims[i][0][1]

            # Stage 3: Generate code
            s = ''
            for i in range(len(files)):
                for j in range(len(files[i])):
                    thisDim = ((dims[0][0] * imageDims[i][j][0] / sumW, dims[0][1]) if dims[0] else None,
                               (dims[1][0] * imageDims[i][j][1] / sumH, dims[1][1]) if dims[1] else None)
                    if not (dims[0] or dims[1]):
                        if implicitFillWidth:
                            thisDim = ((imageDims[i][j][0] / sumW, r'\textwidth'), None)
                        else:
                            thisDim = (None, (imageDims[i][j][1] / sumH, r'\textheight'))
                    s += singleImage(thisDim, files[i][j], True)
                s += r'\mbox{}\\'

            # TODO Fit inside with no stretch?

#             x=0
#             y=len(files)
#             for line in files:
#                 if len(line) > x:
#                     x = len(line)
#             dims = ((dims[0][0] / x, dims[0][1]) if dims[0] else None,
#                     (dims[1][0] / y, dims[1][1]) if dims[1] else None)
#             if not (dims[0] or dims[1]):
#                 if implicitFillWidth:
#                     dims = ((1.0/x, r'\textwidth'), None)
#                 else:
#                     dims = (None, (1.0/y, r'\textheight'))
#     
#             s = ''
#             for line in files:
#                 for file in line:
#                     s += singleImage(dims, file=file)
#                 s += r'\\'
            return s

        # Map symbols to shapes
        shapes = {'|': vStrip,
                  '-': hStrip,
                  '+': grid  }

        # Single image (no or unrecognised shape)
        if self.shape not in shapes:
            if len(self.files) > 1 or len(self.files[0]) > 1:
                warn('Image frame: Shape not specified therefore only first of multiple files will be used', range=self.lineno)
            if Config.getRaw('safe'):
                file = self.resolveFile(self.files[0][0])
                return singleImage(self.dims, file)
            else:
                return singleImage(self.dims, self.files[0][0])

        # Multi image, choose from shape above
        return shapes[self.shape](self.dims, self.files)


class PlusEnv(Text):

    def __init__(self, txt):
        # TODO
        warn('Plus integration not yet implemented', slideLexer.lineno+1)
        super(PlusEnv, self).__init__( 'Plus: ' + txt)
        slideLexer.lineno = slideLexer.nextlineno


class TableEnv(Text):
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

        # Stringify all children
        for arri in self.arr:
            for j in range(len(arri)):
                arri[j] = str(arri[j]).strip()

        from beamr.interpreters import Config
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
        s = Config.get('~orgTable', begin)(aligns)
        hBar = Config.getRaw('~orgTable', 'hBar')

        for i in range(len(self.arr)):
            if i in self.hBars:
                s += hBar
            s += '\n' + ' & '.join(self.arr[i]) + r' \\'

        # Don't forget horizontal bar spec after last line
        if len(self.arr) in self.hBars:
            s += hBar

        s += Config.getRaw('~orgTable', end)
        return s


class ScissorEnv(Text):
    rRange = re.compile(r'\d+(-\d+)?(,\d+(-\d+)?)*')

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

            if _fullmatch_greedy(self.rRange, arr[1]):
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

def _fullmatch_greedy(r,s):
    '''Check if regex object r fully matches string s
    In Python 3 this is done by calling r.fullmatch()
    In Python 2 this is done by comparing the length of the matched substring to that of s.
    Therefore, equivalence is only guaranteed on regex without non-greedy operators.
    '''
    try:
        return bool(r.fullmatch(s))
    except:
        m = r.match(s)
        return m and m.end() == len(s)
