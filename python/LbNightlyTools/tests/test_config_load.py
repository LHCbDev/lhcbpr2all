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

import os
import json

from LbNightlyTools.tests.utils import processFile
from LbNightlyTools.tests.utils import TemporaryDir

from LbNightlyTools import Configuration

def show(left, right, width=80, headers=None):
    '''
    Pretty print two objects side by side, highlighting the differences.
    '''
    from pprint import pformat
    from itertools import izip
    half_width = (width - 3) / 2
    left_lines = pformat(left, width=half_width).splitlines()
    right_lines = pformat(right, width=half_width).splitlines()

    to_extend = left_lines if len(left_lines) < len(right_lines) else right_lines
    to_extend.extend([''] * abs(len(right_lines) - len(left_lines)))

    format_str = '{{0:<{0}}} {{2}} {{1:<{0}}}'.format(half_width)
    def format_line(a, b):
        return format_str.format(a, b, ' ' if a == b else '|')

    if headers:
        print format_line(*headers)
        print width * '-'

    print '\n'.join(format_line(a, b) for a, b in izip(left_lines, right_lines))

def assert_equals(found, expected):
    show(found, expected, width=120, headers=('found', 'expected'))
    assert found == expected

def add_defaults(expected):
    '''
    Helper to avoid hardcoding everywhere default values.
    '''
    slot_defaults = {'packages': [],
                     'description': 'Generic nightly build slot.',
                     'build_tool': 'cmake',
                     'build_id': 0,
                     'disabled': False,
                     'env': [],
                     'preconditions': [],
                     'error_exceptions': [],
                     'warning_exceptions': []}
    project_defaults = {'checkout': 'getpack',
                        'checkout_opts': {},
                        'disabled': False,
                        'env': [],
                        'overrides': {},
                        'dependencies': [],
                        'with_shared': False}
    package_defaults = {'checkout': 'getpack',
                        'container': 'DBASE'}

    for k in slot_defaults:
        if k not in expected:
            expected[k] = slot_defaults[k]

    for project in expected['projects']:
        for k in project_defaults:
            if k not in project:
                project[k] = project_defaults[k]

    for package in expected.get('packages', []):
        for k in package_defaults:
            if k not in package:
                package[k] = package_defaults[k]


def test_loadJSON():
    'Configuration.load(json_file)'
    data ={'slot': 'slot-name',
           'projects': [{'name': 'Gaudi',
                         'version': 'v23r5'},
                        {'dependencies': ['Gaudi'],
                         'name': 'LHCb',
                         'version': 'v32r5'}]}
    expected = {'build_tool': 'cmake',
                'slot': 'slot-name',
                'projects':[{'checkout': 'gaudi',
                             'name': u'Gaudi',
                             'version': u'v23r5'},
                            {'name': u'LHCb',
                             'version': u'v32r5',
                             'dependencies': [u'Gaudi']}]}
    add_defaults(expected)

    found = processFile(json.dumps(data), Configuration.parse).toDict()
    assert_equals(found, expected)

def test_loadJSON_2():
    'Configuration.load(json_with_slot)'
    data = {'projects':[{"name": "Gaudi",
                         "version": "v23r5"},
                        {"name": "LHCb",
                         "version": "v32r5",
                         "dependencies": ["Gaudi"]}],
            'cmake_cache': {'KEY': 'VALUE'}}
    expected = {'slot': 'special-slot',
                'projects':[{"name": u"Gaudi",
                             "version": u"v23r5",
                             "checkout": "gaudi"},
                            {"name": u"LHCb",
                             "version": u"v32r5",
                             "dependencies": [u"Gaudi"]}],
                'build_tool': 'cmake',
                'cmake_cache': {'KEY': 'VALUE'}}
    add_defaults(expected)

    with TemporaryDir() as path:
        filepath = os.path.join(path, 'special-slot.json')
        with open(filepath, 'w') as f:
            f.write(json.dumps(data))
        slot = Configuration.getSlot('special-slot', path)
        found = slot.toDict()

    assert_equals(slot.cache_entries, expected['cmake_cache'])
    print ''
    assert_equals(found, expected)

