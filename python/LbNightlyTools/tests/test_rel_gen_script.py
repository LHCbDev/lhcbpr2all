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

from LbNightlyTools import Release

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
        s = Release.ConfigGenerator()
        s.run(['-o', tmpname])

        output = json.load(open(tmpname))
        pprint(output)

        assert output['slot'] == 'lhcb-release'
        assert output['projects'] == []
        assert output['USE_CMT'] is False
        assert output['no_patch'] is True
        assert len(output['default_platforms']) == 2

        assert output == s.genConfig()

    finally:
        os.remove(tmpname)

def test_options_error():
    try:
        s = Release.ConfigGenerator()
        s.run(['ProjA'])
        assert False, 'the script did not fail'
    except SystemExit:
        pass # expected behavior

def test_LHCb():
    tmpfd, tmpname = mkstemp()
    os.close(tmpfd)
    try:
        s = Release.ConfigGenerator()
        s.run(['-o', tmpname, 'LHCb', 'v36r1'])

        output = json.load(open(tmpname))
        pprint(output)

        assert output['slot'] == 'lhcb-release'
        assert output['projects'] == [{'name': 'LHCb', 'version': 'v36r1',
                                       'checkout_opts': {'export': True}}]
        assert output['USE_CMT'] is False
        assert output['no_patch'] is True

        assert output == s.genConfig()

    finally:
        os.remove(tmpname)

def test_Gaudi():
    tmpfd, tmpname = mkstemp()
    os.close(tmpfd)
    try:
        s = Release.ConfigGenerator()
        s.run(['-o', tmpname, 'Gaudi', 'v23r9'])

        output = json.load(open(tmpname))
        pprint(output)

        assert output['slot'] == 'lhcb-release'
        assert output['projects'] == [{'name': 'Gaudi', 'version': 'v23r9',
                                       'checkout': 'git',
                                       'checkout_opts': {'url': 'http://git.cern.ch/pub/gaudi',
                                                         'commit': 'GAUDI/GAUDI_v23r9',
                                                         'export': True}}]
        assert output['USE_CMT'] is False
        assert output['no_patch'] is True

        assert output == s.genConfig()

    finally:
        os.remove(tmpname)

def test_Geant4():
    tmpfd, tmpname = mkstemp()
    os.close(tmpfd)
    try:
        s = Release.ConfigGenerator()
        s.run(['-o', tmpname, 'Geant4', 'v95r2p7'])

        output = json.load(open(tmpname))
        pprint(output)

        assert output['slot'] == 'lhcb-release'
        assert output['projects'] == [{'name': 'Geant4', 'version': 'v95r2p7',
                                       'with_shared': True,
                                       'checkout_opts': {'export': True}}]
        assert output['USE_CMT'] is False
        assert output['no_patch'] is True

        assert output == s.genConfig()

    finally:
        os.remove(tmpname)

def test_Dirac():
    tmpfd, tmpname = mkstemp()
    os.close(tmpfd)
    try:
        s = Release.ConfigGenerator()
        s.run(['-o', tmpname, 'Dirac', 'v6r12p1'])

        output = json.load(open(tmpname))
        pprint(output)

        assert output['slot'] == 'lhcb-release'
        assert output['projects'] == [{'name': 'Dirac', 'version': 'v6r12p1',
                                       'checkout': 'dirac',
                                       'checkout_opts': {'export': True}}]
        assert output['USE_CMT'] is False
        assert output['no_patch'] is True

        assert output == s.genConfig()

    finally:
        os.remove(tmpname)

def test_LHCbGrid():
    tmpfd, tmpname = mkstemp()
    os.close(tmpfd)
    try:
        s = Release.ConfigGenerator()
        s.run(['-o', tmpname, 'LHCbGrid', 'v0r4'])

        output = json.load(open(tmpname))
        pprint(output)

        assert output['slot'] == 'lhcb-release'
        assert output['projects'] == [{'name': 'LHCbGrid', 'version': 'v0r4',
                                       'checkout': 'lhcbgrid',
                                       'checkout_opts': {'export': True}}]
        assert output['USE_CMT'] is False
        assert output['no_patch'] is True

        assert output == s.genConfig()

    finally:
        os.remove(tmpname)

