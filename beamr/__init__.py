'''
Beamr - Minimal markup language for Beamer

Setup & usage content helpers

@author:     Teodor G Nistor

@copyright:  2018 Teodor G Nistor

@license:    MIT License
'''

cli_name = 'beamr'

setup_arg = {
    'name': 'Beamr',
    'version': '0.3.5',
    'description': 'Markup language for Beamer',
    'long_description': 'Beamr is a markup language (and interpreter thereof) for creating PDF slide shows from simple, easy to understand text files. It uses the full power of LaTeX and its Beamer document class.',
    'keywords': 'Beamer,LaTeX',
    'url': 'https://teonistor.github.io/beamr',
    'project_urls': {
        'Documentation': 'https://teonistor.github.io/beamr',
        'Source': 'https://github.com/teonistor/beamr/'},
    'author': 'Teodor G Nistor',
    'author_email': 'tn1g15@ecs.soton.ac.uk',
    'license': 'MIT',
    'classifiers': ['Programming Language :: Python', 'Development Status :: 4 - Beta'],
    'install_requires': ['ply>=3.11', 'pyaml>=17.12', 'docopt>=0.6'],
    'python_requires': '>2.6',
    'entry_points': {
        'console_scripts': [
            '%s=beamr.cli:main' % cli_name,
        ],
    }
}
