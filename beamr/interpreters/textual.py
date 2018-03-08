'''
Created on 6 Feb 2018

@author: Teodor Gherasim Nistor

'''
import os.path
import re
from beamr.lexers import imageLexer
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
        debug('Comment ', txt)
        super(Comment, self).__init__('% ' + txt)


class Escape(Text):
    def __init__(self, txt):
        super(Escape, self).__init__(txt[1:])


class Citation(Text):
    def __str__(self):
        from beamr.interpreters.config import Config
        if Config.effectiveConfig['bib']:
            return r'\cite{' + self.txt + '}'
        else:
            warn('Citations used but no bibliography file given.')
            return ''


class Url(Text):
    def __init__(self, txt):
        super(Url, self).__init__(r'\url{' + txt + '}')


class Heading(Text):
    usedMarkers = []
    formats = [
#         '\\chapter{ %s }\n', # Invalid?
        '\\section{ %s }\n',
        '\\subsection{ %s }\n',
        '\\subsubsection{ %s }\n'
        ]
    
    def __init__(self, txt):
        txt = txt.strip().splitlines()
        marker = txt[1][0]
        
        try:
            i = Heading.usedMarkers.index(marker)
        except:
            i = len(Heading.usedMarkers)
            Heading.usedMarkers.append(marker)

        if i > 2: # Anti-stupid
            warn("Something's wrong with heading marker", marker, 'having index', i)
            i = 2
            
        super(Heading, self).__init__(Heading.formats[i] % txt[0])
        debug('Heading level', i, marker, txt[0])


class ImageEnv(Text):
    # TODo cf \includepdf[pages=61,width=\paperwidth,height=\paperheight]{yourfile.pdf}

    markers = [r'\includegraphics[width=%.3f%s,height=%.3f%s]{%s}',
               r'\includegraphics[width=%.3f%s]{%s}',
               r'\includegraphics[height=%.3f%s]{%s}',
               r'\includegraphics[%s]{%s}']

    def __init__(self, txt):
        try:
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
            warn('Image Frame: PIL support not yet implemented, falling back to basic grid. Some images may be distorted.')
            return grid(dims, files, implicitFillWidth)

        shapes = {'|': vStrip,
                  '-': hStrip,
                  '+': grid,
                  '#': smartGrid}

        super(ImageEnv, self).__init__(shapes.get(shape, singleImage)(dims, files))


class PlusEnv(Text):

    def __init__(self, txt):
        # TODO
        warn('Plus integration not yet implemented')
        super(PlusEnv, self).__init__( 'Plus: ' + txt)


class TableEnv(Text):
    
    def __init__(self, txt):
        # TODO
        warn('Tables not yet implemented')
        super(TableEnv, self).__init__( 'Table: ' + txt )


class ScissorEnv(Text):

    includeCmd = r'{\setbeamercolor{background canvas}{bg=}\includepdf%s{%%s}}'
    pagesSpec = '[pages={%s}]'

    def __init__(self, txt):
        super(ScissorEnv, self).__init__(self._init_helper(txt.strip().split()) + '\n')

    def _init_helper(self, arr):
        if len(arr) == 0:
            warn('Skipping empty scissor command')
            return ''

        if not (os.path.isfile(arr[0]) or os.path.isfile(arr[0] + '.pdf')):
            # TODO Link to safety net
            # if .safe:
            #     warn('File included in scissor command not found, omitting')
            #     return ''
            # else:
            warn('File included in scissor command not found, proceeding unsafely...')

        if len(arr) > 1:
            if re.fullmatch(r'\d+(-\d+)?(,\d+(-\d+)?)*', arr[1]):
                cmd = self.includeCmd % self.pagesSpec
                return cmd % (arr[1], arr[0])
            else:
                warn('Ignoring malformed page range in scissor command')
            if len(arr) > 2:
                warn('Ignoring extraneous arguments in scissor command')

        cmd = self.includeCmd % ''
        return cmd % arr[0]


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
        self.insertCmd = Config.get('vbtmCmds', 'insertion')(lettr)
        self.head = head
        self.body = body
        super(VerbatimEnv, self).__init__(self.insertCmd)

    @classmethod
    def resolve(cls):
        if cls.count:

            # Ensure proper package name is given
            from beamr.interpreters import Config
            package = Config.getRaw('verbatim')
            packageList = Config.getRaw('vbtmCmds', 'packageNames')
            if package not in packageList:
                package = packageList[0]
                Config.effectiveConfig['verbatim'] = package
            Config.effectiveConfig['packages'].append(package)

            cls.preambleDefs = Config.getRaw('vbtmCmds', 'once', package) + '\n'

            for f in cls.todo:
                if f.head:
                    cls.preambleDefs += Config.getRaw('vbtmCmds', 'foreach', package) % (
                             f.insertCmd,
                             f.head,
                             f.body)
                else:
                    cls.preambleDefs += Config.getRaw('vbtmCmds', 'foreachNoLang', package) % (
                             f.insertCmd,
                             f.body)
