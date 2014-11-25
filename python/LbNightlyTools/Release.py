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

import os
import json
import urllib2
import codecs

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
    PROJECT_NAMES = ['LHCb', 'DaVinci', 'DecFilesTests', 'MooreOnline',
                     'LbScripts', 'VanDerMeer', 'LHCbDirac']

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
class ConfigGenerator(LbUtils.Script.PlainScript):
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
        self.parser.add_option('--packages',
                               help='space-separated list of data packages, '
                                    'with versions, to add')
        self.parser.set_defaults(slot='lhcb-release',
                                 cmt=False,
                                 output='-',
                                 platforms=DEFAULT_PLATFORMS,
                                 packages='')

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
            project = {'name': proj, 'version': vers,
                       'checkout_opts': {'export': True}}

            added.append(proj)

            # we check out Gaudi from git
            if proj == 'Gaudi':
                project['checkout'] = 'git'
                extra_opts = {'url': 'http://git.cern.ch/pub/gaudi',
                              'commit': 'GAUDI/GAUDI_' + vers}
                project['checkout_opts'].update(extra_opts)
            elif proj in ('Dirac', 'LHCbDirac', 'LHCbGrid'):
                project['checkout'] = proj.lower()

            if proj in ('Geant4'):
                project['with_shared'] = True

            projects.append(project)

        packages = []
        if self.options.packages:
            packages_opt = self.options.packages.split()
            for pack, vers in zip(packages_opt[::2], packages_opt[1::2]):
                package = {'version': vers,
                           'checkout_opts': {'export': True}}
                # the package name could by just the name or <container>:<name>
                if ':' not in pack:
                    package['name'] = pack
                else:
                    package['container'], package['name'] = pack.split(':', 1)
                if package not in packages: # ignore duplicates
                    packages.append(package)

        default_platforms = (self.options.platforms.replace(',', ' ')
                             .strip().split())

        # prepare the configuration dictionary
        config = {'slot': self.options.slot,
                  'description': 'Slot used for releasing projects.',
                  'projects': projects,
                  'packages': packages,
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

class Poll(LbUtils.Script.PlainScript):
    '''
    Poll a URL for the list of stacks not yet released and return those that
    need to be built.
    '''
    __usage__ = '%prog [options] url'

    def defineOpts(self):
        '''
        Options specific to this script.
        '''
        self.parser.add_option('--state-file', action='store',
                               help='file where to keep the latest state of the'
                                    ' stacks to be built')
        self.parser.add_option('--output-param-file', action='store',
                               help='file where to store the parameter for the '
                                    'release trigger job in Jenkins. If '
                                    'there is nothing to build, the file is '
                                    'removed (for integration with Jenkins).')

        self.parser.set_defaults(state_file='stacks.json',
                                 output_param_file='params.txt')

    def main(self):
        '''
        Script logic.
        '''
        if len(self.args) != 1:
            self.parser.error('wrong number of arguments')

        # URL to poll
        url = self.args[0]

        state_file = self.options.state_file
        output_param_file = self.options.output_param_file

        # get the stacks triggered last time
        self.log.debug('load previous state')
        previous = []
        if os.path.exists(state_file):
            with codecs.open(state_file, 'r', 'utf-8') as state:
                previous = json.load(state)
        self.log.debug('found %d stacks', len(previous))

        # retrieve the list of stacks to build
        self.log.debug('retrieving %s', url)
        stacks = json.loads(urllib2.urlopen(url).read())
        # sort the list for stable behavior
        for stack in stacks:
            for k in stack:
                stack[k].sort()
        stacks.sort()
        self.log.debug('found %d stacks', len(stacks))

        # overwrite the last run data for the next poll
        self.log.debug('write new state')
        with codecs.open(state_file, 'w', 'utf-8') as output:
            json.dump(stacks, output)

        # check which entries need to be built
        indexes = [str(i)
                   for i, s in enumerate(stacks)
                   if s not in previous]

        if indexes:
            self.log.debug('write parameters file')
            with open(output_param_file, 'w') as output:
                output.write('indexes=%s\n' % ' '.join(indexes))
                output.write('stacks=%s\n' % json.dumps(stacks))
        else:
            # prevent further triggering
            self.log.debug('nothing to build')
            if os.path.exists(output_param_file):
                os.remove(output_param_file)

        return 0

class Trigger(LbUtils.Script.PlainScript):
    '''
    Poll a URL for the list of stacks not yet released and return those that
    need to be built.
    '''
    __usage__ = '%prog [options] <stacks JSON file> <index>'

    def defineOpts(self):
        '''
        Options specific to this script.
        '''
        self.parser.add_option('--output-param-file', action='store',
                               help='file where to store the parameter for the '
                                    'release trigger job in Jenkins. If '
                                    'there is nothing to build, the file is '
                                    'removed (for integration with Jenkins).')

        self.parser.set_defaults(output_param_file='params.txt')

    def main(self):
        '''
        Script logic.
        '''
        if len(self.args) != 2:
            self.parser.error('wrong number of arguments')

        # URL to poll
        stacks_file = self.args[0]
        try:
            index = int(self.args[1])
        except:
            self.parser.error('invalid argument "%s": it should be an int' %
                              self.args[1])

        if os.path.exists(stacks_file):
            with codecs.open(stacks_file, 'r', 'utf-8') as state:
                stacks = json.load(state)
        else:
            self.log.error('file %s not found', stacks_file)
            return 1

        stack = stacks[index]

        projects_list = ' '.join(' '.join(project_version) for project_version in stack.get('projects', []))
        platforms = ' '.join(stack.get('platforms', []))

        output_param_file = self.options.output_param_file
        if projects_list and platforms:
            data = 'projects_list={0}\nplatforms={1}\n'.format(projects_list,
                                                               platforms)
            with open(output_param_file, 'w') as output:
                output.write(data)
        else:
            self.log.error('invalid stack configuration')
            if os.path.exists(output_param_file):
                os.remove(output_param_file)
            return 1

        return 0

_manifest_template = u'''<?xml version='1.0' encoding='UTF-8'?>
<manifest>
  <project name="{project}" version="{version}" />
  <heptools>
    <version>{heptools}</version>
    <binary_tag>{platform}</binary_tag>
    <lcg_system>{system}</lcg_system>
  </heptools>{used_projects}{used_data_pkgs}
</manifest>
'''

def createManifestFile(project, version, platform, build_dir):
    '''
    Generate a manifest.xml from the CMT configuration.
    '''
    from subprocess import Popen, PIPE
    import re
    container_package = ((project + 'Sys')
                         if project != 'Gaudi'
                         else 'GaudiRelease')
    container_dir = os.path.join(build_dir, container_package, 'cmt')
    env = dict((key, value) for key, value in os.environ.iteritems()
               if key not in ('PWD', 'CWD'))
    proc = Popen(['cmt', 'show', 'projects'], cwd=build_dir, env=env,
                 stdout=PIPE, stderr=PIPE)
    out, _err = proc.communicate()

    # no check because we must have a dependency on LCGCMT
    heptools = re.search(r'LCGCMT_([^ ]+)', out).group(1)

    projects = ['    <project name="%s" version="%s" />' %
                (fixProjectCase(name), vers.split('_')[-1])
                for name, vers in [x.split()[0:2]
                                   for x in out.splitlines()
                                   if re.match(r'^  [^ ]', x)]
                if name not in ('DBASE', 'PARAM', 'LCGCMT')]
    if projects:
        projects.insert(0, '\n  <used_projects>')
        projects.append('  </used_projects>')

    data_pkgs = []
    if 'DBASE' in out or 'PARAM' in out:
        proc = Popen(['cmt', 'show', 'uses'], cwd=container_dir, env=env,
                     stdout=PIPE, stderr=PIPE)
        out, _err = proc.communicate()
        out = out.splitlines()
        data_pkgs = [x.replace(' ', ',').split(',')[1:4:2]
                     for x in out
                     if re.search(r'DBASE|PARAM', x)]
        def findVersion(pkg):
            v = (x.split()[3] for x in out
                 if re.match(r'^#.*%s' % pkg, x)).next()
            if v == 'v*':
                v = '*'
            return v

        data_pkgs = ['    <package name="%s" version="%s" />' %
                     (hat + '/' + name if hat else name,
                      findVersion(name))
                     for name, hat in data_pkgs]
        if data_pkgs:
            data_pkgs.insert(0, '\n  <used_data_pkgs>')
            data_pkgs.append('  </used_data_pkgs>')

    return _manifest_template.format(project=project, version=version,
                                     platform=platform,
                                     system=platform[:platform.rfind('-')],
                                     heptools=heptools,
                                     used_projects='\n'.join(projects),
                                     used_data_pkgs='\n'.join(data_pkgs))
