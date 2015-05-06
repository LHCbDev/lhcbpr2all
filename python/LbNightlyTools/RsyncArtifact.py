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
Contains scripts fo push or get artifact with rsync
'''
__author__ = 'Colas Pomies <colas.pomies@cern.ch>'

import os
import logging
import LbUtils.Script

from socket import gethostname
from LbNightlyTools.Utils import timeout_call as call, ensureDirs

def execute_rsync(src, dest, includes = [], excludes = [], extra_param = []):

    cmd = ['rsync', '--archive', '--whole-file',
           '--partial-dir=.rsync-partial.%s.%d' %
           (gethostname(), os.getpid()),
           '--delay-updates', '--rsh=ssh']

    for param in extra_param:
        cmd.append(param)

    for include in includes:
        cmd.append('--include=%s' % include)

    for exclude in excludes:
        cmd.append('--exclude=%s' % exclude)

    cmd.append(src + '/')
    cmd.append(dest + '/')

    # create destination directory, if missing
    if ':' in dest:
        host, path = dest.split(':', 1)
        call(['ssh', host, 'mkdir -pv "%s"' % path])
    else:
        ensureDirs([dest])

    logging.info("Rsync call : %s", cmd)

    return call(cmd)

class Script(LbUtils.Script.PlainScript):

    __usage__ = '%prog [options]'
    __version__ = ''

    def defineOpts(self):
        """ User options -- has to be overridden """
        from LbNightlyTools.ScriptsCommon import (addBasicOptions,
                                                  addDashboardOptions)
        addBasicOptions(self.parser)
        addDashboardOptions(self.parser)

        self.parser.add_option('--get-config',
                               action='store_true',
                               dest='get_config',
                               help='Synchronize configs files')

        self.parser.add_option('--get-sources',
                               action='store_true',
                               dest='get_sources',
                               help='Synchronize sources files')
        '''
        self.parser.add_option('--progress',
                               action='store_true',
                               dest='progress',
                               help='Shows progress during rsync')
        '''
        self.parser.add_option('-d', '--destination',
                               action='store',
                               help='Destination folder')

        self.parser.add_option('-s', '--source',
                               action='store',
                               help='Source folder')

        self.parser.set_defaults(get_config=False,
                                 get_sources=False,
                                 source=None,
                                 destination=None)

    def main(self):

        if len(self.args) != 0:
            self.parser.error('wrong number of arguments')

        opts = self.options

        if not opts.source:
            self.log.error("Source folder needs to be defined with -s or --source")
            return 1

        if not opts.destination:
            self.log.error("Destination folder needs to be defined with -d or --destination")
            return 1

        includes_param = []
        excludes_param = []
        extra_param = []

        if opts.get_config:
            includes_param.append("*.json")
            includes_param.append("*.xml")
            excludes_param = ["*"]
        if opts.get_sources:
            includes_param.append("*.src.*")
            includes_param.append("checkout_job_url.txt")
            excludes_param = ["*"]

        if self.log.level <= logging.INFO:
            extra_param = ['--progress']

        return execute_rsync(
            opts.source,
            opts.destination,
            includes_param,
            excludes_param,
            extra_param)
