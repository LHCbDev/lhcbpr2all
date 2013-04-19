import os

from xml.etree import ElementTree as ET
from StringIO import StringIO

# Uncomment to disable the tests.
#__test__ = False

from .. import BuildSlot


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
