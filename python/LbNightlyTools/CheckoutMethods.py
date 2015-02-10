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

def getpack(desc):
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

    rootdir = desc.rootdir
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

def ignore(desc):
    '''
    Special checkout function used to just declare a project version in the
    configuration but do not perform the checkout, so that it's picked up from
    the release area.
    '''
    __log__.info('checkout not requested for %s', desc)

def git(desc):
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
    dest = os.path.join(desc.rootdir, desc.baseDir)
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

def svn(desc):
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
    dest = os.path.join(desc.rootdir, desc.baseDir)
    call(['svn', 'checkout' if not export else 'export', url, dest])
    makefile = os.path.join(dest, 'Makefile')
    if not os.path.exists(makefile):
        f = open(makefile, 'w')
        f.write('include $(LBCONFIGURATIONROOT)/data/Makefile\n')
        f.close()
    else:
        __log__.debug('using original Makefile')
    __log__.debug('checkout of %s completed in %s', desc, dest)

def copy(desc):
    '''
    Copy the content of a directory.

    Requires a mandatory 'src' field in the 'checkout_opts' of the
    project description.
    '''
    if 'src' not in desc.checkout_opts:
        raise RuntimeError('mandatory checkout_opts "src" is missing')
    src = desc.checkout_opts['src']
    __log__.debug('copying %s from %s', desc, src)
    dest = os.path.join(desc.rootdir, desc.baseDir)
    ensureDirs([dest])
    shutil.copytree(os.path.join(src, os.curdir), dest)
    top_makefile = os.path.join(dest, 'Makefile')
    if not os.path.exists(top_makefile):
        f = open(top_makefile, 'w')
        f.write('include $(LBCONFIGURATIONROOT)/data/Makefile\n')
        f.close()
    __log__.debug('copy of %s completed in %s', desc, dest)

def untar(desc):
    '''
    Unpack a tarball in the rootdir of desc (assuming that the tarball already
    contains the <PROJECT>/<PROJECT>_<version> directories).

    Requires a mandatory 'src' field in the 'checkout_opts' of the
    project description.
    '''
    if 'src' not in desc.checkout_opts:
        raise RuntimeError('mandatory checkout_opts "src" is missing')
    src = desc.checkout_opts['src']
    __log__.debug('unpacking %s', src)
    call(['tar', '-x', '-C', desc.rootdir, '-f', src])
    dest = os.path.join(desc.rootdir, desc.baseDir)
    if not os.path.isdir(dest):
        raise RuntimeError('the tarfile %s does not contain %s',
                           src, desc.baseDir)
    top_makefile = os.path.join(dest, 'Makefile')
    if not os.path.exists(top_makefile):
        f = open(top_makefile, 'w')
        f.write('include $(LBCONFIGURATIONROOT)/data/Makefile\n')
        f.close()
    __log__.debug('unpacking of %s from %s completed', desc, src)

def dirac(desc):
    '''
    Special hybrid checkout needed to release DIRAC.
    '''
    from os.path import normpath, join, isdir, exists, basename, dirname

    url = desc.checkout_opts.get('url', 'git://github.com/DIRACGrid/DIRAC.git')
    commit = desc.checkout_opts.get('commit', desc.version)
    if commit.lower() == 'head':
        commit = 'master'
    export = desc.checkout_opts.get('export', False)
    etc_orig = desc.checkout_opts.get('etc',
                   '/afs/cern.ch/lhcb/software/releases/DIRAC/etc')

    protocol = os.environ.get('GETPACK_PROTOCOL', 'anonymous')
    getpack_cmd = ['getpack', '--batch', '--no-config',
                   '--no-eclipse', '--branches',
                   '--protocol', protocol]
    if export:
        getpack_cmd.append('--export')

    rootdir = desc.rootdir
    prjroot = normpath(join(rootdir, desc.baseDir))

    if not os.path.exists(rootdir):
        __log__.debug('creating %s', rootdir)
        os.makedirs(rootdir)

    __log__.debug('checking out project %s', desc)
    call(getpack_cmd + ['--project', desc.name, desc.version],
         cwd=rootdir, retry=3)
    for pkg in ('DiracPolicy', 'DiracConfig', 'DiracSys'):
        __log__.debug('checking out package %s', pkg)
        call(getpack_cmd + [pkg, desc.version], cwd=prjroot, retry=3)

    dest = normpath(join(prjroot, 'DIRAC'))
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
    __log__.debug('checkout of %s completed in %s', desc, prjroot)

    __log__.debug('starting post-checkout step for %s', desc)
    __log__.debug('deploying scripts')
    scripts_dir = join(prjroot, 'scripts')
    if not isdir(scripts_dir):
        os.makedirs(scripts_dir)
    for root, dirs, files in os.walk(prjroot):
        if root == prjroot:
            if 'scripts' in dirs:
                dirs.remove('scripts')
        elif 'scripts' in dirs:
            __log__.debug('  - %s', root)
            # we are only interested in the content of the scripts directories
            dirs[:] = ['scripts']
        elif basename(root) == 'scripts':
            dirs[:] = [] # avoid further recursion (it should not be needed)
            for f in files:
                if f.endswith('.py'):
                    dst = join(scripts_dir, f[:-3])
                else:
                    dst = join(scripts_dir, f)
                shutil.copyfile(join(root, f), dst)
                os.chmod(dst, 0755) # ensure that the new file is executable

    __log__.debug('generate cmt dirs')
    # loop over the directories in the DIRAC directory (excluding . and ..)
    for cmt in [join(dest, pkg, 'cmt')
                for pkg in os.listdir(dest)
                if pkg[0] != '.' and isdir(join(dest, pkg))]:
        if not exists(cmt):
            __log__.debug('creating %s', cmt)
            os.makedirs(cmt)
            #__log__.debug('writing version.cmt')
            with open(join(cmt, 'version.cmt'), 'w') as f:
                f.write(desc.version + '\n')
            #__log__.debug('writing requirements')
            with open(join(cmt, 'requirements'), 'w') as f:
                f.write('package %s\nuse DiracPolicy *\n' %
                        basename(dirname(cmt)))
    __log__.debug('populate etc directory')
    shutil.copytree(etc_orig, join(prjroot, 'etc'))
    __log__.debug('prepare dummy Makefile')
    with open(join(prjroot, 'Makefile'), 'w') as f:
        f.write('''
all:
\tmkdir -p InstallArea/${{CMTCONFIG}}
\techo '# Building package {project} [0/0]' > build.${{CMTCONFIG}}.log
\techo 'nothing to build' >> build.${{CMTCONFIG}}.log
\techo '<?xml version="1.0" encoding="UTF-8"?>' > InstallArea/${{CMTCONFIG}}/manifest.xml
\techo '<manifest><project name="{project}" version="{version}" /></manifest>' >> InstallArea/${{CMTCONFIG}}/manifest.xml
tests:
'''.format(project=desc.name, version=desc.version))


