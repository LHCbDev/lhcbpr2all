#!/usr/bin/env python
'''
Module containing the classes and functions used to checkout a set of projects,
fixing their dependencies to produce a consistent set.
'''
__author__ = 'Marco Clemencic <marco.clemencic@cern.ch>'

import logging
import shutil
import os
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
            cmake.append('    "%s"' % x.replace('"', r'\"'))
        cmake.append('    )\n')

    if u'error_exceptions' in config:
        cmake.append('set(CTEST_CUSTOM_ERROR_EXCEPTION ${CTEST_CUSTOM_ERROR_EXCEPTION}')
        for x in config[u'error_exceptions']:
            cmake.append('    "%s"' % x.replace('"', r'\"'))
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
                call(['tar', 'xf', f], cwd=build_dir)

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

        log.info('building %s', p.dir)
        call(build_cmd, cwd=projdir)

        genBuildLogReport(build_dir, p, platform, config, old_build_id)

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

def parseBuildLog(logfile, config=None):
    '''
    Scan a build log file looking for warnings and errors.

    @param logfile: file object (iterable) to process
    @param config: configuration dictionary, with the list of exclusions
    @return: generator of warnings or errors as tuples (line_number, type, message)
    '''
    import re
    from collections import deque

    if config is None:
        config = {}

    wExp = re.compile(r'\bwarning\b', re.IGNORECASE)
    eExp = re.compile(r'\berror\b', re.IGNORECASE)

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

    wExc = map(ExclusionCounter, config.get('warning_exceptions', []))
    eExc = map(ExclusionCounter, config.get('error_exceptions', []))

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
        return None

    summary = dict([(k, ListDict()) for k in ['error', 'warning']])
    context = deque()
    for i, l in enumerate(logfile):
        context.append(l)
        if len(context) > 5:
            context.popleft()
        t = getLineType(l)
        if t:
            summary[t].append(l, (i, list(context)))
    summary['ignored_warning'] = [w for w in wExc if w.count]
    summary['ignored_error'] = [e for e in eExc if e.count]
    return summary


def genBuildLogReport(build_dir, project, platform, config, old_build_id):
    '''
    Produce the build log reports for a project built.
    '''
    from os.path import exists, join
    import codecs
    import cgi

    build_log = join(build_dir, 'summaries', project.name, 'build.log')

    if not exists(build_log):
        logging.warning('cannot generate build log report: missing file %s', build_log)
        return

    summary = parseBuildLog(codecs.open(build_log, 'r', 'utf-8'), config)
    wCount = sum(map(len, summary['warning'].values()))
    eCount = sum(map(len, summary['error'].values()))


    log_summary = old_build_id + '-log.summary'
    log_summary = join(build_dir, 'summaries', project.name, log_summary)

    html_summary = log_summary.replace('.summary', '.html')

    shutil.copy(build_log, log_summary.replace('-log.summary', '.log'))

    # HTML generation
    htmlData = []
    htmlData.append(u'<html><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8"/><title>LogCheck for project %s</title>' % project.name)
    htmlData.append(u'''<style type="text/css">
pre { margin-top: 0px; }
a.error { color: red; }
a.warning { color: blue; }
a.errorlink { text-decoration: none; color: blue; cursor:pointer; cursor:hand; }
a.warninglink { text-decoration: none; color: blue; cursor:pointer; cursor:hand; }
/*
li.errorli { display: none; }
li.warningli { display: none; }
*/
a.morebtn { color: red; cursor:pointer; cursor:hand }
a.packageLink { text-decoration: none; cursor:pointer; cursor:hand; color:blue; }
.odd { background-color: #FFFFFF; font-family: monospace; }
.even { background-color: #F0F0F0; font-family: monospace; }
</style>
''')
    htmlData.append(u'<script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jquery/1.5.1/jquery.min.js"></script>\n')
    htmlData.append(u'<!-- <script type="text/javascript" src="http://lhcb-nightlies.web.cern.ch/lhcb-nightlies/js/summaryJQ.js"></script> -->\n')
    htmlData.append(u'</head><body>\n')
    htmlData.append(u'<h3>LogCheck for package %s on %s</h3>' % (project.name, socket.gethostname()))
    htmlData.append(u'<p>Warnings : %d<br/> Errors   : %d<br/></p>' % (wCount, eCount))

    if summary['ignored_error']:
        htmlData.append(u'<h3>Ignored errors:</h3>\n')
        htmlData.extend([u'<strong>%d</strong>&nbsp;&rArr;&nbsp;%s<br/>\n' % (w.count, w.exp)
                         for w in summary['ignored_error']])

    if summary['ignored_warning']:
        htmlData.append(u'<h3>Ignored warnings:</h3>\n')
        htmlData.extend([u'<strong>%d</strong>&nbsp;&rArr;&nbsp;%s<br/>\n' % (w.count, w.exp)
                         for w in summary['ignored_warning']])

    htmlData.append(u'''<h3>Shortcuts:</h3>
<ul>
<li><a href="#summary_errors">Summary of errors</a></li>
<li><a href="#summary_warnings">Summary of warnings</a></li>
<li><a href="#environment">Environment</a></li>
<li><a href="#checkout">Checkout (getpack) log</a></li>
<li><a href="#packages_list">List of packages (logs)</a></li>
</ul>
''')

    # Note: error and warning are dictionaries where the keys are the reported
    #       lines and the values are lists of pairs with line number and context
    #       in the log
    if eCount:
        htmlData.append(u'<h3 id="summary_errors">Summary of errors:</h3><hr/>')
        # take all the lines sorted by first occurrence (line number of first value)
        for l in sorted(summary['error'], key=lambda l: summary['error'][l][0][0]):
            htmlData.append(u'<ul class="errorul">')
            for i, ctx in summary['error'][l]:
                htmlData.append(u'<li class="errorli"><a class="errorlink" href="#l%d"><pre>%s</pre></a></li>'
                                % (i, cgi.escape(''.join(ctx))))
            htmlData.append(u'</ul><hr/>')
    if wCount:
        htmlData.append(u'<h3 id="summary_warnings">Summary of warnings:</h3><hr/>')
        # take all the lines sorted by first occurrence (line number of first value)
        for l in sorted(summary['warning'], key=lambda l: summary['warning'][l][0][0]):
            htmlData.append(u'<ul class="warningul">')
            for i, ctx in summary['warning'][l]:
                htmlData.append(u'<li class="warningli"><a class="warninglink" href="#l%d"><pre>%s</pre></a></li>'
                                % (i, cgi.escape(''.join(ctx))))
            htmlData.append(u'</ul><hr/>')

    htmlData.append(u'<p>Here will be the full log.</p>\n')

    htmlData.append(u'</body></html>\n')

    f = codecs.open(html_summary, 'w', 'utf-8')
    f.writelines(htmlData)

    f = open(log_summary, 'w')
    t = time.time()
    f.write('{t} ({at}) {slot} {project}_{version} {platform}\n'
            .format(t=t,
                    at=time.ctime(t),
                    slot=config[u'slot'],
                    project=project.name.upper(),
                    version=project.version,
                    platform=platform))
    f.write(','.join(map(str, [wCount, eCount, 0, 0])))
    f.write('\n')
    f.close()

