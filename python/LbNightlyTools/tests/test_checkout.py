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
import json
import tempfile
import os
import re
import shutil
import nose
from subprocess import Popen, PIPE
from xml.etree import ElementTree as ET
from os.path import normpath, join, exists, islink
from LbNightlyTools.tests.utils import *


_testdata = normpath(join(*([__file__] + [os.pardir] * 4 + ['testdata'])))

# Uncomment to disable the tests.
#__test__ = False

from LbNightlyTools import StackCheckout
from LbNightlyTools import Utils
from LbNightlyTools import CheckoutMethods

os.environ['LANG'] = 'C'

def test_retry_call():
    'Utils.retry_call()'
    # standard calls
    assert Utils.retry_call(['true']) == 0
    assert Utils.retry_call(['false']) == 1
    # calls with retry
    assert Utils.retry_call(['true'], retry=3) == 0
    try:
        Utils.retry_call(['false'], retry=3)
    except RuntimeError, x:
        assert str(x) == "the command ['false'] failed 3 times"

def test_ProjectDesc():
    'StackCheckout.ProjectDesc'
    ProjectDesc = StackCheckout.ProjectDesc

    mockCheckout = MockFunc()

    p = ProjectDesc('Gaudi', 'v23r5')
    assert p.name == 'Gaudi'
    assert p.version == 'v23r5'
    assert p.overrides == {}
    assert p._checkout == CheckoutMethods.default
    assert p.projectDir == 'GAUDI/GAUDI_v23r5'
    assert str(p) == 'Gaudi v23r5'

    p = ProjectDesc('Gaudi', 'head')
    assert p.name == 'Gaudi'
    assert p.version == 'HEAD'
    assert p.overrides == {}
    assert p._checkout == CheckoutMethods.default
    assert p.projectDir == 'GAUDI/GAUDI_HEAD'
    assert str(p) == 'Gaudi HEAD'

    p = ProjectDesc('Gaudi', 'v23r5', checkout=mockCheckout)
    assert p.name == 'Gaudi'
    assert p.version == 'v23r5'
    assert p.overrides == {}
    assert p._checkout == mockCheckout

    p = ProjectDesc('Gaudi', 'v23r5',
                    overrides={'GaudiPolicy': 'head',
                               'GaudiProfiling': None,
                               'GaudiObjDesc': 'v11r17'},
                    checkout=mockCheckout)
    assert p.name == 'Gaudi'
    assert p.version == 'v23r5'
    assert p.overrides == {'GaudiPolicy': 'head',
                           'GaudiProfiling': None,
                           'GaudiObjDesc': 'v11r17'}
    assert p._checkout == mockCheckout

    cb = MockFunc()
    p = ProjectDesc('Gaudi', 'v23r5', checkout=cb)
    p.checkout()
    assert cb.args == (p,)
    assert cb.kwargs == {'rootdir': '.'}
    p.checkout('/tmp')
    assert cb.args == (p,)
    assert cb.kwargs == {'rootdir': '/tmp'}

def test_StackDesc():
    'StackCheckout.StackDesc'
    StackDesc = StackCheckout.StackDesc
    ProjectDesc = StackCheckout.ProjectDesc

    s = StackDesc()
    assert s.projects == []
    assert s.name == None

    s = StackDesc(name='lhcb-gaudi-head')
    assert s.projects == []
    assert s.name == 'lhcb-gaudi-head'

    cb = MockFunc()
    p = ProjectDesc('Gaudi', 'v23r5', checkout=cb)
    s = StackDesc([p])
    s.checkout()
    assert cb.args == (p,)
    assert cb.kwargs == {'rootdir': '.'}
    s.checkout('/tmp')
    assert cb.args == (p,)
    assert cb.kwargs == {'rootdir': '/tmp'}

def test_PartialCheckout():
    'PartialCheckout'
    StackDesc = StackCheckout.StackDesc
    ProjectDesc = StackCheckout.ProjectDesc

    gcb = MockFunc()
    p1 = ProjectDesc('Gaudi', 'v23r5', checkout=gcb)
    lcb = MockFunc()
    p2 = ProjectDesc('LHCb', 'HEAD', checkout=lcb)

    s = StackDesc([p1, p2])
    s.checkout(requested=set(['gaudi']))

    assert gcb.args == (p1,)
    assert gcb.kwargs == {'rootdir': '.'}
    assert lcb.args == None
    assert lcb.kwargs == None

