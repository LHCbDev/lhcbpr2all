#!/usr/bin/env python
# encoding: utf-8
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
Module containing the classes and functions used install in a directory the
products of a nightly build.
'''
__author__ = 'Marco Clemencic <marco.clemencic@cern.ch>'

import os
import HTMLParser
import urllib2
import re
import logging
import time
import shutil
import json

from subprocess import Popen, PIPE, call
from tempfile import mkstemp
from datetime import datetime
from socket import gethostname

ARTIFACTS_URL = 'https://buildlhcb.cern.ch/artifacts'

def _list_http(url):
    '''
    Implementation of listdir for HTTP.

    The HTTP server must allow listing of directories with the typical Apache
    format.
    '''
    class ListHTMLParser(HTMLParser.HTMLParser):
        '''
        Specialized HTML parser to extract the list of files from standard
        Apache directory listing.
        '''
        # pylint: disable=R0904
        def __init__(self):
            HTMLParser.HTMLParser.__init__(self)
            self.data = []
        def handle_starttag(self, tag, attrs):
            if tag == 'a':
                attrs = dict(attrs)
                # avoid check for '' in the following 'if'
                href = attrs.get('href', '?')
                # ignore special entries like sorting links ("?...") or link to
                # parent directory
                if '?' not in href and href not in url:
                    self.data.append(href)
    parser = ListHTMLParser()
    parser.feed(urllib2.urlopen(url).read())
    return parser.data

def _list_ssh(url):
    '''
    Implementation of listdir for SSH.
    '''
    host, path = url.split(':', 1)
    proc = Popen(['ssh', host, 'ls -a1 %r' % path], stdout=PIPE)
    return proc.communicate()[0].splitlines()

def _url_protocol(url):
    '''
    @return the protocol id of the given URL
    '''
    if re.match(r'https?://', url):
        return 'http'
    elif re.match(r'([a-z0-9]+@)?[a-z][a-z0-9.]*:', url):
        return 'ssh'
    else:
        return 'file'

def listdir(url):
    '''
    @return the list of entries in a directory, being it over HTTP, ssh or
            local filesystem.
    '''
    protocol = _url_protocol(url)
    listing = {'http': _list_http,
               'ssh': _list_ssh,
               'file': os.listdir}[protocol](url)
    return sorted(listing)


def getURL(url, dst):
    '''
    Generic URL retriever with suppotr for 'http:', 'file:' and 'ssh:'
    protocols.
    '''
    protocol = _url_protocol(url)
    def getHTTP(url, dst):
        '''Retrieve from 'http:'.'''
        # code copied from shutil.copyfile
        fsrc = None
        fdst = None
        try:
            fsrc = urllib2.urlopen(url)
            fdst = open(dst, 'wb')
            shutil.copyfileobj(fsrc, fdst)
        finally:
            if fdst:
                fdst.close()
            if fsrc:
                fsrc.close()
    def getSSH(url, dst):
        '''Retrieve from 'ssh:'.'''
        call(['scp', '-q', url, dst])
    return {'http': getHTTP,
            'ssh': getSSH,
            'file': shutil.copy2}[protocol](url, dst)

def unpack(url, dest):
    '''
    Unpack a tarball from 'url' into the directory 'dest'.
    '''
    # download on a local file
    log = logging.getLogger('unpack')
    protocol = _url_protocol(url)
    tmpfd = None
    try:
        if protocol != 'file':
            tmpfd, tmpname = mkstemp()
            os.close(tmpfd)
            log.info('retrieving %s', url)
            log.debug('using tempfile %s', tmpname)
            getURL(url, tmpname)
        else:
            tmpname = os.path.abspath(url)
        log.info('unpacking %s', url)
        retcode = call(['tar', '-x', '-f', tmpname], cwd=dest)
    finally:
        if tmpfd is not None:
            os.remove(tmpname)
    return retcode

def install(url, dest):
    '''
    Install the file at 'url' in the directory 'dest'.

    If url points to a tarball, it is unpacked, otherwise it is just copied.
    '''
    log = logging.getLogger('install')
    if not os.path.exists(dest):
        log.info('creating directory "%s"', dest)
        os.makedirs(dest)
    if url.endswith('.tar.bz2'):
        return unpack(url, dest)
    else:
        log.info('installing %s', url)
        return getURL(url, os.path.join(dest, url.rsplit('/', 1)[1]))


def getDependencies(projects, slot_configuration):
    ''' Extract dependencies of a list of projects,
    using the slot configuration passed '''

    needed_projects = set()
    log = logging.getLogger('getDependencies')

    # Iterating over the projects
    for proj in projects:
        # First check the configuration
        proj_lower = proj.lower()
        pdata = None
        for cp in slot_configuration['projects']:
            # Comparing lower case to be sure...
            if cp['name'].lower() == proj_lower:
                pdata = cp
                break

        # If pdata still None, we have a problem...
        if pdata == None:
            raise Exception("Project %s not in slot metadata" % proj)

        # Looking up the project/dependency info
        pdeps = pdata.get('dependencies', [])

        # Adding the direct deps to the set
        for dep in pdeps:
            log.debug('%s depends on %s' % (proj_lower, dep))
            needed_projects.add(dep)

        # Now looking for transitive deps and adding dependencies
        alldeps = getDependencies(pdeps, slot_configuration)
        needed_projects |= alldeps

    return needed_projects


def requiredPackages(files, projects=None, platforms=None, skip=None,
                     metadataurl=None,
                     add_dependencies=True):
    '''
    Extract from the list of tarballs those that need to be installed considering
    the list of requested projects (default: all of them), platforms (default:
    all of them) and what to skip (default: nothing).
    '''
    log = logging.getLogger('requiredPackages')

    if skip is None:
        skip = set()
    else:
        skip = set(skip)
    if projects:
        # change to lowercase to make the check case-insensitive
        projects = map(str.lower, projects)

    # Checking that we have the right info for the dependencies
    if add_dependencies and metadataurl == None:
        raise Exception("Dependency analysis requires slot configuration URL")

    slot_configuration = None
    # Getting the project metadata
    if metadataurl != None:
        response = urllib2.urlopen(metadataurl)
        slot_configuration = json.load(response)

    # Actually getting the dependencies and merging them with the project list
    if add_dependencies:
        allprojects = getDependencies(projects, slot_configuration)
        for proj in allprojects:
            if proj not in projects:
                log.debug("Adding %s to the list of projects" % proj)
                projects.append(proj.lower())

    for filename in files:
        # file names have the format
        #   <project>.<version>.<tag.id>.<platform>.tar.bz2
        tokens = filename.split('.')
        project, platform = tokens[0], tokens[-3]
        if projects is None or project.lower() in projects:
            if platforms is None or platform in platforms:
                if filename not in skip:
                    yield filename

def findGlimpseFilenames(path):
    '''
    Give a top directory, return the iterator over all the .glimpse_filenames
    files that can be found (excluding some special directories).
    '''
    excluded_dirs = set(['DOC', 'docs', 'scripts', 'scripts.old',
                         'DBASE', 'PARAM', 'TOOLS',
                         'XmlEditor'])
    log = logging.getLogger('findGlimpseFilenames')
    path = os.path.abspath(path)
    log.debug('Looking for .glimpse_filenames in %s', path)
    for root, dirs, files in os.walk(path):
        if '.glimpse_filenames' in files:
            yield os.path.join(root, '.glimpse_filenames')
            # do not enter subdirectories (we assume no nested indexes)
            dirs[:] = []
        elif 'Makefile' in files:
            # do not descend the projects substructure
            dirs[:] = []
        else:
            # do not descend the known special directories
            dirs[:] = list(set(dirs) - excluded_dirs)

def fixGlimpseIndexes(iterable):
    '''
    Give a list of of paths to .glimpse_filenames files, replace the relative
    paths with absolute ones.
    '''
    log = logging.getLogger('fixGlimpseIndexes')
    log.debug('Fixing .glimpse_filenames')
    for filename in iterable:
        log.debug(' - %s', filename)
        f = open(filename)
        lines = f.readlines()
        f.close()
        root = os.path.dirname(filename)
        # join the file directory on all the lines except the first one
        # (it's a number)
        lines = lines[:1] + [os.path.join(root, l) for l in lines[1:]]
        f = open(filename, 'w')
        f.writelines(lines)
        f.close()

import LbUtils.Script
class Script(LbUtils.Script.PlainScript):
    '''
    Script to install a in a directory a nightly build or a part of it.
    '''
    __usage__ = '%prog [options] slot-name build-id'
    __version__ = ''

    def defineOpts(self):
        parser = self.parser
        parser.add_option('--artifacts-root',
                          action='store', metavar='URI',
                          help='URL or directory where the build artifacts can '
                               'be found [default: %default]')
        parser.add_option('--projects',
                          action='store',
                          help='comma-separated list of projects to install '
                               '[default: all]')
        parser.add_option('--platforms',
                          action='store',
                          help='comma-separated list of platforms to install '
                               '(the special platform "src" is always included)'
                               ' [default: all]')
        parser.add_option('--dest',
                          action='store',
                          help='directory where to install the artifacts '
                               '[default: <slot-name>/<build-id>]')

        parser.add_option('--nodeps',
                          action='store_true',
                          help='Disable the download of dependencies for a project '
                               '[default: False]',
                          default=False)

        parser.set_defaults(artifacts_root=ARTIFACTS_URL)

    def main(self):
        # split the 'comma-separated list' options
        opts = self.options
        if opts.projects:
            opts.projects = map(str.strip, opts.projects.split(','))
        if opts.platforms:
            opts.platforms = map(str.strip, opts.platforms.split(','))
            opts.platforms.append('src') # ensure that 'src' is included

        try:
            slot, build_id = self.args
        except ValueError:
            self.parser.error('wrong number of arguments')

        dest = opts.dest or os.path.join(slot, build_id)
        if not os.path.exists(dest):
            self.log.debug('creating directory %s' % dest)
            os.makedirs(dest)

        url = '/'.join([opts.artifacts_root, slot, build_id])
        history_file = os.path.join(dest, '.installed')

        # URL for the slot-config file used to get the dependencies
        metadataurl = '/'.join([url, 'slot-config.json'])

        lock_file = os.path.join(dest, '.lock')
        self.log.debug('check for lock file %s', lock_file)
        for _ in xrange(30):
            if not os.path.exists(lock_file):
                break
            time.sleep(10)
        else:
            # the log file is still there: give up
            try:
                pid, timestamp = (open(lock_file).readline()
                                  .strip().split(':', 1))
                self.log.error('lockfile %s still present '
                               '(generated by pid %s on %s)',
                               lock_file, pid, timestamp)
                return 2
            except os.error:
                # if we cannot read the file, probably it just disappeared
                pass
            except ValueError:
                # the lock file looks invalid, we can ignore it
                pass

        f = open(lock_file, 'w')
        f.write('{0}@{1}:{2}\n'.format(os.getpid(), gethostname(),
                                       datetime.now().isoformat()))
        f.close()
        self.log.debug('created lock file %s', lock_file)

        try:
            urllist = listdir(url)
            tarfiles = [f for f in urllist if f.endswith('.tar.bz2')]
            installed = {}
            if os.path.exists(history_file):
                installed = dict([l.strip().split(':', 1)
                                  for l in open(history_file)])
            tarfiles = requiredPackages(tarfiles,
                                        opts.projects, opts.platforms,
                                        installed,
                                        metadataurl,
                                        add_dependencies=not opts.nodeps)

            required_files = list(tarfiles) # tarfiles is a generator (so far)
            # add required non-tar files
            other_files = set(['configuration.xml', 'confSummary.py',
                               'searchPath.cmake', 'slot-config.json'])
            required_files.extend(other_files.intersection(urllist) -
                                 set(installed))
            if required_files:
                self.log.info('installing %d files', len(required_files))
            else:
                self.log.info('nothing to install')

            # search for indexes already present so that we can skip fixing them
            pre_existing_indexes = set(findGlimpseFilenames(dest))

            index_installed = False
            for f in required_files:
                if install(url + '/' + f, dest): # 0 or None mean success
                    raise RuntimeError('error installing %s' % f)
                installed[f] = datetime.now().isoformat()
                # record what has been installed so far
                histfile = open(history_file, 'w')
                histfile.writelines(['%s:%s\n' % i
                                     for i in sorted(installed.items())])
                histfile.close()
                if 'index' in f:
                    index_installed = True

            if index_installed:
                fixGlimpseIndexes(f for f in findGlimpseFilenames(dest)
                                  if f not in pre_existing_indexes)

            if 'confSummary.py' in installed:
                # generate shell script equivalents
                data = {}
                execfile(os.path.join(dest, 'confSummary.py'), data)
                search_path = data.get('cmtProjectPathList', [])
                # we need to prepend the installation directory
                search_path.insert(0, os.path.abspath(dest))
                # write bash script
                shell_name = os.path.join(dest, 'setupSearchPath.sh')
                self.log.info('writing %s', shell_name)
                with open(shell_name, 'w') as shell_script:
                    shell_script.write('export CMTPROJECTPATH=%s\n' %
                                       (':'.join(search_path)))
                # write tcsh script
                shell_name = os.path.join(dest, 'setupSearchPath.csh')
                self.log.info('writing %s', shell_name)
                with open(shell_name, 'w') as shell_script:
                    shell_script.write('setenv CMTPROJECTPATH %s\n' %
                                       (':'.join(search_path)))

        except Exception, ex:
            self.log.error('Fatal error: %s' % ex)
            if logging.getLogger().level <= logging.DEBUG:
                # re-raise the exception in debug mode
                raise
            return 1

        finally:
            # this is call even after an exception or a return
            os.remove(lock_file)

        return 0
