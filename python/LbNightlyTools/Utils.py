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