def test_parseConfigFile():
    'StackCheckout.parseConfigFile()'

    doCall = lambda data: processFileWithName(json.dumps(data), 'dummy.json', StackCheckout.parseConfigFile)

    CheckoutMethods.special_test = MockFunc()

    s = doCall({'projects':[{"name": "Gaudi",
                             "version": "v23r5",
                             "checkout": "special_test"},
                            {"name": "LHCb",
                             "version": "v32r5",
                             "overrides": {"GaudiObjDesc": "HEAD",
                                           "GaudiPython": "v12r4",
                                           "Online/RootCnv": None}}]})
    assert s.name == 'dummy'
    assert len(s.projects) == 2
    p = s.projects[0]
    assert (p.name, p.version) == ('Gaudi', 'v23r5')
    assert p._checkout == CheckoutMethods.special_test #@UndefinedVariable
    p = s.projects[1]
    assert (p.name, p.version) == ('LHCb', 'v32r5')
    assert p._checkout == CheckoutMethods.default
    assert p.overrides == {"GaudiObjDesc": "HEAD",
                           "GaudiPython": "v12r4",
                           "Online/RootCnv": None}

    s = doCall({'projects':[], 'slot': 'lhcb-head'})
    assert s.name == 'lhcb-head'
    assert len(s.projects) == 0

    s = doCall({'projects':[{"name": "P",
                             "version": "V",
                             "checkout": "os.path.exists"}]})
    assert len(s.projects) == 1
    p = s.projects[0]
    assert (p.name, p.version) == ('P', 'V')
    assert p._checkout == os.path.exists

    try:
        s = doCall({'projects':[{"name": "Gaudi"}]})
    except KeyError:
        pass

