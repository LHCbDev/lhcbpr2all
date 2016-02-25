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
import re
from subprocess import Popen, PIPE
from LbNightlyTools.Utils import (retry_log_call as _retry_log_call,
                                  log_call as _log_call, ensureDirs,
                                  getMRsource)

__log__ = logging.getLogger(__name__)
__log__.setLevel(logging.DEBUG)

def retry_log_call(*args, **kwargs):
    '''
    Helper to send log messages of retry_log_call to __log__ by default.
    '''
    if 'logger' not in kwargs:
        kwargs['logger'] = __log__.getChild(args[0][0].replace('.', '_'))
    return _retry_log_call(*args, **kwargs)

def log_call(*args, **kwargs):
    '''
    Helper to send log messages of log_call to __log__ by default.
    '''
    if 'logger' not in kwargs:
        kwargs['logger'] = __log__.getChild(args[0][0].replace('.', '_'))
    return _log_call(*args, **kwargs)

def _merge_outputs(outputs):
    '''
    Helper function to merge the tuples returned by log_call.

    >>> _merge_outputs([(1, 'a\\n', ''), (0, 'b\\n', '')])
    (1, 'a\\nb\\n', '')
    '''
    returncode = 0
    for out in outputs:
        if out[0]:
            returncode = out[0]
    return (returncode,
            ''.join(step[1] for step in outputs),
            ''.join(step[2] for step in outputs))

def getpack(desc, recursive_head=None, export=False, protocol=None):
    '''
    Checkout the project described by the Project instance 'desc'.
    '''
    from os.path import normpath, join
    log = __log__.getChild('getpack')
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
        log.debug('creating %s', rootdir)
        os.makedirs(rootdir)

    log.debug('checking out %s', desc)
    outputs = [retry_log_call(cmd, cwd=rootdir, retry=3)]

    if hasattr(desc, 'overrides') and desc.overrides:
        errors = False
        log.debug('overriding packages')
        for package, version in desc.overrides.items():
            if version:
                cmd = getpack_cmd + [package, version]
                try:
                    outputs.append(retry_log_call(cmd, cwd=prjroot, retry=3))
                except RuntimeError, x:
                    log.warning(str(x))
                    errors = True
            else:
                log.debug('removing %s', package)
                outputs.append((0, 'Removing %s\n' % package, ''))
                shutil.rmtree(join(prjroot, package), ignore_errors=True)
        if errors:
            raise RuntimeError('problems handling overrides')

    log.debug('checkout of %s completed in %s', desc, prjroot)
    return _merge_outputs(outputs)

def ignore(desc, export=False):
    '''
    Special checkout function used to just declare a project version in the
    configuration but do not perform the checkout, so that it's picked up from
    the release area.
    '''
    log = __log__.getChild('ignore')
    log.info('checkout not requested for %s', desc)
    return (0, 'checkout not requested for %s' % desc, '')

# default URLs for known projects (project names must be lowercase)
GIT_URLS = {'gaudi': 'https://gitlab.cern.ch/gaudi/Gaudi.git',
            'lhcbintegrationtests':
                'https://gitlab.cern.ch/lhcb/LHCbIntegrationTests.git',
            'lhcbgrid': 'https://gitlab.cern.ch/lhcb-dirac/LHCbGrid.git',
            'lhcbdirac': 'https://gitlab.cern.ch/lhcb-dirac/LHCbDIRAC.git',
            'lbscripts': 'https://gitlab.cern.ch/lhcb-core/LbScripts.git',
            }

