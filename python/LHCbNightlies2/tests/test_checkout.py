import json
import tempfile
import os

from .. import StackCheckout

def mockCheckout(self, rootdir='.'):
    '''
    Dummy no-op checkout function.
    '''
    pass

class MockFunc(object):
    '''
    Helper class to record the arguments a callback is called with.
    '''
    def __init__(self):
        self.args = None
        self.kwargs = None
    def __call__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

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

    p = ProjectDesc('Gaudi', 'v23r5')
    assert p.name == 'Gaudi'
    assert p.version == 'v23r5'
    assert p.overrides == {}
    assert p._checkout == StackCheckout.defaultCheckout
    assert p.projectDir == 'GAUDI/GAUDI_v23r5'
    assert str(p) == 'Gaudi v23r5'

    p = ProjectDesc('Gaudi', 'head')
    assert p.name == 'Gaudi'
    assert p.version == 'HEAD'
    assert p.overrides == {}
    assert p._checkout == StackCheckout.defaultCheckout
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

def test_parseConfigFile():
    'StackCheckout.parseConfigFile()'

    def doCall(data):
        'helper function'
        fd, path = tempfile.mkstemp()
        f = os.fdopen(fd, 'w')
        try:
            json.dump(data, f)
            f.close()
            return StackCheckout.parseConfigFile(path)
        finally:
            os.remove(path)

    StackCheckout.specialCheckoutFunction = MockFunc()

    s = doCall({'projects':[{"name": "Gaudi",
                             "version": "v23r5",
                             "checkout": "specialCheckoutFunction"},
                            {"name": "LHCb",
                             "version": "v32r5",
                             "overrides": {"GaudiObjDesc": "HEAD",
                                           "GaudiPython": "v12r4",
                                           "Online/RootCnv": None}}]})
    assert s.name == None
    assert len(s.projects) == 2
    p = s.projects[0]
    assert (p.name, p.version) == ('Gaudi', 'v23r5')
    assert p._checkout == StackCheckout.specialCheckoutFunction #@UndefinedVariable
    p = s.projects[1]
    assert (p.name, p.version) == ('LHCb', 'v32r5')
    assert p._checkout == StackCheckout.defaultCheckout
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
