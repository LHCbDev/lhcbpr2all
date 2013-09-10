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

from LbNightlyTools.Utils import retry_call as call, ensureDirs

__log__ = logging.getLogger(__name__)

def getpack(desc, rootdir='.'):
    '''
    Checkout the project described by the ProjectDesc 'desc'.

    The optional field 'recursive_head' in the 'checkout_opts' can be used to
    override the default behavior (i.e. use the head of all the packages for
    the project HEAD and the tags for an explicit project version).
    '''
    from os.path import normpath, join
    getpack_cmd = ['getpack', '--batch', '--no-config',
                   '--protocol', 'ssh']
    recursive_head = desc.checkout_opts.get('recursive_head',
                                            desc.version == 'HEAD')
    cmd = getpack_cmd + ['-P',
                         '-H' if recursive_head else '-r',
                         desc.name, desc.version]
    __log__.debug('checking out %s', desc)
    call(cmd, cwd=rootdir, retry=3)

    prjroot = normpath(join(rootdir, desc.projectDir))

    overrides = desc.overrides
    if overrides:
        __log__.debug('overriding packages')
        for package, version in overrides.items():
            if version:
                cmd = getpack_cmd + [package, version]
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

def svn(desc, rootdir='.'):
    '''
    Checkout from an svn repository.

    This function requires mandatory 'url' field in the 'checkout_opts' of the
    project description.
    '''
    if 'url' not in desc.checkout_opts:
        raise RuntimeError('mandatory checkout_opts "url" is missing')
    url = desc.checkout_opts['url']
    __log__.debug('checking out %s from %s', desc, url)
    dest = os.path.join(rootdir, desc.projectDir)
    call(['svn', 'checkout', url, dest])
    makefile = os.path.join(dest, 'Makefile')
    if not os.path.exists(makefile):
        f = open(makefile, 'w')
        f.write('include $(LBCONFIGURATIONROOT)/data/Makefile\n')
        f.close()
    else:
        __log__.debug('using original Makefile')
    __log__.debug('checkout of %s completed in %s', desc, dest)

def copy(desc, rootdir='.'):
    '''
    Copy the content of a directory.

    Requires a mandatory 'src' field in the 'checkout_opts' of the
    project description.
    '''
    if 'src' not in desc.checkout_opts:
        raise RuntimeError('mandatory checkout_opts "src" is missing')
    src = desc.checkout_opts['src']
    __log__.debug('copying %s from %s', desc, src)
    dest = os.path.join(rootdir, desc.projectDir)
    ensureDirs([dest])
    shutil.copytree(os.path.join(src, os.curdir), dest)
    top_makefile = os.path.join(dest, 'Makefile')
    if not os.path.exists(top_makefile):
        f = open(top_makefile, 'w')
        f.write('include $(LBCONFIGURATIONROOT)/data/Makefile\n')
        f.close()
    __log__.debug('copy of %s completed in %s', desc, dest)

def untar(desc, rootdir='.'):
    '''
    Unpack a tarball in the rootdir (assuming that the tarball already contains
    the <PROJECT>/<PROJECT>_<version> directories).

    Requires a mandatory 'src' field in the 'checkout_opts' of the
    project description.
    '''
    if 'src' not in desc.checkout_opts:
        raise RuntimeError('mandatory checkout_opts "src" is missing')
    src = desc.checkout_opts['src']
    __log__.debug('unpacking %s', src)
    call(['tar', '-x', '-C', rootdir, '-f', src])
    dest = os.path.join(rootdir, desc.projectDir)
    if not os.path.isdir(dest):
        raise RuntimeError('the tarfile %s does not contain %s',
                           src, desc.projectDir)
    top_makefile = os.path.join(dest, 'Makefile')
    if not os.path.exists(top_makefile):
        f = open(top_makefile, 'w')
        f.write('include $(LBCONFIGURATIONROOT)/data/Makefile\n')
        f.close()
    __log__.debug('unpacking of %s from %s completed', desc, src)



# set default checkout method
default = getpack # pylint: disable=C0103