def test_loadJSON_3():
    'JSON with data packages'
    data = {'slot': 'slot-with-packages',
            'packages': [
                         {
                          'checkout_opts': { 'export': True },
                          'name': 'ProdConf',
                          'version': 'v1r19'
                          },
                         {
                          'checkout_opts': { 'export': True },
                          'container': 'PARAM',
                          'name': 'TMVAWeights',
                          'version': 'v1r4'
                          }
                         ],
            'projects': []
            }
    expected = dict(data)
    add_defaults(expected)
    expected['projects'] = [{'checkout': 'ignore',
                             'disabled': False,
                             'name': 'DBASE',
                             'no_test': True,
                             'version': 'None'},
                            {'checkout': 'ignore',
                             'disabled': False,
                             'name': 'PARAM',
                             'no_test': True,
                             'version': 'None'},
                            ]

    slot = Configuration.Slot.fromDict(data)
    found = slot.toDict()

    # order of projects and packages is not relevant in this case
    found['projects'].sort()
    found['packages'].sort()
    expected['projects'].sort()
    expected['packages'].sort()

    assert_equals(found, expected)


TEST_XML = u'''
<configuration xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="configuration.xsd">
    <general>
        <ignore>
            <error value="distcc["/>
            <error value="assert (error"/>
            <warning value="__shadow__::__"/>
            <warning value="was hidden"/>
        </ignore>
    </general>
    <slot name="lhcb-lcg-head" description="lhcb-lcg-head - head of everything against GAUDI_HEAD, LCGCMT head of all repositories from today's LCG dev slot" mails="false" hidden="false" computedependencies="false" disabled="true" renice="+6" use_cmake="false">
        <cmtprojectpath>
            <path value="dir1"/>
            <path value="dir2/%DAY%"/>
            <path value="/afs/cern.ch/lhcb/software/releases"/>
        </cmtprojectpath>
        <platforms>
            <platform name="x86_64-slc5-gcc43-dbg"/>
            <platform name="i686-slc5-gcc43-opt"/>
            <platform name="x86_64-slc6-gcc46-opt"/>
            <platform name="x86_64-slc6-gcc46-dbg"/>
            <platform name="x86_64-slc6-gcc47-opt"/>
            <platform name="x86_64-slc6-clang32-opt"/>
        </platforms>
        <waitfor flag="/afs/cern.ch/sw/lcg/app/nightlies/dev/%DAY%/isDone-%PLATFORM%"/>
        <cmtextratags value="use-distcc,no-pyzip"/>
        <projects>
            <project name="Gaudi" tag="GAUDI_HEAD" headofeverything="true">
                <dependence project="LCGCMT" tag="LCGCMT_preview"/>
            </project>
            <project name="Online" tag="ONLINE_HEAD" headofeverything="true"/>
            <project name="LHCb" tag="LHCB_HEAD" headofeverything="true">
                <change package="Det/DetDescSvc" value="v2r2"/>
                <addon package="Tools/EventIndexer" value="HEAD"/>
            </project>
            <project name="Lbcom" tag="LBCOM_HEAD" headofeverything="true"/>
            <project name="Boole" tag="BOOLE_HEAD" headofeverything="true"/>
            <project name="Rec" tag="REC_HEAD" headofeverything="true"/>
            <project name="Brunel" tag="BRUNEL_HEAD" headofeverything="true"/>
        </projects>
    </slot>
    <slot name="lhcb-lcg-test" description="a test" mails="false" hidden="false" computedependencies="false" disabled="true" renice="+6">
        <cmtprojectpath>
            <path value="dir1"/>
            <path value="dir2/%DAY%"/>
            <path value="/afs/cern.ch/lhcb/software/releases"/>
        </cmtprojectpath>
        <platforms>
            <platform name="x86_64-slc6-gcc47-opt"/>
            <platform name="x86_64-slc6-clang32-opt"/>
        </platforms>
        <cmtextratags value="use-distcc,no-pyzip"/>
        <projects>
            <project name="LCGCMT" tag="LCGCMT_preview" headofeverything="false" disabled="true"/>
            <project name="Gaudi" tag="GAUDI_HEAD" headofeverything="true">
            </project>
        </projects>
    </slot>
    <slot name="lhcb-compatibility-x" description="lhcb-compatibility-x - testing released software against latest database tags" mails="false" hidden="false" computedependencies="false" disabled="true" renice="+6">
        <paths>
            <path value="%BUILDROOT%/nightlies/%SLOT%/%DAY%/%CMTCONFIG%" name="builddir"/>
            <path value="%BUILDROOT%/builders/%SLOT%" name="buildersdir"/>
            <path value="%AFSROOT%/cern.ch/lhcb/software/nightlies/%SLOT%/%DAY%" name="releasedir"/>
            <path value="%AFSROOT%/cern.ch/lhcb/software/nightlies/www/logs/%SLOT%" name="wwwdir"/>
        </paths>
        <cmtprojectpath>
            <path value="/afs/cern.ch/lhcb/software/DEV/nightlies"/>
            <path value="/afs/cern.ch/sw/Gaudi/releases"/>
            <path value="/afs/cern.ch/sw/lcg/app/releases"/>
            <path value="/afs/cern.ch/lhcb/software/releases"/>
        </cmtprojectpath>
        <platforms>
            <platform name="x86_64-slc5-gcc43-opt"/>
            <platform name="x86_64-slc5-gcc43-dbg"/>
        </platforms>
        <cmtextratags value="use-distcc,no-pyzip"/>
        <days mon="false" tue="false" wed="false" thu="false" fri="false" sat="false" sun="false"/>
        <projects>
            <project name="Brunel" tag="BRUNEL_v37r8p4"/>
            <project name="Moore" tag="MOORE_v10r2p4"/>
            <project name="DaVinci" tag="DAVINCI_v26r3p3"/>
        </projects>
    </slot>
    <slot name="lhcb-headofeverything" description="testing headofeverything override flag" mails="false" hidden="false" computedependencies="false" disabled="true" renice="+6">
        <paths>
            <path value="%BUILDROOT%/nightlies/%SLOT%/%DAY%/%CMTCONFIG%" name="builddir"/>
            <path value="%BUILDROOT%/builders/%SLOT%" name="buildersdir"/>
            <path value="%AFSROOT%/cern.ch/lhcb/software/nightlies/%SLOT%/%DAY%" name="releasedir"/>
            <path value="%AFSROOT%/cern.ch/lhcb/software/nightlies/www/logs/%SLOT%" name="wwwdir"/>
        </paths>
        <cmtprojectpath>
            <path value="/afs/cern.ch/lhcb/software/DEV/nightlies"/>
            <path value="/afs/cern.ch/sw/Gaudi/releases"/>
            <path value="/afs/cern.ch/sw/lcg/app/releases"/>
            <path value="/afs/cern.ch/lhcb/software/releases"/>
        </cmtprojectpath>
        <platforms>
            <platform name="x86_64-slc6-gcc47-opt"/>
        </platforms>
        <cmtextratags value="use-distcc,no-pyzip"/>
        <days mon="false" tue="false" wed="false" thu="false" fri="false" sat="false" sun="false"/>
        <projects>
            <project name="Brunel" tag="BRUNEL_HEAD" headofeverything="false"/>
            <project name="Moore" tag="MOORE_v10r2p4" headofeverything="true"/>
        </projects>
    </slot>
    <slot name="lhcb-sim" description="testing Geant4 special case">
        <cmtprojectpath>
            <path value="/afs/cern.ch/lhcb/software/DEV/nightlies"/>
            <path value="/afs/cern.ch/sw/Gaudi/releases"/>
            <path value="/afs/cern.ch/sw/lcg/app/releases"/>
            <path value="/afs/cern.ch/lhcb/software/releases"/>
        </cmtprojectpath>
        <platforms>
            <platform name="x86_64-slc6-gcc48-opt"/>
        </platforms>
        <cmtextratags value="use-distcc,no-pyzip"/>
        <days mon="false" tue="false" wed="false" thu="false" fri="false" sat="false" sun="false"/>
        <projects>
            <project name="Geant4" tag="GEANT4_HEAD" />
            <project name="Gauss" tag="GAUSS_HEAD" />
        </projects>
    </slot>
    <slot name="lhcb-cmake" description="CMake-enabled slot" use_cmake="true">
        <cmtprojectpath>
            <path value="/afs/cern.ch/lhcb/software/releases"/>
        </cmtprojectpath>
        <platforms>
            <platform name="x86_64-slc6-gcc49-opt"/>
        </platforms>
        <projects>
            <project name="LCGCMT" tag="LCGCMT_preview" headofeverything="false" disabled="true"/>
            <project name="Gaudi" tag="GAUDI_HEAD" headofeverything="true">
            </project>
        </projects>
    </slot>
</configuration>
'''
def config_parse_xml_check(name, expected):
    add_defaults(expected)
    parse = lambda path: Configuration.parse('{0}#{1}'.format(path, name))
    found = processFile(TEST_XML, parse).toDict()
    assert_equals(found, expected)