def git(desc, url=None, commit=None, export=False, merge=None):
    '''
    Checkout from a git repository.

    @param desc: Configuration.Project instance
    @param url: git repository URL (default derived from desc.name)
    @param commit: commit id to checkout (default derived from desc.version)
    @param export: whether to use git "checkout" or "archive"
    @param merge: merge options as (<url>, <commit> [, <remote_name>])
    '''
    if not url:
        url = GIT_URLS[desc.name.lower()]
    if not commit:
        if desc.version.lower() == 'head':
            commit = 'master'
        else:
            commit = desc.version
    log = __log__.getChild('git')
    log.debug('checking out %s from %s (%s)', desc, url, commit)
    dest = desc.baseDir
    if merge:
        if export:
            log.warning('merge option is ignored when export is True')
            merge = merge_url = merge_commit = None
        else:
            if len(merge) == 2:
                merge += ('merge_source',)
            merge_url, merge_commit, merge_source = merge
            log.debug('merging %s from %s (%s)',
                      merge_commit, merge_source, merge_url)

    outputs = []
    def call(*args, **kwargs):
        'helper to simplify the code'
        outputs.append(log_call(*args, **kwargs))

    commit_id = merge_commit_id = None

    log.debug('cloning git repository %s', url)
    call(['git', 'clone', '--no-checkout', url, dest])
    if not os.path.exists(dest):
        # ensure the destination directory exists even when the cloning fails
        os.makedirs(dest)
    else:
        if merge:
            call(['git', 'remote', 'add', '-f', merge_source, merge_url],
                 cwd=dest)

        log.debug('extracting the list of branches')
        proc = Popen(['git', 'branch', '-a'], cwd=dest, stdout=PIPE)
        branches = set(branch[2:].rstrip()
                       for branch in proc.communicate()[0].splitlines())
        if commit not in branches and 'remotes/origin/' + commit in branches:
            commit = 'origin/' + commit
        commit_id = Popen(['git', 'rev-parse', commit],
                          cwd=dest, stdout=PIPE).communicate()[0].strip()

        if merge:
            if 'remotes/%s/%s' % (merge_source, merge_commit) in branches:
                merge_commit = '%s/%s' % (merge_source, merge_commit)
            merge_commit_id = Popen(['git', 'rev-parse', merge_commit],
                                    cwd=dest,
                                    stdout=PIPE).communicate()[0].strip()

    if not export:
        log.debug('checkout commit %s for %s', commit, desc)
        call(['git', 'checkout', commit], cwd=dest)
        if merge:
            log.debug('merging %s', merge_commit)
            call(['git', 'merge', '--no-ff', merge_commit], cwd=dest)
        # handle submodules
        if os.path.exists(os.path.join(dest, '.gitmodules')):
            call(['git', 'submodule', 'update', '--init', '--recursive'],
                 cwd=dest)
        for subdir, version in desc.overrides.iteritems():
            if version is None:
                log.debug('removing %s', subdir)
                shutil.rmtree(path=os.path.join(dest, subdir),
                              ignore_errors=True)
            else:
                log.debug('checking out commit %s for dir %s',
                              version, subdir)
                call(['git', 'checkout', version, subdir], cwd=dest)
    else:
        # FIXME: the outputs of git archive is not collected
        log.debug('export commit %s for %s', commit, desc)
        call(['git', 'checkout', commit], cwd=dest)
        if os.path.exists(os.path.join(dest, '.gitmodules')):
            call(['git', 'submodule', 'update', '--init', '--recursive'],
                 cwd=dest)
            submodules = [os.path.join(dest, l.split()[1])
                          for l in Popen(['git', 'submodule',
                                          'status', '--recursive'],
                                         cwd=dest, stdout=PIPE)
                          .communicate()[0].splitlines()]
        else:
            submodules = []


        def git_export(path, commit):
            log.debug('export commit %s in %s', commit, path)
            proc1 = Popen(['git', 'archive', commit],
                          cwd=path, stdout=PIPE)
            proc2 = Popen(['tar', '--extract', '--overwrite', '--file', '-'],
                          cwd=path, stdin=proc1.stdout)
            proc1.stdout.close()  # Allow proc1 to receive a SIGPIPE if proc2 exits.
            if proc2.wait() or proc1.wait():
                log.warning('problems exporting commit %s in %s', commit, path)
            shutil.rmtree(path=os.path.join(path, '.git'), ignore_errors=True)

        git_export(dest, commit)
        for path in submodules:
            git_export(path, 'HEAD')

    f = open(os.path.join(dest, 'Makefile'), 'w')
    f.write('include $(LBCONFIGURATIONROOT)/data/Makefile\n')
    f.close()
    if not os.path.exists(os.path.join(dest, 'toolchain.cmake')):
        f = open(os.path.join(dest, 'toolchain.cmake'), 'w')
        f.write('include($ENV{LBUTILSROOT}/data/toolchain.cmake)\n')
        f.close()
    log.debug('checkout of %s completed in %s', desc, dest)
    if commit_id:
        log.debug('using commit %s', commit_id)
        if merge_commit_id:
            log.debug('merging commit %s', merge_commit_id)
    else:
        log.warning('unable to detect the used commit id')
    return _merge_outputs(outputs)