def test_checkout():
    'checkout functions'
    if not which('getpack') or not which('git'):
        raise nose.SkipTest

    ProjectDesc = StackCheckout.ProjectDesc

    tmpdir = tempfile.mkdtemp()
    def check(files):
        for f in files:
            assert exists(join(tmpdir, f)), 'Missing %s' % f
    try:
        CheckoutMethods.default(ProjectDesc('Brunel', 'v44r1'), tmpdir)
        check([join('BRUNEL', 'BRUNEL_v44r1', join(*x))
               for x in [('Makefile',),
                         ('CMakeLists.txt',),
                         ('cmt', 'project.cmt'),
                         ('BrunelSys', 'cmt', 'requirements')]])

        CheckoutMethods.default(ProjectDesc('Brunel', 'head'), tmpdir)
        check([join('BRUNEL', 'BRUNEL_HEAD', join(*x))
               for x in [('Makefile',),
                         ('CMakeLists.txt',),
                         ('cmt', 'project.cmt'),
                         ('Rec', 'Brunel', 'cmt', 'requirements'),
                         ('BrunelSys', 'cmt', 'requirements')]])

        shutil.rmtree(join(tmpdir, 'BRUNEL', 'BRUNEL_HEAD'), ignore_errors=True)
        CheckoutMethods.default(ProjectDesc('Brunel', 'head',
                                            overrides={'GaudiObjDesc': 'head',
                                                       'GaudiPolicy': 'v12r0',
                                                       'Rec/Brunel': None}),
                                tmpdir)
        check([join('BRUNEL', 'BRUNEL_HEAD', join(*x))
               for x in [('Makefile',),
                         ('CMakeLists.txt',),
                         ('cmt', 'project.cmt'),
                         ('BrunelSys', 'cmt', 'requirements'),
                         ('GaudiObjDesc', 'cmt', 'requirements'),
                         ('GaudiPolicy', 'cmt', 'requirements')]])
        GaudiPolicy_requirements = open(join(tmpdir, 'BRUNEL', 'BRUNEL_HEAD', 'GaudiPolicy', 'cmt', 'requirements')).read()
        assert re.search(r'version\s+v12r0', GaudiPolicy_requirements)
        assert not exists(join(tmpdir, 'BRUNEL', 'BRUNEL_HEAD', 'Rec', 'Brunel', 'cmt', 'requirements'))

        CheckoutMethods.git(ProjectDesc('Gaudi', 'v23r6',
                                        checkout_opts={'url': 'http://git.cern.ch/pub/gaudi',
                                                       'commit': 'GAUDI/GAUDI_v23r6'}),
                            tmpdir)
        check([join('GAUDI', 'GAUDI_v23r6', join(*x))
               for x in [('Makefile',),
                         ('CMakeLists.txt',),
                         ('cmt', 'project.cmt'),
                         ('GaudiRelease', 'cmt', 'requirements')]])
        #assert 'v23r6' in open(join(tmpdir, 'GAUDI', 'GAUDI_v23r6', 'CMakeLists.txt')).read()
        p = Popen(['git', 'branch'],
                  stdout=PIPE,
                  cwd=join(tmpdir, 'GAUDI', 'GAUDI_v23r6'))
        branches = p.communicate()[0].splitlines()
        assert '* (no branch)' in branches


        CheckoutMethods.git(ProjectDesc('Gaudi', 'HEAD',
                                        checkout_opts={'url': 'http://git.cern.ch/pub/gaudi'}),
                            tmpdir)
        check([join('GAUDI', 'GAUDI_HEAD', join(*x))
               for x in [('Makefile',),
                         ('CMakeLists.txt',),
                         ('cmt', 'project.cmt'),
                         ('GaudiRelease', 'cmt', 'requirements')]])
        p = Popen(['git', 'branch'],
                  stdout=PIPE,
                  cwd=join(tmpdir, 'GAUDI', 'GAUDI_HEAD'))
        branches = p.communicate()[0].splitlines()
        assert '* master' in branches


        shutil.rmtree(join(tmpdir, 'BRUNEL', 'BRUNEL_HEAD'), ignore_errors=True)
        svnurl = 'http://svn.cern.ch/guest/lhcb/Brunel/trunk'
        CheckoutMethods.svn(ProjectDesc('Brunel', 'HEAD',
                                        checkout_opts={'url': svnurl}),
                            tmpdir)
        check([join('BRUNEL', 'BRUNEL_HEAD', join(*x))
               for x in [('Makefile',),
                         ('CMakeLists.txt',),
                         ('cmt', 'project.cmt'),
                         ('Rec', 'Brunel', 'cmt', 'requirements'),
                         ('BrunelSys', 'cmt', 'requirements')]])
        p = Popen(['svn', 'info'],
                  stdout=PIPE,
                  cwd=join(tmpdir, 'BRUNEL', 'BRUNEL_HEAD'))
        infos = p.communicate()[0].splitlines()
        assert 'URL: http://svn.cern.ch/guest/lhcb/Brunel/trunk' in infos


        shutil.rmtree(join(tmpdir, 'GAUDI', 'GAUDI_v23r6'), ignore_errors=True)
        shutil.rmtree(join(tmpdir, 'GAUDI', 'GAUDI_HEAD'), ignore_errors=True)
        CheckoutMethods.ignore(ProjectDesc('Gaudi', 'v23r6'), tmpdir)
        assert not exists(join(tmpdir, 'GAUDI', 'GAUDI_v23r6'))


    finally:
        #print tmpdir
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_checkout_export():
    'checkout functions with option "export"'
    if not which('getpack') or not which('git'):
        raise nose.SkipTest

    ProjectDesc = StackCheckout.ProjectDesc

    tmpdir = tempfile.mkdtemp()
    def check(files):
        for f in files:
            assert exists(join(tmpdir, f)), 'Missing %s' % f
    try:
        CheckoutMethods.default(ProjectDesc('Brunel', 'v44r1',
                                            checkout_opts={'export': True}),
                                tmpdir)
        check([join('BRUNEL', 'BRUNEL_v44r1', join(*x))
               for x in [('Makefile',),
                         ('CMakeLists.txt',),
                         ('cmt', 'project.cmt'),
                         ('BrunelSys', 'cmt', 'requirements')]])
        assert not exists(join(tmpdir, 'BRUNEL', 'BRUNEL_v44r1',
                               'BrunelSys', '.svn'))

        CheckoutMethods.git(ProjectDesc('Gaudi', 'v23r6',
                                        checkout_opts={'url': 'http://git.cern.ch/pub/gaudi',
                                                       'commit': 'GAUDI/GAUDI_v23r6',
                                                       'export': True}),
                            tmpdir)
        check([join('GAUDI', 'GAUDI_v23r6', join(*x))
               for x in [('Makefile',),
                         ('CMakeLists.txt',),
                         ('cmt', 'project.cmt'),
                         ('GaudiRelease', 'cmt', 'requirements')]])
        assert not exists(join(tmpdir, 'GAUDI', 'GAUDI_v23r6', '.git'))

        shutil.rmtree(join(tmpdir, 'BRUNEL', 'BRUNEL_HEAD'), ignore_errors=True)
        svnurl = 'http://svn.cern.ch/guest/lhcb/Brunel/trunk'
        CheckoutMethods.svn(ProjectDesc('Brunel', 'HEAD',
                                        checkout_opts={'url': svnurl,
                                                       'export': True}),
                            tmpdir)
        check([join('BRUNEL', 'BRUNEL_HEAD', join(*x))
               for x in [('Makefile',),
                         ('CMakeLists.txt',),
                         ('cmt', 'project.cmt'),
                         ('Rec', 'Brunel', 'cmt', 'requirements'),
                         ('BrunelSys', 'cmt', 'requirements')]])
        assert not exists(join(tmpdir, 'BRUNEL', 'BRUNEL_HEAD', '.svn'))

    finally:
        #print tmpdir
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_getpack_recursive_head():
    'getpack with recursive head (headofeverything)'
    if not which('getpack') or not which('git'):
        raise nose.SkipTest

    ProjectDesc = StackCheckout.ProjectDesc

    tmpdir = tempfile.mkdtemp()
    def check(files):
        for f in files:
            assert exists(join(tmpdir, f)), 'Missing %s' % f

    def getPkgVersion(path):
        req = open(path).read()
        m = re.search(r'version\s+([vrp0-9]+)', req)
        return m.group(1) if m else None

    def isFromTrunk(path):
        p = Popen(['svn', 'info', '--xml', path], stdout=PIPE, stderr=PIPE)
        out, _ = p.communicate()
        x = ET.fromstring(out)
        url = x.find('entry/url')
        if url is None:
            url = 'None'
        else:
            url = url.text
        return 'trunk' in url

    try:

        CheckoutMethods.default(ProjectDesc('Brunel', 'v44r1'), tmpdir)
        check([join('BRUNEL', 'BRUNEL_v44r1', join(*x))
               for x in [('Makefile',),
                         ('CMakeLists.txt',),
                         ('cmt', 'project.cmt'),
                         ('Rec', 'Brunel', 'cmt', 'requirements'),
                         ('BrunelSys', 'cmt', 'requirements')]])
        req = join(tmpdir, 'BRUNEL', 'BRUNEL_v44r1', 'Rec', 'Brunel', 'cmt', 'requirements')
        assert not isFromTrunk(req)
        assert getPkgVersion(req) == 'v44r1'
        sysreq = join(tmpdir, 'BRUNEL', 'BRUNEL_v44r1', 'BrunelSys', 'cmt', 'requirements')
        assert not isFromTrunk(sysreq)
        assert getPkgVersion(sysreq) == 'v44r1'


        CheckoutMethods.default(ProjectDesc('Brunel', 'head'), tmpdir)
        check([join('BRUNEL', 'BRUNEL_HEAD', join(*x))
               for x in [('Makefile',),
                         ('CMakeLists.txt',),
                         ('cmt', 'project.cmt'),
                         ('Rec', 'Brunel', 'cmt', 'requirements'),
                         ('BrunelSys', 'cmt', 'requirements')]])
        req = join(tmpdir, 'BRUNEL', 'BRUNEL_HEAD', 'Rec', 'Brunel', 'cmt', 'requirements')
        assert isFromTrunk(req)
        assert getPkgVersion(req) != 'v44r1'
        sysreq = join(tmpdir, 'BRUNEL', 'BRUNEL_HEAD', 'BrunelSys', 'cmt', 'requirements')
        assert isFromTrunk(sysreq)
        assert getPkgVersion(sysreq) != 'v44r1'

        shutil.rmtree(join(tmpdir, 'BRUNEL'), ignore_errors=True)
        CheckoutMethods.default(ProjectDesc('Brunel', 'v44r1',
                                            checkout_opts={'recursive_head':
                                                           True}),
                                 tmpdir)
        check([join('BRUNEL', 'BRUNEL_v44r1', join(*x))
               for x in [('Makefile',),
                         ('CMakeLists.txt',),
                         ('cmt', 'project.cmt'),
                         ('Rec', 'Brunel', 'cmt', 'requirements'),
                         ('BrunelSys', 'cmt', 'requirements')]])
        req = join(tmpdir, 'BRUNEL', 'BRUNEL_v44r1', 'Rec', 'Brunel', 'cmt', 'requirements')
        assert isFromTrunk(req)
        sysreq = join(tmpdir, 'BRUNEL', 'BRUNEL_v44r1', 'BrunelSys', 'cmt', 'requirements')
        assert not isFromTrunk(sysreq)

        CheckoutMethods.default(ProjectDesc('Brunel', 'HEAD',
                                            checkout_opts={'recursive_head':
                                                           False}),
                                 tmpdir)
        check([join('BRUNEL', 'BRUNEL_HEAD', join(*x))
               for x in [('Makefile',),
                         ('CMakeLists.txt',),
                         ('cmt', 'project.cmt'),
                         ('Rec', 'Brunel', 'cmt', 'requirements'),
                         ('BrunelSys', 'cmt', 'requirements')]])
        req = join(tmpdir, 'BRUNEL', 'BRUNEL_HEAD', 'Rec', 'Brunel', 'cmt', 'requirements')
        assert not isFromTrunk(req)
        sysreq = join(tmpdir, 'BRUNEL', 'BRUNEL_HEAD', 'BrunelSys', 'cmt', 'requirements')
        assert isFromTrunk(sysreq)

    finally:
        #print tmpdir
        shutil.rmtree(tmpdir, ignore_errors=True)