def test_loadXML():
    'Configuration.load(xml)'
    expected = {'slot': 'lhcb-lcg-head',
                'description': "head of everything against GAUDI_HEAD, LCGCMT head of all repositories from today's LCG dev slot",
                'projects': [{'name': 'LCGCMT',
                              'version': 'preview',
                              'checkout': 'ignore',
                              'disabled': True},
                             {'name': 'Gaudi',
                              'version': 'HEAD',
                              'checkout': 'gaudi'},
                             {'name': 'Online',
                              'version': 'HEAD'},
                             {'name': 'LHCb',
                              'version': 'HEAD',
                              'overrides': {'Det/DetDescSvc': 'v2r2',
                                            'Tools/EventIndexer': 'HEAD'}},
                             {'name': 'Lbcom',
                              'version': 'HEAD'},
                             {'name': 'Boole',
                              'version': 'HEAD'},
                             {'name': 'Rec',
                              'version': 'HEAD'},
                             {'name': 'Brunel',
                              'version': 'HEAD'}],
                'env': ['CMTPROJECTPATH=dir1:dir2/${TODAY}:/afs/cern.ch/lhcb/software/releases',
                        'CMTEXTRATAGS=use-distcc,no-pyzip'],
                'build_tool': 'cmt',
                'platforms': ['x86_64-slc5-gcc43-dbg',
                              'i686-slc5-gcc43-opt',
                              'x86_64-slc6-gcc46-opt',
                              'x86_64-slc6-gcc46-dbg',
                              'x86_64-slc6-gcc47-opt',
                              'x86_64-slc6-clang32-opt'],
                'preconditions': [{'name': 'waitForFile',
                                   'args': {'path': '/afs/cern.ch/sw/lcg/app/nightlies/dev/${TODAY}/isDone-${CMTCONFIG}'}}],
                'error_exceptions': ['distcc\\[', 'assert\\ \\(error'],
                'warning_exceptions': ['\\_\\_shadow\\_\\_\\:\\:\\_\\_', 'was\\ hidden']
                }

    config_parse_xml_check('lhcb-lcg-head', expected)


