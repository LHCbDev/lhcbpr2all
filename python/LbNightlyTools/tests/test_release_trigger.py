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

from LbNightlyTools.Release import Trigger

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
    with codecs.open('stacks.json', 'w', 'utf-8') as output:
        json.dump(stacks, output)
    return stacks

def test_wrong_args_1():
    try:
        script = Trigger()
        script.run([])
        assert False, 'Script should have exited'
    except SystemExit, x:
        assert x.code != 0

def test_wrong_args_2():
    try:
        script = Trigger()
        script.run(['stacks.json'])
        assert False, 'Script should have exited'
    except SystemExit, x:
        assert x.code != 0

def test_wrong_args_3():
    try:
        script = Trigger()
        script.run(['stacks.json', 'abc'])
        assert False, 'Script should have exited'
    except SystemExit, x:
        assert x.code != 0

def test_wrong_args_4():
    script = Trigger()
    retcode = script.run(['stacks.json', '0'])
    assert retcode != 0

def test_wrong_args_5():
    prepare_data([{'platforms': ['p1', 'p2'],
                   'projects': [['Proj1', 'v1'],
                                ['Proj2', 'v2']]}])
    try:
        script = Trigger()
        script.run(['stacks.json', '1234'])
        assert False, 'Script should have exited'
    except SystemExit, x:
        assert x.code != 0
    except IndexError:
        pass

def test_simple_call():
    try:
        stacks = prepare_data([{'platforms': ['p1', 'p2'],
                                'projects': [['Proj1', 'v1'],
                                             ['Proj2', 'v2']],
                                'build_tool': 'CMake'}])

        script = Trigger()
        retcode = script.run(['stacks.json', '0'])
    except IndexError:
        pass
        assert retcode == 0

    assert exists(script.options.output_param_file)

    params = dict(line.strip().split('=', 1)
                  for line in open(script.options.output_param_file))
    pprint(params)

    assert set(params) == set(['platforms', 'projects_list', 'build_tool'])
    assert params['platforms'].split() == stacks[0]['platforms']
    assert params['projects_list'].split() == ['Proj1', 'v1', 'Proj2', 'v2']
    assert params['build_tool'].lower() == stacks[0]['build_tool'].lower()

def test_simple_with_cmt():
    try:
        stacks = prepare_data([{'platforms': ['p1', 'p2'],
                                'projects': [['Proj1', 'v1'],
                                             ['Proj2', 'v2']],
                                'build_tool': 'cmt'}])

        script = Trigger()
        retcode = script.run(['stacks.json', '0'])
    except IndexError:
        pass
        assert retcode == 0

    assert exists(script.options.output_param_file)

    params = dict(line.strip().split('=', 1)
                  for line in open(script.options.output_param_file))
    pprint(params)

    assert set(params) == set(['platforms', 'projects_list', 'build_tool'])
    assert params['platforms'].split() == stacks[0]['platforms']
    assert params['projects_list'].split() == ['Proj1', 'v1', 'Proj2', 'v2']
    assert params['build_tool'].lower() == stacks[0]['build_tool'].lower()

def test_simple_no_build_tool():
    try:
        stacks = prepare_data([{'platforms': ['p1', 'p2'],
                                'projects': [['Proj1', 'v1'],
                                             ['Proj2', 'v2']]}])

        script = Trigger()
        retcode = script.run(['stacks.json', '0'])
    except IndexError:
        pass
        assert retcode == 0

    assert exists(script.options.output_param_file)

    params = dict(line.strip().split('=', 1)
                  for line in open(script.options.output_param_file))
    pprint(params)

    assert set(params) == set(['platforms', 'projects_list', 'build_tool'])
    assert params['platforms'].split() == stacks[0]['platforms']
    assert params['projects_list'].split() == ['Proj1', 'v1', 'Proj2', 'v2']
    assert params['build_tool'].lower() == 'cmt'

def test_bad_stack():
    prepare_data([{'projects': [['Proj1', 'v1'],
                                ['Proj2', 'v2']]}])

    script = Trigger()
    retcode = script.run(['stacks.json', '0'])
    assert retcode != 0
    assert not exists(script.options.output_param_file)