def svn(desc, url, export=False):
    '''
    Checkout from an svn repository.
    '''
    log = __log__.getChild('svn')
    log.debug('checking out %s from %s', desc, url)
    dest = desc.baseDir
    output = log_call(['svn', 'checkout' if not export else 'export',
                       url, dest])
    makefile = os.path.join(dest, 'Makefile')
    if not os.path.exists(makefile):
        f = open(makefile, 'w')
        f.write('include $(LBCONFIGURATIONROOT)/data/Makefile\n')
        f.close()
    else:
        log.debug('using original Makefile')
    log.debug('checkout of %s completed in %s', desc, dest)
    return output

def copy(desc, src, export=False):
    '''
    Copy the content of a directory.
    '''
    log = __log__.getChild('copy')
    log.debug('copying %s from %s', desc, src)
    dest = desc.baseDir
    ensureDirs([os.path.dirname(dest)])
    shutil.copytree(os.path.join(src, os.curdir), dest)
    top_makefile = os.path.join(dest, 'Makefile')
    if not os.path.exists(top_makefile):
        f = open(top_makefile, 'w')
        f.write('include $(LBCONFIGURATIONROOT)/data/Makefile\n')
        f.close()
    log.debug('copy of %s completed in %s', desc, dest)
    return (0, 'copied %s from %s' % (desc, src), '')

def untar(desc, src, export=False):
    '''
    Unpack a tarball in the current directory (assuming that the tarball already
    contains the <PROJECT>/<PROJECT>_<version> directories).
    '''
    log = __log__.getChild('untar')
    log.debug('unpacking %s', src)
    output = log_call(['tar', '-x', '-f', src])
    dest = desc.baseDir
    if not os.path.isdir(dest):
        raise RuntimeError('the tarfile %s does not contain %s',
                           src, desc.baseDir)
    top_makefile = os.path.join(dest, 'Makefile')
    if not os.path.exists(top_makefile):
        f = open(top_makefile, 'w')
        f.write('include $(LBCONFIGURATIONROOT)/data/Makefile\n')
        f.close()
    log.debug('unpacking of %s from %s completed', desc, src)
    return output

def dirac(desc, url='git://github.com/DIRACGrid/DIRAC.git', commit=None,
          export=False, etc='/afs/cern.ch/lhcb/software/releases/DIRAC/etc'):
    '''
    Special hybrid checkout needed to release DIRAC.
    '''
    from os.path import normpath, join, isdir, exists, basename, dirname
    log = __log__.getChild('dirac')

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
        outputs.append(log_call(*args, **kwargs))
    def rcall(*args, **kwargs):
        'helper to simplify the code'
        outputs.append(retry_log_call(*args, **kwargs))

    log.debug('checking out project %s', desc)
    rcall(getpack_cmd + ['--project', desc.name, desc.version], retry=3)
    for pkg in ('DiracPolicy', 'DiracConfig', 'DiracSys'):
        log.debug('checking out package %s', pkg)
        rcall(getpack_cmd + [pkg, desc.version], cwd=prjroot, retry=3)

    dest = normpath(join(prjroot, 'DIRAC'))
    log.debug('cloning git repository %s', url)
    commit_id = None
    call(['git', 'clone', '--no-checkout', url, dest])

    if not os.path.exists(dest):
        # ensure the destination directory exists even when the cloning fails
        os.makedirs(dest)
    else:
        log.debug('extracting the list of branches')
        proc = Popen(['git', 'branch', '-a'], cwd=dest, stdout=PIPE)
        branches = set(branch[2:].rstrip()
                       for branch in proc.communicate()[0].splitlines())
        if commit not in branches and 'remotes/origin/' + commit in branches:
            commit = 'origin/' + commit

        commit_id = Popen(['git', 'rev-parse', commit],
                          cwd=dest, stdout=PIPE).communicate()[0].strip()

    if not export:
        log.debug('checkout commit %s for %s', commit, desc)
        call(['git', 'checkout', commit], cwd=dest)
    else:
        # FIXME: the outputs of git archive is not collected
        log.debug('export commit %s for %s', commit, desc)
        proc1 = Popen(['git', 'archive', commit],
                   cwd=dest, stdout=PIPE)
        proc2 = Popen(['tar', '--extract', '--file', '-'],
                   cwd=dest, stdin=proc1.stdout)
        proc1.stdout.close()  # Allow proc1 to receive a SIGPIPE if proc2 exits.
        if proc2.wait() or proc1.wait():
            log.warning('problems exporting commit %s for %s', commit, desc)
        shutil.rmtree(path=os.path.join(dest, '.git'), ignore_errors=True)
    log.debug('checkout of %s completed in %s', desc, prjroot)
    if commit_id:
        log.debug('using commit %s', commit_id)
    else:
        log.warning('unable to detect the used commit id')

    log.debug('starting post-checkout step for %s', desc)
    log.debug('deploying scripts')
    scripts_dir = join(prjroot, 'scripts')
    if not isdir(scripts_dir):
        os.makedirs(scripts_dir)
    for root, dirs, files in os.walk(prjroot):
        if root == prjroot:
            if 'scripts' in dirs:
                dirs.remove('scripts')
        elif 'scripts' in dirs:
            log.debug('  - %s', root)
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

    log.debug('generate cmt dirs')
    # loop over the directories in the DIRAC directory (excluding . and ..)
    for cmt in [join(dest, pkg, 'cmt')
                for pkg in os.listdir(dest)
                if pkg[0] != '.' and isdir(join(dest, pkg))]:
        if not exists(cmt):
            log.debug('creating %s', cmt)
            os.makedirs(cmt)
            #log.debug('writing version.cmt')
            with open(join(cmt, 'version.cmt'), 'w') as f:
                f.write(desc.version + '\n')
            #log.debug('writing requirements')
            with open(join(cmt, 'requirements'), 'w') as f:
                f.write('package %s\nuse DiracPolicy *\n' %
                        basename(dirname(cmt)))
    log.debug('populate etc directory')
    shutil.copytree(etc, join(prjroot, 'etc'))
    log.debug('prepare dummy Makefile')
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


