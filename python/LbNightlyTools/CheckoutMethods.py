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
Module grouping the common checkout functions.
'''
__author__ = 'Marco Clemencic <marco.clemencic@cern.ch>'

import logging
import shutil
import os

from LbNightlyTools._utils import retry_call as call

__log__ = logging.getLogger(__name__)

def default(desc, rootdir='.'):
    '''
    Checkout the project described by the ProjectDesc 'desc'.
    '''
    from os.path import normpath, join
    getpack = ['getpack', '--batch', '--no-config']
    __log__.debug('checking out %s', desc)
    cmd = getpack + ['-P',
                     '-H' if desc.version == 'HEAD' else '-r',
                     desc.name, desc.version]
    call(cmd, cwd=rootdir, retry=3)

    prjroot = normpath(join(rootdir, desc.projectDir))

    overrides = desc.overrides
    if overrides:
        __log__.debug('overriding packages')
        for package, version in overrides.items():
            if version:
                cmd = getpack + [package, version]
                call(cmd, cwd=prjroot, retry=3)
            else:
                print 'Removing', package
                shutil.rmtree(join(prjroot, package), ignore_errors=True)

    __log__.debug('checkout of %s completed in %s', desc, prjroot)

def ignore(desc, rootdir='.'): # pylint: disable=W0613
    '''
    Special checkout function used to just declare a project version in the
    configuration but do not perform the checkout, so that it's picked up from
    the release area.
    '''
    __log__.info('checkout not requested for %s', desc)

def git(desc, rootdir='.'):
    '''
    Checkout from a git repository.

    This function requires mandatory 'url' field in the 'checkout_opts' of the
    project description.
    '''
    if 'url' not in desc.checkout_opts:
        raise RuntimeError('mandatory checkout_opts "url" is missing')
    url = desc.checkout_opts['url']
    commit = desc.checkout_opts.get('commit', 'master')
    __log__.debug('checking out %s from %s (%s)', desc, url, commit)
    dest = os.path.join(rootdir, desc.projectDir)
    call(['git', 'clone', url, dest])
    call(['git', 'checkout', commit], cwd=dest)
    f = open(os.path.join(dest, 'Makefile'), 'w')
    f.write('include $(LBCONFIGURATIONROOT)/data/Makefile\n')
    f.close()
    __log__.debug('checkout of %s completed in %s', desc, dest)
