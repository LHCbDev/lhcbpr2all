#!/usr/bin/env python
'''
Module containing the classes and functions used to build a "Nightly Build Slot".
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
import Configuration

from subprocess import call
from string import Template
from socket import gethostname
from datetime import datetime, date
try:
    from multiprocessing import cpu_count
except ImportError:
    cpu_count = lambda : 0

# no-op 'call' function for testing
#call = lambda *a,**k: None

log = logging.getLogger(__name__)

COV_PASSPHRASE_FILE = os.path.join(os.path.expanduser('~'), 'private', 'cov-admin')

def genProjectXml(name, projects):
    '''
    Take a list of ProjDesc instances and return the XML string usable to
    configure subprojects in CDash.
    '''
    versions = dict([(p.name, str(p)) for p in projects])

    xml = [u'<Project name="{0}">'.format(name)]
    for p in projects:
        xml.append(u'  <SubProject name="{0}">'.format(p))
        for d in p.deps:
            xml.append(u'    <Dependency name="{0}"/>'.format(versions[d]))
        xml.append(u'  </SubProject>')
    xml.append(u'</Project>\n')

    return u'\n'.join(xml)

def genSlotConfig(config):
    projects = config[u'projects']

    cmake = ['set(slot %(slot)s)' % config,
             'set(config $ENV{CMTCONFIG})',
             'set(projects %s)' % ' '.join([p[u'name']
                                            for p in projects])]

    for p in projects:
        cmake.append('set(%(name)s_version %(version)s)' % p)

    for p in projects:
        cmake.append('set(%s_version %s)' % (p[u'name'], ' '.join(p.get(u'dependencies', []))))

    if u'warning_exceptions' in config:
        cmake.append('set(CTEST_CUSTOM_WARNING_EXCEPTION ${CTEST_CUSTOM_WARNING_EXCEPTION}')
        for x in config[u'warning_exceptions']:
            cmake.append('    "%s"' % x.replace('\\', '\\\\').replace('"', r'\"'))
        cmake.append('    )\n')

    if u'error_exceptions' in config:
        cmake.append('set(CTEST_CUSTOM_ERROR_EXCEPTION ${CTEST_CUSTOM_ERROR_EXCEPTION}')
        for x in config[u'error_exceptions']:
            cmake.append('    "%s"' % x.replace('\\', '\\\\').replace('"', r'\"'))
        cmake.append('    )\n')

    return '\n'.join(cmake)

class ProjDesc():
    def __init__(self, desc_dict):
        self.name = desc_dict[u'name']
        self.version = desc_dict[u'version']
        self.deps = desc_dict.get(u'dependencies', [])
        self.dir = os.path.join(self.name.upper(),
                                '{0}_{1}'.format(self.name.upper(), self.version))
    def __str__(self):
        return '{0} {1}'.format(self.name, self.version)

def sortedByDeps(deps):
    '''
    Take a dictionary of dependencies as {'depender': ['dependee', ...]} and
    return the list of keys sorted according to their dependencies so that
    that a key comes after its dependencies.

    >>> sortedByDeps({'4': ['2', '3'], '3': ['1'], '2': ['1'], '1': ['0'], '0': []})
    ['0', '1', '3', '2', '4']
    '''
    def unique(l):
        '''Return only the unique elements in the list l.

        >>> unique([0, 0, 1, 2, 1])
        [0, 1, 2]
        '''
        u = []
        for i in l:
            if i not in u:
                u.append(i)
        return u
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
        excl = lambda f: False
    from os.path import join
    for r, ds, fs in os.walk(path):
        for f in fs:
            if not excl(f):
                yield join(r, f)
        ds[:] = [d for d in ds if not excl(d)]

def main():
    from optparse import OptionParser
    parser = OptionParser(usage='%prog [options] <config.json>')
    models = ['Nightly', 'Experimental', 'Continuous']
    parser.add_option('-m', '--model',
                      action='store', type='choice', choices=models,
                      help='build model: {0} (default: {0[0]}).'.format(models))
    parser.add_option('--no-clean',
                      action='store_true',
                      help='do not purge the build directory before building')
    parser.add_option('-d', '--debug',
                      action='store_const', dest='level',
                      const=logging.DEBUG,
                      help='print debug informations.')
    parser.add_option('-q', '--quiet',
                      action='store_const', dest='level',
                      const=logging.WARNING,
                      help='be less verbose.')
    parser.add_option('--timeout',
                      metavar='SECONDS',
                      action='store', type='int',
                      help='set a global timeout on all tests (default: 600)')
    parser.add_option('--build-only',
                      action='store_true',
                      help='build only, do not run the tests')
    parser.add_option('--no-submit',
                      action='store_true',
                      help='do not submit the results to CDash server')
    parser.add_option('-j', '--jobs',
                      action='store', type='int',
                      help='number of parallel jobs to use during the build '
                           '(default: sequential build)')
    parser.add_option('-l', '--load-average',
                      action='store', type='float',
                      help='load average limit for parallel builds, use 0 to '
                           'remove the limit (default: N of cores if building '
                           'in parallel)')
    parser.add_option('--build-id',
                      action='store',
                      help='string to add to the tarballs of the build to '
                           'distinguish them from others, the string can be a '
                           'format string using the parameters "timestamp" '
                           'and "slot" (a separation "." will '
                           'be added automatically) [default: %default]')

    parser.add_option('--deploy-reports-to',
                      action='store', metavar='DEST_DIR', dest='deploy_dir',
                      help='if the destination directory is specified, the '
                           'old-style summaries are deployed to that directory '
                           'as soon as they are produced')

    parser.add_option('--artifacts-dir',
                      action='store', metavar='DIR',
                      help='directory where to store the artifacts (accepts '
                           'the same format specification as --build-id) '
                           '[default: %default]')

    parser.add_option('--rsync-dest',
                      action='store', metavar='DEST',
                      help='deploy artifacts to this location using rsync '
                           '(accepts the same format specification as --build-id)')

    parser.add_option('--coverity',
                      action='store_true',
                      help='enable special Coverity static analysis on the '
                           'build (Coverity commands must be on the PATH)')

    parser.set_defaults(model=models[0],
                        level=logging.INFO,
                        timeout=600,
                        jobs=1,
                        load_average=cpu_count(),
                        build_id='{slot}.{timestamp}',
                        artifacts_dir='artifacts')

    opts, args = parser.parse_args()
    logging.basicConfig(level=opts.level,
                        format='%(asctime)s:' + logging.BASIC_FORMAT)

    if len(args) != 1:
        parser.error('wrong number of arguments')

    from os.path import join, dirname
    config = Configuration.load(args[0])

    from _utils import setDayNamesEnv
    setDayNamesEnv()

    # FIXME: we need something better
    platform = os.environ['CMTCONFIG']

    starttime = datetime.now()
    timestamp = os.environ.get('TIMESTAMP', date.today().isoformat())

    # replace tokens in the options
    expanded_tokens = {'slot': config[u'slot'], 'timestamp': timestamp}
    for opt_name in ['build_id', 'artifacts_dir', 'rsync_dest']:
        v = getattr(opts, opt_name)
        if v:
            setattr(opts, opt_name, v.format(**expanded_tokens))

    build_dir = join(os.getcwd(), 'build')
    artifacts_dir = join(os.getcwd(), opts.artifacts_dir)

    if not opts.no_clean:
        log.info('Cleaning build directory.')
        if os.path.exists(build_dir):
            shutil.rmtree(build_dir)

    # ensure that we have the artifacs directory for the sources
    if not os.path.exists(artifacts_dir):
        os.makedirs(artifacts_dir)

    if not os.path.exists(build_dir):
        os.makedirs(build_dir)

    log.info('Preparing build directory...')
    for f in os.listdir(artifacts_dir):
        if f.endswith('.tar.bz2'):
            f = join(artifacts_dir, f)
            log.info('  unpacking %s', f)
            # do not overwrite existing sources when unpacking
            # (either we just cleaned the directory or we were asked not to do it)
            call(['tar', '-x', '--no-overwrite-dir', '--keep-old-files',
                  '-f', f], cwd=build_dir)

    log.info("Generating CTest scripts and configurations.")

    def write(path, data):
        f = open(path, 'w')
        f.write(data)
        f.close()

    configCmake = genSlotConfig(config)
    ctestConfig = Template(open(join(dirname(__file__), 'CTestConfig.template.cmake')).read())
    ctestScript = Template(open(join(dirname(__file__), 'CTestScript.template.cmake')).read())

    if u'cmake_cache' in config:
        cache_preload = '\n'.join(['set(%s "%s" CACHE STRING "override")' % i
                                   for i in config[u'cmake_cache'].items()]) + '\n'
    else:
        cache_preload = None

    projects = dict([(p.name, p) for p in map(ProjDesc, config[u'projects'])])
    deps = dict([(p.name, p.deps) for p in projects.values()])
    sorted_projects = [projects[p] for p in sortedByDeps(deps)]

    project_xml = genProjectXml(config[u'slot'], sorted_projects)
    write(join(build_dir, 'Project.xml'), project_xml)
    write(join(artifacts_dir, 'Project.xml'), project_xml)
    del project_xml # no need to keep this temp variable

    # prepare special environment, if needed
    for e in config.get(u'env', []):
        n, v = e.split('=', 1)
        os.environ[n] = os.path.expandvars(v)

    fileListExcl = re.compile((r'^(InstallArea)|(build\.{0})|({0})|'
                               r'(\.git)|(\.svn)|'
                               r'(\.{0}\.d)|(Testing)|(.*\.pyc)$'
                               ).format(platform)).match

    if opts.deploy_dir:
        # ensure that the deployment dir ends with the slot name...
        if os.path.basename(opts.deploy_dir) != config[u'slot']:
            opts.deploy_dir = join(opts.deploy_dir, config[u'slot'])
        # ... and that the directory exists
        if not os.path.exists(opts.deploy_dir):
            os.makedirs(opts.deploy_dir)
        def deployReports(files):
            for f in files:
                try:
                    d = join(opts.deploy_dir, os.path.basename(f))
                    if os.path.isdir(d):
                        shutil.rmtree(d)
                    elif os.path.isfile(d) or os.path.islink(d):
                        os.remove(d)
                    log.info('Copying %s to deployment directory', f)
                    if os.path.isdir(f):
                        shutil.copytree(f, d)
                    elif os.path.isfile(f):
                        shutil.copy2(f, d)
                    else:
                        log.warning('Cannot deploy %s (does it exist?)', f)
                except os.error, err:
                    log.warning('Problems deploying %s: %s', f, err)
    else:
        def deployReports(_):
            pass

    class AsyncTask(threading.Thread):
        '''
        Simple wrapper around subprocess.call to execute it in a separate thread.
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
            self.join()
            return self.retcode

    class TestTask(AsyncTask):
        '''
        Asynchronously run the tests and deploy the test reports, if needed.

        The special parameter reports is passed to deployReports.
        '''
        def __init__(self, *args, **kwargs):
            self.reports = kwargs.get('reports', [])
            if 'reports' in kwargs:
                del kwargs['reports']
            super(TestTask, self).__init__(*args, **kwargs)
        def run(self):
            super(TestTask, self).run()
            deployReports(self.reports)

    class DeployArtifactsTask(threading.Thread):
        '''
        Call asynchronously 'rsync' to deploy the build artifacts.
        '''
        def __init__(self):
            if opts.rsync_dest:
                self.retcode = -1
                super(DeployArtifactsTask, self).__init__()
                self.start()
            else:
                self.retcode = 0
        def run(self):
            # create destination directory, if missing
            if ':' in opts.rsync_dest:
                host, path = opts.rsync_dest.split(':', 1)
                call(['ssh', host, 'mkdir -pv "%s"' % path])
            elif not os.path.exists(opts.rsync_dest):
                os.makedirs(opts.rsync_dest)

            cmd = ['rsync', '--archive',
                   '--partial-dir=.rsync-partial.'+ gethostname(),
                   '--delay-updates', '--rsh=ssh',
                   artifacts_dir + '/', opts.rsync_dest]
            self.retcode = call(cmd)
        def wait(self):
            if opts.rsync_dest:
                self.join()
            return self.retcode

    jobs = []
    for p in sorted_projects:
        projdir = join(build_dir, p.dir)
        summary_dir = join(artifacts_dir, 'summaries.{0}'.format(platform), p.name)
        # use the ramdisk for Coverity intermediate dir if possible
        if os.path.exists('/dev/shm'):
            coverity_int = join('/dev/shm/coverity.{0}'.format(platform), opts.build_id, p.name)
        else:
            coverity_int = join(build_dir, 'coverity', p.name)
        coverity_mod = join(summary_dir, 'coverity', 'models')
        coverity_logs = join(summary_dir, 'coverity', p.name)

        # ignore missing directories (the project may not have been checked out)
        if not os.path.exists(projdir):
            log.warning('no sources for %s, skip build', p)
            continue

        packname = [p.name, p.version]
        if opts.build_id:
            packname.append(opts.build_id)
        packname.append(platform)
        packname.append('tar.bz2')
        packname = '.'.join(packname)
        packname = os.path.join(artifacts_dir, packname)
        if os.path.exists(packname):
            log.info('binary tarball for %s already present, skip build', p)
            continue

        old_build_id = OLD_BUILD_ID.format(slot=config[u'slot'],
                                           today=os.environ['TODAY'],
                                           project=p.name.upper(),
                                           version=p.version,
                                           platform=platform)

        Configuration.save(join(projdir, 'SlotConfig.json'), config)
        write(join(projdir, 'SlotConfig.cmake'), configCmake)
        if cache_preload:
            write(join(projdir, 'cache_preload.cmake'), cache_preload)
        write(join(projdir, 'CTestConfig.cmake'),
              ctestConfig.substitute(config))
        write(join(projdir, 'CTestScript.cmake'),
              ctestScript.substitute({'project': p.name, 'version': p.version,
                                      'build_dir': build_dir, 'site': gethostname(),
                                      'summary_dir': summary_dir,
                                      'Model': opts.model,
                                      'old_build_id': old_build_id}))

        cmd = ['ctest', '--timeout', str(opts.timeout)]
        if opts.jobs != 1:
            cmd.append('-DJOBS=%d' % opts.jobs)
            if opts.load_average > 0:
                cmd.append('-DMAX_LOAD=%g' % opts.load_average)

        if opts.no_submit:
            cmd.append('-DNO_SUBMIT=TRUE')

        if config.get(u'USE_CMT'):
            cmd.append('-DUSE_CMT=TRUE')

        build_cmd = cmd + ['-DSTEP=BUILD', '-S', 'CTestScript.cmake']
        test_cmd = cmd + ['-DSTEP=TEST', '-S', 'CTestScript.cmake']

        if opts.level <= logging.INFO:
            build_cmd.insert(1, '-VV')
        if opts.level <= logging.DEBUG:
            test_cmd.insert(1, '-VV')

        if opts.coverity:
            # create all the directories that are missing
            map(os.makedirs, filter(lambda x: not os.path.exists(x),
                                    [coverity_int, coverity_mod, coverity_logs]))
            build_cmd = ['cov-build', '--dir', coverity_int] + build_cmd

        def writeExtraSummary(name, data):
            if not os.path.isdir(summary_dir):
                os.makedirs(summary_dir)
            f = codecs.open(os.path.join(summary_dir, name), 'w', 'utf-8')
            f.write(data)
            f.close()

        def dumpFileListSummary(name):
            data = '\n'.join(sorted(listAllFiles(projdir, fileListExcl)))
            data += '\n'
            writeExtraSummary(name, data)

        def dumpConfSummary():
            '''Create special summary file used by SetupProject.'''
            data = ''
            # find the declaration of CMTPROJECTPATH in the configuration
            for e in config.get(u'env', []):
                if e.startswith('CMTPROJECTPATH='):
                    # dump it as a list in the summary file
                    data += ('cmtProjectPathList = %r\n' %
                             map(os.path.expandvars,
                                e.split('=', 1)[1].split(':')))
            if data:
                f = codecs.open(os.path.join(artifacts_dir, 'confSummary.py'), 'w', 'utf-8')
                f.write(data)
                f.close()

        dumpConfSummary()
        dumpFileListSummary('sources.list')
        log.info('building %s', p.dir)
        build_retcode = call(build_cmd, cwd=projdir)
        if build_retcode != 0:
            log.warning('build exited with code %d', build_retcode)
        dumpFileListSummary('sources_built.list')

        reporter = BuildReporter(summary_dir, p, platform, config, old_build_id)
        deployReports(reporter.genOldSummaries())

        log.info('packing %s', p.dir)

        call(['tar', 'chjf', packname,
              os.path.join(p.dir, 'InstallArea')], cwd=build_dir)

        if opts.rsync_dest:
            jobs.append(DeployArtifactsTask())

        if opts.coverity:
            # run the Coverity analysis
            if build_retcode != 0:
                log.error('cannot run Coverity analysis on a failed build')
            else:
                # this call actually does not "submit" (commit-defects), it just
                # run the analysis
                log.info('running Coverity analysis from %s', coverity_int)
                call(['analyze-submit.sh', coverity_int, coverity_mod])
                # keep a copy of the logs
                for clf in ['log.txt', 'BUILD.metrics.xml']:
                    shutil.copy2(join(coverity_int, clf), coverity_logs)
                # collect models for use with the other projects
                log.info('collecting Coverity models')
                call(['cov-collect-models', '--dir', coverity_int,
                      '-of', join(coverity_mod, p.name + '.xmldb')])
                # ensure that there is no stale lock
                # FIXME: is it needed?
                try:
                    os.remove(join(coverity_mod, p.name + '.xmldb.lock'))
                except:
                    pass
                # commit defect to Coverity Integrity Manager
                cov_commit_cmd = ['cov-commit-defects',
                                  '--host', 'lhcb-coverity.cern.ch',
                                  '--port', '8080',
                                  '--user', 'admin',
                                  '--stream', p.name.lower() + '_trunk']
                for x in sorted_projects:
                    cov_commit_cmd.append('--strip-path')
                    cov_commit_cmd.append(join(build_dir, x.dir) + '/')
                cov_commit_cmd += open(join(coverity_int,
                                            'c', 'output',
                                            'commit-args.txt')).read().split()

                tmpenv = {'COVERITY_PASSPHRASE': open(COV_PASSPHRASE_FILE).read().strip()}
                tmpenv.update(os.environ)
                log.info('committing results Coverity Integrity Manager')
                call(cov_commit_cmd, env=tmpenv)
                del tmpenv

            # remove the Coverity intermediate directory if it is on the ramdisk
            if coverity_int.startswith('/dev/shm'):
                log.debug('cleaning Coverity intermediate directory')
                shutil.rmtree(coverity_int, ignore_errors=True)
                try:
                    os.removedirs(os.path.dirname(coverity_int))
                except os.error:
                    log.warning("failed to clean %s", coverity_int)

        if not opts.build_only and not opts.coverity:
            log.info('testing (in background) %s', p.dir)
            jobs.append(TestTask(['nice'] + test_cmd, cwd=projdir,
                                 reports = [join(summary_dir, old_build_id + suff)
                                            for suff in ['-qmtest', '-qmtest.log']]))

    if opts.coverity:
        # try again to clean the Coverity scratch space in the ramdisk (if it was ever created)
        shutil.rmtree(join('/dev/shm/coverity.{0}'.format(platform)), ignore_errors=True)

    if jobs:
        log.info('waiting for pending tasks (tests, etc.)...')
        for j in jobs:
            j.wait()

    log.info('build completed in %s', datetime.now() - starttime)
    if opts.rsync_dest:
        log.info('deploying artifacts...')
        retcode = DeployArtifactsTask().wait()
        if retcode == 0:
            log.info('... artifacts deployed')
        else:
            log.error('artifacts deployment failed')
            return retcode
    return 0

