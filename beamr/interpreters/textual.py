'''
Created on 6 Feb 2018

@author: Teodor Gherasim Nistor

'''
from __future__ import division
import os.path
import re
from beamr.lexers import imageLexer
from beamr.parsers import imageParser
from beamr.debug import debug, warn


class Text(object):
    
    def __init__(self, txt, lineno, nextlineno, lexer, **kw):
        '''
        Record text parameters and advence lexer. kw takes any additional
        parameters required by sbuclasses
        :param txt: Text itself
        :param lineno: Line number at the beginning
        :param nextlineno: Line number at the end
        :param lexer: Lexer being used
        '''
        self.txt = txt
        self.lineno = lineno
        self.nextlineno = nextlineno
        self.lexer = lexer
        self.kw = kw
        lexer.lineno = nextlineno

    def __str__(self):
        'The string form of simple text is itself'
        return self.txt


class Comment(Text):
    def __str__(self):
        '''Add LaTeX comment in front of the text of this comment,
        specifying line number in originating file'''
        debug('Comment ', self.txt, range=self.lineno)
        from beamr.interpreters import Config
        return Config.get('~comment')((self.lineno, self.txt[1:]))


class Escape(Text):
    def __str__(self):
        '''Return escaped character alone, except if it is a hash,
        in which case preserve the escaping backslash'''
        debug('Escape', self.txt, range=self.lineno)
        if self.txt == r'\#':
            return self.txt
        return self.txt[1:]


class AsciiArt(Text):
    def __str__(self):
        'Return the corresponding command from config'
        from beamr.interpreters import Config
        return Config.getRaw('~asciiArt', self.txt) or ''


class Antiescape(Text):
    def __str__(self):
        '''If this symbol exists in the antiescape string in the config, put
        a backslash in front; otherwise return the symbol as is'''
        from beamr.interpreters.config import Config
        if self.txt in Config.getRaw('antiescape'):
            return '\\' + self.txt
        else:
            return self.txt


class Citation(Text):
    def __str__(self):
        from beamr.interpreters.config import Config

        # Check that there exists a source of citations
        if Config.getRaw('bib') or Config.getRaw('bibFile'):
            opts = self.kw['opts']
            if opts:
                return Config.get('~citeOpts')((opts, self.txt))
            else:
                return Config.get('~citeSimple')(self.txt)
        else:
            warn('Citations used but no bibliography file given! Skipping.', range=self.lineno)
            return ''


class Url(Text):
    def __str__(self):
        'Wrap this URL in the URL command from config'
        from beamr.interpreters.config import Config

        # 'txt' is the target, while text is the 'text' to be displayed
        text = self.kw['text'] or self.txt
        return Config.get('~url')((self.txt, text))


