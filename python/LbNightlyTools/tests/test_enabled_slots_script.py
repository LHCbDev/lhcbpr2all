##############################################################################
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
__author__ = 'Colas Pomies <colas.pomies@cern.ch>'
__test_mode__ = True

from LbNightlyTools import EnabledSlots

import os
import re
import json

from os.path import normpath, join, exists
from LbNightlyTools.tests.utils import TemporaryDir

_testdata = normpath(join(*([__file__] + [os.pardir] * 4 + ['testdata'])))

_env_bk = dict(os.environ)

def setup():
    global _env_bk
    _env_bk = dict(os.environ)
    os.environ['JENKINS_HOME'] = 'JENKINS_HOME'
    os.environ['flavour'] = 'flavour'

def teardown():
    global _env_bk
    os.environ.clear()
    os.environ.update(_env_bk)

def test_wrong_number_argument():
    with TemporaryDir(chdir=True):
        try:
            EnabledSlots.Script().run([])
            assert False, 'Script should have exited'
        except SystemExit, x:
            assert x.code != 0
            assert len([x for x in os.listdir('.') if re.match(r'^slot-param-.*\.txt', x)]) == 0


def test_no_data():

    with TemporaryDir(chdir=True):
        retval = EnabledSlots.Script().run(['slot-param-{0}.txt'])
        assert retval == 0
        assert len([x for x in os.listdir('.') if re.match(r'^slot-param-.*\.txt', x)]) == 0


def test_no_file():

    with TemporaryDir(chdir=True):
        os.makedirs('./configs')
        retval = EnabledSlots.Script().run(['slot-param-{0}.txt'])
        assert retval == 0
        assert len([x for x in os.listdir('.') if re.match(r'^slot-param-.*\.txt', x)]) == 0

def test_one_file_json_chmod_111():

    conf_data = {'slot': 'lhcb-TEST',
                'description': 'Test for unit test',
                'disabled': False,
                'projects': [],
                'default_platforms': ['x86_64-slc6-gcc48-opt', 'x86_64-slc6-gcc46-opt'],
                'USE_CMT': True}

    with TemporaryDir(chdir=True):
        os.makedirs('./configs')
        with open('configs/lhcb-TEST.json', 'w') as slot_file:
            slot_file.write(json.dumps(conf_data))
        os.chmod('configs/lhcb-TEST.json', 0111)
        slots = EnabledSlots.Script().extractFromJson('lhcb-*.json')
        EnabledSlots.Script().writeFiles(slots, 'slot-param-{0}.txt')
        retval = EnabledSlots.Script().run(['slot-param-{0}.txt'])
        assert retval == 0
        assert exists(join('configs/lhcb-TEST.json'))
        assert len([x for x in os.listdir('.') if re.match(r'^slot-param-.*\.txt', x)]) == 0


def test_one_file_json_disabled_flase():

    conf_data = {'slot': 'lhcb-TEST',
                'description': 'Test for unit test',
                'disabled': False,
                'projects': [],
                'default_platforms': ['x86_64-slc6-gcc48-opt', 'x86_64-slc6-gcc46-opt'],
                'USE_CMT': True}

    with TemporaryDir(chdir=True):
        os.makedirs('./configs')
        with open('configs/lhcb-TEST.json', 'w') as slot_file:
            slot_file.write(json.dumps(conf_data))
        retval = EnabledSlots.Script().run(['slot-param-{0}.txt'])
        assert retval == 0
        assert exists(join('configs/lhcb-TEST.json'))
        assert json.load(open('configs/lhcb-TEST.json')) == conf_data
        assert len([x for x in os.listdir('.') if re.match(r'^slot-param-.*\.txt', x)]) == 1


def test_one_file_json_disabled_true():

    conf_data = {'slot': 'lhcb-TEST',
                'description': 'Test for unit test',
                'disabled': True,
                'projects': [],
                'default_platforms': ['x86_64-slc6-gcc48-opt', 'x86_64-slc6-gcc46-opt'],
                'USE_CMT': True}

    with TemporaryDir(chdir=True):
        os.makedirs('./configs')
        with open('configs/lhcb-TEST.json', 'w') as slot_file:
            slot_file.write(json.dumps(conf_data))
        retval = EnabledSlots.Script().run(['slot-param-{0}.txt'])
        assert retval == 0
        assert exists(join('configs/lhcb-TEST.json'))
        assert json.load(open('configs/lhcb-TEST.json')) == conf_data
        assert len([x for x in os.listdir('.') if re.match(r'^slot-param-.*\.txt', x)]) == 0


