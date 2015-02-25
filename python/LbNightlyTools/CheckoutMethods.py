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
from LbNightlyTools.Utils import retry_tee_call, tee_call, ensureDirs

__log__ = logging.getLogger(__name__)

def _merge_outputs(outputs):
    '''
    Helper function to merge the tuples returned by tee_call.

    >>> _merge_outputs([(1, 'a\\n', ''), (0, 'b\\n', '')]
    (1, 'a\\nb\\n', '')
    '''
    returncode = 0
    for out in outputs:
        if out[0]:
            returncode = out[0]
    return (returncode,
            ''.join(step[1] for step in outputs),
            ''.join(step[2] for step in outputs))

def getpack(desc, recursive_head=None, export=False,
            protocol=None, verbose=False):
    '''
    Checkout the project described by the Project instance 'desc'.
    '''
    from os.path import normpath, join
    protocol = protocol or os.environ.get('GETPACK_PROTOCOL', 'anonymous')
    getpack_cmd = ['getpack', '--batch', '--no-config',
                   '--no-eclipse', '--branches',
                   '--protocol', protocol]

    if recursive_head is None:
        recursive_head = desc.version == 'HEAD'

    rootdir = os.curdir
    prjroot = normpath(desc.baseDir)
    from LbNightlyTools.Configuration import Project
    if isinstance(desc, Project):
        # we are checking out a project
        cmd = getpack_cmd + ['-P',
                             '-H' if recursive_head else '-r']
    else:
        # we are checking out a data package
        cmd = getpack_cmd + ['-v']
        if desc.container:
            rootdir = desc.container.baseDir
    if export:
        cmd.append('--export')
    cmd.extend([desc.name, desc.version])

    if not os.path.exists(rootdir):
        __log__.debug('creating %s', rootdir)
        os.makedirs(rootdir)

    __log__.debug('checking out %s', desc)
    outputs = [retry_tee_call(cmd, cwd=rootdir, retry=3, verbose=verbose)]

    if hasattr(desc, 'overrides') and desc.overrides:
        __log__.debug('overriding packages')
        for package, version in desc.overrides.items():
            if version:
                cmd = getpack_cmd + [package, version]
                outputs.append(retry_tee_call(cmd, cwd=prjroot, retry=3,
                                              verbose=verbose))
            else:
                if verbose:
                    print 'Removing', package
                outputs.append((0, 'Removing %s\n' % package, ''))
                shutil.rmtree(join(prjroot, package), ignore_errors=True)

    __log__.debug('checkout of %s completed in %s', desc, prjroot)
    return _merge_outputs(outputs)

def ignore(desc, export=False, verbose=False):
    '''
    Special checkout function used to just declare a project version in the
    configuration but do not perform the checkout, so that it's picked up from
    the release area.
    '''
    __log__.info('checkout not requested for %s', desc)
    return (0, 'checkout not requested for %s' % desc, '')

def git(desc, url, commit='master', export=False, verbose=False):
    '''
    Checkout from a git repository.
    '''
    __log__.debug('checking out %s from %s (%s)', desc, url, commit)
    dest = desc.baseDir
    __log__.debug('cloning git repository %s', url)

    outputs = []
    def call(*args, **kwargs):
        'helper to simplify the code'
        outputs.append(tee_call(*args, verbose=verbose, **kwargs))

    call(['git', 'clone', '--no-checkout', url, dest])
    if not export:
        __log__.debug('checkout commit %s for %s', commit, desc)
        call(['git', 'checkout', commit], cwd=dest)
        for subdir, version in desc.overrides.iteritems():
            if version is None:
                __log__.debug('removing %s', subdir)
                shutil.rmtree(path=os.path.join(dest, subdir),
                              ignore_errors=True)
            else:
                __log__.debug('checking out commit %s for dir %s',
                              version, subdir)
                call(['git', 'checkout', version, subdir], cwd=dest)
    else:
        # FIXME: the outputs of git archive is not collected
        __log__.debug('extracting the list of branches')
        proc = Popen(['git', 'branch', '-a'], cwd=dest, stdout=PIPE)
        branches = set(branch[2:].rstrip()
                       for branch in proc.communicate()[0].splitlines())
        if 'remotes/origin/' + commit in branches:
            commit = 'origin/' + commit
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
    if not os.path.exists(os.path.join(dest, 'toolchain.cmake')):
        f = open(os.path.join(dest, 'toolchain.cmake'), 'w')
        f.write('include($ENV{LBUTILSROOT}/data/toolchain.cmake)\n')
        f.close()
    __log__.debug('checkout of %s completed in %s', desc, dest)
    return _merge_outputs(outputs)

def svn(desc, url, export=False, verbose=False):
    '''
    Checkout from an svn repository.
    '''
    __log__.debug('checking out %s from %s', desc, url)
    dest = desc.baseDir
    output = tee_call(['svn', 'checkout' if not export else 'export',
                       url, dest], verbose=verbose)
    makefile = os.path.join(dest, 'Makefile')
    if not os.path.exists(makefile):
        f = open(makefile, 'w')
        f.write('include $(LBCONFIGURATIONROOT)/data/Makefile\n')
        f.close()
    else:
        __log__.debug('using original Makefile')
    __log__.debug('checkout of %s completed in %s', desc, dest)
    return output

