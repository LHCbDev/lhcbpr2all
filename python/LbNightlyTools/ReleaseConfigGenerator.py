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

# FIXME: we need a better way to define the default platforms
DEFAULT_PLATFORMS = 'x86_64-slc6-gcc48-opt,x86_64-slc6-gcc48-dbg'

# get the correct case for projects
try:
    from LbConfiguration.Project import project_names as PROJECT_NAMES
except ImportError:
    # if we cannot find the list of names, we use a minimal hardcoded list
    PROJECT_NAMES = [ "LHCb", "DaVinci" ]

# convert the names to a a conversion dictionary
PROJECT_NAMES = dict((name.lower(), name) for name in PROJECT_NAMES)
def fixProjectCase(name):
    '''
    Convert a project name to it's canonical case.

    >>> fixProjectCase('GAUDI')
    'Gaudi'
    >>> fixProjectCase('davinci')
    'DaVinci'
    >>> fixProjectCase('uNkNoWn')
    'Unknown'
    '''
    return PROJECT_NAMES.get(name.lower(), name.capitalize())

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
        self.parser.add_option('--platforms',
                               help='space or comma -separated list of '
                                    'platforms required [default: %default]')
        self.parser.set_defaults(slot='lhcb-release',
                                 cmt=False,
                                 output='-',
                                 platforms=DEFAULT_PLATFORMS)

    def genConfig(self):
        '''
        Return the configuration dictionary.
        '''
        projects = []
        added = []
        # convert from [0, 1, 2, 3, ...] to [(0, 1), (2, 3), ...]
        for proj, vers in zip(self.args[::2], self.args[1::2]):
            proj = fixProjectCase(proj)
            if proj in added:
                raise RuntimeError('project %s repeated: each project can '
                                   'appear only once' % proj)
            project = {'name': proj, 'version': vers}

            added.append(proj)

            # we check out Gaudi from git
            if proj == 'Gaudi':
                project['checkout'] = 'git'
                project['checkout_opts'] = {"url":
                                              "http://git.cern.ch/pub/gaudi",
                                            "commit": "GAUDI/GAUDI_" + vers}

            projects.append(project)

        default_platforms = (self.options.platforms.replace(',', ' ')
                             .strip().split())

        # prepare the configuration dictionary
        config = {'slot': self.options.slot,
                  'description': 'Slot used for releasing projects.',
                  'projects': projects,
                  'USE_CMT': self.options.cmt,
                  'no_patch': True,
                  'error_exceptions': ERR_EXCEPT,
                  'warning_exceptions': WARN_EXCEPT,
                  'default_platforms': default_platforms
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