def test_one_file_json_no_disabled():

    conf_data = {'slot': 'lhcb-TEST',
                'description': 'Test for unit test',
                'projects': [],
                'default_platforms': ['x86_64-slc6-gcc48-opt', 'x86_64-slc6-gcc46-opt'],
                'USE_CMT': True}

    with TemporaryDir(chdir=True):
        os.makedirs('./configs')
        with open('configs/lhcb-TEST.json', 'w') as slot_file:
            slot_file.write(json.dumps(conf_data))
        retval = EnabledSlots.Script().run(['slot-param-{0}.txt'])
        assert retval == 0
        assert exists(join('configs/lhcb-TEST.json'))
        assert json.load(open('configs/lhcb-TEST.json')) == conf_data
        assert len([x for x in os.listdir('.') if re.match(r'^slot-param-.*\.txt', x)]) == 1


def test_one_file_json_no_slot():

    conf_data = {'description': 'Test for unit test',
                'disabled': False,
                'projects': [],
                'default_platforms': ['x86_64-slc6-gcc48-opt', 'x86_64-slc6-gcc46-opt'],
                'USE_CMT': True}

    with TemporaryDir(chdir=True):
        os.makedirs('./configs')
        with open('configs/lhcb-TEST.json', 'w') as slot_file:
            slot_file.write(json.dumps(conf_data))
        retval = EnabledSlots.Script().run(['slot-param-{0}.txt'])
        assert retval == 0
        assert exists(join('configs/lhcb-TEST.json'))
        assert json.load(open('configs/lhcb-TEST.json')) == conf_data
        assert len([x for x in os.listdir('.') if re.match(r'^slot-param-.*\.txt', x)]) == 1


def test_two_file_json():

    conf_data1 = {'description': 'Test for unit test',
                'disabled': False,
                'projects': [],
                'default_platforms': ['x86_64-slc6-gcc48-opt', 'x86_64-slc6-gcc46-opt'],
                'USE_CMT': True}
    conf_data2 = {'slot': 'lhcb-TEST2',
                'description': 'Test for unit test',
                'disabled': False,
                'projects': [],
                'default_platforms': ['x86_64-slc6-gcc48-opt', 'x86_64-slc6-gcc46-opt'],
                'USE_CMT': True}

    with TemporaryDir(chdir=True):
        os.makedirs('./configs')
        with open('configs/lhcb-TEST1.json', 'w') as slot_file:
            slot_file.write(json.dumps(conf_data1))
        with open('configs/lhcb-TEST2.json', 'w') as slot_file:
            slot_file.write(json.dumps(conf_data2))
        retval = EnabledSlots.Script().run(['slot-param-{0}.txt'])
        assert retval == 0
        assert exists(join('configs/lhcb-TEST1.json'))
        assert exists(join('configs/lhcb-TEST2.json'))
        assert json.load(open('configs/lhcb-TEST1.json')) == conf_data1
        assert json.load(open('configs/lhcb-TEST2.json')) == conf_data2
        assert len([x for x in os.listdir('.') if re.match(r'^slot-param-.*\.txt', x)]) == 2


def test_one_job_xml_disbaled_false():

    test_xml = u'''
    <configuration xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="configuration.xsd">
        <slot disabled="false" hidden="false" name="lhcb-TEST" renice="+2" mails="true" description="lhcb-TEST use for unit TEST">
        </slot>
    </configuration>
    '''
    with TemporaryDir(chdir=True):
        os.makedirs('./configs')
        with open('configs/configuration.xml', 'w') as cfg_file:
            cfg_file.write(test_xml)
        retval = EnabledSlots.Script().run(['slot-param-{0}.txt'])
        assert retval == 0
        assert exists(join('configs/configuration.xml'))
        assert len([x for x in os.listdir('.') if re.match(r'^slot-param-.*\.txt', x)]) == 1


def test_one_job_xml_disabled_true():

    test_xml = u'''
    <configuration xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="configuration.xsd">
        <slot disabled="true" hidden="false" name="lhcb-TEST" renice="+2" mails="true" description="lhcb-TEST use for unit TEST">
        </slot>
    </configuration>
    '''
    with TemporaryDir(chdir=True):
        os.makedirs('./configs')
        with open('configs/configuration.xml', 'w') as cfg_file:
            cfg_file.write(test_xml)
        retval = EnabledSlots.Script().run(['slot-param-{0}.txt'])
        assert retval == 0
        assert exists(join('configs/configuration.xml'))
        assert len([x for x in os.listdir('.') if re.match(r'^slot-param-.*\.txt', x)]) == 0


