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

from LbNightlyTools.tests.utils import processFile, processFileWithName

# Uncomment to disable the tests.
#__test__ = False

from LbNightlyTools import Configuration

def test_loadJSON():
    'Configuration.load(json_file)'
    expected = {'slot': 'slot-name',
                'projects':[{"name": "Gaudi",
                             "version": "v23r5",
                             "checkout": "specialCheckoutFunction"},
                            {"name": "LHCb",
                             "version": "v32r5",
                             "dependencies": ["Gaudi"]}]}

    found = processFile(json.dumps(expected), Configuration.load)
    assert found == expected

def test_loadJSON_2():
    'Configuration.load(json_with_slot)'
    expected = {'projects':[{"name": "Gaudi",
                             "version": "v23r5",
                             "checkout": "specialCheckoutFunction"},
                            {"name": "LHCb",
                             "version": "v32r5",
                             "dependencies": ["Gaudi"]}]}


    found = processFileWithName(json.dumps(expected), 'special-slot.json', Configuration.load)
    expected['slot'] = 'special-slot'
    assert found == expected

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
    <slot name="lhcb-lcg-head" description="lhcb-lcg-head - head of everything against GAUDI_HEAD, LCGCMT head of all repositories from today's LCG dev slot" mails="false" hidden="false" computedependencies="false" disabled="true" renice="+6">
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
                <dependence project="LCGCMT" tag="LCGCMT-preview"/>
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
            <project name="LCGCMT" tag="LCGCMT-preview" headofeverything="false" disabled="true"/>
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
</configuration>
'''

def test_loadXML():
    'Configuration.load(xml)'
    expected = {'slot': 'lhcb-lcg-head',
                'description': "head of everything against GAUDI_HEAD, LCGCMT head of all repositories from today's LCG dev slot",
                'projects': [{'name': 'LCGCMT',
                              'version': 'preview',
                              'checkout': 'ignore',
                              'overrides': {}},
                             {'name': 'Gaudi',
                              'version': 'HEAD',
                              'overrides': {}},
                             {'name': 'Online',
                              'version': 'HEAD',
                              'overrides': {}},
                             {'name': 'LHCb',
                              'version': 'HEAD',
                              'overrides': {'Det/DetDescSvc': 'v2r2',
                                            'Tools/EventIndexer': 'HEAD'}},
                             {'name': 'Lbcom',
                              'version': 'HEAD',
                              'overrides': {}},
                             {'name': 'Boole',
                              'version': 'HEAD',
                              'overrides': {}},
                             {'name': 'Rec',
                              'version': 'HEAD',
                              'overrides': {}},
                             {'name': 'Brunel',
                              'version': 'HEAD',
                              'overrides': {}}],
                'env': ['CMTPROJECTPATH=dir1:dir2/${TODAY}:/afs/cern.ch/lhcb/software/releases',
                        'CMTEXTRATAGS=use-distcc,no-pyzip'],
                'USE_CMT': True,
                'default_platforms': ['x86_64-slc5-gcc43-dbg',
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

    load = lambda path: Configuration.load(path+"#lhcb-lcg-head")
    found = processFile(TEST_XML, load)
    from pprint import pprint
    pprint(found)
    pprint(expected)
    assert found == expected

def test_loadXML_2():
    'Configuration.load(xml) [with LCGCMT-preview]'

    expected = {'slot': 'lhcb-lcg-test',
                'description': "a test",
                'projects': [{'name': 'LCGCMT',
                              'version': 'preview',
                              'checkout': 'ignore',
                              'overrides': {}},
                             {'name': 'Gaudi',
                              'version': 'HEAD',
                              'overrides': {}}],
                'env': ['CMTPROJECTPATH=dir1:dir2/${TODAY}:/afs/cern.ch/lhcb/software/releases',
                        'CMTEXTRATAGS=use-distcc,no-pyzip'],
                'USE_CMT': True,
                'default_platforms': ['x86_64-slc6-gcc47-opt',
                                      'x86_64-slc6-clang32-opt'],
                'error_exceptions': ['distcc\\[', 'assert\\ \\(error'],
                'warning_exceptions': ['\\_\\_shadow\\_\\_\\:\\:\\_\\_', 'was\\ hidden']
                }

    load = lambda path: Configuration.load(path+"#lhcb-lcg-test")
    found = processFile(TEST_XML, load)
    #from pprint import pprint
    #pprint(found)
    #pprint(expected)
    assert found == expected

def test_loadXML_3():
    'Configuration.load(xml) [with lhcb-compatibility*]'

    expected = {'slot': 'lhcb-compatibility-x',
                'description': "testing released software against latest database tags",
                'projects': [{'name': 'Brunel',
                              'version': 'v37r8p4',
                              'overrides': {}},
                             {'name': 'Moore',
                              'version': 'v10r2p4',
                              'overrides': {}},
                             {'name': 'DaVinci',
                              'version': 'v26r3p3',
                              'overrides': {}}],
                'env': ['CMTPROJECTPATH=' +
                          ':'.join(['/afs/cern.ch/lhcb/software/DEV/nightlies',
                                    '/afs/cern.ch/sw/Gaudi/releases',
                                    '/afs/cern.ch/sw/lcg/app/releases',
                                    '/afs/cern.ch/lhcb/software/releases']),
                        'CMTEXTRATAGS=use-distcc,no-pyzip',
                        'GAUDI_QMTEST_DEFAULT_SUITE=compatibility'],
                'USE_CMT': True,
                'default_platforms': ['x86_64-slc5-gcc43-opt',
                                      'x86_64-slc5-gcc43-dbg'],
                'error_exceptions': ['distcc\\[', 'assert\\ \\(error'],
                'warning_exceptions': ['\\_\\_shadow\\_\\_\\:\\:\\_\\_', 'was\\ hidden']
                }

    load = lambda path: Configuration.load(path+"#lhcb-compatibility-x")
    found = processFile(TEST_XML, load)
    #from pprint import pprint
    #pprint(found)
    #pprint(expected)
    assert found == expected

def test_loadXML_4():
    'Configuration.load(xml) [with lhcb-headofeverything]'

    expected = {'slot': 'lhcb-headofeverything',
                'description': "testing headofeverything override flag",
                'projects': [{'name': 'Brunel',
                              'version': 'HEAD',
                              'overrides': {},
                              'checkout_opts': {'recursive_head': False}},
                             {'name': 'Moore',
                              'version': 'v10r2p4',
                              'overrides': {},
                              'checkout_opts': {'recursive_head': True}}],
                'env': ['CMTPROJECTPATH=' +
                          ':'.join(['/afs/cern.ch/lhcb/software/DEV/nightlies',
                                    '/afs/cern.ch/sw/Gaudi/releases',
                                    '/afs/cern.ch/sw/lcg/app/releases',
                                    '/afs/cern.ch/lhcb/software/releases']),
                        'CMTEXTRATAGS=use-distcc,no-pyzip'],
                'USE_CMT': True,
                'default_platforms': ['x86_64-slc6-gcc47-opt'],
                'error_exceptions': ['distcc\\[', 'assert\\ \\(error'],
                'warning_exceptions': ['\\_\\_shadow\\_\\_\\:\\:\\_\\_', 'was\\ hidden']
                }

    load = lambda path: Configuration.load(path+"#lhcb-headofeverything")
    found = processFile(TEST_XML, load)
    from pprint import pprint
    pprint(found)
    pprint(expected)
    assert found == expected

def test_loadXML_5():
    'Configuration.load(xml) [with lhcb-sim]'

    expected = {'slot': 'lhcb-sim',
                'description': "testing Geant4 special case",
                'projects': [{'name': 'Geant4',
                              'version': 'HEAD',
                              'overrides': {},
                              'with_shared': True},
                             {'name': 'Gauss',
                              'version': 'HEAD',
                              'overrides': {}}],
                'env': ['CMTPROJECTPATH=' +
                          ':'.join(['/afs/cern.ch/lhcb/software/DEV/nightlies',
                                    '/afs/cern.ch/sw/Gaudi/releases',
                                    '/afs/cern.ch/sw/lcg/app/releases',
                                    '/afs/cern.ch/lhcb/software/releases']),
                        'CMTEXTRATAGS=use-distcc,no-pyzip'],
                'USE_CMT': True,
                'default_platforms': ['x86_64-slc6-gcc48-opt'],
                'error_exceptions': ['distcc\\[', 'assert\\ \\(error'],
                'warning_exceptions': ['\\_\\_shadow\\_\\_\\:\\:\\_\\_', 'was\\ hidden']
                }

    load = lambda path: Configuration.load(path+"#lhcb-sim")
    found = processFile(TEST_XML, load)
    from pprint import pprint
    pprint(found)
    pprint(expected)
    assert found == expected
