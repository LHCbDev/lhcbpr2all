#!/usr/bin/env python
'''
Module containing the classes and functions used to checkout a set of projects,
fixing their dependencies to produce a consistent set.
'''
__author__ = 'Marco Clemencic <marco.clemencic@cern.ch>'

import logging
import shutil
import os
import re
import time
import socket
import Configuration
from subprocess import Popen, call
from string import Template
from socket import gethostname
from datetime import date

log = logging.getLogger(__name__)

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
        cmake.append('set(%s_version %s)' % (p[u'name'], ' '.join(p[u'dependencies'])))

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
                      action='store', type='string',
                      help='set a global timeout on all tests (default: 600)')
    parser.add_option('--build-only',
                      action='store_true',
                      help='build only, do not run the tests')
    parser.add_option('--no-submit',
                      action='store_true',
                      help='do not submit the results to CDash server')
    parser.add_option('-j', '--jobs',
                      action='store',
                      help='number of parallel jobs to use during the build (default: sequential build)')
    parser.add_option('--build-id',
                      action='store',
                      help='string to add to the tarballs of the build to '
                           'distinguish them from others, the string can be a '
                           'format string using the parameters "timestamp" '
                           'and "slot" (a separation "." will '
                           'be added automatically) [default: %default]')

    parser.set_defaults(model=models[0],
                        level=logging.INFO,
                        timeout='600',
                        jobs='1',
                        build_id='{slot}.{timestamp}')

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

    from datetime import datetime
    starttime = datetime.now()

    build_dir = join(os.getcwd(), 'build')
    sources_dir = join(os.getcwd(), 'sources')

    if not opts.no_clean:
        log.info('Cleaning directories.')
        if os.path.exists(build_dir):
            shutil.rmtree(build_dir)

    if not os.path.exists(build_dir):
        os.makedirs(build_dir)
        log.info('Preparing sources...')
        for f in os.listdir(sources_dir):
            if f.endswith('.tar.bz2'):
                f = join(sources_dir, f)
                log.info('  unpacking %s', f)
                # do not overwrite existing sources when unpacking
                # (either we just cleaned the directory or we were asked not to do it)
                call(['tar', '-x', '--no-overwrite-dir', '--keep-old-files',
                      '-f', f], cwd=build_dir)

    log.info("Generating CTest scripts and configurations.")
    timestamp = date.today().isoformat()

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

    write(join(build_dir, 'Project.xml'),
          genProjectXml(config[u'slot'], sorted_projects))

    # prepare special environment, if needed
    for e in config.get(u'env', []):
        n, v = e.split('=', 1)
        os.environ[n] = os.path.expandvars(v)

    fileListExcl = re.compile((r'^(InstallArea)|(build\.{0})|({0})|'
                               r'(\.git)|(\.svn)|'
                               r'(\.{0}\.d)|(Testing)$'
                               ).format(platform)).match

    jobs = []
    for p in sorted_projects:
        projdir = join(build_dir, p.dir)

        # ignore missing directories (the project may not have been checked out)
        if not os.path.exists(projdir):
            log.warning('no sources for %s, skip build', p)
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
                                      'Model': opts.model,
                                      'old_build_id': old_build_id}))

        cmd = ['ctest', '--timeout', opts.timeout]
        if opts.jobs != '1':
            cmd.append('-DJOBS=' + opts.jobs)
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

        def dumpFileListSummary(name):
            d = os.path.join(build_dir, 'summaries', p.name)
            if not os.path.isdir(d):
                os.makedirs(d)
            filelist = open(os.path.join(d, name), 'w')
            filelist.write('\n'.join(sorted(listAllFiles(projdir, fileListExcl))))
            filelist.write('\n')
            filelist.close()

        dumpFileListSummary('sources.list')
        log.info('building %s', p.dir)
        call(build_cmd, cwd=projdir)
        dumpFileListSummary('sources_built.list')

        reporter = BuildReporter(build_dir, p, platform, config, old_build_id)
        reporter.genOldSummaries()

        log.info('packing %s', p.dir)
        packname = [p.name, p.version]
        if opts.build_id:
            packname.append(opts.build_id.format(slot=config[u'slot'],
                                                 timestamp=timestamp))
        packname.append(platform)
        packname.append('tar.bz2')
        packname = '.'.join(packname)

        call(['tar', 'chjf', packname,
              os.path.join(p.dir, 'InstallArea')], cwd=build_dir)

        if not opts.build_only:
            log.info('testing (in background) %s', p.dir)
            jobs.append(Popen(test_cmd, cwd=projdir))

    if jobs:
        log.info('waiting for tests still running...')
        for j in jobs:
            j.wait()

    log.info('build completed in %s', datetime.now() - starttime)
    return 0

