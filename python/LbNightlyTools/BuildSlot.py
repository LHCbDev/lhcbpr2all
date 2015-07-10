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

from LbNightlyTools.Configuration import getSlot, parse as parseConfig
from LbNightlyTools.Utils import timeout_call as call, ensureDirs, pack, chdir
from LbNightlyTools.Utils import Dashboard
from LbNightlyTools.RsyncManager import execute_rsync

from string import Template
from datetime import datetime
from collections import defaultdict
from os.path import join

try:
    from collections import OrderedDict
except ImportError:
    # Backward compatibility with older versions of Python
    # (CMTCONFIG=*-slc6-gcc46-*)
    OrderedDict = dict

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

def listAllFiles(path, excl=None):
    '''
    Return the list of all files in a directory and in its subdirectories.
    '''
    if excl is None:
        excl = lambda _: False
    for root, dirs, files in os.walk(path):
        for f in files:
            if not excl(f):
                yield join(root, f)
        dirs[:] = [d for d in dirs if not excl(d)]

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
    Script to build the projects in a slot configuration.
    '''
    __usage__ = '%prog [options] <slot name or config file>'
    __version__ = ''

    # unavoidable or fake warnings
    # pylint: disable=E1002,W0201
    def defineBuildOptions(self):
        '''
        Add build-specific options to the parser.
        '''
        from optparse import OptionGroup
        group = OptionGroup(self.parser, "Build Options")

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

        group.add_option('--coverity',
                         action='store_true',
                         help='enable special Coverity static analysis on the '
                              'build (Coverity commands must be on the PATH)')

        self.parser.add_option_group(group)
        if 'LBN_LOAD_AVERAGE' in os.environ:
            load_average = float(os.environ['LBN_LOAD_AVERAGE'])
        else:
            load_average = cpu_count()*LOAD_AVERAGE_SCALE
        self.parser.set_defaults(jobs=1,
                                 load_average=load_average,
                                 coverity=False)

    def defineOpts(self):
        '''
        Prepare the option parser.
        '''
        from LbNightlyTools.ScriptsCommon import (addBasicOptions,
                                                  addBuildDirOptions,
                                                  addDeploymentOptions,
                                                  addDashboardOptions)

        addBasicOptions(self.parser)

        self.defineBuildOptions()

        addBuildDirOptions(self.parser)

        addDeploymentOptions(self.parser)

        addDashboardOptions(self.parser)

    def _setup(self):
        '''
        Initialize variables.
        '''
        from os.path import basename, exists
        from LbNightlyTools.ScriptsCommon import expandTokensInOptions

        opts = self.options

        if exists(self.args[0].split('#')[0]):
            self.slot = parseConfig(self.args[0])
        else:
            self.slot = getSlot(self.args[0],
                           'configs' if exists('configs') else os.curdir)

        from LbNightlyTools.Utils import setDayNamesEnv
        setDayNamesEnv()

        # FIXME: we need something better
        self.platform = os.environ['CMTCONFIG']

        self._file_excl_rex = re.compile((r'^(InstallArea)|(build\.{0})|({0})|'
                                          r'(\.git)|(\.svn)|'
                                          r'(\.{0}\.d)|(Testing)|(.*\.pyc)$'
                                          ).format(self.platform))

        self.starttime = datetime.now()

        expandTokensInOptions(opts, ['build_id', 'artifacts_dir', 'rsync_dest'],
                              slot=self.slot.name)

        self.build_dir = join(os.getcwd(), 'build')
        self.artifacts_dir = join(os.getcwd(), opts.artifacts_dir)

        # ensure that we have the artifacts directory for the sources
        ensureDirs([self.artifacts_dir, self.build_dir])

        # template data to be reported in every JSON file
        self.json_tmpl = {'slot': self.slot.name,
                          'build_id': int(os.environ.get('slot_build_id', 0)),
                          'platform': self.platform}

        self.dashboard = Dashboard(credentials=None,
                                   dumpdir=os.path.join(self.artifacts_dir,
                                                        'db'),
                                   submit=opts.submit,
                                   flavour=opts.flavour)
        if opts.projects:
            opts.projects = set(p.strip().lower()
                                for p in opts.projects.split(','))
        else:
            opts.projects = None

        if opts.deploy_dir:
            # ensure that the deployment dir ends with the slot name...
            if basename(opts.deploy_dir) != self.slot.name:
                opts.deploy_dir = join(opts.deploy_dir, self.slot.name)
            # ... and that the directory exists
            ensureDirs([opts.deploy_dir])

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
        with codecs.open(path, 'w', 'utf-8') as f:
            f.write(data)

    def writeBin(self, path, data):
        '''
        Simple function to write some binary data to a file.

        @param path: name of the file to write
        @param data: string to write
        '''
        self.log.debug('writing (bin) %s', path)
        ensureDirs([os.path.dirname(path)])
        with open(path, 'wb') as f:
            f.write(data)

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
        from os.path import basename, isdir, isfile, islink
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
            # FIXME: this can be done asynchronously
            self.log.info('Cleaning build directory.')
            if os.path.exists(self.build_dir):
                shutil.rmtree(self.build_dir)
                ensureDirs([self.build_dir])

        if not self.options.no_unpack:
            # FIXME: this can be done asynchronously
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

        def dumpConfSummary():
            '''Create special summary file used by SetupProject.'''
            data = defaultdict(list)
            env = dict(decl.split('=', 1)
                       for decl in self.slot.env)
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

        # keep a list of the files in the source directories before the build
        for proj in self.slot.activeProjects:
            self._recordSourcesLists(proj, 'sources.list')

    def _summaryDir(self, proj, *subdirs):
        '''
        Return the path to the summary directory for a given project.

        If extra arguments are given, the output is equivalent to
        os.path.join(self._summaryDir(proj), level1, level2).
        '''
        return join(self.artifacts_dir, 'summaries.' + self.platform,
                    proj.name, *subdirs)

    def _buildDir(self, proj, *subdirs):
        '''
        Return the path to the build directory for a given project.

        If extra arguments are given, the output is equivalent to
        os.path.join(self._buildDir(proj), level1, level2).
        '''
        return join(self.build_dir, proj.baseDir, *subdirs)

    def _recordSourcesLists(self, proj, name):
        '''
        Record the list of files in the sources directories for a project.

        @param proj: project instance to scan
        @param name: name of the file to write in the project summary dir
        '''
        # keep a list of the files in the source directories
        data = sorted(listAllFiles(self._buildDir(proj),
                                   self._file_excl_rex.match))
        data.append('')
        self.write(self._summaryDir(proj, name), '\n'.join(data))

    def main(self):
        '''
        Main function of the script.
        '''
        if len(self.args) != 1:
            self.parser.error('wrong number of arguments')

        opts = self.options

        if opts.coverity:
            self.log.warning('Coverity analysis not implemented yet')

        self._setup()

        if opts.submit and not opts.projects:
            # ensure that results for the current slot/build/platform are
            # not in the dashboard (useful in case of rebuild), but only
            # if we need to publish the results and it's not a partial build
            self.dashboard.dropBuild(slot=self.json_tmpl['slot'],
                                     build_id=self.json_tmpl['build_id'],
                                     platform=self.json_tmpl['platform'])

        self._prepareBuildDir()

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

                self.retcode = execute_rsync(self.script.artifacts_dir,
                                             self.script.options.rsync_dest)
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
        from subprocess import STDOUT
        with chdir(self.build_dir):
            for proj, result in self.slot.buildGen(projects=opts.projects,
                                                   stderr=STDOUT):
                # get the project instance
                proj = getattr(self.slot, proj)
                summary_dir = self._summaryDir(proj)

                ensureDirs([summary_dir])
                if result.returncode != 0:
                    self.log.warning('build exited with code %d',
                                     result.returncode)

                if self.slot.name == 'lhcb-release':
                    manifest_file = self._buildDir(proj, 'InstallArea',
                                                   self.platform,
                                                   'manifest.xml')
                    if not os.path.exists(manifest_file):
                        self.log.warning('%s not generated by the build, '
                                         'we try to produce one',
                                         manifest_file)
                        from LbNightlyTools.Release import createManifestFile
                        # ensure that the destination directory exists, in case
                        # of builds that failed very badly
                        if not os.path.exists(os.path.dirname(manifest_file)):
                            os.makedirs(os.path.dirname(manifest_file))
                        with open(manifest_file, 'w') as manif:
                            manif.write(createManifestFile(proj.name, proj.version,
                                                           self.platform,
                                                           proj.build_dir))

                with open(join(summary_dir, 'build.log'), 'w') as f:
                    f.write(result.stdout)
                reporter = BuildReporter(summary_dir, proj.name,
                                         self.platform,
                                         self.slot, result)
                self.deployReports(reporter.genOldSummaries())
                self.dump_json(reporter.json())

                self._recordSourcesLists(proj, 'sources_built.list')

                self.log.info('packing %s', proj.baseDir)

                pack([os.path.join(proj.baseDir, 'InstallArea')],
                     genPackageName(proj, self.platform,
                                    build_id=self.options.build_id,
                                    artifacts_dir=self.artifacts_dir),
                     cwd=self.build_dir, checksum='md5')

                # FIXME
                if proj.with_shared:
                    shr_packname = genPackageName(proj, "shared",
                                                  build_id=self.options.build_id,
                                                  artifacts_dir=self.artifacts_dir)
                    to_pack_list = (set(open(join(summary_dir,
                                                  'sources_built.list'))) -
                                    set(open(join(summary_dir,
                                                  'sources.list'))))
                    pack([os.path.relpath(f.strip(), self.build_dir)
                          for f in sorted(to_pack_list)],
                         shr_packname, cwd=self.build_dir, checksum='md5')

        if jobs:
            self.log.info('waiting for pending tasks...')
            for i, j in enumerate(jobs):
                self.log.info('- (%d/%d) %s', i+1, len(jobs), j)
                j.wait()

        self.completetime = datetime.now()

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
    def __init__(self, summary_dir, project, platform, slot, result):
        '''
        Initialize the instance.

        @param summary_dir: directory of the build summaries
        @param project: ProjDesc instance of the project
        @param platform: platform id
        @param config: configuration dictionary
        '''
        self.summary_dir = summary_dir
        self.project = project
        self.platform = platform
        self.slot = slot
        self.result = result

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
                     "slot": self.slot.name,
                     "build_id": int(os.environ.get('slot_build_id', 0)),
                     "project": self.project,
                     "platform": self.platform,
                     'started': self.result.started.isoformat(),
                     'completed': self.result.completed.isoformat(),
                     'retcode': self.result.returncode,
                     "warnings": w_count,
                     "errors": e_count})
        return data

    def genOldSummaries(self):
        '''
        Produce summary files compatible with the old dashboard.

        @return: list of generated files and directories
        '''
        from os.path import dirname, exists
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
                elif re.search(r'\*\*\* Break \*\*\*', line, re.IGNORECASE):
                    style_cls = 'error'
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

        if not os.path.exists(self.build_log):
            # very bad: the build log was not produced, let's create a dummy one
            f = open(self.build_log, 'w')
            f.write('error: the build log file was not generated '
                    '(ctest failure?)\n')
            f.close()

        # copy the build log, prepending environment and checkout
        env_lines = ['%s=%s\n' % i for i in sorted(os.environ.items())]
        checkout_logfile = join(self.summary_dir, os.pardir, os.pardir,
                                self.project + '.checkout.log')
        if exists(checkout_logfile):
            def checkout_log():
                from itertools import cycle
                from xml.sax.saxutils import escape
                cl = cycle(('even', 'odd'))
                for l in open(checkout_logfile):
                    yield u'<div class="{0}">{1}</div>\n'.format(cl.next(),
                                                                 escape(l))
            checkout_lines = list(checkout_log())
        elif exists(join(self.summary_dir, os.pardir, os.pardir,
                         'checkout_job_url.txt')):
            checkout_fmt = u'<a href="{0}console">available on ''Jenkins</a>\n'
            jenkins_co_url = (open(join(self.summary_dir,
                                        os.pardir, os.pardir,
                                        'checkout_job_url.txt'))
                              .read().strip())
            checkout_lines = [checkout_fmt.format(jenkins_co_url)]
        else:
            checkout_lines = [u'<div class="even">no checkout log</div>\n']

        # generate HTML summary main page
        html_summary = join(self.summary_dir, 'build_log.html')
        f = codecs.open(html_summary, 'w', 'utf-8')
        f.write(self._oldHtml(len(env_lines), len(checkout_lines)))
        f.close()


        # generate HTML log chunks
        # - convert the sections from (name, begin) -> (name, begin, end+1)
        chunksdir = join(self.summary_dir, 'build_log.chunks')
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

        # copy the JavascriptCode
        shutil.copy(join(dirname(__file__), 'logFileJQ.js'),
                    join(self.summary_dir, 'logFileJQ.js'))

        return [join(self.summary_dir, 'logFileJQ.js')]

    def _parseLog(self):
        '''
        Scan the build log file looking for warnings and errors.

        @return: a dictionary with the list of errors, warnings and ignored ones
        '''
        from collections import deque

        w_exp = re.compile(r'\bwarning\b|\bSyntaxWarning:', re.IGNORECASE)
        e_exp = re.compile(r'\berror\b|\*\*\* Break \*\*\*', re.IGNORECASE)
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

        w_exc = map(ExclusionCounter, self.slot.warning_exceptions)
        e_exc = map(ExclusionCounter, self.slot.error_exceptions)
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
        current_section = 'all'
        build_section_offset = -1
        for i, line in enumerate(logfile):
            context.append(line)
            linetype = getLineType(line)
            if linetype:
                summary[linetype][line].append((i, list(context)))
            if str(self.slot.build_tool) == 'CMT':
                if line.startswith('# Building package'):
                    sections.append((line.split()[3], i-1))
            else:
                if line.startswith('#### CMake'):
                    current_section = line.split()[2]
                    if current_section != 'all':
                        if sections and sections[-1][0].startswith('lines'):
                            j = i - build_section_offset
                            s = sections[-1]
                            sections[-1] = (s[0] + str(j-1), s[1])
                        sections.append((current_section, i))
                if current_section == 'all':
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

    def _oldHtml(self, env_size=0, checkout_size=0):
        '''
        @param env_size: number of lines of the log file used for the
                         environment dump
        @param checkout_size: number of lines of the log file used for the
                              checkout dump

        @return: HTML report page of the build of a project.
        '''
        from os.path import dirname
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
                              'desc': 'Show checkout log'})
        offset = env_size + checkout_size

        special_sections = set(['configure', "'global'",
                                'install', 'unsafe-install', 'post-install'])
        for name, begin in self.summary['sections']:
            begin += offset
            logfile_links[-1]['l'] = begin - 1
            desc = (('' if name in special_sections or name.startswith('lines')
                     else 'Package ') +
                    ('<strong>%s</strong>' % name))
            logfile_links.append({'id': 'section%d' % begin,
                                  'f': begin,
                                  'name': name,
                                  'desc': desc})
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
                               slot=self.slot.name,
                               host=socket.gethostname(),
                               logfile_links=dumps(logfile_links, indent=2),
                               code_links=dumps(code_links, indent=2),
                               ignored_counts=dumps(ignored_counts, indent=2),
                               eCount=e_count,
                               wCount=w_count,
                               covCount=c_count,
                               errors_summary=e_summ,
                               warnings_summary=w_summ,
                               coverity_summary=c_summ)
