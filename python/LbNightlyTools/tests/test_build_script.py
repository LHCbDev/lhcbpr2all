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
import codecs

from datetime import date
from os.path import exists, normpath, join, dirname, isfile
from LbNightlyTools.Utils import ensureDirs
from subprocess import call, Popen, PIPE

_testdata = normpath(join(*([__file__] + [os.pardir] * 4 + ['testdata'])))

_env_bk = dict(os.environ)

def setup():
    global _env_bk
    _env_bk = dict(os.environ)
    if 'LBN_LOAD_AVERAGE' in os.environ:
        del os.environ['LBN_LOAD_AVERAGE']

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
    chunks_dir = ('summaries.{config}/{project}/'
                  '{slot}.{weekday}_{PROJECT}_{version}-{config}.log.chunks')

    assert_files_exist(artifacts_dir,
                       'Project.xml',
                       *[f.format(**info)
                         for f in ['{project}.{version}.{slot}.{config}.tar.bz2',
                                   'summaries.{config}/{project}/build_log.html',
                                   chunks_dir,
                                   'db/{slot}.{build_id}.{config}.job-start.json',
                                   'db/{slot}.{build_id}.{config}.job-end.json',
                                   'db/{slot}.{build_id}.{project}.{config}.build-result.json',
                                   ]]
                       )
    # check that the build log chunks are not empty
    chunks_dir = join(artifacts_dir, chunks_dir.format(**info))
    for f in os.listdir(chunks_dir):
        f = join(chunks_dir, f)
        assert codecs.open(f, 'r', 'utf-8').read() != u'<html>\n</html>\n', ('empty file ' + f)

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
                    weekday = date.today().strftime("%a"),
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

def test_simple_build_parallel():
    tmpd = mkdtemp()
    shutil.copytree(_testdata, join(tmpd, 'testdata'))
    oldcwd = os.getcwd()
    try:
        os.chdir(join(tmpd, 'testdata'))
        info = dict(
                    today = str(date.today()),
                    weekday = date.today().strftime("%a"),
                    config = os.environ['CMTCONFIG'],
                    slot = 'testing-slot',
                    build_id = 0,
                    project = 'TestProject',
                    PROJECT = 'TESTPROJECT',
                    version = 'HEAD'
                    )

        script = BuildSlot.Script()
        retcode = script.run(['-j', '4', 'testing-slot.json'])
        assert retcode == 0
        assert script.options.jobs == 4

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

def test_simple_build_load():
    tmpd = mkdtemp()
    shutil.copytree(_testdata, join(tmpd, 'testdata'))
    oldcwd = os.getcwd()
    try:
        os.chdir(join(tmpd, 'testdata'))
        info = dict(
                    today = str(date.today()),
                    weekday = date.today().strftime("%a"),
                    config = os.environ['CMTCONFIG'],
                    slot = 'testing-slot',
                    build_id = 0,
                    project = 'TestProject',
                    PROJECT = 'TESTPROJECT',
                    version = 'HEAD'
                    )

        script = BuildSlot.Script()
        retcode = script.run(['-j', '4', '-l', '8', 'testing-slot.json'])
        assert retcode == 0
        assert script.options.jobs == 4
        assert script.options.load_average == 8

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

def test_simple_build_load_env():
    tmpd = mkdtemp()
    shutil.copytree(_testdata, join(tmpd, 'testdata'))
    oldcwd = os.getcwd()
    try:
        os.chdir(join(tmpd, 'testdata'))
        info = dict(
                    today = str(date.today()),
                    weekday = date.today().strftime("%a"),
                    config = os.environ['CMTCONFIG'],
                    slot = 'testing-slot',
                    build_id = 0,
                    project = 'TestProject',
                    PROJECT = 'TESTPROJECT',
                    version = 'HEAD'
                    )
        os.environ['LBN_LOAD_AVERAGE'] = '6.5'
        script = BuildSlot.Script()
        retcode = script.run(['-j', '4', 'testing-slot.json'])
        assert retcode == 0
        assert script.options.jobs == 4
        assert script.options.load_average == 6.5

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
                    weekday = date.today().strftime("%a"),
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

