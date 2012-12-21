#!/usr/bin/env python
import os
import sys
from nose.core import main

argv = ['nosetests', '-v', '--with-doctest']
if not 'coverage' in sys.modules:
    # nosetests coverage conflicts with the PyDev one, so we enable it only
    # if the coverage is not yet in memory
    argv.extend(['--with-coverage', '--cover-erase', '--cover-inclusive',
                 '--cover-package', 'LHCbNightlies2'])

main(defaultTest=os.path.dirname(os.path.dirname(__file__)), argv=argv)
