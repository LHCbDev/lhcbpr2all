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

from LbNightlyTools.Release import Poll

import os
import shutil
import codecs
import json

from tempfile import mkdtemp
from os.path import exists
from pprint import pprint

tmpd = None
oldcwd = None

def setup():
    global tmpd, oldcwd
    tmpd = mkdtemp()
    oldcwd = os.getcwd()
    os.chdir(tmpd)

def teardown():
    global tmpd, oldcwd
    os.chdir(oldcwd)
    shutil.rmtree(tmpd, ignore_errors=True)

def prepare_data(stacks):
    ''' helper function '''
    with codecs.open('data.json', 'w', 'utf-8') as output:
        json.dump(stacks, output)
    return stacks

def test_wrong_args():
    try:
        script = Poll()
        script.run([])
        assert False, 'Script should have exited'
    except SystemExit, x:
        assert x.code != 0

def test_simple_call():
    stacks = prepare_data([{'platforms': ['p1', 'p2'],
                            'projects': [['Proj1', 'v1'],
                                         ['Proj2', 'v2']],
                            'build_tool': 'CMAKE'}])

    script = Poll()
    retcode = script.run(['file:data.json'])
    assert retcode == 0

    assert exists(script.options.state_file)
    assert exists(script.options.output_param_file)

    params = dict(line.strip().split('=', 1)
                  for line in open(script.options.output_param_file))
    pprint(params)

    assert set(params) == set(['indexes', 'stacks'])
    assert params['indexes'].split() == ['0']

    assert json.loads(params['stacks']) == stacks

def test_no_input():
    prepare_data([])

    script = Poll()
    retcode = script.run(['file:data.json'])
    assert retcode == 0

    assert exists(script.options.state_file)
    assert not exists(script.options.output_param_file)

def test_sorting():
    prepare_data([{'platforms': ['p2', 'p1'],
                   'projects': [['ZZZ', 'v1'],
                                ['AAA', 'v2']],
                   'build_tool': 'CMT'},
                  {'platforms': ['f1', 'f2'],
                   'projects': [['P1', 'v1'],
                                ['P2', 'v2']],
                   'build_tool': 'CMAKE'}])
    expected = [{'platforms': ['f1', 'f2'],
                 'projects': [['P1', 'v1'],
                              ['P2', 'v2']],
                 'build_tool': 'CMAKE'},
                {'platforms': ['p1', 'p2'],
                 'projects': [['AAA', 'v2'],
                              ['ZZZ', 'v1']],
                 'build_tool': 'CMT'}]

    script = Poll()
    retcode = script.run(['file:data.json'])
    assert retcode == 0

    assert exists(script.options.state_file)
    with codecs.open(script.options.state_file, 'r', 'utf-8') as data:
        stacks = json.load(data)

    print 'expected:'
    pprint(expected)
    print 'stacks:'
    pprint(stacks)
    assert stacks == expected


def test_stability():
    prepare_data([{'platforms': ['p1', 'p2'],
                   'projects': [['Proj1', 'v1'],
                                ['Proj2', 'v2']]}])
    # first iteration
    script = Poll()
    retcode = script.run(['file:data.json'])
    assert retcode == 0

    assert exists(script.options.state_file)
    assert exists(script.options.output_param_file)

    params = dict(line.strip().split('=', 1)
                  for line in open(script.options.output_param_file))
    pprint(params)

    assert set(params) == set(['indexes', 'stacks'])
    assert params['indexes'].split() == ['0']

    # second iteration (no-op)
    script = Poll()
    retcode = script.run(['file:data.json'])
    assert retcode == 0

    assert exists(script.options.state_file)
    assert not exists(script.options.output_param_file)

    # third iteration (one extra stack)
    prepare_data([{'platforms': ['p1', 'p2'],
                   'projects': [['Proj1', 'v1'],
                                ['Proj2', 'v2']]},
                  {'platforms': ['p1', 'p2'],
                   'projects': [['Proj1', 'v3'],
                                ['Proj2', 'v4']]}])

    script = Poll()
    retcode = script.run(['file:data.json'])
    assert retcode == 0

    assert exists(script.options.state_file)
    assert exists(script.options.output_param_file)

    params = dict(line.strip().split('=', 1)
                  for line in open(script.options.output_param_file))
    pprint(params)

    assert set(params) == set(['indexes', 'stacks'])
    assert params['indexes'].split() == ['1']

    # fourth iteration (one stack less, nothing to build)
    prepare_data([{'platforms': ['p1', 'p2'],
                   'projects': [['Proj1', 'v3'],
                                ['Proj2', 'v4']]}])

    script = Poll()
    retcode = script.run(['file:data.json'])
    assert retcode == 0

    assert exists(script.options.state_file)
    assert not exists(script.options.output_param_file)