class BuildReporter(object):
    '''
    Class to analyze the build log of project and produce reports.
    '''
    def __init__(self, summary_dir, project, platform, config, old_build_id):
        '''
        Initialize the instance.

        @param build_dir: root directory of the build
        @param project: ProjDesc instance of the project
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


    def genOldSummaries(self):
        '''
        Produce summary files compatible with the old dashboard.

        @return: list of generated files and directories
        '''
        from os.path import join, dirname
        from itertools import islice
        import cgi

        def formatTxt(iterable, lineOffset=0):
            '''
            Helper function to generate HTML version of a log file.
            '''
            lineclass = ['even', 'odd']
            yield u'<html>\n'
            for i, line in enumerate(iterable):
                styleCls = None
                found = re.search(r'\b(error|warning)\b', line, re.IGNORECASE)
                if found:
                    styleCls = found.group(1).lower()
                if line.startswith('Scanning dependencies') or line.startswith('Linking '):
                    styleCls = 'cmake_message'
                elif re.match(r'\[[ 0-9]{3}%\]', line):
                    styleCls = 'cmake_progress'
                i += lineOffset
                line = cgi.escape(line.rstrip())
                if styleCls:
                    line = '<a id="line_%s" class="%s">%s</a>' % (i, styleCls, line)
                yield u'<div class="%s">%s</div>\n' % (lineclass[i % 2], line or '&nbsp;')
            yield u'</html>\n'

        report_files = []
        def reportFileName(suff):
            f = join(self.summary_dir, self.old_build_id + suff)
            report_files.append(f)
            return f

        log_summary = reportFileName('-log.summary')

        if not os.path.exists(self.build_log):
            # very bad: the build log was not produced, let's create a dummy one
            f = open(self.build_log, 'w')
            f.write('error: the build log file was not generated (ctest failure?)\n')
            f.close()

        full_log = reportFileName('.log')
        shutil.copy(self.build_log, full_log)

        # generate the small summary file with the counts of warnings
        f = open(log_summary, 'w')
        f.write(self._oldSummary())
        f.close()

        # copy the build log, prepending environment and checkout
        env_lines = ['%s=%s\n' % i for i in sorted(os.environ.items())]
        checkout_lines = ['no checkout log\n']
        f = codecs.open(full_log, 'w', 'utf-8')
        f.writelines(env_lines)
        env_block_size = len(env_lines)
        f.writelines(checkout_lines)
        checkout_block_size = 1
        f.writelines(codecs.open(self.build_log, 'r', 'utf-8'))
        f.close()

        # generate HTML summary main page
        html_summary = reportFileName('-log.html')
        f = codecs.open(html_summary, 'w', 'utf-8')
        f.write(self._oldHtml(env_block_size, checkout_block_size))
        f.close()


        # generate HTML log chunks
        # - convert the sections from (name, start) -> (name, start, end+1)
        chunksdir = reportFileName('.log.chunks')
        if not os.path.isdir(chunksdir):
            os.makedirs(chunksdir)
        sections = []
        for n, i in self.summary['sections']:
            if sections:
                sections[-1][-1] = i
            sections.append([n, i, 0])
        sections[-1][-1] = self.summary['size']
        logfile = codecs.open(self.build_log, 'r', 'utf-8')
        offset = 0
        for n, lines in zip(['env', 'checkout'], [env_lines, checkout_lines]):
            chunkname = join(chunksdir, n)
            chunkfile = codecs.open(chunkname, 'w', 'utf-8')
            chunkfile.writelines(formatTxt(lines, offset))
            chunkfile.close()
            offset += len(lines)
        for n, b, e in sections:
            chunkname = join(chunksdir, 'section%d' % (b+offset))
            chunkfile = codecs.open(chunkname, 'w', 'utf-8')
            chunkfile.writelines(formatTxt(islice(logfile, e-b), b))
            chunkfile.close()

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

        wExp = re.compile(r'\bwarning\b', re.IGNORECASE)
        eExp = re.compile(r'\berror\b', re.IGNORECASE)
        #cExp = re.compile(r'cov-|(Coverity (warning|error|message))', re.IGNORECASE)

        class ExclusionCounter(object):
            '''
            Simple wrapper around re.search to count the number of matches.
            '''
            def __init__(self, exp):
                self.exp = exp
                self._exp = re.compile(exp)
                self.count = 0
            def search(self, l):
                r = self._exp.search(l)
                if r:
                    self.count += 1
                return r

        wExc = map(ExclusionCounter, self.config.get('warning_exceptions', []))
        eExc = map(ExclusionCounter, self.config.get('error_exceptions', []))
        #cExc = []

        def excluded(l, excl):
            for e in excl:
                if e.search(l):
                    return True
            return False

        class ListDict(dict):
            def append(self, k, v):
                if k not in self:
                    self[k] = [v]
                else:
                    self[k].append(v)

        def getLineType(l):
            '''tell the type of line'''
            if eExp.search(l) and not excluded(l, eExc):
                return 'error'
            elif wExp.search(l) and not excluded(l, wExc):
                return 'warning'
            #elif cExp.search(l) and not excluded(l, cExc):
            #    return 'coverity'
            return None

        summary = dict([(k, ListDict()) for k in ['error', 'warning', 'coverity']])
        context = deque()
        sections = [] # List of section descriptions: ('name', start)
        i = -1
        logfile = codecs.open(self.build_log, 'r', 'utf-8')
        current_section = 'build'
        build_section_offset = -1
        for i, l in enumerate(logfile):
            context.append(l)
            if len(context) > 5:
                context.popleft()
            t = getLineType(l)
            if t:
                summary[t].append(l, (i, list(context)))
            if self.config.get('USE_CMT'):
                if l.startswith('# Building package'):
                    sections.append((l.split()[3], i-1))
            else:
                if l.startswith('#### CMake'):
                    current_section = l.split()[2]
                    if current_section != 'build':
                        if sections and sections[-1][0].startswith('lines'):
                            i2 = i - build_section_offset
                            s = sections[-1]
                            sections[-1] = (s[0] + str(i2-1), s[1])
                        sections.append((current_section, i))
                if current_section == 'build':
                    if build_section_offset < 0:
                        build_section_offset = i
                    i2 = i - build_section_offset
                    if (i2 % 500) == 0:
                        if sections and sections[-1][0].startswith('lines'):
                            s = sections[-1]
                            sections[-1] = (s[0] + str(i2-1), s[1])
                        sections.append(('lines %d-' % i2, i))
        summary['ignored_warning'] = [w for w in wExc if w.count]
        summary['ignored_error'] = [e for e in eExc if e.count]
        summary['size'] = i + 1
        summary['sections'] = sections
        return summary

    def _oldSummary(self):
        '''
        @return: content of the summary file used by the old dashboard.
        '''
        wCount = sum(map(len, self.summary['warning'].values()))
        eCount = sum(map(len, self.summary['error'].values()))
        t = time.time()
        data = ('{t} ({at}) {slot} {project}_{version} {platform}\n'
                .format(t=t,
                        at=time.ctime(t),
                        slot=self.config[u'slot'],
                        project=self.project.name.upper(),
                        version=self.project.version,
                        platform=self.platform))
        data += ','.join(map(str, [wCount, eCount, 0, 0])) + '\n'
        return data

    def _oldHtml(self, env_size=0, checkout_size=0):
        '''
        @param env_size: number of lines of the log file used for the environment dump
        @param checkout_size: number of lines of the log file used for the checkout dump

        @return: HTML report page of the build of a project.
        '''
        from os.path import join, dirname
        from json import dumps
        from itertools import cycle
        import cgi

        html = Template(open(join(dirname(__file__), 'report.template.html')).read())

        logfile_links = []
        logfile_links.append({'id': 'env',
                              'f': 0, 'l': max(0, env_size-1),
                              'desc': 'Show details of environment'})
        logfile_links.append({'id': 'checkout',
                              'f': env_size, 'l': env_size + max(0, checkout_size-1),
                              'desc': 'Show getpack log'})
        offset = env_size + checkout_size
        # When using CMT, the logfile_links must have 'name' and not 'desc'
        if self.config.get('USE_CMT'):
            descKey = 'name'
        else:
            descKey = 'desc'
        for n, i in self.summary['sections']:
            i += offset
            logfile_links[-1]['l'] = i - 1
            logfile_links.append({'id': 'section%d' % i,
                                  'f': i,
                                  descKey: n})
        logfile_links[-1]['l'] = self.summary['size'] - 1


        ignored_counts = []
        for k in ['error', 'warning']:
            ignored = self.summary['ignored_' + k]
            if ignored:
                ignored_counts.append({'name': k + 's',
                                       'entries': [{'count': w.count,
                                                    'text': w.exp}
                                                   for w in ignored]})

        wCount = sum(map(len, self.summary['warning'].values()))
        eCount = sum(map(len, self.summary['error'].values()))
        cCount = sum(map(len, self.summary['coverity'].values()))

        def find_block(l):
            l += offset
            for d in logfile_links:
                if d['f'] <= l <= d['l']:
                    return d['id']

        code_links = []
        def formatList(cls):
            '''
            Format the summary entries as a sequence of HTML <li> elements.

            The argument has to be a dictionary of the format:
            {'key': [(<line>, [<context>,...]), ...], ...}
            '''

            # sort the values according to their first occurrence
            values = sorted(self.summary[cls].values(), key=lambda x: x[0][0])
            li = '<li><a class="codeLink" id="%s%s">%s</a></li>'
            lines = []
            for v in values:
                lines.append('<ul class="%s">' % cls)
                for l, c in v:
                    # convert a list of lines in something like
                    # ['<div class="even">line one</div>',
                    #  '<div class="odd">line two &amp;</div>']
                    c = ['<div class="%s">%s</div>' % x
                         for x in zip(cycle(['even', 'odd']),
                                      map(cgi.escape, c))]
                    c[-1] = '<strong>%s</strong>' % c[-1].rstrip()
                    c = ''.join(c)
                    lines.append(li % (cls, l, c))
                    code_links.append({'id': '%s%s' % (cls, l),
                                       'block': find_block(l),
                                       'line': l})
                lines.append('</ul>')
            return '\n'.join(lines)

        eSumm = formatList('error')
        wSumm = formatList('warning')
        cSumm = formatList('coverity')

        return html.substitute(project=self.project,
                               slot=self.config['slot'],
                               host=socket.gethostname(),
                               old_build_id=self.old_build_id,
                               logfile_links=dumps(logfile_links, indent=2),
                               code_links=dumps(code_links, indent=2),
                               ignored_counts=dumps(ignored_counts, indent=2),
                               eCount=eCount,
                               wCount=wCount,
                               covCount=cCount,
                               errors_summary=eSumm,
                               warnings_summary=wSumm,
                               coverity_summary=cSumm)