def test_simple_build_env_search_path():
    tmpd = mkdtemp()
    shutil.copytree(_testdata, join(tmpd, 'testdata'))
    oldcwd = os.getcwd()
    try:
        os.chdir(join(tmpd, 'testdata'))
        info = dict(
                    today = str(date.today()),
                    weekday = date.today().strftime("%a"),
                    config = os.environ['CMTCONFIG'],
                    slot = 'testing-slot-env',
                    build_id = 0,
                    project = 'TestProject',
                    PROJECT = 'TESTPROJECT',
                    version = 'HEAD'
                    )

        os.environ['CMAKE_PREFIX_PATH'] = '/some/cmake:/another/cmake'
        os.environ['CMTPROJECTPATH'] = '/some/cmt:/another/cmt'
        os.environ['PWD'] = os.getcwd() # this is usually done by the shell

        script = BuildSlot.Script()
        retcode = script.run(['testing-slot-env.json'])
        assert retcode == 0

        proj_root = join(tmpd, 'testdata', 'build',
                         info['PROJECT'], '{PROJECT}_{version}'.format(**info))
        assert_files_exist(proj_root,
                           'Makefile',
                           join('InstallArea', info['config'],
                                'bin', 'HelloWorld.exe'))
        artifacts_dir = join(tmpd, 'testdata', 'artifacts')
        assert_files_exist(artifacts_dir,
                           'searchPath.cmake',
                           'confSummary.py')

        _check_build_artifacts(join(tmpd, 'testdata'), info)

        expected_cmake = ['/another/path', '/new/root/inner', '/some/cmake', '/another/cmake',
                          '/some/path', '/some/cmt', '/another/cmt']
        expected_cmt = ['/some/path', '/some/cmt', '/another/cmt',
                        '/another/path', '/new/root/inner', '/some/cmake', '/another/cmake']

        loc = {}
        exec open(join(artifacts_dir, 'confSummary.py')).read() in {'__file__': '/new/root/confSummary.py'}, loc
        assert loc['cmtProjectPathList'] == expected_cmt, 'expected %r, found %r' % (expected_cmt, loc['cmtProjectPathList'])

        os.makedirs(join(tmpd, 'new_loc'))
        with open(join(tmpd, 'new_loc', 'searchPath.cmake'), 'w') as new_file:
            new_file.writelines(open(join(artifacts_dir, 'searchPath.cmake')))
            new_file.write('\nforeach(entry ${CMAKE_PREFIX_PATH})\nmessage(STATUS "${entry}")\nendforeach()\n')
        print open(join(tmpd, 'new_loc', 'searchPath.cmake')).read()
        proc = Popen(['cmake', '-P', join(tmpd, 'new_loc', 'searchPath.cmake')], stdout=PIPE)
        expected_cmake = ['-- %s\n' % s.replace('/new/root', join(tmpd, 'new_loc'))
                          for s in expected_cmake]
        output = list(proc.stdout)
        print '--- CMake output ---'
        print output
        print '--- CMake expected ---'
        print expected_cmake
        assert output == expected_cmake
        assert proc.wait() == 0

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
                    weekday = date.today().strftime("%a"),
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
        shutil.rmtree(tmpd, ignore_errors=True)

def test_simple_build_2():
    # Test the case of "disabled" projects.
    tmpd = mkdtemp()
    shutil.copytree(_testdata, join(tmpd, 'testdata'))
    oldcwd = os.getcwd()
    try:
        os.chdir(join(tmpd, 'testdata'))
        info = dict(
                    today = str(date.today()),
                    weekday = date.today().strftime("%a"),
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

def test_explicit_list():
    # Test the case of explicit project list.
    tmpd = mkdtemp()
    shutil.copytree(_testdata, join(tmpd, 'testdata'))
    oldcwd = os.getcwd()
    try:
        os.chdir(join(tmpd, 'testdata'))
        info = dict(
                    today = str(date.today()),
                    weekday = date.today().strftime("%a"),
                    config = os.environ['CMTCONFIG'],
                    slot = 'testing-slot-2',
                    build_id = 0,
                    project = 'DummyProject',
                    PROJECT = 'DUMMYPROJECT',
                    version = 'HEAD'
                    )
        # I reuse the TestProject renaming it DummyProject
        os.makedirs('build')
        call(['tar', 'xf', join(os.pardir, 'artifacts',
                                'TestProject.HEAD.testing-slot.src.tar.bz2')],
             cwd='build')
        os.rename(join('build', 'TESTPROJECT'), join('build', 'DUMMYPROJECT'))
        os.rename(join('build', 'DUMMYPROJECT', 'TESTPROJECT_HEAD'),
                  join('build', 'DUMMYPROJECT', 'DUMMYPROJECT_HEAD'))

        script = BuildSlot.Script()
        retcode = script.run(['--projects', 'DummyProject', 'testing-slot-2.json'])
        assert retcode == 0

        proj_root = join(tmpd, 'testdata', 'build',
                         info['PROJECT'], '{PROJECT}_{version}'.format(**info))
        assert_files_exist(proj_root,
                           'Makefile',
                           join('InstallArea', info['config'],
                                'bin', 'HelloWorld.exe'))
        other_project_build_dir = join(tmpd, 'testdata', 'build',
                                       'TESTPROJECT', 'TESTPROJECT_HEAD',
                                       'InstallArea', info['config'])
        assert not os.path.exists(other_project_build_dir)

        _check_build_artifacts(join(tmpd, 'testdata'), info)

    finally:
        os.chdir(oldcwd)
        shutil.rmtree(tmpd, ignore_errors=True)


def test_with_shared():
    tmpd = mkdtemp()
    shutil.copytree(_testdata, join(tmpd, 'testdata'))
    oldcwd = os.getcwd()
    try:
        os.chdir(join(tmpd, 'testdata'))
        info = dict(
                    today = str(date.today()),
                    weekday = date.today().strftime("%a"),
                    config = os.environ['CMTCONFIG'],
                    slot = 'testing-slot-with-shared',
                    build_id = 0,
                    project = 'TestProject',
                    PROJECT = 'TESTPROJECT',
                    version = 'HEAD'
                    )

        script = BuildSlot.Script()
        retcode = script.run(['--debug', 'testing-slot-with-shared.json'])
        assert retcode == 0

        proj_root = join(tmpd, 'testdata', 'build',
                         info['PROJECT'], '{PROJECT}_{version}'.format(**info))
        assert_files_exist(proj_root,
                           'Makefile',
                           join('InstallArea', info['config'],
                                'bin', 'HelloWorld.exe'))

        _check_build_artifacts(join(tmpd, 'testdata'), info)

        shr_file = '{project}.{version}.{slot}.shared.tar.bz2'.format(**info)
        assert_files_exist(join(tmpd, 'testdata', 'artifacts'), shr_file)

    finally:
        os.chdir(oldcwd)
        shutil.rmtree(tmpd, ignore_errors=True)
