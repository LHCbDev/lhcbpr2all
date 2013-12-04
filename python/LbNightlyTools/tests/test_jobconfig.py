'''
Created on Jan 8, 2014

@author: Ben Couturier
'''
import unittest

from LbNightlyTools.Utils import JenkinsTest

class Test(unittest.TestCase):

    def test_simple_withlabel(self):
        'JenkinsTest'
        teststr = 'lhcb-testing.74.LHCb.x86_64-slc5-gcc46-opt.mylabel'
        test = JenkinsTest.fromJenkinsString(teststr)
        assert test.slot == 'lhcb-testing'
        assert test.slot_build_id == "74"
        assert test.project == 'LHCb'
        assert test.platform == 'x86_64-slc5-gcc46-opt'
        assert test.os_label == 'mylabel'

    def test_simple_nolabel(self):
        'JenkinsTest'
        teststr = 'lhcb-testing.74.LHCb.x86_64-slc5-gcc46-opt'
        test = JenkinsTest.fromJenkinsString(teststr)
        assert test.os_label == 'slc5'

    def test_simple_withgroup(self):
        'JenkinsTest'
        teststr = 'lhcb-testing.74.LHCb.x86_64-slc5-gcc46-opt.mylabel.mygroup'
        test = JenkinsTest.fromJenkinsString(teststr)
        assert test.os_label == 'mylabel'
        assert test.testgroup == 'mygroup'

    def test_simple_withgroup_nolabel(self):
        'JenkinsTest'
        teststr = 'lhcb-testing.74.LHCb.x86_64-slc5-gcc46-opt.none.mygroup'
        test = JenkinsTest.fromJenkinsString(teststr)
        assert test.os_label == "slc5"
        assert test.testgroup == 'mygroup'

    def test_simple_withrunner(self):
        'JenkinsTest'
        teststr = 'lhcb-testing.74.LHCb.x86_64-slc5-gcc46-opt.mylabel.mygroup.myrunner'
        test = JenkinsTest.fromJenkinsString(teststr)
        assert test.os_label == 'mylabel'
        assert test.testgroup == 'mygroup'
        assert test.testrunner == 'myrunner'

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()