def test_LHCbDirac():
    tmpfd, tmpname = mkstemp()
    os.close(tmpfd)
    try:
        s = Release.ConfigGenerator()
        s.run(['-o', tmpname, 'LHCbDirac', 'v7r6p24'])

        output = json.load(open(tmpname))
        pprint(output)

        assert output['slot'] == 'lhcb-release'
        assert output['projects'] == [{'name': 'LHCbDirac', 'version': 'v7r6p24',
                                       'checkout': 'lhcbdirac',
                                       'checkout_opts': {'export': True}}]
        assert output['USE_CMT'] is False
        assert output['no_patch'] is True

        assert output == s.genConfig()

    finally:
        os.remove(tmpname)

def test_two_projects():
    tmpfd, tmpname = mkstemp()
    os.close(tmpfd)
    try:
        s = Release.ConfigGenerator()
        s.run(['-o', tmpname, 'LHCb', 'v36r1', 'Lbcom', 'v14r1'])

        output = json.load(open(tmpname))
        pprint(output)

        assert output['slot'] == 'lhcb-release'
        assert output['projects'] == [{'name': 'LHCb', 'version': 'v36r1',
                                       'checkout_opts': {'export': True}},
                                      {'name': 'Lbcom', 'version': 'v14r1',
                                       'checkout_opts': {'export': True}}]
        assert output['USE_CMT'] is False
        assert output['no_patch'] is True

        assert output == s.genConfig()

    finally:
        os.remove(tmpname)

def test_fixCase():
    tmpfd, tmpname = mkstemp()
    os.close(tmpfd)
    try:
        s = Release.ConfigGenerator()
        s.run(['-o', tmpname, 'lhcb', 'v36r1', 'dAvinCi', 'v34r0'])

        output = json.load(open(tmpname))
        pprint(output)

        assert output['slot'] == 'lhcb-release'
        assert output['projects'] == [{'name': 'LHCb', 'version': 'v36r1',
                                       'checkout_opts': {'export': True}},
                                      {'name': 'DaVinci', 'version': 'v34r0',
                                       'checkout_opts': {'export': True}}]
        assert output['USE_CMT'] is False
        assert output['no_patch'] is True

        assert output == s.genConfig()

    finally:
        os.remove(tmpname)

def test_dup_projects():
    try:
        s = Release.ConfigGenerator()
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

        s = Release.ConfigGenerator()
        s.run(['-o', '-', 'LHCb', 'v36r1'])

        output = json.loads(sys.stdout.getvalue())
        sys.stdout = old_stdout

        pprint(output)

        assert output['slot'] == 'lhcb-release'
        assert output['projects'] == [{'name': 'LHCb', 'version': 'v36r1',
                                       'checkout_opts': {'export': True}}]
        assert output['USE_CMT'] is False
        assert output['no_patch'] is True

        assert output == s.genConfig()

    finally:
        os.remove(tmpname)

def test_with_cmt():
    tmpfd, tmpname = mkstemp()
    os.close(tmpfd)
    try:
        s = Release.ConfigGenerator()
        s.run(['--cmt', '-o', tmpname, 'LHCb', 'v36r1'])

        output = json.load(open(tmpname))
        pprint(output)

        assert output['slot'] == 'lhcb-release'
        assert output['projects'] == [{'name': 'LHCb', 'version': 'v36r1',
                                       'checkout_opts': {'export': True}}]
        assert output['USE_CMT'] is True
        assert output['no_patch'] is True

        assert output == s.genConfig()

    finally:
        os.remove(tmpname)