def test_collectDeps():
    expected = {'LCGCMT': [],
                'Gaudi': ['LCGCMT'],
                'Online': ['Gaudi'],
                'LHCb': ['Gaudi'],
                'Lbcom': ['LHCb'],
                'Rec': ['LHCb'],
                'Brunel': ['Lbcom', 'Rec']
                }

    mlh = MockLoggingHandler()
    StackCheckout.__log__.addHandler(mlh)

    rootdir = join(_testdata, 'collect_deps', 'cmt')
    slot = StackCheckout.parseConfigFile(join(rootdir, 'conf.json'))
    deps = slot.collectDeps(rootdir)
    print 'CMT:', deps
    assert deps == expected
    assert len(mlh.messages['warning']) == 1
    assert 'LCGCMT' in mlh.messages['warning'].pop()

    rootdir = join(_testdata, 'collect_deps', 'cmake')
    slot = StackCheckout.parseConfigFile(join(rootdir, 'conf.json'))
    deps = slot.collectDeps(rootdir)
    print 'CMake:', deps
    assert deps == expected
    assert len(mlh.messages['warning']) == 1
    assert 'LCGCMT' in mlh.messages['warning'].pop()

    rootdir = join(_testdata, 'collect_deps', 'broken')
    slot = StackCheckout.parseConfigFile(join(rootdir, 'conf.json'))
    deps = slot.collectDeps(rootdir)
    expected = {'Gaudi': [],
                'BadCMT': [],
                'BadCMake': [],
                'Missing': []}
    print 'Broken:', deps
    assert deps == expected
    warnings = mlh.messages['warning']
    assert filter(re.compile(r'cannot discover dependencies for BadCMT').match, warnings)
    assert filter(re.compile(r'cannot discover dependencies for BadCMake').match, warnings)
    assert filter(re.compile(r'cannot discover dependencies for Missing').match, warnings)
    assert not filter(re.compile(r'cannot discover dependencies for Gaudi').match, warnings)

