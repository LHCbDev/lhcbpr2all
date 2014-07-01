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
Module containing the classes and functions used to build a
"Nightly Build Slot".
'''
__author__ = 'Marco Clemencic <marco.clemencic@cern.ch>'

import logging
import shutil
import os
import re
import time
import socket
import threading
import codecs
import json

from LbNightlyTools import Configuration
from LbNightlyTools.Utils import timeout_call as call, ensureDirs, pack
from LbNightlyTools.Utils import Dashboard

from string import Template
from socket import gethostname
from datetime import datetime
from collections import defaultdict, OrderedDict
try:
    from multiprocessing import cpu_count
except ImportError:
    cpu_count = lambda : 0 # pylint: disable=C0103

# no-op 'call' function for testing
#call = lambda *a,**k: None

__log__ = logging.getLogger(__name__)

COV_PASSPHRASE_FILE = os.path.join(os.path.expanduser('~'),
                                   'private', 'cov-admin')

LOAD_AVERAGE_SCALE = 1.2

def genProjectXml(name, projects):
    '''
    Take a list of ProjDesc instances and return the XML string usable to
    configure subprojects in CDash.
    '''
    versions = dict([(p.name, str(p)) for p in projects])

    xml = [u'<Project name="{0}">'.format(name)]
    for proj in projects:
        xml.append(u'  <SubProject name="{0}">'.format(proj))
        for dep in proj.deps:
            xml.append(u'    <Dependency name="{0}"/>'.format(versions[dep]))
        xml.append(u'  </SubProject>')
    xml.append(u'</Project>\n')

    return u'\n'.join(xml)

def genSlotConfig(config):
    '''
    Generate SlotConfig.cmake, needed by the CTest build script.

    @return: the data to be written to the file
    '''
    projects = config[u'projects']

    cmake = ['set(slot %(slot)s)' % config,
             'set(config $ENV{CMTCONFIG})',
             'set(projects %s)' % ' '.join([p[u'name']
                                            for p in projects])]

    for proj in projects:
        cmake.append('set(%(name)s_version %(version)s)' % proj)

    for proj in projects:
        cmake.append('set(%s_dependencies %s)' %
                     (proj[u'name'], ' '.join(proj.get(u'dependencies', []))))

    if u'warning_exceptions' in config:
        cmake.append('set(CTEST_CUSTOM_WARNING_EXCEPTION '
                     '${CTEST_CUSTOM_WARNING_EXCEPTION}')
        for ex in config[u'warning_exceptions']:
            cmake.append('    "%s"' %
                         ex.replace('\\', '\\\\').replace('"', r'\"'))
        cmake.append('    )\n')

    if u'error_exceptions' in config:
        cmake.append('set(CTEST_CUSTOM_ERROR_EXCEPTION '
                     '${CTEST_CUSTOM_ERROR_EXCEPTION}')
        for ex in config[u'error_exceptions']:
            cmake.append('    "%s"' %
                         ex.replace('\\', '\\\\').replace('"', r'\"'))
        cmake.append('    )\n')

    return '\n'.join(cmake)

class ProjDesc():
    '''
    Description of the project to build.
    '''
    # pylint: disable=R0903
    def __init__(self, desc_dict):
        self.name = desc_dict[u'name']
        self.version = desc_dict[u'version']
        self.deps = desc_dict.get(u'dependencies', [])
        self.dir = os.path.join(self.name.upper(),
                                '{0}_{1}'.format(self.name.upper(),
                                                 self.version))
        cov_version = self.version.lower()
        if cov_version == 'head':
            cov_version = 'trunk' # we use 'trunk' instead of 'head' in Coverity
        self.coverity_stream = desc_dict.get(u'coverity_stream',
                                             '{0}_{1}'.format(self.name.lower(),
                                                              cov_version))
        self.with_shared = desc_dict.get(u'with_shared', False)

    def __str__(self):
        return '{0} {1}'.format(self.name, self.version)

def sortedByDeps(deps):
    '''
    Take a dictionary of dependencies as {'depender': ['dependee', ...]} and
    return the list of keys sorted according to their dependencies so that
    that a key comes after its dependencies.

    >>> sortedByDeps({'4':['2','3'],'3':['1'],'2':['1'],'1':['0'],'0':[]})
    ['0', '1', '3', '2', '4']

    If the argument is an OrderedDict, the returned list preserves the order of
    the keys (if possible).

    >>> sortedByDeps(dict([('1', []), ('2', ['1']), ('3', ['1'])]))
    ['1', '3', '2']
    >>> sortedByDeps(OrderedDict([('1', []), ('2', ['1']), ('3', ['1'])]))
    ['1', '2', '3']
    '''
    def unique(iterable):
        '''Return only the unique elements in the list l.

        >>> unique([0, 0, 1, 2, 1])
        [0, 1, 2]
        '''
        uniquelist = []
        for item in iterable:
            if item not in uniquelist:
                uniquelist.append(item)
        return uniquelist
    def recurse(keys):
        '''
        Recursive helper function to sort by dependency: for each key we
        first add (recursively) its dependencies then the key itself.'''
        result = []
        for k in keys:
            result.extend(recurse(deps[k]))
            result.append(k)
        return unique(result)
    return recurse(deps)

OLD_BUILD_ID = '{slot}.{today}_{project}_{version}-{platform}'

def listAllFiles(path, excl=None):
    '''
    Return the list of all files in a directory and in its subdirectories.
    '''
    if excl is None:
        excl = lambda _: False
    from os.path import join
    for root, dirs, files in os.walk(path):
        for f in files:
            if not excl(f):
                yield join(root, f)
        dirs[:] = [d for d in dirs if not excl(d)]

def setenv(definitions):
    '''
    Modify the environment from a list of definitions of the type 'name=value',
    expanding the variables in 'value'.

    >>> setenv(['foo=bar'])
    >>> os.environ['foo']
    'bar'
    >>> setenv(['baz=some_${foo}'])
    >>> os.environ['baz']
    'some_bar'
    '''
    for item in definitions:
        name, value = item.split('=', 1)
        os.environ[name] = os.path.expandvars(value)

def genPackageName(proj, platform, build_id=None, artifacts_dir=None):
    '''
    Generate the binary tarball name for a project.

    >>> genPackageName(ProjDesc({'name': 'Gaudi', 'version': 'HEAD'}),
    ...                'x86_64-slc6-gcc48-opt')
    'Gaudi.HEAD.x86_64-slc6-gcc48-opt.tar.bz2'
    >>> genPackageName(ProjDesc({'name': 'Gaudi', 'version': 'v25r0'}),
    ...                'x86_64-slc6-gcc48-dbg',
    ...                build_id='dummy', artifacts_dir='artifacts')
    'artifacts/Gaudi.v25r0.dummy.x86_64-slc6-gcc48-dbg.tar.bz2'
    '''
    packname = [proj.name, proj.version]
    if build_id:
        packname.append(build_id)
    packname.append(platform)
    packname.append('tar.bz2')
    packname = '.'.join(packname)
    if artifacts_dir:
        packname = os.path.join(artifacts_dir, packname)
    return packname


import LbUtils.Script
class Script(LbUtils.Script.PlainScript):
    '''
    Script to build and test all the projects described in a configuration file.
    '''
    __usage__ = '%prog [options] <config.json>'
    __version__ = ''

    # unavoidable or fake warnings
    # pylint: disable=E1002,W0201
    def defineBuildOptions(self):
        '''
        Add build-specific options to the parser.
        '''
        from optparse import OptionGroup
        group = OptionGroup(self.parser, "Build Options")

        group.add_option('--clean',
                         action='store_true',
                         help='purge the build directory before building')

        group.add_option('--no-clean',
                         action='store_false', dest='clean',
                         help='do not purge the build directory before '
                              'building')

        group.add_option('-j', '--jobs',
                         action='store', type='int',
                         help='number of parallel jobs to use during the build '
                              '(default: sequential build)')

        group.add_option('-l', '--load-average',
                         action='store', type='float',
                         help='load average limit for parallel builds, use 0 '
                              'to remove the limit (default: '
                              '$LBN_LOAD_AVERAGE or N of cores x %g)'
                              % LOAD_AVERAGE_SCALE)

        group.add_option('--no-distcc',
                         action='store_true',
                         help='prevent use of distcc (used by default if '
                              'present on the system)')

        group.add_option('--no-unpack',
                         action='store_true',
                         help='assume that the sources are already present')

        group.add_option('--coverity',
                         action='store_true',
                         help='enable special Coverity static analysis on the '
                              'build (Coverity commands must be on the PATH)')

        self.parser.add_option_group(group)
        if 'LBN_LOAD_AVERAGE' in os.environ:
            load_average = float(os.environ['LBN_LOAD_AVERAGE'])
        else:
            load_average = cpu_count()*LOAD_AVERAGE_SCALE
        self.parser.set_defaults(clean=False,
                                 jobs=1,
                                 load_average=load_average,
                                 no_distcc=False,
                                 coverity=False)

    def defineTestOptions(self):
        '''
        Add test-specific options to the parser.
        '''
        from optparse import OptionGroup
        group = OptionGroup(self.parser, "Test Options")

        group.add_option('--with-tests',
                         action='store_true',
                         help='run the tests after the build')

        group.add_option('--tests-only',
                         action='store_true',
                         help='run the tests without building')

        group.add_option('--test-suite',
                         action='store',
                         help='specify a test suite to launch '
                              '[default: all test]')

        group.add_option('--timeout',
                         metavar='SECONDS',
                         action='store', type='int',
                         help='set a global timeout on all tests '
                              '(default: %default)')

        self.parser.add_option_group(group)
        self.parser.set_defaults(with_tests=False,
                                 tests_only=False,
                                 test_suite=None,
                                 timeout=600)

    def defineDeploymentOptions(self):
        '''
        Add report-specific options to the parser.
        '''
        from optparse import OptionGroup
        group = OptionGroup(self.parser, "Deployment Options")

        group.add_option('--deploy-reports-to',
                         action='store', metavar='DEST_DIR', dest='deploy_dir',
                         help='if the destination directory is specified, the '
                              'old-style summaries are deployed to that '
                              'directory as soon as they are produced')

        group.add_option('--rsync-dest',
                         action='store', metavar='DEST',
                         help='deploy artifacts to this location using rsync '
                              '(accepts the same format specification as '
                              '--build-id)')

        self.parser.add_option_group(group)
        self.parser.set_defaults(deploy_dir=None,
                                 rsync_dest=None)

    def defineCDashOptions(self):
        '''
        Add CDash-specific options to the parser.
        '''
        from optparse import OptionGroup
        group = OptionGroup(self.parser, "CDash Options")

        models = ['Nightly', 'Experimental', 'Continuous']
        group.add_option('--model',
                         action='store', type='choice', choices=models,
                         help='build model: {0} (default: {0[0]}).'
                              .format(models))

        group.add_option('--cdash-submit',
                         action='store_true',
                         help='submit the results to CDash server')

        group.add_option('--no-cdash-submit',
                         action='store_false', dest='cdash_submit',
                         help='do not submit the results to CDash server '
                              '(default)')

        self.parser.add_option_group(group)
        self.parser.set_defaults(model=models[0],
                                 cdash_submit=False)

    def defineOpts(self):
        '''
        Prepare the option parser.
        '''
        from LbNightlyTools.ScriptsCommon import (addBasicOptions,
                                                  addDashboardOptions)

        addBasicOptions(self.parser)

        self.defineBuildOptions()
        self.defineTestOptions()
        self.defineDeploymentOptions()

        addDashboardOptions(self.parser)

        self.defineCDashOptions()


    def _setup(self):
        '''
        Initialize variables.
        '''
        from os.path import join, dirname, basename
        from LbNightlyTools.ScriptsCommon import expandTokensInOptions

        opts = self.options

        self.config = Configuration.load(self.args[0])

        from LbNightlyTools.Utils import setDayNamesEnv
        setDayNamesEnv()

        # FIXME: we need something better
        self.platform = os.environ['CMTCONFIG']

        self.starttime = datetime.now()

        expandTokensInOptions(opts, ['build_id', 'artifacts_dir', 'rsync_dest'],
                              slot=self.config[u'slot'])

        self.build_dir = join(os.getcwd(), 'build')
        self.artifacts_dir = join(os.getcwd(), opts.artifacts_dir)

        # ensure that we have the artifacts directory for the sources
        ensureDirs([self.artifacts_dir, self.build_dir])

        # template data to be reported in every JSON file
        self.json_tmpl = {'slot': self.config['slot'],
                          'build_id': int(os.environ.get('slot_build_id', 0)),
                          'platform': self.platform}

        self.dashboard = Dashboard(credentials=None,
                                   dumpdir=os.path.join(self.artifacts_dir,
                                                        'db'),
                                   submit=opts.submit,
                                   flavour=opts.flavour)

        self.log.info("Preparing CTest scripts and configurations.")
        # load CTest script templates
        filename = join(dirname(__file__), 'CTest{0}.template.cmake')
        self.ctest_config = Template(open(filename.format('Config')).read())
        self.ctest_script = Template(open(filename.format('Script')).read())

        self.config_cmake = genSlotConfig(self.config)

        if u'cmake_cache' in self.config:
            preload_lines = ['set(%s "%s" CACHE STRING "override")' % item
                             for item in self.config[u'cmake_cache'].items()]
            self.cache_preload = '\n'.join(preload_lines)
        else:
            self.cache_preload = None

        self.projects = OrderedDict([(p.name, p)
                                     for p in map(ProjDesc,
                                                  self.config[u'projects'])])

        deps = OrderedDict([(p.name, p.deps) for p in self.projects.values()])
        self.sorted_projects = [self.projects[p] for p in sortedByDeps(deps)]

        if opts.projects:
            opts.projects = set(p.strip().lower()
                                for p in opts.projects.split(','))
        else:
            opts.projects = None

        if opts.deploy_dir:
            # ensure that the deployment dir ends with the slot name...
            if basename(opts.deploy_dir) != self.config[u'slot']:
                opts.deploy_dir = join(opts.deploy_dir, self.config[u'slot'])
            # ... and that the directory exists
            ensureDirs([opts.deploy_dir])

        # Prepare command lines for the build
        cmd = ['ctest', '--timeout', str(opts.timeout)]
        if opts.jobs != 1:
            cmd.append('-DJOBS=%d' % opts.jobs)
            if opts.load_average > 0:
                cmd.append('-DMAX_LOAD=%g' % opts.load_average)

        if not opts.cdash_submit:
            cmd.append('-DNO_SUBMIT=TRUE')

        if self.config.get(u'USE_CMT'):
            cmd.append('-DUSE_CMT=TRUE')

        if opts.no_distcc:
            cmd.append('-DDISABLE_DISTCC=TRUE')

        self.build_cmd = cmd + ['-DSTEP=BUILD', '-S', 'CTestScript.cmake']
        self.test_cmd = cmd + ['-DSTEP=TEST', '-S', 'CTestScript.cmake']

        log_level = self.log.getEffectiveLevel()
        if log_level <= logging.INFO:
            self.build_cmd.insert(1, '-VV')
        if log_level <= logging.DEBUG:
            self.test_cmd.insert(1, '-VV')


    def dump_json(self, data):
        '''
        Write a JSON file into the special artifacts 'db' directory.

        @param data: mapping with the data to write
        '''
        output_data = dict(self.json_tmpl)
        output_data.update(data)
        self.dashboard.publish(output_data)

    def write(self, path, data):
        '''
        Simple function to write some text (UTF-8) to a file.

        @param path: name of the file to write
        @param data: string to write
        '''
        self.log.debug('writing %s', path)
        ensureDirs([os.path.dirname(path)])
        f = codecs.open(path, 'w', 'utf-8')
        f.write(data)
        f.close()

    def writeBin(self, path, data):
        '''
        Simple function to write some binary data to a file.

        @param path: name of the file to write
        @param data: string to write
        '''
        self.log.debug('writing (bin) %s', path)
        ensureDirs([os.path.dirname(path)])
        f = open(path, 'wb')
        f.write(data)
        f.close()

    def keepArtifact(self, src, dst=os.path.curdir, new_name=None):
        '''
        Copy a file in the artifacts directory.

        @param src: file to copy
        @param dst: subdirectory of the artifacts directory where to store the
                    copy
        @param new_name: name to give to the file in the artifacts directory
                         (by default keep the same name)
        '''
        if not new_name:
            new_name = os.path.basename(src)
        self.log.debug('keep %s as artifact %s in %s', src, new_name, dst)
        ensureDirs([dst])
        shutil.copy(src, os.path.join(self.artifacts_dir, dst, new_name))

    def deployReports(self, files):
        '''
        Helper function to copy the reports in the required directory.
        '''
        if not self.options.deploy_dir:
            return
        from os.path import join, basename, isdir, isfile, islink
        for filename in files:
            try:
                dirname = join(self.options.deploy_dir, basename(filename))
                if isdir(dirname):
                    shutil.rmtree(dirname)
                elif isfile(dirname) or islink(dirname):
                    os.remove(dirname)
                self.log.info('Copying %s to deployment directory %s',
                              filename, dirname)
                if isdir(filename):
                    shutil.copytree(filename, dirname)
                elif isfile(filename):
                    shutil.copy2(filename, dirname)
                else:
                    self.log.warning('Cannot deploy %s (does it exist?)',
                                     filename)
            except os.error, err:
                self.log.warning('Problems deploying %s: %s', filename, err)

    def _prepareBuildDir(self):
        '''
        Prepare the build directory unpacking all the available artifacts
        tarballs, cleaning it before if requested.
        '''
        if self.options.clean:
            self.log.info('Cleaning build directory.')
            if os.path.exists(self.build_dir):
                shutil.rmtree(self.build_dir)
                ensureDirs([self.build_dir])

        if not self.options.no_unpack:
            self.log.info('Preparing build directory...')
            for f in os.listdir(self.artifacts_dir):
                if f.endswith('.tar.bz2'):
                    f = os.path.join(self.artifacts_dir, f)
                    self.log.info('  unpacking %s', f)
                    # do not overwrite existing sources when unpacking
                    # (we must preserve user changes, anyway we have the
                    # --clean option)
                    call(['tar', '-x',
                          '--no-overwrite-dir', '--keep-old-files',
                          '-f', f], cwd=self.build_dir)

        project_xml = genProjectXml(self.config[u'slot'], self.sorted_projects)
        project_xml_name = os.path.join(self.build_dir, 'Project.xml')
        self.write(project_xml_name, project_xml)
        self.keepArtifact(project_xml_name)

        def dumpConfSummary():
            '''Create special summary file used by SetupProject.'''
            data = defaultdict(list)
            env = dict(decl.split('=', 1)
                       for decl in self.config.get(u'env', []))
            # collect the expanded values for  CMTPROJECTPATH and
            # CMAKE_PREFIX_PATH in the local environment
            for name in ('CMTPROJECTPATH', 'CMAKE_PREFIX_PATH'):
                if name in env:
                    data[name] = os.path.expandvars(env[name]).split(':')
            if data:
                py_templ = Template(u'''# -*- coding: utf-8 -*-