def test_with_build_tool_cmt():
    tmpfd, tmpname = mkstemp()
    os.close(tmpfd)
    try:
        s = Release.ConfigGenerator()
        s.run(['--build-tool', 'cmt', '-o', tmpname, 'LHCb', 'v36r1'])

        output = json.load(open(tmpname))
        pprint(output)

        assert output['slot'] == 'lhcb-release'
        assert output['projects'] == [{'name': 'LHCb', 'version': 'v36r1',
                                       'checkout_opts': {'export': True}}]
        assert output['USE_CMT'] is True
        assert output['no_patch'] is True

        assert output == s.genConfig()

    finally:
        os.remove(tmpname)

def test_platforms():
    tmpfd, tmpname = mkstemp()
    os.close(tmpfd)
    try:
        s = Release.ConfigGenerator()
        s.run(['--platforms',
               ' x86_64-slc6-gcc48-opt x86_64-slc6-gcc48-dbg,'
               'x86_64-slc6-gcc48-test',
               '-o', tmpname])

        output = json.load(open(tmpname))
        pprint(output)

        assert output['slot'] == 'lhcb-release'
        assert output['no_patch'] is True
        assert output['default_platforms'] == ['x86_64-slc6-gcc48-opt',
                                               'x86_64-slc6-gcc48-dbg',
                                               'x86_64-slc6-gcc48-test']

        assert output == s.genConfig()

    finally:
        os.remove(tmpname)

def test_packages():
    tmpfd, tmpname = mkstemp()
    os.close(tmpfd)
    try:
        s = Release.ConfigGenerator()
        s.run(['--packages',
               '',
               '-o', tmpname])

        output = json.load(open(tmpname))
        pprint(output)

        assert output['slot'] == 'lhcb-release'
        assert output['no_patch'] is True
        assert output['packages'] == []

        assert output == s.genConfig()


        s = Release.ConfigGenerator()
        s.run(['--packages',
               'MyPack v1r0',
               '-o', tmpname])

        output = json.load(open(tmpname))
        pprint(output)

        assert output['slot'] == 'lhcb-release'
        assert output['no_patch'] is True
        assert output['packages'] == [{'name': 'MyPack', 'version': 'v1r0',
                                       'checkout_opts': {'export': True}}]

        assert output == s.genConfig()


        s = Release.ConfigGenerator()
        s.run(['--packages',
               'MyPack v1r0 Some/OtherPack v9r99',
               '-o', tmpname])

        output = json.load(open(tmpname))
        pprint(output)

        assert output['slot'] == 'lhcb-release'
        assert output['no_patch'] is True
        assert output['packages'] == [{'name': 'MyPack', 'version': 'v1r0',
                                       'checkout_opts': {'export': True}},
                                      {'name': 'Some/OtherPack', 'version': 'v9r99',
                                       'checkout_opts': {'export': True}}]

        assert output == s.genConfig()


        s = Release.ConfigGenerator()
        s.run(['--packages',
               'MyPack v1r0 MyPack v2r3 MyPack v1r0 ',
               '-o', tmpname])

        output = json.load(open(tmpname))
        pprint(output)

        assert output['slot'] == 'lhcb-release'
        assert output['no_patch'] is True
        assert output['packages'] == [{'name': 'MyPack', 'version': 'v1r0',
                                       'checkout_opts': {'export': True}},
                                      {'name': 'MyPack', 'version': 'v2r3',
                                       'checkout_opts': {'export': True}}]

        assert output == s.genConfig()


        s = Release.ConfigGenerator()
        s.run(['--packages',
               'DBASE:MyPack v1r0 PARAM:AnotherPack v2r3',
               '-o', tmpname])

        output = json.load(open(tmpname))
        pprint(output)

        assert output['slot'] == 'lhcb-release'
        assert output['no_patch'] is True
        assert output['packages'] == [{'name': 'MyPack', 'version': 'v1r0',
                                       'container': 'DBASE',
                                       'checkout_opts': {'export': True}},
                                      {'name': 'AnotherPack', 'version': 'v2r3',
                                       'container': 'PARAM',
                                       'checkout_opts': {'export': True}}]

        assert output == s.genConfig()

    finally:
        os.remove(tmpname)
