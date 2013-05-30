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

from LbNightlyTools.tests.utils import processFile

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

def test_loadXML():
    'Configuration.load(xml)'
    xml = u'''
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
</configuration>
    '''
    expected = {'slot': 'lhcb-lcg-head',
                'description': "head of everything against GAUDI_HEAD, LCGCMT head of all repositories from today's LCG dev slot",
                'projects': [{'name': 'LCGCMT',
                              'version': 'preview',
                              'checkout': 'ignore',
                              'dependencies': [],
                              'overrides': {}},
                             {'name': 'Gaudi',
                              'version': 'HEAD',
                              'dependencies': ['LCGCMT'],
                              'overrides': {}},
                             {'name': 'Online',
                              'version': 'HEAD',
                              'dependencies': ['LCGCMT', 'Gaudi'],
                              'overrides': {}},
                             {'name': 'LHCb',
                              'version': 'HEAD',
                              'dependencies': ['LCGCMT', 'Gaudi', 'Online'],
                              'overrides': {'Det/DetDescSvc': 'v2r2',
                                            'Tools/EventIndexer': 'HEAD'}},
                             {'name': 'Lbcom',
                              'version': 'HEAD',
                              'dependencies': ['LCGCMT', 'Gaudi', 'Online', 'LHCb'],
                              'overrides': {}},
                             {'name': 'Boole',
                              'version': 'HEAD',
                              'dependencies': ['LCGCMT', 'Gaudi', 'Online', 'LHCb', 'Lbcom'],
                              'overrides': {}},
                             {'name': 'Rec',
                              'version': 'HEAD',
                              'dependencies': ['LCGCMT', 'Gaudi', 'Online', 'LHCb', 'Lbcom', 'Boole'],
                              'overrides': {}},
                             {'name': 'Brunel',
                              'version': 'HEAD',
                              'dependencies': ['LCGCMT', 'Gaudi', 'Online', 'LHCb', 'Lbcom', 'Boole', 'Rec'],
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
    found = processFile(xml, load)
    #from pprint import pprint
    #pprint(found)
    #pprint(expected)
    assert found == expected
