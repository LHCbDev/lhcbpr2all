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
Common utility functions used in scripts.
'''
__author__ = 'Marco Clemencic <marco.clemencic@cern.ch>'

import os

def addBasicOptions(parser):
    '''
    Add some basic (common) options to the option parser (optparse.OptionParser
    instance).
    '''
    parser.add_option('--build-id',
                      action='store',
                      help='string to add to the tarballs of the build to '
                           'distinguish them from others, the string can '
                           'be a format string using the parameter '
                           '"slot" [default: %default]')

    parser.add_option('--artifacts-dir',
                      action='store', metavar='DIR',
                      help='directory where to store the artifacts')

    parser.add_option('--projects',
                      action='store',
                      help='comma-separated list of projects to consider'
                           ' [default: all]')

    parser.set_defaults(build_id='{slot}',
                        artifacts_dir='artifacts')
    return parser

def addBuildDirOptions(parser):
    '''
    Add build directory specific options to the parser.
    '''
    from optparse import OptionGroup
    group = OptionGroup(parser, "Build Dir Options")

    group.add_option('--clean',
                     action='store_true',
                     help='purge the build directory before building')

    group.add_option('--no-clean',
                     action='store_false', dest='clean',
                     help='do not purge the build directory before '
                          'building')

    group.add_option('--no-unpack',
                     action='store_true',
                     help='assume that the sources are already present')

    parser.add_option_group(group)
    parser.set_defaults(clean=False,
                        no_unpack=False)
    return parser

def addDeploymentOptions(parser):
    '''
    Add report-specific options to the parser.
    '''
    from optparse import OptionGroup
    group = OptionGroup(parser, "Deployment Options")

    group.add_option('--rsync-dest',
                     action='store', metavar='DEST',
                     help='deploy artifacts to this location using rsync '
                          '(accepts the same format specification as '
                          '--build-id)')

    parser.add_option_group(group)
    parser.set_defaults(rsync_dest=None)
    return parser

def addDashboardOptions(parser):
    '''
    Add dashboard-related options to the option parser (optparse.OptionParser
    instance).
    '''
    from optparse import OptionGroup
    group = OptionGroup(parser, "Dashboard Options")

    group.add_option('--submit',
                     action='store_true',
                     help='submit the results to Dashboard server')

    group.add_option('--no-submit',
                     action='store_false', dest='submit',
                     help='do not submit the results to Dashboard server '
                          '(default)')

    group.add_option('--flavour',
                     help='which build server to use (build flavour)')

    parser.add_option_group(group)
    parser.set_defaults(submit=False, flavour='nightly')
    return parser

def expandTokensInOptions(options, opt_names, **kwargs):
    '''
    Given an options instance, the list of option names, and the list of
    keywords to replace, replace the options with the correct expanded stings.

    >>> from optparse import Values
    >>> options = Values()
    >>> options.name = '{token}'
    >>> expandTokensInOptions(options, ['name'], token='Hello')
    >>> options.name
    'Hello'
    '''
    for opt_name in opt_names:
        try:
            val = getattr(options, opt_name)
            if val:
                setattr(options, opt_name, val.format(**kwargs))
        except AttributeError:
            pass

import LbUtils.Script
class BaseScript(LbUtils.Script.PlainScript):
    '''
    Base class for LbNightlyToolsScripts
    '''
    __usage__ = '%prog [options] <slot name or config file>'
    __version__ = ''

    def defineOpts(self):
        '''
        Prepare the option parser.
        '''
        addBasicOptions(self.parser)
        addBuildDirOptions(self.parser)
        addDeploymentOptions(self.parser)
        addDashboardOptions(self.parser)

    def parseOpts(self, args):
        '''
        Override PlainScript logging settings.
        '''
        LbUtils.Script.PlainScript.parseOpts(self, args)
        # set the level to the handlers too
        for hdlr in self.log.handlers:
            hdlr.setLevel(self.log.level)

    def _setup(self, build_dir=None, json_type=None):
        '''
        Initialize variables.
        '''
        from os.path import exists, join
        from datetime import datetime
        from LbNightlyTools.Configuration import getSlot, parse as parseConfig
        from LbNightlyTools.Utils import ensureDirs, Dashboard

        opts = self.options
        if len(self.args) != 1:
            self.parser.error('wrong number of arguments')

        if exists(self.args[0].split('#')[0]):
            self.slot = parseConfig(self.args[0])
        else:
            self.slot = getSlot(self.args[0],
                           'configs' if exists('configs') else os.curdir)

        from LbNightlyTools.Utils import setDayNamesEnv
        setDayNamesEnv()

        # FIXME: we need something better
        self.platform = os.environ['CMTCONFIG']

        self.starttime = datetime.now()

        expandTokensInOptions(opts, ['build_id', 'artifacts_dir', 'rsync_dest'],
                              slot=self.slot.name)

        self.build_dir = join(os.getcwd(),
                              'build' if build_dir is None else build_dir)
        self.artifacts_dir = join(os.getcwd(), opts.artifacts_dir)
        self.json_dir = join(self.artifacts_dir, 'db')

        # ensure that we have the artifacts directory for the sources
        ensureDirs([self.artifacts_dir, self.build_dir, self.json_dir])

        # template data to be reported in every JSON file
        self.json_tmpl = {'slot': self.slot.name,
                          'build_id': int(os.environ.get('slot_build_id', 0))}
        if json_type:
            self.json_tmpl['type'] = json_type

        # checkout is platform independent, the others require it
        if json_type != 'slot-config':
            self.json_tmpl['platform'] = self.platform

        # record the Jenkins build URL if available
        if 'BUILD_URL' in os.environ:
            self.json_tmpl['build_url'] = os.environ['BUILD_URL']

        self.dashboard = Dashboard(credentials=None,
                                   dumpdir=self.json_dir,
                                   submit=opts.submit,
                                   flavour=opts.flavour)
        if opts.projects:
            proj_names = dict((proj.name.lower(), proj.name)
                              for proj in self.slot.projects)
            try:
                opts.projects = set(proj_names[p.strip().lower()]
                                    for p in opts.projects.split(','))
            except KeyError, exc:
                self.parser.error('requested project not in slot: "%s"' %
                                  exc.args)
        else:
            opts.projects = None

    def _summaryDir(self, proj, *subdirs):
        '''
        Return the path to the summary directory for a given project.

        If extra arguments are given, the output is equivalent to
        os.path.join(self._summaryDir(proj), level1, level2).
        '''
        return os.path.join(self.artifacts_dir, 'summaries.' + self.platform,
                            proj.name, *subdirs)

    def _buildDir(self, proj, *subdirs):
        '''
        Return the path to the build directory for a given project.

        If extra arguments are given, the output is equivalent to
        os.path.join(self._buildDir(proj), level1, level2).
        '''
        return os.path.join(self.build_dir, proj.baseDir, *subdirs)

    def dump_json(self, data):
        '''
        Write a JSON file into the special artifacts 'db' directory.

        @param data: mapping with the data to write
        '''
        output_data = dict(self.json_tmpl)
        output_data.update(data)
        self.dashboard.publish(output_data)