def lhcbdirac(desc):
    '''
    Special hybrid checkout needed to release LHCbDirac.
    '''
    from os.path import normpath, join, isdir, basename
    if desc.version.lower() == 'head':
        url = 'http://svn.cern.ch/guest/dirac/LHCbDIRAC/trunk/LHCbDIRAC'
    else:
        url = ('http://svn.cern.ch/guest/dirac/LHCbDIRAC/tags/LHCbDIRAC/' +
               desc.version)

    export = desc.checkout_opts.get('export', False)

    protocol = os.environ.get('GETPACK_PROTOCOL', 'anonymous')
    getpack_cmd = ['getpack', '--batch', '--no-config',
                   '--no-eclipse', '--branches',
                   '--protocol', protocol]
    if export:
        getpack_cmd.append('--export')

    rootdir = desc.rootdir
    prjroot = normpath(join(rootdir, desc.baseDir))
    dest = join(prjroot, 'LHCbDIRAC')

    if not os.path.exists(rootdir):
        __log__.debug('creating %s', rootdir)
        os.makedirs(rootdir)

    __log__.debug('checking out project %s', desc)
    call(getpack_cmd + ['--project', desc.name, desc.version],
         cwd=rootdir, retry=3)
    for pkg in ('LHCbDiracPolicy', 'LHCbDiracConfig', 'LHCbDiracSys'):
        __log__.debug('checking out package %s', pkg)
        call(getpack_cmd + [pkg, desc.version], cwd=prjroot, retry=3)

    __log__.debug('checking out %s', url)
    call(['svn', 'checkout' if not export else 'export', url , dest])
    __log__.debug('creating version.cmt files')
    for root, dirs, files in os.walk(dest):
        if basename(root) == 'cmt':
            dirs[:] = [] # stop recursion
            if 'version.cmt' not in files:
                __log__.debug('  writing %s/version.cmt', root)
                open(join(root, 'version.cmt'), 'w').write('v*\n')

    __log__.debug('starting post-checkout step for %s', desc)
    __log__.debug('deploying scripts')
    scripts_dir = join(prjroot, 'scripts')
    if not isdir(scripts_dir):
        os.makedirs(scripts_dir)
    for root, dirs, files in os.walk(dest):
        if 'scripts' in dirs:
            __log__.debug('  - %s', root)
            # we are only interested in the content of the scripts directories
            dirs[:] = ['scripts']
        elif basename(root) == 'scripts':
            dirs[:] = [] # avoid further recursion (it should not be needed)
            for f in files:
                if f.endswith('.py'):
                    dst = join(scripts_dir, f[:-3])
                else:
                    dst = join(scripts_dir, f)
                shutil.copyfile(join(root, f), dst)
                os.chmod(dst, 0755) # ensure that the new file is executable

    __log__.debug('patching Makefile')
    with open(join(prjroot, 'Makefile'), 'a') as f:
        f.write('\nall:\n\t$(RM) InstallArea/python InstallArea/scripts\n')


def lhcbgrid(desc):
    '''
    Special hybrid checkout needed to release LHCbGrid.
    '''
    if 'url' not in desc.checkout_opts:
        if desc.version.lower() == 'head':
            url = 'http://svn.cern.ch/guest/lhcb/LHCbGrid/trunk'
        else:
            url = ('http://svn.cern.ch/guest/lhcb/LHCbGrid/tags/' +
                   'LHCBGRID/LHCBGRID_' + desc.version)
        desc.checkout_opts['url'] = url

    svn(desc)

    dest = os.path.join(desc.rootdir, desc.baseDir)
    __log__.debug('fixing requirements files')
    call(['make', 'clean'], cwd=dest)
    call(['make', 'requirements'], cwd=dest)

# set default checkout method
default = getpack # pylint: disable=C0103

def getMethod(method=None):
    '''
    Helper function to get a checkout method by name.

    If method is a callable we return it, otherwise we look for the name in the
    current module or as a function coming from another module.
    If method is None, we return the default checkout method.
    '''
    if method is None:
        return default
    if hasattr(method, '__call__'):
        return method
    if isinstance(method, basestring):
        if '.' in method:
            # method is a fully qualified function name
            m, f = method.rsplit('.', 1)
            return getattr(__import__(m, fromlist=[f]), f)
        else:
            # it must be a name in this module
            return globals()[method]
