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

# Uncomment to disable the tests.
#__test__ = False

from LbNightlyTools import ReleaseConfigGenerator

import os
import json

from pprint import pprint
from tempfile import mkstemp

_env_bk = dict(os.environ)

def setup():
    global _env_bk
    _env_bk = dict(os.environ)

def teardown():
    global _env_bk
    os.environ.clear()
    os.environ.update(_env_bk)

def test_empty_config():
    tmpfd, tmpname = mkstemp()
    os.close(tmpfd)
    try:
        s = ReleaseConfigGenerator.Script()
        s.run(['-o', tmpname])

        output = json.load(open(tmpname))
        pprint(output)

        assert output['slot'] == 'lhcb-release'
        assert output['projects'] == []
        assert output['USE_CMT'] is False
        assert output['no_patch'] is True
        assert len(output['default_platforms']) == 6

        assert output == s.genConfig()

    finally:
        os.remove(tmpname)

def test_options_error():
    try:
        s = ReleaseConfigGenerator.Script()
        s.run(['ProjA'])
        assert False, 'the script did not fail'
    except SystemExit:
        pass # expected behavior

def test_LHCb():
    tmpfd, tmpname = mkstemp()
    os.close(tmpfd)
    try:
        s = ReleaseConfigGenerator.Script()
        s.run(['-o', tmpname, 'LHCb', 'v36r1'])

        output = json.load(open(tmpname))
        pprint(output)

        assert output['slot'] == 'lhcb-release'
        assert output['projects'] == [{'name': 'LHCb', 'version': 'v36r1'}]
        assert output['USE_CMT'] is False
        assert output['no_patch'] is True

        assert output == s.genConfig()

    finally:
        os.remove(tmpname)

def test_Gaudi():
    tmpfd, tmpname = mkstemp()
    os.close(tmpfd)
    try:
        s = ReleaseConfigGenerator.Script()
        s.run(['-o', tmpname, 'Gaudi', 'v23r9'])

        output = json.load(open(tmpname))
        pprint(output)

        assert output['slot'] == 'lhcb-release'
        assert output['projects'] == [{'name': 'Gaudi', 'version': 'v23r9',
                                       'checkout': 'git',
                                       'checkout_opts': {'url': 'http://git.cern.ch/pub/gaudi',
                                                         'commit': 'GAUDI/GAUDI_v23r9'}}]
        assert output['USE_CMT'] is False
        assert output['no_patch'] is True

        assert output == s.genConfig()

    finally:
        os.remove(tmpname)

def test_two_projects():
    tmpfd, tmpname = mkstemp()
    os.close(tmpfd)
    try:
        s = ReleaseConfigGenerator.Script()
        s.run(['-o', tmpname, 'LHCb', 'v36r1', 'Lbcom', 'v14r1'])

        output = json.load(open(tmpname))
        pprint(output)

        assert output['slot'] == 'lhcb-release'
        assert output['projects'] == [{'name': 'LHCb', 'version': 'v36r1'},
                                      {'name': 'Lbcom', 'version': 'v14r1',
                                       'dependencies': ['LHCb']}]
        assert output['USE_CMT'] is False
        assert output['no_patch'] is True

        assert output == s.genConfig()

    finally:
        os.remove(tmpname)

def test_dup_projects():
    try:
        s = ReleaseConfigGenerator.Script()
        s.run(['LHCb', 'v36r1', 'LHCb', 'v36r2'])
        assert False, 'the script did not fail'
    except SystemExit:
        pass # expected behavior

def test_stdout():
    tmpfd, tmpname = mkstemp()
    os.close(tmpfd)
    try:
        import sys
        from StringIO import StringIO
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        s = ReleaseConfigGenerator.Script()
        s.run(['-o', '-', 'LHCb', 'v36r1'])

        output = json.loads(sys.stdout.getvalue())
        sys.stdout = old_stdout

        pprint(output)

        assert output['slot'] == 'lhcb-release'
        assert output['projects'] == [{'name': 'LHCb', 'version': 'v36r1'}]
        assert output['USE_CMT'] is False
        assert output['no_patch'] is True

        assert output == s.genConfig()

    finally:
        os.remove(tmpname)

def test_with_cmt():
    tmpfd, tmpname = mkstemp()
    os.close(tmpfd)
    try:
        s = ReleaseConfigGenerator.Script()
        s.run(['--cmt', '-o', tmpname, 'LHCb', 'v36r1'])

        output = json.load(open(tmpname))
        pprint(output)

        assert output['slot'] == 'lhcb-release'
        assert output['projects'] == [{'name': 'LHCb', 'version': 'v36r1'}]
        assert output['USE_CMT'] is True
        assert output['no_patch'] is True

        assert output == s.genConfig()

    finally:
        os.remove(tmpname)

