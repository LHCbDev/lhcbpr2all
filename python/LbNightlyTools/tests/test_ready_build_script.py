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

from LbNightlyTools import CheckReadyBuilds
from LbNightlyTools.Utils import JobParams

import os
import re
import json
import time

from subprocess import call
from os.path import normpath, join, exists
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

def test_no_data():
    with TemporaryDir(chdir=True):
        CheckReadyBuilds.main('data', 'test-{0}.txt')
        assert exists(join('data.json'))
        assert json.load(open('data.json')) == []
        assert len([x for x in os.listdir('.') if re.match(r'^test-[0-9]+\.txt', x)]) == 0

def test_no_ready():
    now = time.time()
    conf_data = [['filename', 'slot', 1,
                  'test-project', 'my-platform', now, 'this-os']]
    with TemporaryDir(chdir=True):
        with open('data.json', 'w') as cfg:
            cfg.write(json.dumps(conf_data))
        CheckReadyBuilds.DATA_DIR = '.'
        CheckReadyBuilds.main('data', 'test-{0}.txt')
        assert exists(join('data.json'))
        assert json.load(open('data.json')) == conf_data
        assert len([x for x in os.listdir('.') if re.match(r'^test-[0-9]+\.txt', x)]) == 0

def test_invalid_time():
    now = time.time() + 1000
    conf_data = [['filename', 'slot', 1,
                  'test-project', 'my-platform', now, 'this-os']]
    with TemporaryDir(chdir=True):
        with open('data.json', 'w') as cfg:
            cfg.write(json.dumps(conf_data))
        with open('filename1', 'w') as f:
            f.write('')
        CheckReadyBuilds.DATA_DIR = '.'
        CheckReadyBuilds.main('data', 'test-{0}.txt')
        assert exists(join('data.json'))
        assert json.load(open('data.json')) == conf_data
        assert len([x for x in os.listdir('.') if re.match(r'^test-[0-9]+\.txt', x)]) == 0

def test_one_ready():
    now = time.time() - 1000
    conf_data = [['filename1', 'slot', 1,
                  'test-project', 'my-platform', now, 'this-os'],
                 ['filename2', 'slotX', 2,
                  'other-project', 'new-platform', now, 'next-os']]
    with TemporaryDir(chdir=True):
        with open('data.json', 'w') as cfg:
            cfg.write(json.dumps(conf_data))
        with open('filename2', 'w') as f:
            f.write('')
        CheckReadyBuilds.DATA_DIR = '.'
        CheckReadyBuilds.main('data', 'test-{0}.txt')
        assert exists(join('data.json'))
        assert json.load(open('data.json')) == conf_data[:1]
        assert len([x for x in os.listdir('.') if re.match(r'^test-[0-9]+\.txt', x)]) == 1
        assert exists(join('test-0.txt'))
        slot, build_id, project, platform = conf_data[1][1:-2]
        os_label = conf_data[1][-1]
        expected_params = JobParams(slot=slot,
                                    slot_build_id=build_id,
                                    project=project,
                                    platform=platform,
                                    os_label=os_label)
        print '------- test-0.txt -------'
        import sys
        sys.stdout.writelines(open('test-0.txt'))
        print '--------------------------'
        print '-------  expected  -------'
        print expected_params
        print '--------------------------'

        assert open('test-0.txt').read() == (str(expected_params) + '\n')

def _test_only_projects_conf():
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