def test_one_job_xml_no_disabled():

    test_xml = u'''
    <configuration xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="configuration.xsd">
        <slot hidden="false" name="lhcb-TEST" renice="+2" mails="true" description="lhcb-TEST use for unit TEST">
        </slot>
    </configuration>
    '''
    with TemporaryDir(chdir=True):
        os.makedirs('./configs')
        with open('configs/configuration.xml', 'w') as cfg_file:
            cfg_file.write(test_xml)
        retval = EnabledSlots.Script().run(['slot-param-{0}.txt'])
        assert retval == 0
        assert exists(join('configs/configuration.xml'))
        assert len([x for x in os.listdir('.') if re.match(r'^slot-param-.*\.txt', x)]) == 1


def test_two_job_xml():

    test_xml = u'''
    <configuration xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="configuration.xsd">
        <slot disabled="false" hidden="false" name="lhcb-TEST1" renice="+2" mails="true" description="lhcb-TEST1 use for unit TEST">
        </slot>
        <slot disabled="false" hidden="false" name="lhcb-TEST2" renice="+2" mails="true" description="lhcb-TEST2 use for unit TEST">
        </slot>
    </configuration>
    '''
    with TemporaryDir(chdir=True):
        os.makedirs('./configs')
        with open('configs/configuration.xml', 'w') as cfg_file:
            cfg_file.write(test_xml)
        retval = EnabledSlots.Script().run(['slot-param-{0}.txt'])
        assert retval == 0
        assert exists(join('configs/configuration.xml'))
        assert len([x for x in os.listdir('.') if re.match(r'^slot-param-.*\.txt', x)]) == 2


def test_same_job_xml_and_json():

    test_xml = u'''
     <configuration xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="configuration.xsd">
        <slot disabled="false" hidden="false" name="lhcb-TEST" renice="+2" mails="true" description="lhcb-TEST use for unit TEST">
        </slot>
    </configuration>
    '''
    conf_data = {'slot': 'lhcb-TEST',
                'description': 'Test for unit test',
                'disabled': False,
                'projects': [],
                'default_platforms': ['x86_64-slc6-gcc48-opt', 'x86_64-slc6-gcc46-opt'],
                'USE_CMT': True}

    with TemporaryDir(chdir=True):
        os.makedirs('./configs')
        with open('configs/configuration.xml', 'w') as cfg_file:
            cfg_file.write(test_xml)
        with open('configs/lhcb-TEST.json', 'w') as slot_file:
            slot_file.write(json.dumps(conf_data))

        retval = EnabledSlots.Script().run(['slot-param-{0}.txt'])
        assert retval == 0
        assert exists(join('configs/configuration.xml'))
        assert exists(join('configs/lhcb-TEST.json'))
        assert len([x for x in os.listdir('.') if re.match(r'^slot-param-.*\.txt', x)]) == 1


def test_different_job_xml_and_json():

    test_xml = u'''
     <configuration xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="configuration.xsd">
        <slot disabled="false" hidden="false" name="lhcb-TEST1" renice="+2" mails="true" description="lhcb-TEST1 use for unit TEST">
        </slot>
    </configuration>
    '''
    conf_data = {'slot': 'lhcb-TEST2',
                'description': 'Test for unit test',
                'disabled': False,
                'projects': [],
                'default_platforms': ['x86_64-slc6-gcc48-opt', 'x86_64-slc6-gcc46-opt'],
                'USE_CMT': True}

    with TemporaryDir(chdir=True):
        os.makedirs('./configs')
        with open('configs/configuration.xml', 'w') as cfg_file:
            cfg_file.write(test_xml)
        with open('configs/lhcb-TEST.json', 'w') as slot_file:
            slot_file.write(json.dumps(conf_data))

        retval = EnabledSlots.Script().run(['slot-param-{0}.txt'])
        assert retval == 0
        assert exists(join('configs/configuration.xml'))
        assert exists(join('configs/lhcb-TEST.json'))
        assert len([x for x in os.listdir('.') if re.match(r'^slot-param-.*\.txt', x)]) == 2

def test_one_job_param():

    with TemporaryDir(chdir=True):
        retval = EnabledSlots.Script().run(['slot-param-{0}.txt', 'lhcb-test'])
        assert retval == 0
        assert len([x for x in os.listdir('.') if re.match(r'^slot-param-.*\.txt', x)]) == 1


def test_two_job_param():

    with TemporaryDir(chdir=True):
        retval = EnabledSlots.Script().run(['slot-param-{0}.txt', 'lhcb-test', 'lhcb-test2'])
        assert retval == 0
        assert len([x for x in os.listdir('.') if re.match(r'^slot-param-.*\.txt', x)]) == 2