def test_loadXML_2():
    'Configuration.load(xml) [with LCGCMT_preview]'

    expected = {'slot': 'lhcb-lcg-test',
                'description': "a test",
                'projects': [{'name': 'LCGCMT',
                              'version': 'preview',
                              'checkout': 'ignore',
                              'disabled': True},
                             {'name': 'Gaudi',
                              'version': 'HEAD',
                              'checkout': 'gaudi'}],
                'env': ['CMTPROJECTPATH=dir1:dir2/${TODAY}:/afs/cern.ch/lhcb/software/releases',
                        'CMTEXTRATAGS=use-distcc,no-pyzip'],
                'build_tool': 'cmt',
                'platforms': ['x86_64-slc6-gcc47-opt',
                              'x86_64-slc6-clang32-opt'],
                'error_exceptions': ['distcc\\[', 'assert\\ \\(error'],
                'warning_exceptions': ['\\_\\_shadow\\_\\_\\:\\:\\_\\_', 'was\\ hidden']
                }

    config_parse_xml_check('lhcb-lcg-test', expected)


def test_loadXML_3():
    'Configuration.load(xml) [with lhcb-compatibility*]'

    expected = {'slot': 'lhcb-compatibility-x',
                'description': "testing released software against latest database tags",
                'projects': [{'name': 'Brunel',
                              'version': 'v37r8p4'},
                             {'name': 'Moore',
                              'version': 'v10r2p4'},
                             {'name': 'DaVinci',
                              'version': 'v26r3p3'}],
                'env': ['CMTPROJECTPATH=' +
                          ':'.join(['/afs/cern.ch/lhcb/software/DEV/nightlies',
                                    '/afs/cern.ch/sw/Gaudi/releases',
                                    '/afs/cern.ch/sw/lcg/app/releases',
                                    '/afs/cern.ch/lhcb/software/releases']),
                        'CMTEXTRATAGS=use-distcc,no-pyzip',
                        'GAUDI_QMTEST_DEFAULT_SUITE=compatibility'],
                'build_tool': 'cmt',
                'platforms': ['x86_64-slc5-gcc43-opt',
                              'x86_64-slc5-gcc43-dbg'],
                'error_exceptions': ['distcc\\[', 'assert\\ \\(error'],
                'warning_exceptions': ['\\_\\_shadow\\_\\_\\:\\:\\_\\_', 'was\\ hidden']
                }

    config_parse_xml_check('lhcb-compatibility-x', expected)

