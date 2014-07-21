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

from subprocess import Popen, PIPE
from LbNightlyTools.Utils import retry_call as call, ensureDirs

__log__ = logging.getLogger(__name__)

def getpack(desc, rootdir='.'):
    '''
    Checkout the project described by the Project instance 'desc'.

    The optional field 'recursive_head' in the 'checkout_opts' can be used to
    override the default behavior (i.e. use the head of all the packages for
    the project HEAD and the tags for an explicit project version).
    '''
    from os.path import normpath, join
    protocol = os.environ.get('GETPACK_PROTOCOL', 'anonymous')
    getpack_cmd = ['getpack', '--batch', '--no-config',
                   '--no-eclipse', '--branches',
                   '--protocol', protocol]

    recursive_head = desc.checkout_opts.get('recursive_head',
                                            desc.version == 'HEAD')
    export = desc.checkout_opts.get('export', False)

    prjroot = normpath(join(rootdir, desc.baseDir))
    from LbNightlyTools.Configuration import Project
    if isinstance(desc, Project):
        # we are checking out a project
        cmd = getpack_cmd + ['-P',
                             '-H' if recursive_head else '-r']
    else:
        # we are checking out a data package
        cmd = getpack_cmd + ['-v']
        rootdir = normpath(join(rootdir, desc.container))
    if export:
        cmd.append('--export')
    cmd.extend([desc.name, desc.version])

    if not os.path.exists(rootdir):
        __log__.debug('creating %s', rootdir)
        os.makedirs(rootdir)

    __log__.debug('checking out %s', desc)
    call(cmd, cwd=rootdir, retry=3)

    if hasattr(desc, 'overrides') and desc.overrides:
        __log__.debug('overriding packages')
        for package, version in desc.overrides.items():
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
    export = desc.checkout_opts.get('export', False)

    __log__.debug('checking out %s from %s (%s)', desc, url, commit)
    dest = os.path.join(rootdir, desc.baseDir)
    __log__.debug('cloning git repository %s', url)
    call(['git', 'clone', '--no-checkout', url, dest])
    if not export:
        __log__.debug('checkout commit %s for %s', commit, desc)
        call(['git', 'checkout', commit], cwd=dest)
    else:
        __log__.debug('export commit %s for %s', commit, desc)
        p1 = Popen(['git', 'archive', commit],
                   cwd=dest, stdout=PIPE)
        p2 = Popen(['tar', '--extract', '--file', '-'],
                   cwd=dest, stdin=p1.stdout)
        p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
        if p2.wait() or p1.wait():
            __log__.warning('problems exporting commit %s for %s', commit, desc)
        shutil.rmtree(path=os.path.join(dest, '.git'), ignore_errors=True)
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
    export = desc.checkout_opts.get('export', False)

    __log__.debug('checking out %s from %s', desc, url)
    dest = os.path.join(rootdir, desc.baseDir)
    call(['svn', 'checkout' if not export else 'export', url, dest])
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
    dest = os.path.join(rootdir, desc.baseDir)
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
    dest = os.path.join(rootdir, desc.baseDir)
    if not os.path.isdir(dest):
        raise RuntimeError('the tarfile %s does not contain %s',
                           src, desc.baseDir)
    top_makefile = os.path.join(dest, 'Makefile')
    if not os.path.exists(top_makefile):
        f = open(top_makefile, 'w')
        f.write('include $(LBCONFIGURATIONROOT)/data/Makefile\n')
        f.close()
    __log__.debug('unpacking of %s from %s completed', desc, src)



# set default checkout method
default = getpack # pylint: disable=C0103
