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
import os
from os.path import normpath, join

# Uncomment to disable the tests.
#__test__ = False

from LbNightlyTools.Scripts import Install
from tempfile import mkdtemp
import shutil

_testdata = normpath(join(*([__file__] + [os.pardir] * 4 + ['testdata'])))

def test_fixGlimpseIndexes():
    'Install.fixGlimpseIndexes()'
    tmpd = mkdtemp()
    src = join(_testdata, 'fix_glimpse')
    dst = join(tmpd, 'fix_glimpse')
    shutil.copytree(src, dst)

    untouched = set([join(dst, 'untouched', '.glimpse_filenames')])

    # FIXME: this is equivalent to the code in the script, but we should test
    #        the real code
    Install.fixGlimpseIndexes(f for f in Install.findGlimpseFilenames(dst)
                                  if f not in untouched)


    expected = '''4
{0}/file1
{0}/path/file2
{0}/other/path/file3
/this/is/absolute
'''.format(join(dst, 'level1'))

    found = open(join(dst, 'level1', '.glimpse_filenames')).read()
    #print 'level1'
    #print found
    #print expected
    assert found == expected


    expected = '''2
file1
path/file2
'''

    found = open(join(dst, 'level1', 'level2', '.glimpse_filenames')).read()
    #print 'level1/level2'
    #print found
    assert found == expected


    expected = '''1\n{0}/another\n'''.format(join(dst, 'levelA', 'levelB'))

    found = open(join(dst, 'levelA', 'levelB', '.glimpse_filenames')).read()
    #print 'levelA/levelB'
    #print found
    assert found == expected

    expected = '''1
untouched
'''

    found = open(join(dst, 'untouched', '.glimpse_filenames')).read()
    #print 'untouched'
    #print found
    assert found == expected

    # ignored directories
    found = open(join(dst, 'docs', '.glimpse_filenames')).read()
    #print 'untouched'
    #print found
    assert found == expected
