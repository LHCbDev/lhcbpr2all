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

log = logging.getLogger(__name__)

def genProjectXml(config):
    projects = dict([(p[u'name'], p) for p in config[u'projects']])
    vers = lambda n: projects[n][u'version']

    xml = ['<Project name="{0}">'.format(config[u'slot'])]
    for p in projects:
        xml.append('  <SubProject name="{0} {1}">'.format(p, vers(p)))
        for d in projects[p][u'dependencies']:
            xml.append('    <Dependency name="{0} {1}"/>'.format(d, vers(d)))
        xml.append('  </SubProject>')
    xml.append('</Project>\n')

    return '\n'.join(xml)

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

def sortedByDeps(deps):
    '''
    Take a dictionary of dependencies as {'depender': ['dependee', ...]} and
    return the list of keys sorted according to their dependencies so that
    that a key comes after its dependencies.

    >>> sortedByDeps({'4': ['2', '3'], '3': ['1'], '2': ['1'], '1': ['0'], '0': []})
    ['0', '1', '3', '2', '4']
    '''
    def unique(l):
        u = []
        for i in l:
            if i not in u:
                u.append(i)
        return u
    def recurse(keys):
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


    parser.set_defaults(model=models[0],
                        level=logging.INFO,
                        timeout='600')

    opts, args = parser.parse_args()
    logging.basicConfig(level=opts.level,
                        format='%(asctime)s:' + logging.BASIC_FORMAT)

    if len(args) != 1:
        parser.error('wrong number of arguments')

    from os.path import join, dirname
    config = parseConfigFile(args[0])

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
    open(join(build_dir, 'Project.xml'), 'w').write(genProjectXml(config))

    def write(path, data):
        f = open(path, 'w')
        f.write(data)
        f.close()

    configCmake = genSlotConfig(config)
    ctestConfig = Template(open(join(dirname(__file__), 'CTestConfig.template.cmake')).read())
    ctestScript = Template(open(join(dirname(__file__), 'CTestScript.template.cmake')).read())

    name2dir = {}
    deps = {}
    for p in config[u'projects']:
        n = p[u'name']
        v = p[u'version']
        projdir = join(n.upper(), '{0}_{1}'.format(n.upper(), v))

        # these are cached for later
        name2dir[n] = projdir
        deps[n] = p[u'dependencies']

        projdir = join(build_dir, projdir)

        shutil.copyfile(args[0], join(projdir, 'SlotConfig.json'))
        write(join(projdir, 'SlotConfig.cmake'), configCmake)
        write(join(projdir, 'CTestConfig.cmake'),
              ctestConfig.substitute(config))
        write(join(projdir, 'CTestScript.cmake'),
              ctestScript.substitute({'project': n, 'version': v,
                                      'build_dir': build_dir, 'site': gethostname(),
                                      'Model': opts.model}))


    jobs = []
    for p in sortedByDeps(deps):
        build_cmd = ['ctest', '-DSTEP=BUILD', '--timeout', opts.timeout, '-S', 'CTestScript.cmake']
        test_cmd =  ['ctest', '-DSTEP=TEST', '--timeout', opts.timeout, '-S', 'CTestScript.cmake']
        if opts.level <= logging.INFO:
            build_cmd.insert(1, '-VV')
        if opts.level <= logging.DEBUG:
            test_cmd.insert(1, '-VV')

        workdir = join(build_dir, name2dir[p])

        log.info('building %s', name2dir[p])
        call(build_cmd, cwd=workdir)

        log.info('packing %s', name2dir[p])
        call(['tar', 'cjf', os.path.basename(name2dir[p]) + '.tar.bz2',
              os.path.join(name2dir[p], 'InstallArea')], cwd=build_dir)

        log.info('testing (in background) %s', name2dir[p])
        jobs.append(Popen(test_cmd, cwd=workdir))

    log.info('waiting for tests still running...')
    for j in jobs:
        j.wait()

    log.info('build completed in %s', datetime.now() - starttime)
    return 0
