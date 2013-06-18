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

# Uncomment to disable the tests.
#__test__ = False

from LbNightlyTools import BuildSlot
from tempfile import mkdtemp
import shutil

from datetime import date
from os.path import exists, normpath, join, dirname, isfile
from LbNightlyTools.Utils import ensureDirs

_testdata = normpath(join(*([__file__] + [os.pardir] * 4 + ['testdata'])))

_env_bk = dict(os.environ)

def setup():
    global _env_bk
    _env_bk = dict(os.environ)

def teardown():
    global _env_bk
    os.environ.clear()
    os.environ.update(_env_bk)

def test_inconsistent_options():
    try:
        script = BuildSlot.Script()
        script.run(['--tests-only', '--coverity'])
        assert False, 'Script should have exited'
    except SystemExit, x:
        assert x.code != 0
        pass

def test_missing_args():
    try:
        script = BuildSlot.Script()
        script.run()
        assert False, 'Script should have exited'
    except SystemExit, x:
        assert x.code != 0
        pass

def assert_files_exist(root, *files):
    '''
    Assert that each specified filename, relative to the root directory, exists.
    '''
    for filename in files:
        filename = join(root, filename)
        assert exists(filename), 'missing expected file %s' % filename

def _check_build_artifacts(root, info):
    artifacts_dir = join(root, 'artifacts')
    assert_files_exist(artifacts_dir,
                       'Project.xml',
                       *[f.format(**info)
                         for f in ['{project}.{version}.{slot}.{today}.{config}.tar.bz2',
                                   'summaries.{config}/{project}/build_log.html',
                                   'db/{slot}.{build_id}.{config}.job-start.json',
                                   'db/{slot}.{build_id}.{config}.job-end.json',
                                   'db/{slot}.{build_id}.{project}.{config}.build-result.json',
                                   ]]
                       )

def _check_test_artifacts(root, info):
    artifacts_dir = join(root, 'artifacts')
    assert_files_exist(artifacts_dir,
                       'Project.xml',
                       *[f.format(**info)
                         for f in ['summaries.{config}/{project}/html/index.html',
                                   'db/{slot}.{build_id}.{project}.{config}.tests-result.json',
                                   ]]
                       )


def test_simple_build():
    tmpd = mkdtemp()
    shutil.copytree(_testdata, join(tmpd, 'testdata'))
    oldcwd = os.getcwd()
    try:
        os.chdir(join(tmpd, 'testdata'))
        info = dict(
                    today = str(date.today()),
                    config = os.environ['CMTCONFIG'],
                    slot = 'testing-slot',
                    build_id = 0,
                    project = 'TestProject',
                    PROJECT = 'TESTPROJECT',
                    version = 'HEAD'
                    )

        script = BuildSlot.Script()
        retcode = script.run(['testing-slot.json'])
        assert retcode == 0

        proj_root = join(tmpd, 'testdata', 'build',
                         info['PROJECT'], '{PROJECT}_{version}'.format(**info))
        assert_files_exist(proj_root,
                           'Makefile',
                           join('InstallArea', info['config'],
                                'bin', 'HelloWorld.exe'))

        _check_build_artifacts(join(tmpd, 'testdata'), info)

    finally:
        os.chdir(oldcwd)
        shutil.rmtree(tmpd, ignore_errors=True)

