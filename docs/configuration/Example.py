# Example of how the configuration of the nightly builds could look like.

from LbNightlyTools.Configuration import Slot, Project

lhcb_head = Slot('lhcb-head',
                 projects=[Project('Gaudi', 'head', disabled=True),
                           Project('LHCb', 'head')],
                 env=['CMTPROJECTPATH=${LHCBDEV}:${CMTPROJECTPATH}'])

class CMakeSlot(Slot):
    env = ['USE_CMAKE=1',
           'PATH=/opt/CMake/bin:${PATH}']


class Gaudi(Project):
    __url__ = 'http://git.cern.ch/pub/gaudi'

    def commitId(self):
        import re
        if self.version == 'head':
            return master
        elif re.match(r'v[0-9]+', self.version):
            return '{0}/{0}_{1}'.format(self.name.upper(), self.version)
        return self.version.replace('/', '_')

    def checkout(self, rootdir='.', export=False):
        from LbNightlyTools.Checkout import git
        return git(self.__url__, self.commitId(), rootdir=rootdir, export=export)

class LHCb(Project):
    pass

class LHCb_head(LHCb):
    override = {'GaudiObjDesc': 'v4r5',
                'Tools/CondDBUI': None}

# note:
#   Project.__init__(self, name, version, ...)
#   Gaudi.__init__(self, version, ...)
#   LHCb_head.__init__(self, version='head', ...)

# lhcb_cmake = CMakeSlot('lhcb-cmake',
#                        projects=[Gaudi('dev/cmake'),
#                                  LHCb_head(),
#                                  Project('Lbcom', 'head')])
CMakeSlot('lhcb-cmake',
          projects=[Gaudi('dev/cmake'),
                    LHCb_head(),
                    Project('Lbcom', 'head')])


# in the scripts:
#from NightlyConf import lhcb_cmake
from LbNightlyTools.Configuration import slots
# this should try to import some default configuration module
# ... or we import it explicitly
lhcb_cmake = slots['lhcb-cmake']

# lhcb_cmake.json() -> JSON representation of the configuration for the dashboard

lhcb_cmake.rootdir = '/a/b/c'
lhcb_cmake.checkout(export)
# lhcb_cmake.dependencies() -> {'LHCb': ['Gaudi'], 'Lbcom': ['LHCb'], 'Gaudi': []}
# ## How to cache the discovered dependencies?
lhcb_cmake.build(...)
lhcb_cmake.Gaudi.deps.build()
build_results = lhcb_cmake.Gaudi.build(clean=True)
# build_results.warnings ->
#   {'warning: xyz', [(13,16), (24,27), (199,205)],
#    ...}
# build_results.errors -> same as warnings
# build_results.gen_report(dest_dir)
# build_results.json() -> JSON summary for the dashboard
test_results = lhcb_cmake.Gaudi.test()
# similar to the build_results


# ---------------
# packages
# ---------------
from LbNightlyTools.Configuration import Slot, Project, Package

lh = Slot('lhcb-head', [Project('Gaudi', 'head'),
                        Project('LHCb', 'head'),
                        Package('AppConfig', 'v3r199'),
                        Package('WG/CharmConfig', 'v3r16')])

lh.WG_CharmConfig.checkout()
