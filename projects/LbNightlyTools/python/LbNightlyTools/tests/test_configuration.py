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

from LbNightlyTools.Configuration import slots, Project, Package, Slot, ProjectsList, DBASE
import LbNightlyTools.BuildMethods as BM

import os

def setup():
    slots.clear()

def test_slots_dict():
    s = Slot('slot1')
    assert len(slots) == 1
    assert slots['slot1'] is s

    s = Slot('slot2')
    assert len(slots) == 2
    assert slots['slot2'] is s

    s = Slot('slot1')
    assert len(slots) == 2
    assert slots['slot1'] is s


def test_ProjectsList():
    slot = object() # dummy object for checking
    pl = ProjectsList(slot)
    assert len(pl) == 0

    pl.insert(0, Project('a', 'v1r0'))
    assert len(pl) == 1
    a = pl['a']
    assert a == pl[0]
    assert a.name == 'a'
    assert a.slot is slot

    pl.append(Project('b', 'v2r0'))
    assert len(pl) == 2
    b = pl['b']
    assert b == pl[1]
    assert b.name == 'b'
    assert b.slot is slot

    del pl[0]
    assert len(pl) == 1
    assert a.slot is None

    pl.append(Project('a/b', 'v3r0'))
    assert len(pl) == 2
    a_b = pl['a/b']
    assert a_b == pl[1]
    assert a_b.name == 'a/b'
    assert a_b == pl['a_b']

    # works as iterable
    assert [p.name for p in pl] == ['b', 'a/b']

def test_slot_projects():
    slot = Slot('test', projects=[Project('a', 'v1r0'), Project('b', 'v2r0')])
    assert len(slot.projects) == 2
    a, b = slot.projects
    assert a.slot == b.slot == slot
    assert a == slot.a
    assert b == slot.b

    del slot.b
    assert len(slot.projects) == 1
    #assert 'a' in slot.projects
    #assert 'b' not in slot.projects
    assert b.slot is None

    try:
        slot.projects = []
        assert False, '"slot.projects = []" should have failed'
    except:
        pass

    class SpecialSlot(Slot):
        projects = [Project('a', 'v1r0'),
                    Project('b', 'v2r0')]

    slot = SpecialSlot('test1')
    assert len(slot.projects) == 2
    a, b = slot.projects
    assert a.slot == b.slot == slot

    slot.projects.insert(0, Project('zero', 'v0r0'))
    assert len(slot.projects) == 3
    assert slot.projects['zero'].slot == slot

    try:
        slot.projects = []
        assert False, '"slot.projects = []" should have failed'
    except:
        pass

def test_deps():
    # explicit dependencies
    slot = Slot('test', projects=[Project('A', 'v1r0',
                                          dependencies=['Zero']),
                                  Project('b', 'v2r0',
                                          dependencies=['c', 'a'])])
    #slot.checkout()
    assert slot.A.dependencies() == ['Zero']
    assert slot.b.dependencies() == ['A', 'c']

    full_deps = slot.fullDependencies()
    expected = {'b': ['A', 'c'], 'A': ['Zero']}
    assert full_deps == expected, full_deps

    deps = slot.dependencies()
    expected = {'A': [], 'b': ['A']}
    assert deps == expected, deps

    b = Project('b', 'v2r0', dependencies=['c', 'a'])
    assert b.dependencies() == ['a', 'c']

def test_slot_def_args():
    # test default arguments
    dummy = Slot('dummy')
    assert len(dummy.projects) == 0

    dummy = Slot('dummy', [Project('A', 'v1r0')])
    assert len(dummy.projects) == 1
    assert dummy.A.version == 'v1r0'

