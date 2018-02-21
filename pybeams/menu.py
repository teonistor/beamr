#!/usr/bin/env python3
# encoding: utf-8
'''
PyBeams - An unfinished program for easily creating LaTeX-powered slide shows.

@author:     Teodor Gherasim Nistor

@copyright:  2018 Teodor Gherasim Nistor

@license:    MIT License
'''

import sys
import pybeams.debug as debug
from docopt import docopt
from subprocess import run, PIPE

def main():
    '''PyBeams - An unfinished program for easily creating LaTeX-powered slide shows.

    Usage:
        pybeams [-n|-p <cmd>] [-q|-v] [--] [- | <input-file>] [- | <output-file>]
        pybeams (-h|--help)
        pybeams --version

    Options:
        -p <cmd>, --pdflatex=<cmd>  Specify pdflatex executable name and/or path to [default: pdflatex]
        -n, --no-pdf   Don't create PDF output file (just generate Latex source)
        -v, --verbose  Print inner workings of the lexer-parser-interpreter cycle to stderr
        -q, --quiet    Print nothing except fatal errors to stderr
        -h, --help     Show this message and exit.
        --version      Print version information
'''

    # Parse arguments nicely with docopt
    arg = docopt(main.__doc__,  version='0.0.1')

    # Set logging level
    if arg['--verbose']:
        debug.verbose = True
    if arg['--quiet']:
        debug.quiet = True

    # Docopt arguments themselves need debugging sometimes...
    debug.debug('args:', str(arg).replace('\n', ''))

    # Establish pdflatex command and parameters if required
    pdflatex = None
    if not arg['--no-pdf']:
        pdflatex = [arg['--pdflatex']]
        if arg['<output-file>']:
            outFile = arg['<output-file>']
            arg['<output-file>'] = None
            i = outFile.rfind('/') + 1
            if (i > 0):
                pdflatex.append('-output-directory=' + outFile[:i])
            pdflatex.append('-jobname=' + outFile[i:])


    # Open I/O files where relevant
    if arg['<input-file>']:
        sys.stdin = open(arg['<input-file>'], 'r')
    if arg['<output-file>']:
        sys.stdout = open(arg['<output-file>'], 'w')

    # Only after setting logging level import our interpreters
    from pybeams.interpreters import Document

    with sys.stdin:
        with sys.stdout:

            # Parse document
            doc = Document(sys.stdin.read())
            tex = str(doc)

            # Run pdflatex on obtained tex source
            if pdflatex:
                runkwarg = {'input': tex, 'encoding': 'utf-8'} # TODO Investigate encoding gotchas

                # If quiet mode enabled, pipe output of pdflatex to this process, where it can be ignored
                if debug.quiet:
                    runkwarg.update({'stdout': PIPE, 'stderr': PIPE})
                
                sp = run(pdflatex, **runkwarg)
                if sp.returncode:
                    debug.err('Fatal: pdflatex exited with nonzero status', sp.returncode)
                    return sp.returncode

            # Just output tex source
            else:
                print(tex)


if __name__ == "__main__":
    sys.exit(main())
