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
from LbNightlyTools.tests.utils import *

# Uncomment to disable the tests.
#__test__ = False

from LbNightlyTools import StackCheckout
from LbNightlyTools import CheckoutMethods

os.environ['LANG'] = 'C'

def test_call():
    'StackCheckout.call()'
    # standard calls
    assert StackCheckout.call(['true']) == 0
    assert StackCheckout.call(['false']) == 1
    # calls with retry
    assert StackCheckout.call(['true'], retry=3) == 0
    try:
        StackCheckout.call(['false'], retry=3)
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

    from os.path import exists, join
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


def test_getpack_recursive_head():
    'getpack with recursive head (headofeverything)'
    if not which('getpack') or not which('git'):
        raise nose.SkipTest

    from os.path import exists, join
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

