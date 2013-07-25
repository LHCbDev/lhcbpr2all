#!/usr/bin/env python
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
Generate a basic nightly builds configuration file from a list of projects and
versions.
'''
import LbNightlyTools.Configuration


ERR_EXCEPT = ["distcc\\[",
              "::error::",
              "^ *Error *$"]
WARN_EXCEPT = [".*/boost/.*",
               "^--->> genreflex: WARNING:.*",
               " note:",
               "distcc\\[",
               "Warning\\:\\ The\\ tag\\ (use-distcc|no-pyzip|"
                 "LCG\\_NIGHTLIES\\_BUILD|COVERITY|"
                 "use\\-dbcompression)\\ is\\ not\\ used.*",
               ".*#CMT---.*Warning: Structuring style used.*",
               ".*/Boost/.*warning:.*",
               ".*/ROOT/.*warning:.*",
               ".*stl_algo.h:[0-9]+: warning: array subscript is above array "
                 "bounds"]


import LbUtils.Script
class Script(LbUtils.Script.PlainScript):
    '''
    Given a list of projects and versions, generate a basic configuration file.
    '''
    __usage__ = '%prog [options] project version [project version...]'

    def defineOpts(self):
        '''
        Options specific to this script.
        '''
        self.parser.add_option('-s', '--slot',
                               help='name of the slot to add to the JSON data')
        self.parser.add_option('-b', '--build-id',
                               help='build id to add to the JSON data')
        self.parser.add_option('-o', '--output',
                               help='name of the output file [default "-", '
                                    'i.e. standard output]')
        self.parser.add_option('--cmt', action='store_true',
                               help='configure to use CMT for the build')
        self.parser.set_defaults(slot='lhcb-release',
                                 cmt=False,
                                 output='-')

    def genConfig(self):
        '''
        Return the configuration dictionary.
        '''
        projects = []
        added = []
        # convert from [0, 1, 2, 3, ...] to [(0, 1), (2, 3), ...]
        for proj, vers in zip(self.args[::2], self.args[1::2]):
            if proj in added:
                raise RuntimeError('project %s repeated: each project can '
                                   'appear only once' % proj)
            project = {'name': proj, 'version': vers}

            # FIXME: once LBCORE-146 is fixed, we can remove this hack
            # build the projects in the order they are specified
            if added:
                project['dependencies'] = list(added)

            added.append(proj)

            # we check out Gaudi from git
            if proj == 'Gaudi':
                project['checkout'] = 'git'
                project['checkout_opts'] = {"url":
                                              "http://git.cern.ch/pub/gaudi",
                                            "commit": "GAUDI/GAUDI_" + vers}

            projects.append(project)

        # prepare the configuration dictionary
        config = {'slot': self.options.slot,
                  'description': 'Slot used for releasing projects.',
                  'projects': projects,
                  'USE_CMT': self.options.cmt,
                  'no_patch': True,
                  'error_exceptions': ERR_EXCEPT,
                  'warning_exceptions': WARN_EXCEPT,
                  # FIXME: we need a better way to define the default platforms
                  'default_platforms': ['x86_64-slc5-gcc46-opt',
                                        'x86_64-slc5-gcc46-dbg',
                                        'x86_64-slc6-gcc46-opt',
                                        'x86_64-slc6-gcc46-dbg',
                                        'x86_64-slc6-gcc47-opt',
                                        'x86_64-slc6-gcc47-dbg']
                  }

        return config

    def main(self):
        '''
        Script logic.
        '''

        if len(self.args) % 2 != 0:
            self.parser.error('wrong number of arguments: we need a list of '
                              'projects and their versions')

        try:
            # prepare the configuration dictionary
            config = self.genConfig()
        except RuntimeError, ex:
            self.parser.error(str(ex))


        if self.options.output != '-':
            LbNightlyTools.Configuration.save(self.options.output, config)
        else:
            print LbNightlyTools.Configuration.configToString(config)

        return 0
