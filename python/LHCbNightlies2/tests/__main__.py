#!/usr/bin/env python
import os
from nose.core import main
main(defaultTest=os.path.dirname(os.path.dirname(__file__)),
     argv=['nosetests', '-v', '--with-doctest',
           '--with-coverage', '--cover-erase', '--cover-inclusive',
           '--cover-package', 'LHCbNightlies2'])
