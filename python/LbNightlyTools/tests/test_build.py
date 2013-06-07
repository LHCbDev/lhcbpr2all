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

from xml.etree import ElementTree as ET
from StringIO import StringIO

# Uncomment to disable the tests.
#__test__ = False

from LbNightlyTools import BuildSlot

def test_ProjDesc():
    'BuildSlot.ProjDesc'
    p = BuildSlot.ProjDesc({u'name': u'MyProject',
                            u'version': u'v1r0',
                            u'dependencies': [u'MyBase']})
    assert p.name == u'MyProject'
    assert p.version == u'v1r0'
    assert p.deps == [u'MyBase']
    assert p.dir == os.path.join('MYPROJECT', 'MYPROJECT_v1r0')
    assert str(p) == 'MyProject v1r0'

    p = BuildSlot.ProjDesc({u'name': u'MyProject',
                            u'version': u'v1r0'})
    assert p.deps == []

def test_genProjectXml():
    'BuildSlot.genProjectXml()'
    projects = map(BuildSlot.ProjDesc,
                   [{u'name': u'MyBase',
                     u'version': u'v3r2'},
                    {u'name': u'MyProject',
                     u'version': u'v1r0',
                     u'dependencies': [u'MyBase']}])
    xml = BuildSlot.genProjectXml('the-slot', projects)

    versions = dict([(p.name, str(p)) for p in projects])

    data = ET.parse(StringIO(xml))

    getName = lambda e: e.attrib['name']
    root = data.getroot()
    assert root.attrib['name'] == 'the-slot'

    children = root.getchildren()
    assert len(children) == len(projects)
    for e, p in zip(children, projects):
        assert e.attrib['name'] == str(p)
        deps = e.getchildren()
        assert len(deps) == len(p.deps)
        for a, b in zip(sorted(map(getName, deps)), sorted(map(versions.get, p.deps))):
            assert a == b, 'Dependencies of %s not matching (%s != %s)' % (p, a, b)


def test_genSlotConfig():
    'BuildSlot.genSlotConfig()'
    config = dict(slot='some-slot',
                  projects=[{'name': 'Gaudi', 'version': 'v23r8'},
                            {'name': 'LHCb', 'version': 'HEAD',
                             'dependencies': ['Gaudi']}],
                  warning_exceptions=['.*/Boost/.*warning', '.*/ROOT/.*warning'],
                  error_exceptions=[r'\[distcc\]'])
    cmake = BuildSlot.genSlotConfig(config)

    print cmake

    assert 'set(slot some-slot)\n' in cmake
    assert 'set(config $ENV{CMTCONFIG})\n' in cmake
    assert 'set(projects Gaudi LHCb)\n' in cmake
    assert 'set(Gaudi_version v23r8)\n' in cmake
    assert 'set(LHCb_version HEAD)\n' in cmake
    assert 'set(Gaudi_dependencies )\n' in cmake
    assert 'set(LHCb_dependencies Gaudi)\n' in cmake

    # FIXME: these shoud be improved
    assert r'.*/Boost/.*warning' in cmake
    assert r'.*/ROOT/.*warning' in cmake
    assert r'"\\[distcc\\]"' in cmake