def test_env():
    slot = Slot('test', projects=[Project('a', 'v1r0', env=['proj=a'])],
                env=['slot=test', 'proj=none'])

    special = {'CMAKE_PREFIX_PATH': os.getcwd(), 'CMTPROJECTPATH': os.getcwd()}
    def expected(d):
        '''hack to extend the expected dictionary with search paths'''
        d.update(special)
        return d

    # extend CMake and CMT search paths
    initial = {'CMAKE_PREFIX_PATH': '/usr/local/bin:/usr/bin'}
    env = slot.environment(initial)
    assert env['CMAKE_PREFIX_PATH'] == os.pathsep.join([os.getcwd(), initial['CMAKE_PREFIX_PATH']])
    assert env['CMTPROJECTPATH'] == os.getcwd()

    initial = {'CMTPROJECTPATH': '/usr/local/bin:/usr/bin'}
    env = slot.environment(initial)
    assert env['CMTPROJECTPATH'] == os.pathsep.join([os.getcwd(), initial['CMTPROJECTPATH']])
    assert env['CMAKE_PREFIX_PATH'] == os.getcwd()

    # with dummy env
    initial = {}
    env = slot.environment(initial)
    assert env == expected({'slot': 'test', 'proj': 'none'}), (env, expected({'slot': 'test', 'proj': 'none'}))
    assert initial == {}

    env = slot.a.environment(initial)
    assert env == expected({'slot': 'test', 'proj': 'a'})
    assert initial == {}

    # with os.environ
    key = 'USER'
    if key not in os.environ:
        os.environ[key] = 'dummy'
    value = os.environ[key]

    initial = dict(os.environ)

    slot.env.append('me=${%s}' % key)

    env = slot.environment()
    assert env['slot'] == 'test'
    assert env['proj'] == 'none'
    assert env[key] == value
    assert env['me'] == value
    assert os.environ == initial

    env = slot.a.environment()
    assert env['slot'] == 'test'
    assert env['proj'] == 'a'
    assert env[key] == value
    assert env['me'] == value
    assert os.environ == initial

    # derived class
    class SpecialSlot(Slot):
        projects = []
        env = ['slot=test', 'proj=none']
    slot = SpecialSlot('test')

    env = slot.environment({})
    assert env == expected({'slot': 'test', 'proj': 'none'})

    slot.env.append('another=entry')
    env = slot.environment({})
    assert env == expected({'slot': 'test', 'proj': 'none', 'another': 'entry'})
    # ensure that touching the instance 'env' attribute does not change the
    # class
    assert SpecialSlot.env == SpecialSlot.__env__ == ['slot=test', 'proj=none']

    # derived class
    class ExtendedSlot(SpecialSlot):
        env = ['proj=dummy']
    slot = ExtendedSlot('test')

    env = slot.environment({})
    assert env == expected({'slot': 'test', 'proj': 'dummy'})

def test_slot_desc():
    slot = Slot('test')
    assert slot.desc == Slot.__doc__.strip()

    slot = Slot('test', desc='a test slot')
    assert slot.desc == 'a test slot'

    class MyTest(Slot):
        '''
        This is My Test.
        '''
    slot = MyTest('test')
    assert slot.desc == 'This is My Test.'

    class NoDesc(Slot):
        pass
    slot = NoDesc('test')
    assert slot.desc == '<no description>'


def test_build_tool_prop():
    #######
    p = Project('p', 'v')
    assert p.__build_tool__ is None
    assert isinstance(p.build_tool, BM.default)

    p.build_tool = 'echo'
    assert isinstance(p.build_tool, BM.echo)

    p.build_tool = BM.cmt
    assert isinstance(p.build_tool, BM.cmt)

    #######
    class MyProj(Project):
        build_tool = 'echo'

    mp = MyProj('v')
    assert isinstance(mp.build_tool, BM.echo)

    mp.build_tool = BM.cmt
    assert isinstance(mp.build_tool, BM.cmt)

    #######
    s = Slot('s')
    assert s.__build_tool__ is None
    assert isinstance(s.build_tool, BM.default)

    s.build_tool = 'echo'
    assert isinstance(s.build_tool, BM.echo)

    s.build_tool = BM.cmt
    assert isinstance(s.build_tool, BM.cmt)

    #######
    class MySlot(Slot):
        build_tool = 'echo'

    ms = MySlot('ms')
    assert isinstance(ms.build_tool, BM.echo)

    ms.build_tool = BM.cmt
    assert isinstance(ms.build_tool, BM.cmt)

    #######
    p.build_tool = BM.cmt
    s.build_tool = 'echo'
    s.projects.append(p)
    assert isinstance(p.build_tool, BM.echo)
    try:
        p.build_tool = 'cmake'
        assert False, 'exception expected'
    except AttributeError:
        pass
    except:
        assert False, 'AttributeError exception expected'

