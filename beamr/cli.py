#!/usr/bin/env python3
# encoding: utf-8
'''
Beamr - Minimal markup language for Beamer

Command line interface module

@author:     Teodor G Nistor

@copyright:  2018 Teodor G Nistor

@license:    MIT License
'''
from __future__ import print_function
import sys
import os, re
import beamr.debug as debug
from beamr import setup_arg, cli_name
from docopt import docopt


_rOutFile = re.compile(r'(.*\/)?((?:[^/])+?)(?:\.(pdf|tex))?$')

def main():
    'Run command line interface'

    halp = '''%s - %s

    Usage:
        %s [-p|-n] [-s|-u] [-v|-q...] [-c <cfg>...] [--nomk] [--] [- | <input-file>] [<output-file>]
        %s (-h|-e [<editor> -d]) [-v]
        %s --version

    Options:
        -c <cfg>, --config=<cfg>    Override configuration. <cfg> can be Yaml code or a file name
        -e, --edit-config     Open user configuration file for editing. An editor must be specified if configuration doesn't exist or doesn't mention one
        -d, --dump-config     Open user configuration file as above, but first add the default config at the bottom of it (useful to see what is available for editing)
        -p, --pdf      Create PDF output file (default unless output filename has .tex extension)
        -n, --no-pdf   Don't create PDF output file (just generate LaTeX source)
        -s, --safe     Omit unverified external files (default unless overriden in config)
        -u, --unsafe   Trust unverified external files (useful when generating LaTeX code for elsewhere)
        -v, --verbose  Print inner workings of the lexer-parser-interpreter cycle and other debugging info to stderr
        -q, --quiet    Once: mute pdflatex/latexmk. Twice: also mute warnings. 3 times: mute everything
        --nomk     Don't attempt to call latexmk
        --help     Show this message and exit.
        --version  Print version information
''' % (setup_arg['name'], setup_arg['description'], cli_name, cli_name, cli_name)

    # Parse arguments nicely with docopt
    arg = docopt(halp, version='Beamr version ' + setup_arg['version'])

    # Set logging level
    if arg['--verbose']:
        debug.verbose = 1
    if arg['--quiet']:
        debug.quiet = arg['--quiet']

    # Docopt arguments themselves need debugging sometimes...
    debug.debug('args:', str(arg).replace('\n', ''))

    # If configuration editing mode, delegate to Config
    from beamr.interpreters.config import Config
    if arg['--edit-config']:
        return Config.editUserConfig(arg['<editor>'], arg['--dump-config'])

    # Establish names and what to run
    inFileName = arg['<input-file>']
    if inFileName:
        if not os.path.exists(inFileName):
            conceptualName = inFileName
            inFileName += '.bm'
        elif inFileName[-3:] == '.bm':
            conceptualName = inFileName[:-3]
        else:
            conceptualName = inFileName
    else:
        conceptualName = 'texput'

    outFileName = arg['<output-file>']
    if not outFileName:
        if arg['--no-pdf']:
            runThis = None
        else:
            runThis = Config.getRaw('pdfEngines', 'all')
        outFileName = conceptualName + '.tex'
    elif outFileName == '-':
        if arg['--pdf']:
            runThis = Config.getRaw('pdfEngines', 'all')
            outFileName = conceptualName + '.tex'
        else:
            outFileName = None
            runThis = None
    else:
        splitOut = _rOutFile.match(outFileName).groups()
        outFileName = (splitOut[0] or '') + splitOut[1] + '.tex'

        if arg['--no-pdf'] or splitOut[2] == 'tex' and not arg['--pdf']:
            runThis = None
        else:
            runThis = Config.getRaw('pdfEngines', 'all')
            
    if runThis:
        splitOut = _rOutFile.match(outFileName).groups()
        if splitOut[0]:
            runThis.append('-output-directory=' + splitOut[0])
        runThis.append(outFileName)


    # Open I/O files where relevant
    if inFileName:
        debug.infname = inFileName
        sys.stdin = open(inFileName, 'r')
    if outFileName:
        sys.stdout = open(outFileName, 'w')

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

            # Read and parse document
            doc = Document(sys.stdin.read())
            dic = {'s': str(doc)}
            ppc = '\n'.join(Config.getRaw('postProcess'))
            exec(ppc, dic)
            tex = dic['s']

            # Output LaTeX result
            print(tex)

    # Run latexmk/pdflatex as required
    if runThis != None:
        from subprocess import Popen, call, PIPE
        mute = {'stdout': PIPE, 'stderr': PIPE}

        # Further establish what to run
        if not arg['--nomk']:
            try:
                call(Config.getRaw('pdfEngines', 'test'), **mute)
                runThis = Config.getRaw('pdfEngines', 'latexmk') + runThis
            except:
                runThis = Config.getRaw('pdfEngines', 'pdflatex') + runThis
        else:
            runThis = Config.getRaw('pdfEngines', 'pdflatex') + runThis

        # And finally run it
        runkwarg = {'stdin': PIPE}
        if debug.quiet:
            runkwarg.update(mute)
        sp = Popen(runThis, **runkwarg)
        sp.stdin.close()
        rcode = sp.wait()

        if rcode:
            debug.err(runThis[0], 'exited with nonzero status', rcode)
            return rcode


if __name__ == "__main__":
    sys.exit(main())