cmtProjectPathList = ${path}

# relocate
try:
    from os.path import dirname
    nightlyBuildRoot = ${build_root}
    newRoot = dirname(__file__)
    cmtProjectPathList = [s.replace(nightlyBuildRoot, newRoot)
                          for s in cmtProjectPathList]
except NameError:
    pass # __file__ gets defined only with LbScripts > v8r0\n''')
                values =  {'path': repr(data['CMTPROJECTPATH'] +
                                        data['CMAKE_PREFIX_PATH']),
                           'build_root': repr(self.build_dir)}
                self.write(os.path.join(self.artifacts_dir, 'confSummary.py'),
                           py_templ.substitute(values))
                cmake_templ = Template(u'''set(NIGHTLY_BUILD_ROOT ${build_root})
set(CMAKE_PREFIX_PATH ${path} $${CMAKE_PREFIX_PATH})

string(REPLACE "$${NIGHTLY_BUILD_ROOT}" "$${CMAKE_CURRENT_LIST_DIR}"
       CMAKE_PREFIX_PATH "$${CMAKE_PREFIX_PATH}")\n''')
                values = {'path': ' '.join(data['CMAKE_PREFIX_PATH'] +
                                           data['CMTPROJECTPATH']),
                          'build_root': self.build_dir}
                self.write(os.path.join(self.artifacts_dir, 'searchPath.cmake'),
                           cmake_templ.substitute(values))

        dumpConfSummary()

    def _prepareProject(self, proj):
        '''
        Prepare a project directory for build or test.
        '''
        from os.path import join

        proj.build_dir = join(self.build_dir, proj.dir)
        proj.enabled = os.path.exists(proj.build_dir)
        if not proj.enabled:
            self.log.debug('%s not found, imply %s disabled', proj.dir, proj)

        proj.summary_dir = join(self.artifacts_dir,
                                'summaries.' + self.platform,
                                proj.name)
        # use the ramdisk for Coverity intermediate dir if possible
        if os.path.exists('/dev/shm'):
            proj.coverity_int = join('/dev/shm/coverity.' + self.platform,
                                     self.options.build_id, proj.name)
        else:
            proj.coverity_int = join(self.build_dir, 'coverity', proj.name)
        proj.coverity_mod = join(proj.summary_dir, 'coverity', 'models')
        proj.coverity_logs = join(proj.summary_dir, 'coverity', proj.name)

        proj.old_build_id = OLD_BUILD_ID.format(slot=self.config[u'slot'],
                                                today=os.environ['TODAY'],
                                                project=proj.name.upper(),
                                                version=proj.version,
                                                platform=self.platform)

        proj.started = proj.completed = proj.build_retcode = None

        proj.packname = genPackageName(proj, self.platform,
                                       build_id=self.options.build_id,
                                       artifacts_dir=self.artifacts_dir)

        if proj.enabled:
            # write files only if the project is enabled
            Configuration.save(join(proj.build_dir, 'SlotConfig.json'),
                               self.config)

            self.write(join(proj.build_dir, 'SlotConfig.cmake'),
                       self.config_cmake)

            if self.cache_preload:
                self.write(join(proj.build_dir, 'cache_preload.cmake'),
                           self.cache_preload + '\n')

            self.write(join(proj.build_dir, 'CTestConfig.cmake'),
                       self.ctest_config.substitute(self.config))

            script_data = {'project': proj.name,
                           'version': proj.version,
                           'build_dir': self.build_dir,
                           'site': gethostname(),
                           'summary_dir': proj.summary_dir,
                           'Model': self.options.model,
                           'old_build_id': proj.old_build_id}
            self.write(join(proj.build_dir, 'CTestScript.cmake'),
                       self.ctest_script.substitute(script_data))

        return proj

    def _buildProject(self, proj):
        '''
        Build a project of the slot.
        '''
        from os.path import join

        if os.path.exists(proj.packname):
            self.log.info('binary tarball for %s already present, skip build',
                          proj)
            return

        build_cmd = self.build_cmd
        if self.options.coverity:
            # create all the directories that are missing
            ensureDirs([proj.coverity_int, proj.coverity_mod,
                        proj.coverity_logs])
            build_cmd = ['cov-build', '--dir', proj.coverity_int] + build_cmd

        def dumpFileListSummary(name):
            '''
            Dump the list of all the files in the project directory in the
            summary file 'name'.
            '''
            file_excl_rex = re.compile((r'^(InstallArea)|(build\.{0})|({0})|'
                                        r'(\.git)|(\.svn)|'
                                        r'(\.{0}\.d)|(Testing)|(.*\.pyc)$'
                                        ).format(self.platform))

            data = sorted(listAllFiles(proj.build_dir, file_excl_rex.match))
            data.append('')
            self.write(os.path.join(proj.summary_dir, name), '\n'.join(data))

        dumpFileListSummary('sources.list')

        self.log.info('building %s', proj.dir)
        proj.started = datetime.now()
        self.log.debug('cmd: %s', build_cmd)
        proj.build_retcode = call(build_cmd, cwd=proj.build_dir,
                                  timeout=28800, # timeout of 8 hours
                                  timeoutmsg='building %s' % proj.name)
        if proj.build_retcode != 0:
            self.log.warning('build exited with code %d', proj.build_retcode)
        proj.completed = datetime.now()

        dumpFileListSummary('sources_built.list')

        # copy the file with the URL of the checkout job to the summaries
        if os.path.exists(join(self.artifacts_dir, 'checkout_job_url.txt')):
            shutil.copy(join(self.artifacts_dir, 'checkout_job_url.txt'),
                        proj.summary_dir)

        reporter = BuildReporter(proj.summary_dir, proj, self.platform,
                                 self.config, proj.old_build_id)
        self.deployReports(reporter.genOldSummaries())
        self.dump_json(reporter.json())

        self.log.info('packing %s', proj.dir)

        pack([os.path.join(proj.dir, 'InstallArea')], proj.packname,
             cwd=self.build_dir, checksum='md5')

        if proj.with_shared:
            shr_packname = genPackageName(proj, "shared",
                                          build_id=self.options.build_id,
                                          artifacts_dir=self.artifacts_dir)
            to_pack_list = (set(open(join(proj.summary_dir,
                                          'sources_built.list'))) -
                            set(open(join(proj.summary_dir,
                                          'sources.list'))))
            pack([os.path.relpath(f.strip(), self.build_dir)
                  for f in sorted(to_pack_list)],
                 shr_packname, cwd=self.build_dir, checksum='md5')

        return proj

    def _coverityAnalysis(self, proj):
        '''
        Run the coverity analysis on a project.
        '''
        from os.path import join
        # this call actually does not "submit" (commit-defects), it just
        # run the analysis
        self.log.info('running Coverity analysis from %s', proj.coverity_int)
        call(['analyze-submit.sh', proj.coverity_int, proj.coverity_mod])
        # keep a copy of the logs
        for clf in ['log.txt', 'BUILD.metrics.xml', 'build-log.txt']:
            shutil.copy2(join(proj.coverity_int, clf), proj.coverity_logs)
        # collect models for use with the other projects
        self.log.info('collecting Coverity models')
        call(['cov-collect-models', '--dir', proj.coverity_int,
              '-of', join(proj.coverity_mod, proj.name + '.xmldb')])
        # ensure that there is no stale lock
        # FIXME: is it needed?
        try:
            os.remove(join(proj.coverity_mod, proj.name + '.xmldb.lock'))
        except:
            pass
        # commit defect to Coverity Integrity Manager
        cov_commit_cmd = ['cov-commit-defects',
                          '--host', 'lhcb-coverity.cern.ch',
                          '--port', '8080',
                          '--user', 'admin',
                          '--stream', proj.coverity_stream]
        # strip the project build directories when submitting
        proj_build_dirs = [join(self.build_dir, p.dir) + '/'
                           for p in self.sorted_projects]
        # (this is an interesting trick to intersperse two lists)
        from itertools import repeat
        cov_commit_cmd += [val
                           for pair in zip(repeat('--strip-path'),
                                           proj_build_dirs)
                           for val in pair]
        cov_commit_cmd += open(join(proj.coverity_int,
                                    'c', 'output',
                                    'commit-args.txt')).read().split()

        tmpenv = {'COVERITY_PASSPHRASE':
                  open(COV_PASSPHRASE_FILE).read().strip()}
        tmpenv.update(os.environ)
        self.log.info('committing results Coverity Integrity Manager')
        call(cov_commit_cmd, env=tmpenv)

    def main(self):
        '''
        Main function of the script.
        '''
        if len(self.args) != 1:
            self.parser.error('wrong number of arguments')

        opts = self.options

        # implied options:
        # - we run the test if we ask for them in a way or another
        opts.with_tests = opts.with_tests or opts.tests_only
        # - do not run the tests if building for coverity
        opts.with_tests = opts.with_tests and not opts.coverity
        # - test-only and coverity cannot coexist
        if opts.tests_only and opts.coverity:
            self.parser.error('incompatible options --tests-only and '
                              '--coverity')


        self._setup()

        if opts.submit and not opts.projects and not opts.tests_only:
            # ensure that results for the current slot/build/platform are
            # not in the dashboard (useful in case of rebuild), but only
            # if we need to publish the results and it's not a partial build
            # or a "test-only" run
            self.dashboard.dropBuild(slot=self.json_tmpl['slot'],
                                     build_id=self.json_tmpl['build_id'],
                                     platform=self.json_tmpl['platform'])
        if not opts.tests_only:
            self.dump_json({'type': 'job-start',
                            'host': gethostname(),
                            'build_number': os.environ.get('BUILD_NUMBER', 0),
                            'started': self.starttime.isoformat()})

        self._prepareBuildDir()

        # prepare special environment, if needed
        setenv(self.config.get(u'env', []))

        class AsyncTask(threading.Thread):
            '''
            Simple wrapper around subprocess.call to execute it in a separate
            thread.
            '''
            def __init__(self, *args, **kwargs):
                super(AsyncTask, self).__init__()
                self.args = args
                self.kwargs = kwargs
                self.retcode = -1
                self.start()
            def run(self):
                self.retcode = call(*self.args, **self.kwargs)
            def wait(self):
                '''
                Block until the subprocess exits and return its exit code.
                '''
                self.join()
                return self.retcode

        class TestTask(AsyncTask):
            '''
            Asynchronously run the tests and deploy the test reports, if needed.

            The special parameter reports is passed to deployReports.
            '''
            def __init__(self, *args, **kwargs):
                self.reports = []
                self.project = None
                self.script = None

                local_args = ['reports', 'project', 'script']
                for arg in local_args:
                    setattr(self, arg, kwargs.pop(arg, None))

                self.artifacts_dir = self.script.artifacts_dir
                self.config = self.script.config
                self.platform = self.script.platform

                self.cwd = kwargs.get('cwd', os.path.curdir)

                self.started = self.completed = None

                super(TestTask, self).__init__(*args, **kwargs)

            def getTestSummary(self):
                '''
                Return the JSON object in the file summary.json in the reports, if
                it exists, otherwise an empty list.
                '''
                cadidates = [os.path.join(self.project.summary_dir,
                                          'html', 'summary.json')]
                cadidates.extend([os.path.join(rep, 'summary.json')
                                  for rep in self.reports])
                for rep in cadidates:
                    if os.path.exists(rep):
                        return json.load(codecs.open(rep, 'r', 'utf-8'))
                return []

            def run(self):
                self.started = datetime.now()
                super(TestTask, self).run()
                self.completed = datetime.now()
                # generate the test summary JSON file for the new dashboard
                self.script.dump_json({"type": "tests-result",
                                       "project": self.project.name,
                                       "started": self.started.isoformat(),
                                       "completed": self.completed.isoformat(),
                                       "results": self.getTestSummary()})
                # Find the .new files in the project directory and copy them to
                # the artifacts directory.
                self.script.log.debug('looking for .new files')
                from os.path import join, relpath
                new_refs = listAllFiles(self.cwd)
                for src in new_refs:
                    if not src.endswith('.new'):
                        continue
                    dst = join(self.artifacts_dir,
                               'newrefs.' + self.script.platform,
                               self.project.name, relpath(src, self.cwd))
                    dst = os.path.dirname(dst)
                    try:
                        self.script.keepArtifact(src, dst)
                    except IOError:
                        # ignore failures in the copy (not fatal)
                        pass
                # deploy the test reports if needed
                self.script.deployReports(self.reports)

            def __str__(self):
                '''
                Task description.
                '''
                return 'testing %s' % self.project

        class DeployArtifactsTask(threading.Thread):
            '''
            Call asynchronously 'rsync' to deploy the build artifacts.
            '''
            def __init__(self, script):
                self.script = script
                if self.script.options.rsync_dest:
                    self.retcode = -1
                    super(DeployArtifactsTask, self).__init__()
                    self.start()
                else:
                    self.retcode = 0
            def run(self):
                # create destination directory, if missing
                if ':' in self.script.options.rsync_dest:
                    host, path = self.script.options.rsync_dest.split(':', 1)
                    call(['ssh', host, 'mkdir -pv "%s"' % path])
                else:
                    ensureDirs([self.script.options.rsync_dest])

                cmd = ['rsync', '--archive', '--whole-file',
                       '--partial-dir=.rsync-partial.%s.%d' %
                       (gethostname(), os.getpid()),
                       '--delay-updates', '--rsh=ssh',
                       self.script.artifacts_dir + '/',
                       self.script.options.rsync_dest]
                self.retcode = call(cmd)
            def wait(self):
                '''
                Block until the subprocess exits and return its exit code.
                '''
                if self.script.options.rsync_dest:
                    self.join()
                return self.retcode
            def __str__(self):
                '''
                Task description.
                '''
                return 'deploy artifacts'

        jobs = []
        for proj in self.sorted_projects:
            # Consider only requested projects (if there was a selection)
            if opts.projects and proj.name.lower() not in opts.projects:
                continue # project not requested: skip

            self._prepareProject(proj)

            if not proj.enabled:
                self.log.warning('project %s disabled, skip build', proj)
                continue

            if not self.options.tests_only:
                self._buildProject(proj)
                if opts.rsync_dest:
                    jobs.append(DeployArtifactsTask(self))

            if opts.coverity:
                if proj.build_retcode != 0:
                    self.log.error('cannot run Coverity analysis on a '
                                   'failed build')
                else:
                    self._coverityAnalysis(proj)
                # try in any case to remove the Coverity intermediate directory
                # if it is on the ramdisk
                if proj.coverity_int.startswith('/dev/shm'):
                    self.log.debug('cleaning Coverity intermediate directory')
                    shutil.rmtree(proj.coverity_int, ignore_errors=True)
                    try:
                        os.removedirs(os.path.dirname(proj.coverity_int))
                    except os.error:
                        self.log.warning("failed to clean %s",
                                         proj.coverity_int)


            if opts.with_tests:
                self.log.info('testing (in background) %s', proj.dir)
                job = TestTask(['nice'] + self.test_cmd,
                               cwd=proj.build_dir,
                               script=self,
                               project=proj,
                               reports=[os.path.join(proj.summary_dir,
                                                     proj.old_build_id + suff)
                                        for suff in ['-qmtest',
                                                     '-qmtest.log']])
                jobs.append(job)

        if opts.coverity:
            # try again to clean the Coverity scratch space in the ramdisk
            # (if it was ever created)
            shutil.rmtree(os.path.join('/dev/shm/coverity.{0}'
                                       .format(self.platform)),
                          ignore_errors=True)

        if jobs:
            self.log.info('waiting for pending tasks (tests, etc.)...')
            for i, j in enumerate(jobs):
                self.log.info('- (%d/%d) %s', i+1, len(jobs), j)
                j.wait()

        self.completetime = datetime.now()

        if not opts.tests_only:
            self.dump_json({'type': 'job-end',
                            'completed': self.completetime.isoformat()})

        self.log.info('build completed in %s',
                      self.completetime - self.starttime)

        if opts.rsync_dest:
            self.log.info('deploying artifacts...')
            retcode = 1
            for _ in range(5):
                retcode = DeployArtifactsTask(self).wait()
                if retcode == 0:
                    self.log.info('... artifacts deployed')
                    break
                self.log.info('problems deploying artifacts, retrying...')
                time.sleep(30)
            else: # this "else" belong to "for count..."
                self.log.error('artifacts deployment failed')
                return retcode

        return 0

