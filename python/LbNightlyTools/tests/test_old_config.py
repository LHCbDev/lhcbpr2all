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

import json

from LbNightlyTools.tests.utils import processFile, processFileWithName

from LbNightlyTools import Configuration

from LbNightlyTools.tests.test_config_load import TEST_XML, assert_equals

def config_parse_xml_check(name, expected):
    load = lambda path: Configuration.load('{0}#{1}'.format(path, name))
    found = processFile(TEST_XML, load)
    assert_equals(found, expected)


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
    assert_equals(found, expected)

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
    assert_equals(found, expected)

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
                              'checkout': 'gaudi',
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
    config_parse_xml_check('lhcb-lcg-head', expected)

def test_loadXML_2():
    'Configuration.load(xml) [with LCGCMT_preview]'

    expected = {'slot': 'lhcb-lcg-test',
                'description': "a test",
                'projects': [{'name': 'LCGCMT',
                              'version': 'preview',
                              'checkout': 'ignore',
                              'disabled': True,
                              'overrides': {}},
                             {'name': 'Gaudi',
                              'version': 'HEAD',
                              'checkout': 'gaudi',
                              'overrides': {}}],
                'env': ['CMTPROJECTPATH=dir1:dir2/${TODAY}:/afs/cern.ch/lhcb/software/releases',
                        'CMTEXTRATAGS=use-distcc,no-pyzip'],
                'USE_CMT': True,
                'default_platforms': ['x86_64-slc6-gcc47-opt',
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
    config_parse_xml_check('lhcb-compatibility-x', expected)

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
    config_parse_xml_check('lhcb-headofeverything', expected)

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
    config_parse_xml_check('lhcb-sim', expected)

def test_loadXML_6():
    'Configuration.load(xml) [with CMake]'

    expected = {'slot': 'lhcb-cmake',
                'description': "CMake-enabled slot",
                'projects': [{'name': 'LCGCMT',
                              'version': 'preview',
                              'checkout': 'ignore',
                              'disabled': True,
                              'overrides': {}},
                             {'name': 'Gaudi',
                              'version': 'HEAD',
                              'checkout': 'gaudi',
                              'overrides': {}}],
                'env': ['CMTPROJECTPATH=/afs/cern.ch/lhcb/software/releases'],
                'default_platforms': ['x86_64-slc6-gcc49-opt'],
                'error_exceptions': ['distcc\\[', 'assert\\ \\(error'],
                'warning_exceptions': ['\\_\\_shadow\\_\\_\\:\\:\\_\\_', 'was\\ hidden']
                }
    config_parse_xml_check('lhcb-cmake', expected)