def lhcbdirac(proj, url=None, export=False):
    '''
    Special hybrid checkout needed to release LHCbDirac.
    '''
    from os.path import join, isdir, basename

    log = __log__.getChild('lhcbdirac')
    if proj.version.lower() == 'head':
        commit = 'devel'
    else:
        commit = proj.version

    prjroot = proj.baseDir

    output = git(proj, url, commit, export)

    log.debug('creating version.cmt files')
    for root, dirs, files in os.walk(prjroot):
        if basename(root) == 'cmt':
            dirs[:] = [] # stop recursion
            if 'version.cmt' not in files:
                log.debug('  writing %s/version.cmt', root)
                with open(join(root, 'version.cmt'), 'w') as f:
                    f.write('v*\n')

    log.debug('starting post-checkout step for %s', proj)
    log.debug('deploying scripts')
    scripts_dir = join(prjroot, 'scripts')
    if not isdir(scripts_dir):
        os.makedirs(scripts_dir)
    for root, dirs, files in os.walk(join(prjroot, 'LHCbDIRAC')):
        if 'scripts' in dirs:
            log.debug('  - %s', root)
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

    log.debug('patching Makefile')
    with open(join(prjroot, 'Makefile'), 'a') as f:
        f.write('\nall:\n\t$(RM) InstallArea/python InstallArea/scripts\n')

    return output


def lhcbgrid(proj, url=None, export=False, merge=None):
    '''
    Special checkout needed to release LHCbGrid.
    '''
    log = __log__.getChild('lhcbgrid')

    if proj.version.lower() == 'head':
        commit = 'master'
    elif re.match(r'mr[0-9]+$', proj.version):
        commit = 'master'
        try:
            merge = merge or getMRsource('lhcb/LHCbGrid', int(proj.version[2:]))
        except:
            log.error('error: failed to get details for merge request %s',
                      proj.version[2:])
            raise
    else:
        commit = proj.version

    outputs = []
    outputs.append(git(proj, url, commit, export, merge))

    def call(*args, **kwargs):
        'helper to simplify the code'
        outputs.append(log_call(*args, **kwargs))

    dest = proj.baseDir
    log.debug('fixing requirements files')
    call(['make', 'clean'], cwd=dest)
    call(['make', 'requirements'], cwd=dest)

    return _merge_outputs(outputs)


