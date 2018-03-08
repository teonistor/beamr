#!/usr/bin/env python3
# encoding: utf-8
'''
Beamr

@author:     Teodor Gherasim Nistor

@copyright:  2018 Teodor Gherasim Nistor

@license:    MIT License
'''
from __future__ import print_function
import sys
import beamr.debug as debug
from beamr import setup_arg, cli_name
from docopt import docopt


def main():
    halp = '''%s - %s

    Usage:
        %s [-n|-p <cmd>] [-q|-v] [-u|-s] [-c <cfg>] [--] [- | <input-file>] [- | <output-file>]
        %s (-h|-e [<editor>]) [-v]
        %s --version

    Options:
        -p <cmd>, --pdflatex=<cmd>  Specify pdflatex executable name and/or path to [default: pdflatex]
        -c <cfg>, --config=<cfg>    Override configuration. <cfg> must be valid Yaml
        -e, --edit-config     Open user configuration file for editing. An editor must be specified if configuration doesn't exist or doesn't mention one
        -n, --no-pdf   Don't create PDF output file (just generate Latex source)
        -u, --unsafe   Trust certain user input which cannot be verified
        -s, --safe     Don't trust user input which cannot be verified
        -v, --verbose  Print inner workings of the lexer-parser-interpreter cycle to stderr
        -q, --quiet    Print nothing except errors to stderr. If using Python >=3.6 this will also mute output from pdflatex
        -h, --help     Show this message and exit.
        --version      Print version information
''' % (setup_arg['name'], setup_arg['description'], cli_name, cli_name, cli_name)

    # Parse arguments nicely with docopt
    arg = docopt(halp,  version=setup_arg['version'])

    # Set logging level
    if arg['--verbose']:
        debug.verbose = True
    if arg['--quiet']:
        debug.quiet = True

    # Docopt arguments themselves need debugging sometimes...
    debug.debug('args:', str(arg).replace('\n', ''))

    # If configuration editing mode, delegate to Config
    from beamr.interpreters.config import Config
    if arg['--edit-config']:
        return Config.editUserConfig(arg['<editor>'])

    # Establish pdflatex command and parameters if required
    pdflatex = None
    if not arg['--no-pdf']:
        pdflatex = [arg['--pdflatex'], '-shell-escape']
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

    # Decode other configuration
    cmdlineSpecial = {}
    if arg['--safe']:
        cmdlineSpecial['safe'] = True
    elif arg['--unsafe']:
        cmdlineSpecial['safe'] = False
    Config.fromCmdline(arg['--config'], **cmdlineSpecial)

    # Only after setting logging level import our interpreters
    from beamr.interpreters import Document

    with sys.stdin:
        with sys.stdout:

            # Parse document
            doc = Document(sys.stdin.read())
            tex = str(doc)

            # Run pdflatex on obtained tex source
            if pdflatex:
                from subprocess import Popen, PIPE

                runkwarg = {'stdin': PIPE} # TODO Investigate encoding gotchas
                if debug.quiet:
                        runkwarg.update({'stdout': PIPE, 'stderr': PIPE})

                sp = Popen(pdflatex, **runkwarg)

                try: # Python 3
                    sp.communicate(bytes(tex, encoding='utf-8'))
                except: # Python 2
                    sp.communicate(bytes(tex))

                sp.stdin.close()
                rcode = sp.wait()

                if rcode:
                    debug.err('Fatal: pdflatex exited with nonzero status', rcode)
                    return rcode

            # Just output tex source
            else:
                print(tex)


if __name__ == "__main__":
    sys.exit(main())
