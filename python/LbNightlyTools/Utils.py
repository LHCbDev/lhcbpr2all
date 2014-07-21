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
Common utility functions.
'''
__author__ = 'Marco Clemencic <marco.clemencic@cern.ch>'

import os
import logging
import json
import codecs
from datetime import datetime

DAY_NAMES = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')

def setDayNamesEnv(day=None):
    '''
    Set the environment variables TODAY and YESTERDAY if not already set.

    @param day: weekday number for 'TODAY', if not specified, defaults to today.
    '''
    if day is None:
        day = datetime.today().weekday()
    os.environ['TODAY'] = os.environ.get('TODAY', DAY_NAMES[day])
    # Note: it works for day == 0 too
    os.environ['YESTERDAY'] = os.environ.get('YESTERDAY', DAY_NAMES[day - 1])


def _timeoutTerminateCB(proc, msg):
    '''
    Safely terminate a running Popen object.
    '''
    if proc.poll() is None:
        try:
            logging.warning(msg)
            proc.terminate()
        except: # pylint: disable=W0702
            pass

def timeout_call(*popenargs, **kwargs):
    """Reimplementation of subprocess.call with the addition of a timeout
    option.
    """
    from subprocess import Popen
    timer = None
    try:
        timeout = kwargs.pop('timeout')
        msg = kwargs.pop('timeoutmsg', 'on command ' + repr(popenargs))
        msg = 'Timeout reached %s (%ds): terminated.' % (msg, timeout)
        from threading import Timer
        proc = Popen(*popenargs, **kwargs)
        timer = Timer(timeout, _timeoutTerminateCB, [proc, msg])
        timer.start()
        result = proc.wait()
        timer.cancel()
        return result
    except KeyError:
        return Popen(*popenargs, **kwargs).wait()
    finally:
        # ensure that we do not wait for the timer if there is an abnormal exit
        if timer:
            timer.cancel()

def retry_call(*args, **kwargs):
    '''
    Replacement for subprocess.call() that can retry if the command fails.
    To enable the retries, pass the keyword argument 'retry' setting it to the
    number of timed to try.

    For example:

    >>> retry_call(['false'], retry=3)
    Traceback (most recent call last):
    ...
    RuntimeError: the command ['false'] failed 3 times

    '''
    import subprocess
    if 'retry' not in kwargs:
        # no retry
        return subprocess.call(*args, **kwargs)
    else:
        retry = kwargs.pop('retry')
        for _count in range(retry):
            if subprocess.call(*args, **kwargs) == 0:
                break
        else: # Note: else of the 'for' block
            raise RuntimeError('the command {0} failed {1} times'
                                .format(args[0], retry))
        return 0


def ensureDirs(dirs):
    '''
    Ensure that the specified directories exist, creating them if needed.
    '''
    for path in dirs:
        if not os.path.exists(path):
            os.makedirs(path)

def genDocId(data):
    '''
    Internal function to generate the document id from the data dictionary.

    The data field used to prepare the id are (in order):

         ['slot', 'build_id', 'project', 'platform', 'type']

    unless the special field '_id' is defined, in which case its value is used
    as id.

    >>> genDocId({'slot': 'lhcb-head', 'build_id': 123, 'type': 'config'})
    'lhcb-head.123.config'
    >>> genDocId({'slot': 'lhcb-head', 'build_id': 123,
    ... 'platform': 'x86_64-slc6-gcc48-opt', 'type': 'start'})
    'lhcb-head.123.x86_64-slc6-gcc48-opt.start'
    >>> genDocId({'slot': 'lhcb-head', 'build_id': 123,
    ... 'platform': 'x86_64-slc6-gcc48-opt', 'type': 'tests',
    ... 'project': 'Gaudi'})
    'lhcb-head.123.Gaudi.x86_64-slc6-gcc48-opt.tests'
    >>> genDocId({'slot': 'lhcb-head', '_id': 'something'})
    'something'
    '''
    if '_id' in data:
        return data['_id']
    fields = ['slot', 'build_id', 'project', 'platform', 'type']
    return '.'.join([str(data[f]) for f in fields if f in data])

class Dashboard(object):
    '''
    Wrapper for the CouchDB-based dashboard.
    '''
    CRED_FILE = os.path.expanduser(os.path.join('~', 'private',
                                                'couchdb-admin'))
    @classmethod
    def dbInfo(cls, flavour):
        '''
        Return server URL and database name for the given flavour.
        '''
        if flavour == 'nightly':
            return ('https://buildlhcb.cern.ch/nightlies/', '_db')
        else:
            return ('https://buildlhcb.cern.ch/nightlies-%s/' % flavour, '_db')

    @classmethod
    def artifactsRoot(cls, flavour):
        '''
        Return the path to the artifacts directory for the given flavour.
        '''
        root = os.path.join(os.path.sep, 'data', 'artifacts')
        if flavour == 'nightly':
            return root
        else:
            return os.path.join(root, flavour)

    def __init__(self, credentials=None, dumpdir=None, submit=True,
                 flavour='nightly', db_info=None):
        '''
        @param credentials: pair with (username, password) of a valid account on
                            the server
        @param dumpdir: optional name of a directory where to keep a dump
                        of the data uploaded to the server
        @param submit: if set to False the data is not sent to the server
        @param flavour: build flavour, used to select the database to use
        @param db_info: tuple with URL of the server and database name
                        (overrides flavour)
        '''
        import couchdb
        import socket

        self._log = logging.getLogger('Dashboard')
        self._log.debug('preparing connection to dashboard')

        if submit and credentials is None:
            if os.path.exists(self.CRED_FILE):
                # make a tuple with the first two lines of the file
                credentials = tuple([l.strip()
                                     for l in open(self.CRED_FILE)][:2])
            else:
                self._log.debug('no couchdb credentials found')

        self.flavour = flavour

        self.artifacts_root = self.artifactsRoot(flavour)

        server, db = db_info or self.dbInfo(flavour)

        self.submit = submit
        if submit:
            self.server = couchdb.Server(server)
            self.server.resource.credentials = credentials
            try:
                self.db = self.server[db]
            except (couchdb.ResourceNotFound,
                    couchdb.ServerError,
                    socket.error):
                self._log.warning('failed to access %s%s', server, db)
                # ignore connection failures
                self.db = None
        else:
            self.server = None
            self.db = None
        self.dumpdir = dumpdir
        if dumpdir:
            if not os.path.isdir(dumpdir):
                os.makedirs(dumpdir)
            self._log.debug('keep JSON back-ups in %s', dumpdir)

    def publish(self, data, name=None):
        '''
        Store the given dictionary in the dashboard database.

        The id of the document is derived from the data dictionary (using the
        function genDocId), but can be overridden with the optional argument
        'name'.
        '''
        from couchdb import ResourceConflict, Unauthorized, ServerError

        if name is None:
            name = genDocId(data)
        self._log.debug('publishing %s', name)

        if self.dumpdir:
            filename = os.path.join(self.dumpdir, name + '.json')
            self._log.debug('dumping to %s', filename)
            f = codecs.open(filename, 'w', 'utf-8')
            json.dump(data, f)
            f.close()

        if self.db:
            try:
                self._log.debug('sending')
                self.db[name] = data
            except ResourceConflict:
                self._log.debug('%s already present: update', name)
                new_data = self.db[name]
                new_data.update(data)
                self.db[name] = new_data
            except (Unauthorized, ServerError), ex:
                self._log.warning('could not send %s: ', name, ex)

    def dropBuild(self, slot, build_id, platform=None):
        '''
        Remove all the documents in the DB that belongs to the given build of
        the given slot.

        @param slot: name of the slot
        @param build_id: numeric id of the build to remove
        @param platform: optional platform, to remove only the documents for one
                         platform
        '''
        viewname = 'dashboard/docsBySlotBuild'
        if platform is not None:
            view = self.db.view(viewname, key=[slot, build_id, platform])
        else:
            # note: we assume that we will never have a platform called zzz12...
            view = self.db.view(viewname,
                                startkey=[slot, build_id],
                                endkey=[slot, build_id, 'zzz'])
        delete_data = []
        for row in view:
            if row.value:
                delete_data.append({'_id': row.id, '_rev': row.value['_rev'],
                                    '_deleted': True})
            else:
                self._log.info('removing %s', row.id)
                del self.db[row.id]
        if delete_data:
            self._log.info('bulk removing:')
            for row in delete_data:
                self._log.info('   %s', row['_id'])
            self.db.update(delete_data)
        self._log.info('removed %d documents', len(view))

    def publishFromFiles(self, path):
        '''
        Publish the JSON objects from a file of from all the files '*.json' in a
        directory.
        '''
        if os.path.isfile(path):
            files = [path]
        else:
            files = [os.path.join(path, f)
                     for f in os.listdir(path) if f.endswith('.json')]
        for f in files:
            name = os.path.basename(f).replace('.json','')
            if name not in self.db:
                print f
                self.publish(json.load(open(f)))

    def publishFromArtifacts(self, day=None):
        '''
        Push the JSON files in /data/artifacts for the given day to the
        dashboard, if not already present.

        @param day: anything that can be converted to a string in the format
                    'YYYY-MM-DD' or the weekday abbreviation [default is today].
        '''
        if day is None:
            from datetime import date
            day = date.today()
        root = self.artifacts_root
        for slot in os.listdir(root):
            slot_dir = os.path.join(root, slot, str(day), 'db')
            if os.path.isdir(slot_dir):
                self.publishFromFiles(slot_dir)

    def slotsByDay(self, start=None, end=None, returnAll=False):
        '''
        Return a generator over the slot built for each day in the specified
        range. The objects in the generator are tuples with ("day", "slot", id).

        @param start: first day to consider ("YYYY-MM-DD")
        @param end: last day to consider ("YYYY-MM-DD")
        '''
        viewname = 'dashboard/slotsByDay'
        opts = {}
        if start:
            opts['startkey'] = start
        if end:
            opts['endkey'] = end
        for r in self.db.iterview(viewname, batch=100, **opts):
            v = r[u'value']
            if returnAll:
                yield(v)
            else:
                yield (r[u'key'], v[u'slot'], v[u'build_id'])



class JenkinsTest(object):
    '''
    Class representing a test ready to be run
    '''

    SLOT = "slot"
    SBID = "slot_build_id"
    PROJECT = "project"
    PLATFORM = "platform"
    TESTGROUP = "testgroup"
    TESTRUNNER = "testrunner"
    TESTENV = "testenv"
    LABEL = "os_label"
    COUNT = "count"
    JOB_ALLATTRIBUTES  = [ SLOT, SBID, PROJECT, PLATFORM, LABEL,
                          TESTGROUP, TESTRUNNER, TESTENV, COUNT]

    @classmethod
    def fromJenkinsString(cls, test_string):
        ''' Build the obkject from the string passed to Jenkins '''
        test_list = test_string.split('.')
        slot = test_list[0]
        slot_build_id = test_list[1]
        project = test_list[2]
        platform = test_list[3]
        os_label = None
        testgroup = None
        testrunner = None
        testenv = None
        count = 1

        # Check it the param nb 5 is specified and if it is != None
        if len(test_list) > 4:
            if test_list[4].lower() != "none":
                os_label = test_list[4]

        # If the label is still None, we take it from teh platform
        if os_label == None:
            os_label = platform.split('-')[1]

        # Now check for the test group and runner
        if len(test_list) > 5:
            testgroup = test_list[5]

        if len(test_list) > 6:
            testrunner = test_list[6]

        if len(test_list) > 7:
            testenv = test_list[7]

        if len(test_list) > 8:
            count = test_list[8]

        return JenkinsTest(slot, slot_build_id, project, platform, os_label,
                            testgroup, testrunner, testenv, count)


    @classmethod
    def fromScheduledTest(cls, stest):
        ''' Build the object from a scheduled test object '''
        return JenkinsTest(stest.slot, stest.build_id, stest.project,
                           stest.platform, stest.os_label, stest.testgroup,
                           stest.testrunner, stest.testenv, stest.count)

    def __init__(self, slot, slot_build_id, project, platform, os_label=None,
                 testgroup=None,testrunner=None, testenv=None, count=1):
        ''' Basic constructor '''
        self.slot_build_id = slot_build_id
        self.slot = slot
        self.project = project
        self.platform = platform
        self.testgroup = testgroup
        self.testrunner = testrunner
        self.os_label = os_label
        self.testenv = testenv
        self.count = count

    def getParameterLines(self):
        ''' Returns a list of key=value lines for each parameter '''
        return (['%s=%s\n' % (x, getattr(self, x))
                for x in JenkinsTest.JOB_ALLATTRIBUTES])

    def toJenkinsString(self):
        ''' Generate the job description for Jenkins '''
        return '.'.join([self.slot,
                         str(self.slot_build_id),
                         self.project,
                         self.platform,
                         self.os_label if self.os_label else "None",
                         self.testgroup,
                         self.testrunner if self.testrunner else "qmtest",
                         self.testenv if self.testenv else "None",
                         str(self.count)])

    def __str__(self):
        '''
        Convert to string
        '''
        return ".".join([ "%s=%s" % (k, getattr(self, k))
                         for k in JenkinsTest.JOB_ALLATTRIBUTES])

def _packcmd(srcs, dest, cwd='.', dereference=True, exclude=None):
    '''
    Helper function to call the packing command.
    '''
    from subprocess import call
    cmd = ['tar', '--create']
    if dereference:
        cmd.append('--dereference')
    if exclude:
        cmd.extend(['--exclude=%s' % x for x in exclude])
    cmd.extend(['--bzip2', '--file', dest])
    cmd.extend(srcs)
    return call(cmd, cwd=cwd)
def _packtestcmd(srcs_, dest, cwd='.', dereference=True, exclude=None):
    '''
    Helper function to call the package test command.
    '''
    from subprocess import call
    cmd = ['tar', '--compare']
    if dereference:
        cmd.append('--dereference')
    if exclude:
        cmd.extend(['--exclude=%s' % x for x in exclude])
    cmd.extend(['--bzip2', '--file', dest])
    return call(cmd, cwd=cwd)

def pack(srcs, dest, cwd='.', checksum=None, dereference=True, exclude=None):
    '''
    Package the directory 'src' into the package (tarball) 'dest' working from
    the directory 'cwd'.
    If a string is passed as 'checksum', together with the package a checksum
    file is produced with name <dest>.<checksum>.  The supported checksum types
    are those understood by the hashlib module (e.g. 'md5', 'sha1', etc.).

    If the creation of the package fails or the package is not consistent with
    the files to be packed, the packing is retried up to 3 times.
    '''
    log = logging.getLogger('pack')
    ok = False
    retry = 3
    while (not ok) and (retry >= 0):
        retry -= 1
        log.debug('packing %s as %s (from %s)', srcs, dest, cwd)
        if _packcmd(srcs, dest, cwd, dereference, exclude) != 0:
            log.warning('failed to produce %s', dest)
            continue

        log.debug('checking %s', dest)
        if _packtestcmd(srcs, dest, cwd, dereference, exclude) != 0:
            log.warning('invalid package %s', dest)
            continue

        if checksum:
            import hashlib
            absdest = os.path.join(cwd, dest)
            hashsum = hashlib.new(checksum)
            log.debug('computing checksum (%s)', checksum)
            with open(absdest, 'rb') as packfile:
                for chunk in iter(lambda: packfile.read(8192), ''):
                    hashsum.update(chunk)
            with open(absdest + '.' + checksum, 'w') as checkfile:
                checkfile.write('%s *%s\n' %
                                (hashsum.hexdigest(),
                                 os.path.basename(absdest)))
            log.debug('checksum written to %s', dest + '.' + checksum)
        # everything seems correct, stop retrying
        ok = True
    if not ok:
        log.error("failed to pack %s, I'm ignoring it", srcs)
        if os.path.exists(os.path.join(cwd, dest)):
            os.remove(os.path.join(cwd, dest))

def shallow_copytree(src, dst, ignore=None):
    '''Create a shallow (made of symlinks) copy of a directory tree.

    The destination directory might exist and in that case it will be
    recursively filled with links pointing to the corresponding entries inside
    the source directory.
    If the destination does not exist, then shallow_copytree is equivalent to
    os.symlink.

    The optional argument `ignore` is a callable with the same semantics of
    the equivalent argument of shutil.copytree:

       callable(src, names) -> ignored_names

    '''
    src = os.path.realpath(src)
    if not os.path.exists(dst):
        os.symlink(src, dst)
    elif os.path.isdir(src):
        names = [name for name in os.listdir(src) if name not in ('.', '..')]
        ignored_names = set() if ignore is None else set(ignore(src, names))
        for name in set(names) - ignored_names:
            shallow_copytree(os.path.join(src, name), os.path.join(dst, name),
                             ignore)

def find_path(name, search_path=None):
    '''
    Look for a file or directory in a search path.

    If the search path is not specified, the concatenation of CMTPROJECTPATH and
    CMAKE_PREFIX_PATH is used.

    >>> find_path('true', ['/usr/local/bin', '/usr/bin', '/bin'])
    '/bin/true'
    >>> print find_path('cannot_find_me', [])
    None
    '''
    from os import environ, pathsep
    from os.path import join, exists
    if search_path is None:
        search_path = (environ.get('CMTPROJECTPATH', '').split(pathsep) +
                       environ.get('CMAKE_PREFIX_PATH', '').split(pathsep))

    try:
        return (join(path, name)
                for path in search_path
                if exists(join(path, name))).next()
    except StopIteration:
        logging.warning('%s not found in the search path', name)
    return None

class IgnorePackageVersions(object):
    '''
    Helper class which instances can be used as ignore argument of
    shallow_copytree to ignore versions of packages when cloning a container
    project.
    '''
    def __init__(self, packages):
        '''
        @param packages: list of objects describing packages, which must have a
                         property 'name' and a property 'version'
        '''
        self._exclusions = dict((os.path.basename(pack.name), [pack.version])
                                for pack in packages)
    def __call__(self, src, names):
        '''
        Implements the semantic of the 'ignore' argument of shallow_copytree.
        '''
        return self._exclusions.get(os.path.basename(src), [])

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