def gaudi(proj, url=None, export=False, merge=None):
    '''
    Wrapper around the git function for Gaudi.
    '''
    log = __log__.getChild('gaudi')
    if proj.version.lower() == 'head':
        commit = 'master'
    elif re.match(r'mr[0-9]+$', proj.version):
        commit = 'master'
        try:
            # Temporary workaround for
            # https://cern.service-now.com/service-portal/view-incident.do?n=INC0964521
            #merge = merge or getMRsource('gaudi/Gaudi', int(proj.version[2:]),
            #                             slot=proj.slot)
            merge = merge or getMRsource(38, int(proj.version[2:]),
                                         slot=proj.slot)
        except:
            log.error('error: failed to get details for merge request %s',
                      proj.version[2:])
            raise
    else:
        commit = proj.version
    return git(proj, url, commit, export, merge)


LCG_MAKEFILE_TEMPLATE = '''
configure:
\tfor s in "{src}"/* ; do if [ -d "$$s" ] ; then ln -svf "$$s" . ; else cp -vf "$$s" . ; fi ; done
\tfor s in LCG_externals_*.txt ; do sed -i 's*{src}*'$$(pwd)'*' "$$s" ; done

all:
install:
\tmkdir -p InstallArea/$(CMTCONFIG)
\ttouch InstallArea/$(CMTCONFIG)/.empty
unsafe-install: install
post-install:
test:
'''
def lcg(proj, src=None):
    '''
    Special checkout method to create a shallow clone of the LCG special
    project.
    '''
    log = __log__.getChild('lcg')

    if not src:
        src = proj.src
    dest = proj.baseDir

    if not os.path.exists(dest):
        log.debug('created %s', dest)
        os.makedirs(dest)

    with open(os.path.join(dest, 'Makefile'), 'w') as mkf:
        mkf.write(LCG_MAKEFILE_TEMPLATE.format(src=src))
        log.debug('created %s', mkf.name)

    log.info('created shallow project %s in %s', proj, dest)

    return (0, '', '')


def ganga(desc, rootdir='.'):
    '''
    Special hybrid checkout needed to release Ganga.
    '''
    __log__.debug('getting checkout script')
    script_url = ('svn+ssh://svn.cern.ch/reps/ganga/trunk/external/'
                  'LHCbSetupProject/scripts/lhcb-prepare')
    retry_log_call(['svn', 'export', script_url], cwd=rootdir)
    __log__.debug('running checkout script')
    retry_log_call([os.path.join(rootdir, 'lhcb-prepare'),
                    '-d', rootdir, desc.version.lower()])

    projdir = os.path.join(rootdir, desc.baseDir)

    __log__.debug('creating Makefile')
    with open(os.path.join(projdir, 'Makefile'), 'w') as f:
        f.write('include ${LBCONFIGURATIONROOT}/data/Makefile\n')


def lbscripts(proj, url=None, export=False, merge=None, commit=None):
    '''
    Specific checkout wrapper for lbscripts
    '''
    from  LbScriptsUtils import updateInstallProject, \
        updateLbConfigurationRequirements, \
        updateVersionCmt

    log = __log__.getChild('lbscripts')

    # Setting commit
    if proj.version.lower() == 'head':
        commit = 'master'
    elif re.match(r'mr[0-9]+$', proj.version):
        commit = 'master'
        try:
            merge = merge or getMRsource('lhcb/LbScripts', int(proj.version[2:]))
        except:
            log.error('error: failed to get details for merge request %s',
                      proj.version[2:])
            raise
    else:
        commit = proj.version

    # Utilities to gather the results of our calls
    outputs = []
    def call(*args, **kwargs):
        'helper to simplify the code'
        outputs.append(log_call(*args, **kwargs))

    # First checking out LbScripts with GIT
    outputs.append(git(proj, url, commit, export, merge))

    # Now hacking the sources.
    # We need to set the version in LbConfiguration and in install_project
    updateInstallProject(proj.baseDir, proj.version)
    updateLbConfigurationRequirements(proj.baseDir, proj.version)

    # Create the version.cmt file in all packages
    updateVersionCmt(proj.baseDir, proj.version)

    # Now calling make directly after the checkout
    # This is needed to have the InstallArea directory in the source archive
    call(['make', 'USE_CMT=1'], cwd=proj.baseDir)

    # Returning the checkout results
    return _merge_outputs(outputs)


# set default checkout method
default = getpack # pylint: disable=C0103

# use git to checkout projects with
for proj_name in GIT_URLS:
    if proj_name not in dir():
        exec '{0} = git'.format(proj_name)
del proj_name

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
