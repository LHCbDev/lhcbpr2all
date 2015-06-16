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

from LbNightlyTools import StackCheckout

import os
import shutil
import re
import json

from subprocess import call
from tempfile import mkdtemp
from os.path import normpath, join, isfile
from LbNightlyTools.Utils import ensureDirs
from LbNightlyTools.tests.utils import TemporaryDir

_testdata = normpath(join(*([__file__] + [os.pardir] * 4 + ['testdata'])))

_env_bk = dict(os.environ)

def setup():
    global _env_bk
    _env_bk = dict(os.environ)

def teardown():
    global _env_bk
    os.environ.clear()
    os.environ.update(_env_bk)

def test_noop_patch():
    tmpd = mkdtemp()
    oldcwd = os.getcwd()
    try:
        os.chdir(tmpd)

        build_dir = join(tmpd, 'checkout')
        ensureDirs([build_dir])

        call(['tar', '-x',
              '-f', join(_testdata, 'artifacts',
                         'TestProject.HEAD.testing-slot.src.tar.bz2'),
              '-C', build_dir])

        configfile = join(_testdata, 'testing-slot.json')
        slot = StackCheckout.parseConfigFile(configfile)

        slot.patch(build_dir, 'slot.patch')

        assert isfile(join(build_dir, 'slot.patch'))
        assert not open(join(build_dir, 'slot.patch')).read().strip(), 'patch file not empty'

        reqfile = join('checkout', 'TESTPROJECT', 'TESTPROJECT_HEAD',
                       'TestProjectSys', 'cmt', 'requirements')
        assert isfile(reqfile)

    finally:
        os.chdir(oldcwd)
        shutil.rmtree(tmpd, ignore_errors=True)

def test_lbcore_192():
    '''https://its.cern.ch/jira/browse/LBCORE-192

    The *Sys package of a project is not correctly updated when new packages are
    added.
    '''
    tmpd = mkdtemp()
    oldcwd = os.getcwd()
    try:
        os.chdir(tmpd)

        build_dir = join(tmpd, 'checkout')
        ensureDirs([build_dir])

        call(['tar', '-x',
              '-f', join(_testdata, 'artifacts',
                         'TestProject.HEAD.testing-slot.src.tar.bz2'),
              '-C', build_dir])

        configfile = join(_testdata, 'testing-slot-lbcore-192.json')
        slot = StackCheckout.parseConfigFile(configfile)

        slot.patch(build_dir, 'slot.patch')

        assert isfile(join(build_dir, 'slot.patch'))

        reqfile = join('checkout', 'TESTPROJECT', 'TESTPROJECT_HEAD',
                       'TestProjectSys', 'cmt', 'requirements')
        assert isfile(reqfile)

        #print open(reqfile).read()
        assert [l for l in open(reqfile)
                if re.match(r'^\s*use\s+NewPack\s+\*\s*$', l)], 'NewPack not in requirements'

    finally:
        os.chdir(oldcwd)
        shutil.rmtree(tmpd, ignore_errors=True)

def test_empty_conf():
    with TemporaryDir(chdir=True):
        with open('test.json', 'w') as cfg:
            cfg.write('{}')
        retval = StackCheckout.Script().run(['test.json'])
        assert retval == 0

def test_only_projects_conf():
    with TemporaryDir(chdir=True):
        with open('test.json', 'w') as cfg:
            conf_data = {'projects': [{'name': 'Gaudi',
                                       'version': 'HEAD',
                                       'checkout': 'git',
                                       'checkout_opts':
                                        {'url': 'https://gitlab.cern.ch/gaudi/Gaudi.git'}}
                                      ]}
            cfg.write(json.dumps(conf_data))
        retval = StackCheckout.Script().run(['test.json'])
        assert retval == 0

def test_only_packages_conf():
    with TemporaryDir(chdir=True):
        with open('test.json', 'w') as cfg:
            conf_data = {'packages': [{'name': 'WG/CharmConfig',
                                       'version': 'head'}]}
            cfg.write(json.dumps(conf_data))
        retval = StackCheckout.Script().run(['test.json'])
        assert retval == 0

def test_lbcore_664():
    '''https://its.cern.ch/jira/browse/LBCORE-664
    '''
    configfile = join(_testdata, 'testing-slot-lbcore-664.json')
    with TemporaryDir(chdir=True):
        StackCheckout.Script().run(['--ignore-checkout-errors',
                                    configfile])
    with TemporaryDir(chdir=True):
        StackCheckout.Script().run([configfile])

    with TemporaryDir(chdir=True):
        try:
            StackCheckout.Script().run(['--no-ignore-checkout-errors', configfile])
            assert False, 'the script should have failed'
        except:
            pass