def test_custom_projects():
    from LbNightlyTools.CheckoutMethods import ignore

    class LHCb(Project):
        checkout = 'ignore'

    p = LHCb('HEAD')
    assert p.name == 'LHCb'
    assert p.version == 'HEAD'
    assert p._checkout == ignore, (p._checkout, ignore)

    class Gaudi(Project):
        __url__ = 'https://gitlab.cern.ch/gaudi/Gaudi.git'
        def commitId(self):
            import re
            if self.version.lower() == 'head':
                return 'master'
            elif re.match(r'v[0-9]+', self.version):
                return '{0}/{0}_{1}'.format(self.name.upper(), self.version)
            return self.version.replace('/', '_')
        def checkout(self, **kwargs):
            args = {'url': self.__url__,
                    'commit': self.commitId()}
            args.update(kwargs)
            return (0, str(args), '')

    g = Gaudi('v26r1')
    assert g.name == 'Gaudi'
    assert g.version == 'v26r1'
    assert g.commitId() == 'GAUDI/GAUDI_v26r1'
    expected = (0, str({'url': 'https://gitlab.cern.ch/gaudi/Gaudi.git',
                        'commit': 'GAUDI/GAUDI_v26r1',
                        'verbose': True}), '')
    output = g.checkout(verbose=True)
    assert output == expected, (output, expected)

    class SpecialGaudi(Project):
        name = 'Special'

    assert SpecialGaudi.__project_name__ == 'Special'
    s = SpecialGaudi('HEAD')
    assert s.name == 'Special', s.name

def test_custom_projects_2():
    from LbNightlyTools.CheckoutMethods import ignore

    class CustomProject(Project):
        checkout = 'ignore'

    p = CustomProject('LHCb', 'HEAD')
    assert p.name == 'LHCb'
    assert p.version == 'HEAD'
    assert p._checkout == ignore, (p._checkout, ignore)

    class LHCb(CustomProject):
        pass

    p = LHCb('HEAD')
    assert p.name == 'LHCb'
    assert p.version == 'HEAD'
    assert p._checkout == ignore, (p._checkout, ignore)

def test_dataproject():
    # test empty constructor
    DBASE()

    name, version = 'AppConfig', 'v3r198'
    d = DBASE(packages=[Package(name, version)])
    assert d.name == 'DBASE'
    assert d.baseDir == 'DBASE'

    assert len(d.packages) == 1
    ac = d.packages[0]
    assert ac.name == name
    assert ac.version == version
    assert ac.baseDir == os.path.join('DBASE', name, version)
    assert d.AppConfig is ac

    name, version = 'Gen/DecFiles', 'v27r39'
    d.packages.append(Package(name, version))
    assert len(d.packages) == 2
    ac = d.packages[name]
    assert ac.name == name
    assert ac.version == version
    assert ac.baseDir == os.path.join('DBASE', name, version)
    assert d.Gen_DecFiles is ac

def test_no_patch_flag():
    s = Slot('lhcb-release')
    assert s.no_patch == False

    d = s.toDict()
    assert d.get('no_patch', False) == False

    s = Slot.fromDict(d)
    assert s.no_patch == False

    s = Slot('lhcb-release', no_patch=True)
    assert s.no_patch == True

    d = s.toDict()
    assert d.get('no_patch', False) == True

    s = Slot.fromDict(d)
    assert s.no_patch == True

    try:
        from StringIO import StringIO
        s.patch(StringIO())
        assert False, "ValueError expected"
    except ValueError:
        pass

def test_no_test_flag():
    s = Slot('lhcb-no-test')
    assert s.no_test == False

    d = s.toDict()
    assert d.get('no_test', False) == False

    s = Slot.fromDict(d)
    assert s.no_test == False

    s = Slot('lhcb-no-test', no_test=True)
    assert s.no_test == True

    d = s.toDict()
    assert d.get('no_test', False) == True

    s = Slot.fromDict(d)
    assert s.no_test == True

    try:
        s.test()
        assert False, "ValueError expected"
    except ValueError:
        pass

    p = Project('Gaudi', 'HEAD')
    assert p.no_test == False

    d = p.toDict()
    assert d.get('no_test', False) == False

    s = Project.fromDict(d)
    assert s.no_test == False

    p = Project('Gaudi', 'HEAD', no_test=True)
    assert p.no_test == True

    d = p.toDict()
    assert d.get('no_test', False) == True

    s = Project.fromDict(d)
    assert p.no_test == True

    p = DBASE()
    assert p.no_test == True
