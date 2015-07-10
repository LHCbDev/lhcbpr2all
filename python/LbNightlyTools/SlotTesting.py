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
'''
Module containing the classes and functions used to test a
"Nightly Build Slot".
'''
__author__ = 'Marco Clemencic <marco.clemencic@cern.ch>'

import os
import shutil

from LbNightlyTools.Utils import chdir
from LbNightlyTools.RsyncManager import execute_rsync
from LbNightlyTools.BuildSlot import unpackArtifacts, wipeDir

from LbNightlyTools.ScriptsCommon import BaseScript
class Script(BaseScript):
    '''
    Script to test the projects described in a slot configuration.
    '''

    def main(self):
        '''
        Script main logic.
        '''

        self._setup()

        opts = self.options

        # prepare build directory
        if opts.clean:
            wipeDir(self.build_dir)
        if not opts.no_unpack:
            unpackArtifacts(self.artifacts_dir, self.build_dir)

        # run tests
        with chdir(self.build_dir):
            for proj, _result in self.slot.testGen(projects=opts.projects):
                html_src = self._buildDir(proj,
                                          'build.{}'.format(self.platform),
                                          'html')
                html_dst = self._summaryDir(proj, 'html')
                if os.path.exists(html_dst):
                    shutil.rmtree(html_dst)
                if os.path.exists(html_src):
                    shutil.copytree(html_src, html_dst)

        # FIXME: execute_rsync

        return 0