class BuildReporter(object):
    '''
    Class to analyze the build log of project and produce reports.
    '''
    def __init__(self, summary_dir, project, platform, config, old_build_id):
        '''
        Initialize the instance.

        @param summary_dir: directory of the build summaries
        @param project: ProjDesc instance of the project
        @param platform: platform id
        @param config: configuration dictionary
        @param old_build_id: build id used in the old nightly builds
        '''
        from os.path import join
        self.summary_dir = summary_dir
        self.project = project
        self.platform = platform
        self.config = config or {'slot': 'no-name'}
        self.old_build_id = old_build_id

        self.build_log = join(self.summary_dir, 'build.log')

        self._summary = None

    @property
    def summary(self):
        '''
        Summary of the errors and warnings in the log file.
        '''
        if self._summary is None:
            self._summary = self._parseLog()
        return self._summary

    def json(self):
        '''
        Return the build report summary as a JSON object (dictionary).
        '''
        w_count = sum(map(len, self.summary['warning'].values()))
        e_count = sum(map(len, self.summary['error'].values()))
        data = {}
        data.update({"type": "build-result",
                     "slot": self.config['slot'],
                     "build_id": int(os.environ.get('slot_build_id', 0)),
                     "project": self.project.name,
                     "platform": self.platform,
                     'started': self.project.started.isoformat(),
                     'completed': self.project.completed.isoformat(),
                     'retcode': self.project.build_retcode,
                     "warnings": w_count,
                     "errors": e_count})
        return data

    def genOldSummaries(self):
        '''
        Produce summary files compatible with the old dashboard.

        @return: list of generated files and directories
        '''
        from os.path import join, dirname, exists
        from itertools import islice
        import cgi

        def formatTxt(iterable, line_offset=0):
            '''
            Helper function to generate HTML version of a log file.
            '''
            lineclass = ['even', 'odd']
            yield u'<html>\n'
            for i, line in enumerate(iterable):
                style_cls = None
                found = re.search(r'\b(error|warning)\b', line, re.IGNORECASE)
                if found:
                    style_cls = found.group(1).lower()
                if (line.startswith('Scanning dependencies') or
                    line.startswith('Linking ')):
                    style_cls = 'cmake_message'
                elif re.match(r'\[[ 0-9]{3}%\]', line):
                    style_cls = 'cmake_progress'
                i += line_offset
                line = cgi.escape(line.rstrip())
                if style_cls:
                    line = ('<a id="line_%s" class="%s">%s</a>' %
                            (i, style_cls, line))
                yield u'<div class="%s">%s</div>\n' % (lineclass[i % 2],
                                                       line or '&nbsp;')
            yield u'</html>\n'

        report_files = []
        def reportFileName(suff):
            '''
            Return the name of a report file given the suffix, and add it to
            the list of report files.
            '''
            f = join(self.summary_dir, self.old_build_id + suff)
            report_files.append(f)
            return f

        log_summary = reportFileName('-log.summary')

        if not os.path.exists(self.build_log):
            # very bad: the build log was not produced, let's create a dummy one
            f = open(self.build_log, 'w')
            f.write('error: the build log file was not generated '
                    '(ctest failure?)\n')
            f.close()

        full_log = reportFileName('.log')
        shutil.copy(self.build_log, full_log)

        # generate the small summary file with the counts of warnings
        f = open(log_summary, 'w')
        f.write(self._oldSummary())
        f.close()

        # copy the build log, prepending environment and checkout
        env_lines = ['%s=%s\n' % i for i in sorted(os.environ.items())]
        if exists(join(self.summary_dir, 'checkout_job_url.txt')):
            checkout_fmt = u'<a href="{0}console">available on ''Jenkins</a>\n'
            jenkins_co_url = (open(join(self.summary_dir,
                                        'checkout_job_url.txt'))
                              .read().strip())
            checkout_lines = [checkout_fmt.format(jenkins_co_url)]
        else:
            checkout_lines = [u'<div class="even">no checkout log</div>\n']
        f = codecs.open(full_log, 'w', 'utf-8')
        f.writelines(env_lines)
        env_block_size = len(env_lines)
        f.writelines(checkout_lines)
        checkout_block_size = 1
        f.writelines(codecs.open(self.build_log, 'r', 'utf-8',
                                 errors='replace'))
        f.close()

        # generate HTML summary main page
        html_summary = reportFileName('-log.html')
        f = codecs.open(html_summary, 'w', 'utf-8')
        f.write(self._oldHtml(env_block_size, checkout_block_size))
        f.close()
        # make a copy with a simpler name
        shutil.copy(html_summary, join(self.summary_dir, 'build_log.html'))


        # generate HTML log chunks
        # - convert the sections from (name, begin) -> (name, begin, end+1)
        chunksdir = reportFileName('.log.chunks')
        ensureDirs([chunksdir])
        sections = []
        for name, begin in self.summary['sections']:
            if sections:
                sections[-1][-1] = begin
            sections.append([name, begin, 0])
        if sections:
            sections[-1][-1] = self.summary['size']
        logfile = codecs.open(self.build_log, 'r', 'utf-8', errors='replace')
        offset = 0
        for chunkname, lines in zip(['env'], [env_lines]):
            chunkname = join(chunksdir, chunkname)
            chunkfile = codecs.open(chunkname, 'w', 'utf-8')
            chunkfile.writelines(formatTxt(lines, offset))
            chunkfile.close()
            offset += len(lines)
        for chunkname, lines in zip(['checkout'], [checkout_lines]):
            chunkname = join(chunksdir, chunkname)
            chunkfile = codecs.open(chunkname, 'w', 'utf-8')
            chunkfile.write(u'<html>\n')
            chunkfile.writelines(lines)
            chunkfile.write(u'</html>\n')
            chunkfile.close()
            offset += len(lines)
        for _, begin, end in sections:
            chunkname = join(chunksdir, 'section%d' % (begin + offset))
            chunkfile = codecs.open(chunkname, 'w', 'utf-8')
            chunkfile.writelines(formatTxt(islice(logfile, end - begin), begin))
            chunkfile.close()

        # FIXME: we should make a copy with a simpler name once the new
        #        dashboard is in place
        #shutil.copytree(chunksdir, join(self.summary_dir, 'build_log.chunks'))

        # copy the JavascriptCode
        shutil.copy(join(dirname(__file__), 'logFileJQ.js'),
                    join(self.summary_dir, 'logFileJQ.js'))

        return report_files + [join(self.summary_dir, 'logFileJQ.js')]

    def _parseLog(self):
        '''
        Scan the build log file looking for warnings and errors.

        @return: a dictionary with the list of errors, warnings and ignored ones
        '''
        from collections import deque

        w_exp = re.compile(r'\bwarning\b|\bSyntaxWarning:', re.IGNORECASE)
        e_exp = re.compile(r'\berror\b', re.IGNORECASE)
        #cExp = re.compile(r'cov-|(Coverity (warning|error|message))',
        #                  re.IGNORECASE)

        class ExclusionCounter(object):
            '''
            Simple wrapper around re.search to count the number of matches.
            '''
            def __init__(self, exp):
                self.exp = exp
                self._exp = re.compile(exp)
                self.count = 0
            def search(self, line):
                '''
                Search the line for the regular expression and increase the
                counter if found.
                '''
                m = self._exp.search(line)
                if m:
                    self.count += 1
                return m

        w_exc = map(ExclusionCounter, self.config.get('warning_exceptions', []))
        e_exc = map(ExclusionCounter, self.config.get('error_exceptions', []))
        #cExc = []

        def excluded(line, excl):
            '''
            Return True if the given line matches an entry in the exclusion
            list.
            '''
            for ex in excl:
                if ex.search(line):
                    return True
            return False

        def getLineType(line):
            '''tell the type of line'''
            if e_exp.search(line) and not excluded(line, e_exc):
                return 'error'
            elif w_exp.search(line) and not excluded(line, w_exc):
                return 'warning'
            #elif cExp.search(l) and not excluded(l, cExc):
            #    return 'coverity'
            return None

        summary = dict([(k, defaultdict(list))
                        for k in ['error', 'warning', 'coverity']])
        context = deque(maxlen=5)
        sections = [] # List of section descriptions: ('name', begin)
        i = -1
        logfile = codecs.open(self.build_log, 'r', 'utf-8', errors='replace')
        current_section = 'build'
        build_section_offset = -1
        for i, line in enumerate(logfile):
            context.append(line)
            linetype = getLineType(line)
            if linetype:
                summary[linetype][line].append((i, list(context)))
            if self.config.get('USE_CMT'):
                if line.startswith('# Building package'):
                    sections.append((line.split()[3], i-1))
            else:
                if line.startswith('#### CMake'):
                    current_section = line.split()[2]
                    if current_section != 'build':
                        if sections and sections[-1][0].startswith('lines'):
                            j = i - build_section_offset
                            s = sections[-1]
                            sections[-1] = (s[0] + str(j-1), s[1])
                        sections.append((current_section, i))
                if current_section == 'build':
                    if build_section_offset < 0:
                        build_section_offset = i
                    j = i - build_section_offset
                    if (j % 500) == 0:
                        if sections and sections[-1][0].startswith('lines'):
                            s = sections[-1]
                            sections[-1] = (s[0] + str(j-1), s[1])
                        sections.append(('lines %d-' % j, i))
        summary['ignored_warning'] = [w for w in w_exc if w.count]
        summary['ignored_error'] = [e for e in e_exc if e.count]
        summary['size'] = i + 1
        summary['sections'] = sections
        return summary

    def _oldSummary(self):
        '''
        @return: content of the summary file used by the old dashboard.
        '''
        w_count = sum(map(len, self.summary['warning'].values()))
        e_count = sum(map(len, self.summary['error'].values()))
        timestamp = time.time()
        data = ('{timestamp} ({ctime}) {slot} {project}_{version} {platform}\n'
                .format(timestamp=timestamp,
                        ctime=time.ctime(timestamp),
                        slot=self.config[u'slot'],
                        project=self.project.name.upper(),
                        version=self.project.version,
                        platform=self.platform))
        data += ','.join(map(str, [w_count, e_count, 0, 0])) + '\n'
        return data

    def _oldHtml(self, env_size=0, checkout_size=0):
        '''
        @param env_size: number of lines of the log file used for the
                         environment dump
        @param checkout_size: number of lines of the log file used for the
                              checkout dump

        @return: HTML report page of the build of a project.
        '''
        from os.path import join, dirname
        from json import dumps
        from itertools import cycle
        import cgi

        html = Template(open(join(dirname(__file__),
                                  'report.template.html')).read())

        logfile_links = []
        logfile_links.append({'id': 'env',
                              'f': 0, 'l': max(0, env_size-1),
                              'desc': 'Show details of environment'})
        logfile_links.append({'id': 'checkout',
                              'f': env_size,
                              'l': env_size + max(0, checkout_size-1),
                              'desc': 'Show getpack log'})
        offset = env_size + checkout_size
        # When using CMT, the logfile_links must have 'name' and not 'desc'
        if self.config.get('USE_CMT'):
            desc_key = 'name'
        else:
            desc_key = 'desc'
        for name, begin in self.summary['sections']:
            begin += offset
            logfile_links[-1]['l'] = begin - 1
            logfile_links.append({'id': 'section%d' % begin,
                                  'f': begin,
                                  desc_key: name})
        logfile_links[-1]['l'] = offset + self.summary['size'] - 1


        ignored_counts = []
        for k in ['error', 'warning']:
            ignored = self.summary['ignored_' + k]
            if ignored:
                ignored_counts.append({'name': k + 's',
                                       'entries': [{'count': w.count,
                                                    'text': w.exp}
                                                   for w in ignored]})

        w_count = sum(map(len, self.summary['warning'].values()))
        e_count = sum(map(len, self.summary['error'].values()))
        c_count = sum(map(len, self.summary['coverity'].values()))

        def find_block(linenum):
            '''
            find the section id containing a line (+offset)
            '''
            linenum += offset
            for block in logfile_links:
                if block['f'] <= linenum <= block['l']:
                    return block['id']

        code_links = []
        def formatList(cls):
            '''
            Format the summary entries as a sequence of HTML <li> elements.

            The argument has to be a dictionary of the format:
            {'key': [(<line>, [<context>,...]), ...], ...}
            '''

            # sort the values according to their first occurrence
            values = sorted(self.summary[cls].values(), key=lambda x: x[0][0])
            li_el = '<li><a class="codeLink" id="%s%s">%s</a></li>'
            lines = []
            for val in values:
                lines.append('<ul class="%s">' % cls)
                for linenum, context_lines in val:
                    # convert a list of lines in something like
                    # ['<div class="even">line one</div>',
                    #  '<div class="odd">line two &amp;</div>']
                    context_lines = ['<div class="%s">%s</div>' % x
                         for x in zip(cycle(['even', 'odd']),
                                      map(cgi.escape, context_lines))]
                    context_lines[-1] = ('<strong>%s</strong>'
                                         % context_lines[-1].rstrip())
                    context_lines = ''.join(context_lines)
                    lines.append(li_el % (cls, linenum, context_lines))
                    code_links.append({'id': '%s%s' % (cls, linenum),
                                       'block': find_block(linenum),
                                       'line': linenum})
                lines.append('</ul>')
            return '\n'.join(lines)

        e_summ = formatList('error')
        w_summ = formatList('warning')
        c_summ = formatList('coverity')

        return html.substitute(project=self.project,
                               slot=self.config['slot'],
                               host=socket.gethostname(),
                               old_build_id=self.old_build_id,
                               logfile_links=dumps(logfile_links, indent=2),
                               code_links=dumps(code_links, indent=2),
                               ignored_counts=dumps(ignored_counts, indent=2),
                               eCount=e_count,
                               wCount=w_count,
                               covCount=c_count,
                               errors_summary=e_summ,
                               warnings_summary=w_summ,
                               coverity_summary=c_summ)
