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
    COUCHDB_SERVER = 'https://buildlhcb.cern.ch/nightlies/'
    COUCHDB_DB = '_db'
    CRED_FILE = os.path.expanduser(os.path.join('~', 'private',
                                                'couchdb-admin'))
    ARTIFACTS_ROOT = os.path.join(os.path.sep, 'data', 'artifacts')

    def __init__(self, credentials=None, dumpdir=None, submit=True,
                 server=None, db=None):
        '''
        @param credentials: pair with (username, password) of a valid account on
                            the server
        @param dumpdir: optional name of a directory where to keep a dump
                        of the data uploaded to the server
        @param submit: if set to False the data is not sent to the server
        @param server: URL of the server
        @param db: database name
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

        if not server:
            server = self.COUCHDB_SERVER
        if not db:
            db = self.COUCHDB_DB

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
        for row in view:
            self._log.info('removing %s', row.id)
            del self.db[row.id]
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
        for slot in os.listdir(self.ARTIFACTS_ROOT):
            slot_dir = os.path.join(self.ARTIFACTS_ROOT, slot, str(day), 'db')
            if os.path.isdir(slot_dir):
                self.publishFromFiles(slot_dir)

    def slotsByDay(self, start=None, end=None):
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
            yield (r[u'key'], v[u'slot'], v[u'build_id'])

def _packcmd(src, dest, cwd='.'):
    '''
    Helper function to call the packing command.
    '''
    from subprocess import call
    return call(['tar', '--create', '--dereference', '--bzip2',
                 '--file', dest, src], cwd=cwd)
def _packtestcmd(src_, dest, cwd='.'):
    '''
    Helper function to call the package test command.
    '''
    from subprocess import call
    return call(['tar', '--compare', '--dereference', '--bzip2',
                 '--file', dest], cwd=cwd)

def pack(src, dest, cwd='.', checksum=None):
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
        log.debug('packing %s as %s (from %s)', src, dest, cwd)
        if _packcmd(src, dest, cwd) != 0:
            log.warning('failed to produce %s', dest)
            continue

        log.debug('checking %s', dest)
        if _packtestcmd(src, dest, cwd) != 0:
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
        log.error("failed to pack %s, I'm ignoring it", src)
        if os.path.exists(os.path.join(cwd, dest)):
            os.remove(os.path.join(cwd, dest))
