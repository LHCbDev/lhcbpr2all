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

from LbNightlyTools.Configuration import slots, Project, Slot, ProjectsList
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
    slot = Slot('test', projects=[Project('a', 'v1r0',
                                          dependencies=['zero']),
                                  Project('b', 'v2r0',
                                          dependencies=['c', 'a'])])
    #slot.checkout()
    deps = slot.dependencies()

    expected = {'a': [], 'b': ['a']}
    assert deps == expected, deps

    full_deps = slot.fullDependencies()
    expected = {'b': ['a', 'c'], 'a': ['zero']}
    assert full_deps == expected, full_deps

def test_env():
    slot = Slot('test', projects=[Project('a', 'v1r0', env=['proj=a'])],
                env=['slot=test', 'proj=none'])
    # with dummy env
    initial = {}
    env = slot.environment(initial)
    assert env == {'slot': 'test', 'proj': 'none'}
    assert initial == {}

    env = slot.a.environment(initial)
    assert env == {'slot': 'test', 'proj': 'a'}
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
    assert env == {'slot': 'test', 'proj': 'none'}

    slot.env.append('another=entry')
    env = slot.environment({})
    assert env == {'slot': 'test', 'proj': 'none', 'another': 'entry'}
    # ensure that touching the instance 'env' attribute does not change the
    # class
    assert SpecialSlot.env == SpecialSlot.__env__ == ['slot=test', 'proj=none']

