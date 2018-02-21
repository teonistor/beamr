'''
Created on 6 Feb 2018

@author: Teodor Gherasim Nistor

'''

from pybeams.lexers import imageLexer
from pybeams.parsers import imageParser
from pybeams.debug import debug, warn


class Text:
    
    def __init__(self, txt):
        self.txt = txt

    def __str__(self):
        return self.txt
    
    def __repr__(self):
        return self.__str__()


class Comment(Text):
    def __init__(self, txt):
        debug('Comment ', txt)
        super().__init__('% ' + txt)


class Escape(Text):
    def __init__(self, txt):
        super().__init__(txt[1:])


class Stretch(Text):

    cmds = {
        '<>': '\\centering\\noindent\\resizebox{0.9\\textwidth}{!}{%s}',
        '><': '\\begin{center}\n%s\n\\end{center}',
        '<<': '\\begin{flushleft}\n%s\n\\end{flushleft}',
        '>>': '\\begin{flushright}\n%s\n\\end{flushright}',
#         '^^': r'%s \vfill',
#         'vv': r'\vfill %s',
#         '^v': r'\vfill %s \vfill',
#         'v^': r'\vfill %s \vfill' # TODO tilted text?
    }
    defaultCmd = '%s'

    def __init__(self, txt):
        flags = txt[1] + txt[-2]
        txt = txt[2:-2]
        super().__init__(self.cmds.get(flags, self.defaultCmd) % txt)


class Emph(Text):
    def __init__(self, txt):
        # Eliminate asterisks and count how many they were
        self.emphLevel = 0
        while txt[0] == txt[-1] == '*':
            self.emphLevel += 1
            txt = txt[1:-1]

        # Anti-stupid
        if self.emphLevel > 4:
            warn("Something's wrong with emphasis level ", self.emphLevel, ', resetting to 4')
            self.emphLevel = 4

        super().__init__(txt)

    def __str__(self):
        from pybeams.interpreters.config import Config
        return Config.effectiveConfig['emph'][self.emphLevel] % super().__str__()


class Note(Text):
    def __init__(self, txt):
        super().__init__('Note '+txt) # TODO do this


class Url(Text):
    def __init__(self, txt):
        super().__init__(r'\url{' + txt + '}')


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
            
        super().__init__(Heading.formats[i] % txt[0])
        debug('Heading level', i, marker, txt[0])


class ImageEnv(Text):

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
            super().__init__('')
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
                s += '\\\\\n'
            return s

        def smartGrid(dims, files, implicitFillWidth=True):
            warn('Image Frame: PIL support not yet implemented, falling back to basic grid. Some images may be distorted.')
            return grid(dims, files, implicitFillWidth)

        shapes = {'|': vStrip,
                  '-': hStrip,
                  '+': grid,
                  '#': smartGrid}

        super().__init__(shapes.get(shape, singleImage)(dims, files))


class PlusEnv(Text):

    def __init__(self, txt):
        # TODO
        warn('Plus integration not yet implemented')
        super().__init__( 'Plus: ' + txt)


class TableEnv(Text):
    
    def __init__(self, txt):
        # TODO
        warn('Tables not yet implemented')
        super().__init__( 'Table: ' + txt )


class ScissorEnv(Text):

    def __init__(self, txt):
        # TODO
        warn('Document concatenation not yet implemented')
        super().__init__( '8< ' + txt)


class VerbatimEnv(Text):
    
    def __init__(self, txt):
        # TODO
        warn('Verbatim environment not yet implemented')
        super().__init__( '[Verbatim env omitted]')