class Heading(Text):
    usedMarkers = []

    def __str__(self):
        'Find the depth of this heading and return corresponding LaTeX command'
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

    def __init__(self, txt, lineno, nextlineno, lexer, **kw):
        super(ImageEnv, self).__init__(txt[2:-1].strip(), lineno, nextlineno, lexer, **kw)

        # First time setup
        if self.__class__.firstRun:
            self.__class__.firstRun = False
            try:
                from PIL import Image
                self.__class__.pilImage = Image
            except ImportError as e:
                self.__class__.pilErr = e

    @classmethod
    def checkFile(cls, file):
        'Check the validity of a file as best as possible under current configuration'
        if cls.pilImage:
            try:
                cls.pilImage.open(file)
                return True
            except:
                return False
        cls.pilWarn()
        return os.path.isfile(file)

    def resolveFile(self, file):
        'Recurse through file paths and extensions until a file is found and return its full path'
        if file and file != '.':
            from beamr.interpreters import Config
            for path in Config.getRaw('graphicspath'):
                f = os.path.join(path, file)
                for ext in Config.getRaw('imgexts'):
                    fe = f + ext
                    if self.checkFile(fe):
                        return fe
            warn('Image Frame: Could not find file', file, range=self.lineno)
        return None

    @classmethod
    def getDims(cls, file):
        '''Obtain and return image dimensions.
        If file not given or not openable, return None
        If file given but PIL unavailable, return dummy dimensions (1,1)'''
        if file:
            if cls.pilImage:
                try:
                    return cls.pilImage.open(file).size
                except:
                    return None
            cls.pilWarn()
            return (1,1)
        return None

    @classmethod
    def pilWarn(cls):
        'Warn only once about the absence of PIL package'
        if cls.pilErr:
            warn('Image Frame:', cls.pilErr, 'Falling back to basic grid. Some images may be distorted.')
            cls.pilErr = None

    def __str__(self):
        'Parse and process contents of this image frame and return the LaTeX commands to generate it if no errors occur'
        imageLexer.lineno = self.lineno
        self.lineno = '%d-%d' % (self.lineno, self.nextlineno)

        # Try and parse contents
        try:
            self.files, self.shape, self.align, self.dims = imageParser.parse(self.txt, imageLexer)
            debug(self.files, self.shape, self.align, self.dims, range=self.lineno)

        # Anti-stupid: Ignore an empty environment
        except:
            self.files = None
            warn('Invalid image frame', range=self.lineno)
        if not self.files:
            return ''

        from beamr.interpreters import Config

        # One image...
        def singleImage(dims, file, makeHspace=False, implicitDims=r'width=\textwidth'):
            '''
            Return the LaTeX command to insert this one image
            :param dims: Image dimensions, as a tuple of optional tuples of numbers and units
            :param file: File name or path
            :param makeHspace: Whether to return command for a horizontal space instead if file is None
            :param implicitDims: Dimensions to be used instead if all tuples in dims are None
            '''
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
            'Flatten files matrix into a vertical list (a list of one-item lists)'
            return grid(dims, [[file] for line in files for file in line], False)

        def hStrip(dims, files):
            'Flatten files matrix into a horizontal list (a list of one list of all items)'
            return grid(dims, [[file for line in files for file in line]], True)

        def grid(dims, files, implicitFillWidth=True):
            '''
            Process a grid of images and return LaTeX commands that create it
            :param dims: Overall dimensions of the grid
            :param files: Matrix of file names
            :param implicitFillWidth: Whether to use full width if dimensions are None (default); otherwise use full height
            '''
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

                    if safe or files[i][j] == '.':
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
    def __str__(self):
        '# TODO'
        warn('Plus integration not yet implemented', range=self.lineno+1)
        return ''


class ScissorEnv(Text):
    rRange = re.compile(r'\d+(-\d+)?(,\d+(-\d+)?)*')

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

    def __init__(self, txt, lineno, nextlineno, lexer, head, **kw):
        ''' Remember head and body of Verbatim environment and assign unique identifier
        based on occurrence count
        :param txt: Body (code contents) of environment
        :param head: Head (language specification) of environment
        :param lineno: Line number at beginning
        :param nextlineno: Line number at end
        :param lexer: Lexer instance in use
        '''
        super(VerbatimEnv, self).__init__(txt, lineno, nextlineno, lexer, **kw)
        self.head = head
        self.body = txt

        # Count occurrences of Verbatim throughout document
        self.__class__.count += 1
        self.__class__.todo.append(self)

        # Create unique identifier for this Verbatim
        self.lettr = ''
        num = self.__class__.count
        while num:
            self.lettr += chr(64 + num%27)
            num //= 27

    @classmethod
    def resolve(cls):
        '''Create each code listing in a box at the beginning of the document, so
        they can more easily be included in slides
        Update each in-document instance with appropriate insertion command'''
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
                f.txt = Config.get('~vbtmCmds', 'insertion')(f.lettr)
                if f.head:
                    cls.preambleDefs += Config.getRaw('~vbtmCmds', 'foreach', package) % (
                             f.txt,
                             f.head,
                             f.body)
                else:
                    cls.preambleDefs += Config.getRaw('~vbtmCmds', 'foreachNoLang', package) % (
                             f.txt,
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
