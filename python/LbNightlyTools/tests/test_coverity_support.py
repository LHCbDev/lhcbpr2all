###############################################################################
# (c) Copyright 2016 CERN                                                     #
#                                                                             #
# This software is distributed under the terms of the GNU General Public      #
# Licence version 3 (GPL Version 3), copied verbatim in the file "COPYING".   #
#                                                                             #
# In applying this licence, CERN does not waive the privileges and immunities #
# granted to it by virtue of its status as an Intergovernmental Organization  #
# or submit itself to any jurisdiction.                                       #
###############################################################################

import os
from os.path import join, exists, abspath
from subprocess import CalledProcessError
from json import load

from .utils import TESTDATA_PATH, TemporaryDir

from ..Scripts.Build import Script as Builder

COV_DATA = join(TESTDATA_PATH, 'coverity')

def setup():
    # add to the path the Coverity mock tools
    os.environ['PATH'] = ':'.join([join(COV_DATA, 'bin'),
                                   join(TESTDATA_PATH, '../scripts'),
                                   os.environ['PATH']])
    os.environ['COVERITY_PASSPHRASE'] = 'dummy'

def in_temp_dir(func):
    '''
    Decorator to run a test in a temporary directory.
    '''
    from functools import wraps
    @wraps(func)
    def wrapper():
        with TemporaryDir(chdir=True, skel=COV_DATA):
            return func()
    return wrapper

def run_build(args):
    '''
    Helper to run the build script.
    '''
    rc = Builder().run(args)
    if rc:
        raise CalledProcessError(rc, ['lbn-build'] + args)

COV_OUT = join('build', 'TEST', 'TEST_HEAD', 'cov-out')

def collect_reports(names=None):
    if names is None:
        names = ['build', 'analyze', 'commit-defects']

    assert exists(COV_OUT), 'missing directory %s' % COV_OUT

    reports = {}
    for name in names:
        filename = join(COV_OUT, 'cov-{0}.report.json'.format(name))
        assert exists(filename), 'missing {0}'.format(filename)
        reports[name] = load(open(filename))
    return reports

def cov_log_file(step):
    return join('artifacts', 'summaries.' + os.environ['CMTCONFIG'], 'Test',
                'cov-' + step)

def check_logfiles(expected, not_expected=None):
    not_expected = not_expected or []
    for logfile in [cov_log_file(step) + ext
                    for step in expected
                    for ext in ['.log', '.err.log']]:
        assert exists(logfile), 'missing %s' % logfile
    for logfile in [cov_log_file(step) + ext
                    for step in not_expected
                    for ext in ['.log', '.err.log']]:
        assert not exists(logfile), 'found unexpected %s' % logfile


@in_temp_dir
def test_analyze():
    run_build(['--coverity', '--slot-build-id', '273', 'test-slot'])

    reports = collect_reports()
    for name in reports:
        assert reports[name]['retcode'] == 0, 'failure in %s' % name

    assert reports['build']['desc'] == 'test-slot-273'

    expected = ['/afs/cern.ch/sw/lcg/releases',
                '/cvmfs/sft.cern.ch/lcg/releases',
                '/cvmfs/lhcb.cern.ch/lib/lcg/releases',
                abspath(join('build', 'TEST'))]

    assert reports['analyze']['strip_path'] == expected, \
        'expected strip-path {0}, found {1}'.format(expected, reports['analyze']['strip_path'])

    for k,v in {"stream": "LHCb-Test-Stream", "host": "lcgapp10.cern.ch",
                "user": "admin", "port": "8080"}.items():
        assert reports['commit-defects'][k] == v, \
            'bad value for {0}: expected {1}, found {2}' \
                .format(k, v, reports['commit-defects'][k])

    check_logfiles(['analyze', 'commit-defects'])


@in_temp_dir
def test_failed_build():
    with open(join('build', 'TEST', 'TEST_HEAD', 'TestPackage', 'main.cpp'), 'w') as f:
        f.write('#error this is an error\n')
    run_build(['--coverity', 'test-slot'])

    reports = collect_reports(['build'])
    assert reports['build']['retcode'] != 0
    for name in ('analyze', 'commit-defects'):
        assert not exists(join(COV_OUT, 'cov-{0}.report.json'.format(name)))

    check_logfiles([], ['analyze', 'commit-defects'])


@in_temp_dir
def test_failed_analysis():
    os.environ['COV_TEST_ANALYZE_RC'] = '1'
    run_build(['--coverity', 'test-slot'])
    del os.environ['COV_TEST_ANALYZE_RC']

    reports = collect_reports(['build', 'analyze'])
    assert reports['build']['retcode'] == 0
    assert reports['analyze']['retcode'] != 0
    for name in ('commit-defects'):
        assert not exists(join(COV_OUT, 'cov-{0}.report.json'.format(name)))

    check_logfiles(['analyze'], ['commit-defects'])


@in_temp_dir
def test_missing_password():
    if 'COVERITY_PASSPHRASE' in os.environ:
        del os.environ['COVERITY_PASSPHRASE']

    run_build(['--coverity', 'test-slot'])

    reports = collect_reports(['build', 'analyze'])
    assert reports['build']['retcode'] == 0
    assert reports['analyze']['retcode'] == 0
    for name in ('commit-defects'):
        assert not exists(join(COV_OUT, 'cov-{0}.report.json'.format(name)))

    check_logfiles(['analyze'], ['commit-defects'])


@in_temp_dir
def test_no_commit():
    run_build(['--coverity', '--no-coverity-commit', 'test-slot'])

    reports = collect_reports(['build', 'analyze'])
    assert reports['build']['retcode'] == 0
    assert reports['analyze']['retcode'] == 0
    for name in ('commit-defects'):
        assert not exists(join(COV_OUT, 'cov-{0}.report.json'.format(name)))

    check_logfiles(['analyze'], ['commit-defects'])