def copy(desc, src, export=False, verbose=False):
    '''
    Copy the content of a directory.
    '''
    __log__.debug('copying %s from %s', desc, src)
    dest = desc.baseDir
    ensureDirs([os.path.dirname(dest)])
    shutil.copytree(os.path.join(src, os.curdir), dest)
    top_makefile = os.path.join(dest, 'Makefile')
    if not os.path.exists(top_makefile):
        f = open(top_makefile, 'w')
        f.write('include $(LBCONFIGURATIONROOT)/data/Makefile\n')
        f.close()
    __log__.debug('copy of %s completed in %s', desc, dest)
    return (0, 'copied %s from %s' % (desc, src), '')

def untar(desc, src, export=False, verbose=False):
    '''
    Unpack a tarball in the current directory (assuming that the tarball already
    contains the <PROJECT>/<PROJECT>_<version> directories).
    '''
    __log__.debug('unpacking %s', src)
    output = tee_call(['tar', '-x', '-f', src],
                      verbose=verbose)
    dest = desc.baseDir
    if not os.path.isdir(dest):
        raise RuntimeError('the tarfile %s does not contain %s',
                           src, desc.baseDir)
    top_makefile = os.path.join(dest, 'Makefile')
    if not os.path.exists(top_makefile):
        f = open(top_makefile, 'w')
        f.write('include $(LBCONFIGURATIONROOT)/data/Makefile\n')
        f.close()
    __log__.debug('unpacking of %s from %s completed', desc, src)
    return output

def dirac(desc, url='git://github.com/DIRACGrid/DIRAC.git', commit=None,
          export=False, etc='/afs/cern.ch/lhcb/software/releases/DIRAC/etc',
          verbose=False):
    '''
    Special hybrid checkout needed to release DIRAC.
    '''
    from os.path import normpath, join, isdir, exists, basename, dirname

    if commit is None:
        commit = desc.version
    if commit.lower() == 'head':
        commit = 'master'

    protocol = os.environ.get('GETPACK_PROTOCOL', 'anonymous')
    getpack_cmd = ['getpack', '--batch', '--no-config',
                   '--no-eclipse', '--branches',
                   '--protocol', protocol]
    if export:
        getpack_cmd.append('--export')

    prjroot = desc.baseDir

    outputs = []
    def call(*args, **kwargs):
        'helper to simplify the code'
        outputs.append(tee_call(*args, verbose=verbose, **kwargs))

    __log__.debug('checking out project %s', desc)
    call(getpack_cmd + ['--project', desc.name, desc.version], retry=3)
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
        # FIXME: the outputs of git archive is not collected
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
    shutil.copytree(etc, join(prjroot, 'etc'))
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

    return _merge_outputs(outputs)


def lhcbdirac(desc, export=False, verbose=False):
    '''
    Special hybrid checkout needed to release LHCbDirac.
    '''
    from os.path import normpath, join, isdir, basename
    if desc.version.lower() == 'head':
        url = 'http://svn.cern.ch/guest/dirac/LHCbDIRAC/trunk/LHCbDIRAC'
    else:
        url = ('http://svn.cern.ch/guest/dirac/LHCbDIRAC/tags/LHCbDIRAC/' +
               desc.version)

    protocol = os.environ.get('GETPACK_PROTOCOL', 'anonymous')
    getpack_cmd = ['getpack', '--batch', '--no-config',
                   '--no-eclipse', '--branches',
                   '--protocol', protocol]
    if export:
        getpack_cmd.append('--export')

    prjroot = desc.baseDir
    dest = join(prjroot, 'LHCbDIRAC')

    outputs = []
    def call(*args, **kwargs):
        'helper to simplify the code'
        outputs.append(tee_call(*args, verbose=verbose, **kwargs))

    __log__.debug('checking out project %s', desc)
    call(getpack_cmd + ['--project', desc.name, desc.version], retry=3)
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

    return _merge_outputs(outputs)


def lhcbgrid(desc, url=None, export=False, verbose=False):
    '''
    Special hybrid checkout needed to release LHCbGrid.
    '''
    if url is None:
        if desc.version.lower() == 'head':
            url = 'http://svn.cern.ch/guest/lhcb/LHCbGrid/trunk'
        else:
            url = ('http://svn.cern.ch/guest/lhcb/LHCbGrid/tags/' +
                   'LHCBGRID/LHCBGRID_' + desc.version)

    svn(desc, url=url, export=export)

    outputs = []
    def call(*args, **kwargs):
        'helper to simplify the code'
        outputs.append(tee_call(*args, verbose=verbose, **kwargs))

    dest = desc.baseDir
    __log__.debug('fixing requirements files')
    call(['make', 'clean'], cwd=dest)
    call(['make', 'requirements'], cwd=dest)

    return _merge_outputs(outputs)


GAUDI_GIT_URL = 'http://git.cern.ch/pub/gaudi'
def gaudi(proj, url=GAUDI_GIT_URL, export=False, verbose=False):
    '''
    Wrapper around the git function for Gaudi.
    '''
    import re
    if proj.version.lower() == 'head':
        commit = 'master'
    elif re.match(r'v[0-9]+r[0-9]+', proj.version):
        commit = '{0}/{0}_{1}'.format(proj.name.upper(), proj.version)
    else:
        commit = proj.version
    return git(proj, url, commit, export, verbose)


LIT_GIT_URL = 'http://git.cern.ch/pub/LHCbIntegrationTests'
def lhcbintegrationtests(proj, url=LIT_GIT_URL, export=False, verbose=False):
    '''
    Wrapper around the git function for LHCbIntegrationTests.
    '''
    if proj.version.lower() == 'head':
        commit = 'master'
    else:
        commit = proj.version
    return git(proj, url, commit, export, verbose)


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