def test_checkout_datapkg():
    '''checkout a single data package (getpack)'''
    if not which('getpack'):
        raise nose.SkipTest

    PackageDesc = StackCheckout.PackageDesc

    mlh = MockLoggingHandler()
    StackCheckout.__log__.addHandler(mlh)

    with TemporaryDir(chdir=True):
        os.makedirs('build')
        pkg = PackageDesc(name='AppConfig', version='v3r198')
        pkg.checkout('build')

        assert exists(join('build', 'DBASE', 'AppConfig', 'v3r198', 'cmt'))

def test_stack_checkout_datapkg():
    '''checkout a data package within a slot'''
    if not which('getpack'):
        raise nose.SkipTest

    PackageDesc = StackCheckout.PackageDesc

    mlh = MockLoggingHandler()
    StackCheckout.__log__.addHandler(mlh)

    with TemporaryDir(chdir=True):
        os.makedirs('build')
        pkgs = [PackageDesc(name='AppConfig', version='v3r198'),
                PackageDesc(name='Det/SQLDDDB', version='HEAD')]
        slot = StackCheckout.StackDesc(packages=pkgs)
        slot.checkout('build')

        for pkg in pkgs:
            assert exists(join('build', pkg.packageDir)), 'missing %s' % pkg.packageDir
        assert exists(join('build', 'DBASE', 'AppConfig', 'v3r198'))
        assert not islink(join('build', 'DBASE', 'AppConfig', 'v3r198'))

        assert islink(join('build', 'DBASE', 'AppConfig', 'v3r196'))

        assert islink(join('build', 'DBASE', 'Gen'))

        assert not islink(join('build', 'DBASE', 'Det'))
        assert not islink(join('build', 'DBASE', 'Det', 'SQLDDDB'))
        assert not islink(join('build', 'DBASE', 'Det', 'SQLDDDB', 'head'))
        assert exists(join('build', 'DBASE', 'Det', 'SQLDDDB', 'head', 'cmt'))
        assert islink(join('build', 'DBASE', 'Det', 'SQLDDDB', 'v7r10'))

        # picked up at random
        assert exists(join('build', 'PARAM', 'QMTestFiles', 'v1r0'))
        assert islink(join('build', 'PARAM'))
