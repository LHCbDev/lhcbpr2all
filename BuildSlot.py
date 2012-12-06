#!/usr/bin/env python
'''
Module containing the classes and functions used to checkout a set of projects,
fixing their dependencies to produce a consistent set.
'''
__author__ = 'Marco Clemencic <marco.clemencic@cern.ch>'

import logging
import shutil
import os
import sys
from subprocess import Popen, PIPE, call
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
        cmake.append('set(%(name)s_version %(version)s' % p)

    for p in projects:
        cmake.append('set(%s_version %s' % (p[u'name'], ' '.join(p[u'dependencies'])))

    cmake.append('set(CTEST_CUSTOM_WARNING_EXCEPTION ${CTEST_CUSTOM_WARNING_EXCEPTION}')
    for x in config[u'warning_exceptions']:
        cmake.append('    "%s"' % x.replace('"', r'\"'))
    cmake.append('    )\n')

    return '\n'.join(cmake)

def parseConfigFile(path):
    import json
    return json.load(open(path))


if __name__ == '__main__':
    from os.path import join

    logging.basicConfig(level=logging.INFO)

    if len(sys.argv) != 2 or '-h' in sys.argv:
        print "Usage: %s config.json" % sys.argv[0]
        sys.exit(1)

    config = parseConfigFile(sys.argv[1])

    build_dir = join(os.getcwd(), 'build')
    sources_dir = join(os.getcwd(), 'sources')

    log.info('Cleaning directories.')
    shutil.rmtree(build_dir)
    shutil.rmtree(sources_dir)

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
    ctestConfig = Template(open(join('cmake', 'CTestConfig.template.cmake')).read()).substitute(config)
    ctestScript = Template(open(join('cmake', 'CTestScript.template.cmake')).read())

    name2dir = {}
    deps = {}
    for p in config[u'projects']:
        n = p[u'name']
        v = p[u'version']
        projdir = join(build_dir, n.upper(), '{0}_{1}'.format(n.upper(), v))

        # these are cached for later
        name2dir[n] = projdir
        deps[n] = p[u'dependencies']

        write(join(projdir, 'SlotConfig.cmake'), configCmake)
        write(join(projdir, 'CTestConfig.cmake'), ctestConfig)
        write(join(projdir, 'CTestScript.cmake'),
              ctestScript.substitute({'project': n, 'version': v,
                                      'build_dir': build_dir, 'site': gethostname()}))


    # sort projects by deps
    def getDeps(projs):
        for p in projs:
            return getDeps(deps[p]) + [p]
    sortedProjs = []
    for p in getDeps(deps):
        if p not in sortedProjs:
            sortedProjs.append(p)

    jobs = []
    for p in sortedProjs:
        call(['ctest', '-VV', '-DSTEP=BUILD', '-S', 'CTestScript.cmake'],
             cwd=name2dir[p])
        jobs.append(Popen(['ctest', '-DSTEP=BUILD', '-S', 'CTestScript.cmake'],
                          cwd=name2dir[p]))
    for j in jobs:
        j.wait()
