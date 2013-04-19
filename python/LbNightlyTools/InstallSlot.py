#!/usr/bin/env python
# encoding: utf-8
'''
Module containing the classes and functions used install in a directory the
products of a nightly build.
'''
__author__ = 'Marco Clemencic <marco.clemencic@cern.ch>'

import os
import HTMLParser
import urllib
import urllib2
import re
import logging
import time
import shutil

from subprocess import Popen, PIPE, call
from tempfile import mkstemp
from datetime import datetime


def _list_http(url):
    '''
    Implementation of listdir for HTTP.

    The HTTP server must allow listing of directories with the typical Apache
    format.
    '''
    class ListHTMLParser(HTMLParser.HTMLParser):
        def __init__(self):
            HTMLParser.HTMLParser.__init__(self)
            self.data = []
        def handle_starttag(self, tag, attrs):
            if tag == 'a':
                attrs = dict(attrs)
                href = attrs.get('href', '?') # avoid check for '' in the following 'if'
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
    p = Popen(['ssh', host, 'ls -a1 %r' % path], stdout=PIPE)
    return p.communicate()[0].splitlines()

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
    @return the list of entries in a directory, being it over HTTP, ssh or local filesystem.
    '''
    protocol = _url_protocol(url)
    l = {'http': _list_http,
         'ssh': _list_ssh,
         'file': os.listdir}[protocol](url)
    l.sort()
    return l


def getURL(url, dst):
    protocol = _url_protocol(url)
    def getHTTP(url, dst):
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
        call(['scp', '-q', url, dst])
    return {'http': getHTTP,
            'ssh': getSSH,
            'file': shutil.copy2}[protocol](url, dst)

def unpack(url, dest):
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
    Install the file at 'url' in the directory dest.

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

def requiredPackages(files, projects=None, platforms=None, skip=None):
    '''
    Extract from the list of taballs those that need to be installed considering
    the list of requested projects (default: all of them), platforms (default:
    all of them) and what to skip (default: nothing).
    '''
    if skip is None:
        skip = set()
    else:
        skip = set(skip)
    if projects:
        projects = map(str.lower, projects) # change to lowercase to make the check case-insensitive
    for f in files:
        # file names have the format
        #   <project>.<version>.<tag.id>.<platform>.tar.bz2
        d = f.split('.')
        pr, pl = d[0], d[-3]
        if projects is None or pr.lower() in projects:
            if platforms is None or pl in platforms:
                if f not in skip:
                    yield f

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
                          action='store', metavar='DIR',
                          help='directory where the build artifacts can be '
                               'found [default: %default]')
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


        parser.set_defaults(artifacts_root='https://buildlhcb.cern.ch/artifacts')

    def main(self):
        # split the 'comma-separated list' options
        if self.options.projects:
            self.options.projects = map(str.strip, self.options.projects.split(','))
        if self.options.platforms:
            self.options.platforms = map(str.strip, self.options.platforms.split(','))
            self.options.platforms.append('src') # ensure that 'src' is included

        try:
            slot, build_id = self.args
        except ValueError:
            self.parser.error('wrong number of arguments')

        dest = self.options.dest or os.path.join(slot, build_id)
        if not os.path.exists(dest):
            self.log.debug('creating directory %s' % dest)
            os.makedirs(dest)

        url = '/'.join([self.options.artifacts_root, slot, build_id])
        history_file = os.path.join(dest, '.installed')

        lock_file = os.path.join(dest, '.lock')
        self.log.debug('check for lock file %s', lock_file)
        for _ in xrange(30):
            if not os.path.exists(lock_file):
                break
            time.sleep(10)
        else:
            # the log file is still there: give up
            try:
                p, t = open(lock_file).readline().strip().split(':', 1)
                self.log.error('lockfile %s still present (generated by pid %s on %s)', lock_file, p, t)
                return 2
            except os.error:
                # if we cannot read the file, probably it just disappeared
                pass
            except ValueError:
                # the lock file looks invalid, we can ignore it
                pass

        f = open(lock_file, 'w')
        f.flush()
        f.write('{0}:{1}\n'.format(os.getpid(), datetime.now().isoformat()))
        f.close()

        try:
            urllist = listdir(url)
            tarfiles = [f for f in urllist if f.endswith('.tar.bz2')]
            installed = {}
            if os.path.exists(history_file):
                installed = dict([l.strip().split(':', 1) for l in open(history_file)])
            tarfiles = requiredPackages(tarfiles,
                                        self.options.projects, self.options.platforms,
                                        installed)

            requiredFiles = list(tarfiles) # tarfiles is a generator (so far)
            requiredFiles.extend(set(['configuration.xml', 'confSummary.py']).intersection(urllist) - set(installed))
            if requiredFiles:
                self.log.info('installing %d files', len(requiredFiles))
            else:
                self.log.info('nothing to install')


            for f in requiredFiles:
                if install(url + '/' + f, dest): # 0 or None mean success
                    raise RuntimeError('error installing %s' % f)
                installed[f] = datetime.now().isoformat()
                # record what has been installed so far
                f = open(history_file, 'w')
                f.writelines(['%s:%s\n' % i for i in sorted(installed.items())])
                f.close()

        except Exception, x:
            self.log.error('Fatal error: %s' % x)
            if logging.getLogger().level <= logging.DEBUG:
                # re-raise the exception in debug mode
                raise
            return 1

        finally:
            # this is call even after an exception or a return
            os.remove(lock_file)

        return 0
