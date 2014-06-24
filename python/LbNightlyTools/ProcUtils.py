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

__all__ = ('call_with_pty', 'call')

import os
import pty
import sys

from subprocess import Popen, call as _call, STDOUT
from threading import Thread
from select import select
from Queue import Queue

class _CollectorThread(Thread):
    '''
    Class used to collect the output of a Popen process on a pseudo-terminal
    (pty).
    '''

    BUF_SIZE = 512

    def __init__(self, proc, fd, queue, echo=None):
        '''
        Initialize the thread.

        @param proc: Popen process that was started with a pty slave as output
        descriptor (either stdout or stderr)
        @param fd: file descriptor of the pty master
        @param queue: Queue instance used to collect the chunks read from fd,
                      recorded as tuples (fd, chunk)
        @param echo: file object where the data can be written while collected
        '''
        super(_CollectorThread, self).__init__()
        self.proc = proc
        self.fd = fd
        self.queue = queue
        self.echo = echo

    def run(self):
        '''
        Core function of the Thread interface.
        '''
        proc, fd, queue, echo = self.proc, self.fd, self.queue, self.echo
        BUF_SIZE = self.BUF_SIZE
        while True:
            if select([fd], [], [], 0.1)[0]:
                chunk = os.read(fd, BUF_SIZE)
                while len(chunk) == BUF_SIZE or select([fd], [], [], 0)[0]:
                    queue.put((fd, chunk))
                    if echo:
                        echo.write(chunk)
                    chunk = os.read(fd, BUF_SIZE)
                if chunk:
                    queue.put((fd, chunk))
                    if echo:
                        echo.write(chunk)
            elif proc.poll() is not None:
                break


def _collate_chunks(input_data, newline='\r\n'):
    '''
    Given an iterable which elements are tuples (fd, chunk), merges the chunks
    with the same fd such that they always end with a newline ('\\r\\n').
    Returns an iterator over the reorganized chunks.

    For example:

    >>> list(_collate_chunks([(1, 'a\\r\\n'), (1, 'b'), (2, 'err\\r\\n'),
    ...                       (1, '\\r\\nc\\r\\n')]))
    [(1, 'a\\r\\n'), (2, 'err\\r\\n'), (1, 'b\\r\\nc\\r\\n')]
    '''
    newline_size = len(newline)
    from collections import defaultdict
    buff = defaultdict(str)
    for fd, chunk in input_data:
        curr = buff[fd]
        curr += chunk
        idx = curr.rfind(newline)
        if idx >= 0:
            yield (fd, curr[:idx + newline_size])
            buff[fd] = curr[idx + newline_size:]
        else:
            buff[fd] = curr
    for item in buff.items():
        if item[1]:
            yield item


def call_with_pty(*args, **kwargs):
    '''
    Similar to subprocess.call, execute a process, but its stdout and stderr are
    bound to a pty and buffered.

    Return a tuple where the first element is the return code of the process and
    the second is an iterable of tuples (fd, chunk), with fd being 1 for stdout
    and 2 for stderr, and chunk is a string that was written on 'fd'.
    '''
    out_fds = pty.openpty()
    err_fds = pty.openpty()
    queue = Queue()

    echo = kwargs.pop('echo', False)

    kwargs['stdout'] = out_fds[1]
    kwargs['stderr'] = err_fds[1]
    proc = Popen(*args, **kwargs)

    out = _CollectorThread(proc, out_fds[0], queue,
                           sys.stdout if echo else None)
    out.start()
    err = _CollectorThread(proc, err_fds[0], queue,
                           sys.stderr if echo else None)
    err.start()

    def data_gen():
        fds = {out_fds[0]: 1, err_fds[0]: 2}
        while not queue.empty():
            fd, chunk = queue.get()
            yield fds[fd], chunk

    retcode = proc.wait()

    out.join()
    err.join()
    for fd in out_fds + err_fds:
        os.close(fd)

    return retcode, _collate_chunks(data_gen())


def call(*args, **kwargs):
    '''
    Similar to subprocess.call, but it supports two new arguments:
    
    @param htmlout: if set, take stdout and stderr and produce HTML code with
                    their content
    @param htmlheader: set it to False to produce only the inner HTML and not
                       the headers
    '''
    htmlout = kwargs.pop('htmlout')
    htmlheader = kwargs.pop('htmlheader', True)
    if htmlout is None:
        return _call(*args, **kwargs)
    else:
        from HTMLUtils import XTerm2HTML
        if htmlout == STDOUT:
            htmlout = sys.stdout
        retcode, data = call_with_pty(*args, **kwargs)
        conv = XTerm2HTML()
        if htmlheader:
            htmlout.write(conv.head(title=' '.join(args[0])))
        style = {1: 'stdout', 2: 'stderr'}
        for fd, chunk in data:
            htmlout.write('<span class="{}">{}</span>'
                            .format(style[fd],
                                    conv.process(chunk.replace('\r', ''))))
        if htmlheader:
            htmlout.write(conv.tail())
        return retcode

if __name__ == '__main__':
    sys.exit(call(sys.argv[1:], htmlout=STDOUT))