class BuildReporter(object):
    '''
    Class to analyze the build log of project and produce reports.
    '''
    def __init__(self, build_dir, project, platform, config, old_build_id):
        '''
        Initialize the instance.

        @param build_dir: root directory of the build
        @param project: ProjDesc instance of the project
        @param config: configuration dictionary
        @param old_build_id: build id used in the old nightly builds
        '''
        from os.path import join
        self.build_dir = build_dir
        self.project = project
        self.platform = platform
        self.config = config or {'slot': 'no-name'}
        self.old_build_id = old_build_id

        self.summary_dir = join(self.build_dir, 'summaries', project.name)
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
        '''
        from os.path import join, dirname
        from itertools import islice
        import cgi
        import codecs

        def formatTxt(iterable, lineOffset=0):
            '''
            Helper function to generate HTML version of a log file.
            '''
            lineclass = ["even", "odd"]
            yield '<html>\n'
            for i, line in enumerate(iterable):
                styleCls = None
                found = re.search(r'\b(error|warning)\b', line, re.IGNORECASE)
                if found:
                    styleCls = found.group(1).lower()
                if line.startswith("Scanning dependencies") or line.startswith("Linking "):
                    styleCls = "cmake_message"
                elif re.match(r'\[[ 0-9]{3}%\]', line):
                    styleCls = 'cmake_progress'
                i += lineOffset
                line = cgi.escape(line.rstrip())
                if styleCls:
                    line = '<a id="line_%s" class="%s">%s</a>' % (i, styleCls, line)
                yield '<div class="%s">%s</div>\n' % (lineclass[i % 2], line.encode('UTF-8'))
            yield '</html>\n'

        log_summary = join(self.summary_dir, self.old_build_id + '-log.summary')

        if not os.path.exists(self.build_log):
            # very bad: the build log was not produced, let's create a dummy one
            f = open(self.build_log, 'w')
            f.write('error: the build log file was not generated (ctest failure?)\n')
            f.close()

        shutil.copy(self.build_log, log_summary.replace('-log.summary', '.log'))

        # generate the small summary file with the counts of warnings
        f = open(log_summary, 'w')
        f.write(self._oldSummary())
        f.close()

        # copy the build log, prepending environment and checkout
        env_lines = ['%s=%s\n' % i for i in sorted(os.environ.items())]
        checkout_lines = ['no checkout log\n']
        f = codecs.open(log_summary.replace('-log.summary', '.log'), 'w', 'utf-8')
        f.writelines(env_lines)
        env_block_size = len(env_lines)
        f.writelines(checkout_lines)
        checkout_block_size = 1
        f.writelines(codecs.open(self.build_log, 'r', 'utf-8'))
        f.close()

        # generate HTML summary main page
        html_summary = log_summary.replace('.summary', '.html')
        f = codecs.open(html_summary, 'w', 'utf-8')
        f.write(self._oldHtml(env_block_size, checkout_block_size))
        f.close()


        # generate HTML log chunks
        # - convert the sections from (name, start) -> (name, start, end+1)
        sections = []
        for n, i in self.summary['sections']:
            if sections:
                sections[-1][-1] = i
            sections.append([n, i, 0])
        sections[-1][-1] = self.summary['size']
        logfile = codecs.open(self.build_log, 'r', 'utf-8')
        offset = 0
        for n, lines in zip(['env', 'checkout'], [env_lines, checkout_lines]):
            chunkfile = codecs.open(log_summary.replace('-log.summary', '.log.' + n), 'w', 'utf-8')
            chunkfile.writelines(formatTxt(lines, offset))
            chunkfile.close()
            offset += len(lines)
        for n, b, e in sections:
            chunkfile = codecs.open(log_summary.replace('-log.summary', '.log.section%d' % (b+offset)), 'w', 'utf-8')
            chunkfile.writelines(formatTxt(islice(logfile, e-b), b))
            chunkfile.close()

        # copy the JavascriptCode
        shutil.copy(join(dirname(__file__), 'logFileJQ.js'),
                    join(self.summary_dir, 'logFileJQ.js'))


    def _parseLog(self):
        '''
        Scan the build log file looking for warnings and errors.

        @return: a dictionary with the list of errors, warnings and ignored ones
        '''
        import codecs
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