def test_simple_build_w_test():
    tmpd = mkdtemp()
    shutil.copytree(_testdata, join(tmpd, 'testdata'))
    oldcwd = os.getcwd()
    try:
        os.chdir(join(tmpd, 'testdata'))
        info = dict(
                    today = str(date.today()),
                    config = os.environ['CMTCONFIG'],
                    slot = 'testing-slot',
                    build_id = 0,
                    project = 'TestProject',
                    PROJECT = 'TESTPROJECT',
                    version = 'HEAD'
                    )

        script = BuildSlot.Script()
        retcode = script.run(['--with-tests', 'testing-slot.json'])
        assert retcode == 0

        proj_root = join(tmpd, 'testdata', 'build',
                         info['PROJECT'], '{PROJECT}_{version}'.format(**info))
        assert_files_exist(proj_root,
                           'Makefile',
                           join('InstallArea', info['config'],
                                'bin', 'HelloWorld.exe'))

        _check_build_artifacts(join(tmpd, 'testdata'), info)

        #########
        teardown()
        script = BuildSlot.Script()
        script.run(['--tests-only', 'testing-slot.json'])

        proj_root = join(tmpd, 'testdata', 'build',
                         info['PROJECT'], '{PROJECT}_{version}'.format(**info))
        assert_files_exist(proj_root,
                           'Makefile',
                           join('InstallArea', info['config'],
                                'bin', 'HelloWorld.exe'))

        _check_test_artifacts(join(tmpd, 'testdata'), info)


    finally:
        os.chdir(oldcwd)
        shutil.rmtree(tmpd, ignore_errors=True)

def test_lbcore_164():
    '''https://its.cern.ch/jira/browse/LBCORE-164

    store in the artifacts of the builds the output of failed tests
    '''

    tmpd = mkdtemp()
    shutil.copytree(_testdata, join(tmpd, 'testdata'))
    oldcwd = os.getcwd()
    try:
        os.chdir(join(tmpd, 'testdata'))
        info = dict(
                    today = str(date.today()),
                    config = os.environ['CMTCONFIG'],
                    slot = 'testing-slot',
                    build_id = 0,
                    project = 'TestProject',
                    PROJECT = 'TESTPROJECT',
                    version = 'HEAD'
                    )

        proj_root = join(tmpd, 'testdata', 'build',
                         info['PROJECT'], '{PROJECT}_{version}'.format(**info))
        filename = join(proj_root, 'TestProjectSys', 'cmt', 'output.ref.new')
        ensureDirs([dirname(filename)])
        f = open(filename, 'w')
        f.write('new reference file\n')
        f.close()

        script = BuildSlot.Script()
        retcode = script.run(['--with-tests', 'testing-slot.json'])
        assert retcode == 0

        assert_files_exist(proj_root,
                           'Makefile',
                           join('InstallArea', info['config'],
                                'bin', 'HelloWorld.exe'))

        _check_build_artifacts(join(tmpd, 'testdata'), info)

        assert isfile(join(tmpd, 'testdata', 'artifacts',
                           'newrefs.{config}'.format(**info),
                           'TestProject', 'TestProjectSys', 'cmt',
                           'output.ref.new'))

    finally:
        os.chdir(oldcwd)
        #shutil.rmtree(tmpd, ignore_errors=True)
        print tmpd

def test_simple_build_2():
    # Test the case of "disabled" projects.
    tmpd = mkdtemp()
    shutil.copytree(_testdata, join(tmpd, 'testdata'))
    oldcwd = os.getcwd()
    try:
        os.chdir(join(tmpd, 'testdata'))
        info = dict(
                    today = str(date.today()),
                    config = os.environ['CMTCONFIG'],
                    slot = 'testing-slot-2',
                    build_id = 0,
                    project = 'TestProject',
                    PROJECT = 'TESTPROJECT',
                    version = 'HEAD'
                    )

        script = BuildSlot.Script()
        retcode = script.run(['testing-slot-2.json'])
        assert retcode == 0

        proj_root = join(tmpd, 'testdata', 'build',
                         info['PROJECT'], '{PROJECT}_{version}'.format(**info))
        assert_files_exist(proj_root,
                           'Makefile',
                           join('InstallArea', info['config'],
                                'bin', 'HelloWorld.exe'))

        _check_build_artifacts(join(tmpd, 'testdata'), info)

    finally:
        os.chdir(oldcwd)
        shutil.rmtree(tmpd, ignore_errors=True)

