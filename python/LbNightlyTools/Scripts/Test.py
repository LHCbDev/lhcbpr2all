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
import json
import codecs
from datetime import datetime

from LbNightlyTools.Utils import chdir, TaskQueue
from LbNightlyTools.Scripts.Build import unpackArtifacts, wipeDir

from LbNightlyTools.Scripts.Common import BaseScript
class Script(BaseScript):
    '''
    Script to test the projects described in a slot configuration.
    '''

    def main(self):
        '''
        Script main logic.
        '''

        self._setup(json_type='tests-result')

        opts = self.options

        # prepare build directory
        if opts.clean:
            wipeDir(self.build_dir)
        if not opts.no_unpack:
            unpackArtifacts(self.artifacts_dir, self.build_dir)

        if self.options.rsync_dest:
            tasks = TaskQueue()
        else:
            tasks = None

        # run tests
        with chdir(self.build_dir):
            def before(proj):
                self.dump_json({'project': proj.name,
                                'started': datetime.now().isoformat()})
            for proj, _result in self.slot.testGen(projects=opts.projects, before=before):
                html_src = self._buildDir(proj,
                                          'build.{}'.format(self.platform),
                                          'html')
                summary_json = os.path.join(html_src, 'summary.json')
                html_dst = self._summaryDir(proj, 'html')
                if os.path.exists(html_dst):
                    shutil.rmtree(html_dst)
                if os.path.exists(html_src):
                    shutil.copytree(html_src, html_dst)
                try:
                    results = json.load(codecs.open(summary_json,
                                                    'rb', 'utf-8'))
                except: # ignore errors reading summary file
                    results = []
                self.dump_json({'project': proj.name,
                                'completed': datetime.now().isoformat(),
                                'results': results})
                if tasks:
                    tasks.add(self.deploy_artifacts)

        if tasks:
            self.log.debug('waiting for pending tasks')
            tasks.join()

        return 0
