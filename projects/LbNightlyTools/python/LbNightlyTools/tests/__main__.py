#!/usr/bin/env python
###############################################################################
# (c) Copyright 2013 CERN                                                     #
#                                                                             #
# This software is distributed under the terms of the GNU General Public      #
# Licence version 3 (GPL Version 3), copied verbatim in the file "COPYING".   #
#                                                                             #
# In applying this licence, CERN does not waive the privileges and immunities #
# granted to it by virtue of its status as an Intergovernmental Organization  #
# or submit itself to any jurisdiction.                                       #
###############################################################################
'''
Wrapper script to run nosetests.
'''

def main():
    import os
    import sys
    from nose.core import main

    argv = ['nosetests', '-v', '--with-doctest', '--with-xunit']
    if not 'coverage' in sys.modules:
        # nosetests coverage conflicts with the PyDev one, so we enable it only
        # if the coverage is not yet in memory
        argv.extend(['--with-coverage', '--cover-erase', '--cover-inclusive',
                     '--cover-package', 'LbNightlyTools'])

    main(defaultTest=os.path.dirname(os.path.dirname(__file__)), argv=argv)

main()