def test_loadXML_4():
    'Configuration.load(xml) [with lhcb-headofeverything]'

    expected = {'slot': 'lhcb-headofeverything',
                'description': "testing headofeverything override flag",
                'projects': [{'name': 'Brunel',
                              'version': 'HEAD',
                              'checkout_opts': {'recursive_head': False}},
                             {'name': 'Moore',
                              'version': 'v10r2p4',
                              'checkout_opts': {'recursive_head': True}}],
                'env': ['CMTPROJECTPATH=' +
                          ':'.join(['/afs/cern.ch/lhcb/software/DEV/nightlies',
                                    '/afs/cern.ch/sw/Gaudi/releases',
                                    '/afs/cern.ch/sw/lcg/app/releases',
                                    '/afs/cern.ch/lhcb/software/releases']),
                        'CMTEXTRATAGS=use-distcc,no-pyzip'],
                'build_tool': 'cmt',
                'platforms': ['x86_64-slc6-gcc47-opt'],
                'error_exceptions': ['distcc\\[', 'assert\\ \\(error'],
                'warning_exceptions': ['\\_\\_shadow\\_\\_\\:\\:\\_\\_', 'was\\ hidden']
                }

    config_parse_xml_check('lhcb-headofeverything', expected)


def test_loadXML_5():
    'Configuration.load(xml) [with lhcb-sim]'

    expected = {'slot': 'lhcb-sim',
                'description': "testing Geant4 special case",
                'projects': [{'name': 'Geant4',
                              'version': 'HEAD',
                              'with_shared': True},
                             {'name': 'Gauss',
                              'version': 'HEAD'}],
                'env': ['CMTPROJECTPATH=' +
                          ':'.join(['/afs/cern.ch/lhcb/software/DEV/nightlies',
                                    '/afs/cern.ch/sw/Gaudi/releases',
                                    '/afs/cern.ch/sw/lcg/app/releases',
                                    '/afs/cern.ch/lhcb/software/releases']),
                        'CMTEXTRATAGS=use-distcc,no-pyzip'],
                'build_tool': 'cmt',
                'platforms': ['x86_64-slc6-gcc48-opt'],
                'error_exceptions': ['distcc\\[', 'assert\\ \\(error'],
                'warning_exceptions': ['\\_\\_shadow\\_\\_\\:\\:\\_\\_', 'was\\ hidden']
                }

    config_parse_xml_check('lhcb-sim', expected)


def test_loadXML_6():
    'Configuration.load(xml) [with CMake]'

    expected = {'build_tool': 'cmake',
                'description': "CMake-enabled slot",
                'env': ['CMTPROJECTPATH=/afs/cern.ch/lhcb/software/releases'],
                'error_exceptions': ['distcc\\[', 'assert\\ \\(error'],
                'platforms': ['x86_64-slc6-gcc49-opt'],
                'projects': [{'name': 'LCGCMT',
                              'checkout': 'ignore',
                              'disabled': True,
                              'version': 'preview',
                              },
                             {'name': 'Gaudi',
                              'checkout': 'gaudi',
                              'version': 'HEAD',
                              }],
                'slot': 'lhcb-cmake',
                'warning_exceptions': ['\\_\\_shadow\\_\\_\\:\\:\\_\\_', 'was\\ hidden'],
                }

    config_parse_xml_check('lhcb-cmake', expected)

def test_loadPy_1():
    'Configuration.getSlot from Python'
    script = '''from LbNightlyTools.Configuration import *
Slot('special-slot-from-python',
     desc='Special slot described directly in Python',
     projects=[Project('Gaudi', 'v23r5'),
               Project('LHCb', 'v32r5', dependencies=['Gaudi'])])
'''
    expected = {'slot': 'special-slot-from-python',
                'description': 'Special slot described directly in Python',
                'projects': [{"name": "Gaudi",
                             "version": "v23r5",
                             "checkout": "gaudi"},
                            {"name": "LHCb",
                             "version": "v32r5",
                             "dependencies": ["Gaudi"]}]}
    add_defaults(expected)

    if 'special-slot-from-python' in Configuration.slots:
        del Configuration.slots['special-slot-from-python']
    assert 'special-slot-from-python' not in Configuration.slots

    with TemporaryDir() as path:
        filepath = os.path.join(path, 'configuration.py')
        with open(filepath, 'w') as f:
            f.write(script)
        slot = Configuration.getSlot('special-slot-from-python', path)
        found = slot.toDict()

    assert_equals(found, expected)
