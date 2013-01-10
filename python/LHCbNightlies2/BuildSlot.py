#!/usr/bin/env python
'''
Module containing the classes and functions used to checkout a set of projects,
fixing their dependencies to produce a consistent set.
'''
__author__ = 'Marco Clemencic <marco.clemencic@cern.ch>'

import logging
import shutil
import os
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

    cmake.append('set(CTEST_CUSTOM_WARNING_EXCEPTION ${CTEST_CUSTOM_WARNING_EXCEPTION}')
    for x in config[u'warning_exceptions']:
        cmake.append('    "%s"' % x.replace('"', r'\"'))
    cmake.append('    )\n')

    return '\n'.join(cmake)

def parseConfigFile(path):
    import json
    return json.load(open(path))

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

    parser.set_defaults(model=models[0],
                        level=logging.INFO,
                        timeout='600',
                        jobs='1')

    opts, args = parser.parse_args()
    logging.basicConfig(level=opts.level,
                        format='%(asctime)s:' + logging.BASIC_FORMAT)

    if len(args) != 1:
        parser.error('wrong number of arguments')

    from os.path import join, dirname
    config = parseConfigFile(args[0])

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

        shutil.copyfile(args[0], join(projdir, 'SlotConfig.json'))
        write(join(projdir, 'SlotConfig.cmake'), configCmake)
        if cache_preload:
            write(join(projdir, 'cache_preload.cmake'), cache_preload)
        write(join(projdir, 'CTestConfig.cmake'),
              ctestConfig.substitute(config))
        write(join(projdir, 'CTestScript.cmake'),
              ctestScript.substitute({'project': p.name, 'version': p.version,
                                      'build_dir': build_dir, 'site': gethostname(),
                                      'Model': opts.model}))

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

        log.info('packing %s', p.dir)
        packname = [p.name, p.version,
                    config[u'slot'], timestamp,
                    platform, 'tar.bz2']
        call(['tar', 'cjf', '.'.join(packname),
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
