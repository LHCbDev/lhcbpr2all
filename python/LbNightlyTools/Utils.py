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

    >>> genDocId({'slot': 'lhcb-head', 'build_id': 123, 'type': 'config'})
    'lhcb-head.123.config'
    >>> genDocId({'slot': 'lhcb-head', 'build_id': 123,
    ... 'platform': 'x86_64-slc6-gcc48-opt', 'type': 'start'})
    'lhcb-head.123.x86_64-slc6-gcc48-opt.start'
    >>> genDocId({'slot': 'lhcb-head', 'build_id': 123,
    ... 'platform': 'x86_64-slc6-gcc48-opt', 'type': 'tests',
    ... 'project': 'Gaudi'})
    'lhcb-head.123.Gaudi.x86_64-slc6-gcc48-opt.tests'
    '''
    fields = ['slot', 'build_id', 'project', 'platform', 'type']
    return '.'.join([str(data[f]) for f in fields if f in data])

class Dashboard(object):
    '''
    Wrapper for the CouchDB-based dashboard.
    '''
    COUCHDB_SERVER = 'https://lbtestbuild.cern.ch/nightlies/'
    COUCHDB_DB = '_db'
    def __init__(self, credentials=None, dumpdir=None, submit=True):
        '''
        @param credentials: pair with (username, password) of a valid account on
                            the server
        @param dumpdir: optional name of a directory where to keep a dump
                        of the data uploaded to the server
        @param submit: if set to False the data is not sent to the server
        '''
        import couchdb
        import socket
        self._log = logging.getLogger('Dashboard')
        self._log.debug('preparing connection to dashboard')
        self.submit = submit
        if submit:
            self.server = couchdb.Server(self.COUCHDB_SERVER)
            self.server.resource.credentials = credentials
            try:
                self.db = self.server[self.COUCHDB_DB]
            except (couchdb.ResourceNotFound,
                    couchdb.ServerError,
                    socket.error):
                self._log.warning('failed to access %s%s',
                                  self.COUCHDB_SERVER, self.COUCHDB_DB)
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

    def publish(self, data):
        '''
        Store the given dictionary in the dashboard database.

        The id of the document is derived from the data dictionary.
        '''
        from couchdb import ResourceConflict, Unauthorized

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
            except Unauthorized, ex:
                self._log.warning('could not send %s: ', name, ex)

    def dropBuild(self, slot, build_id):
        '''
        Remove all the documents in the DB that belongs to the given build of
        the given slot.

        @param slot: name of the slot
        @param build_id: numeric id of the build to remove
        '''
        view = self.db.view('dashboard/docsBySlotBuild', key=[slot, build_id])
        for row in view:
            self._log.info('removing %s', row.id)
            del self.db[row.id]
        self._log.info('removed %d documents', len(view))
