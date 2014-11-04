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
Module supporting the script to index the builds using glimpseindex.
'''
__author__ = 'Marco Clemencic <marco.clemencic@cern.ch>'

import shutil
import os
import re
import logging
from hashlib import sha1 # pylint: disable=E0611
from subprocess import Popen, PIPE

from LbNightlyTools import Configuration
from LbNightlyTools.Utils import pack, ensureDirs
from LbNightlyTools.BuildSlot import ProjDesc

ALLOWED_EXTENSIONS = set([# official sources (yes, including Python and options)
                          '.h', '.cpp', '.icpp', '.py', '.opts',
                          # special sources
                          '.cxx', '.hpp', '.C', '.cc', '.c', '.F', '.inc',
                          # shell scripts
                          '.sh', '.csh',
                          # extras
                          '.txt', '.cmake',
                         ])
INCLUSIONS = [r'.*/requirements$', r'.*/scripts/[^.]*$'
              ]

EXCLUSIONS = [r'.*_confDb\.py$', r'.*Conf\.py$', r'InstallArea.*\.cmake$',
              r'CTest.*\.cmake', r'SlotConfig\.cmake',
              r'cache_preload\.cmake',
              r'(.*/)?(set|clean)up\.c?sh$',
              r'.*_dict\.cpp$',
              r'.*/genConf/.*']

__log__ = logging.getLogger(__name__)

def parseConfigFile(path):
    '''
    Load the slot configuration file and translate it in a list of ProjDesc
    instances.
    '''
    config = Configuration.load(path)
    return config[u'slot'], map(ProjDesc, config[u'projects'])

def _isFileWanted(path):
    '''
    Tell is a path is required according to the allowed extensions, inclusion
    and exclusion rules.

    >>> _isFileWanted('source.cpp')
    True
    >>> _isFileWanted('test.xml')
    False
    >>> _isFileWanted('cmt/requirements')
    True
    >>> _isFileWanted('InstallArea/ProjectConfig.cmake')
    False
    '''
    # helpers
    def isMatchedByAny(path, regexps):
        '@return: True is any expression in regexps matches path'
        return any(re.match(ex, path) for ex in regexps)
    def isIncluded(path):
        '@return: True is the file is in the inclusions list'
        ext = os.path.splitext(path)[1]
        return ext in ALLOWED_EXTENSIONS or isMatchedByAny(path, INCLUSIONS)
    def isExcluded(path):
        '@return: True is the file is in the exclusions list'
        return isMatchedByAny(path, EXCLUSIONS)

    # we accept files that have the right extension or are matched by one of
    # the INCLUSIONS patterns
    return isIncluded(path) and not isExcluded(path)

def filesToIndex(path):
    '''
    Given a directory, return an iterator over the files that need to be
    indexed, according to a filename pattern and avoiding duplication.

    The returned file names are relative to 'path'.
    '''
    hashes = set() # keep track of the contents indexed

    def isNotEmpty(path):
        '@return: True if the path exist and is not empty'
        return os.path.exists(path) and os.stat(path).st_size != 0

    for root, dirs, files in os.walk(path):
        # ensure that we get a predictable order
        dirs.sort()
        files.sort()
        # move 'InstallArea' to the beginning of the list
        if 'InstallArea' in dirs:
            dirs.remove('InstallArea')
            dirs.insert(0, 'InstallArea')
        # remove directories called 'build.*'
        for build_dir in [d for d in dirs if d.startswith('build.')]:
            dirs.remove(build_dir)
        # loop over the list of files
        for filename in files:
            filename = os.path.join(root, filename)
            relname = os.path.relpath(filename, path)
            # accept only the allowed extensions or no extension for scripts
            if _isFileWanted(relname) and isNotEmpty(filename):
                # return this filename only if the content was not yet
                # encountered
                filehash = sha1(open(filename).read()).digest()
                if filehash not in hashes:
                    hashes.add(filehash)
                    yield relname

import LbUtils.Script
class Script(LbUtils.Script.PlainScript):
    '''
    Script to produce the index files for all the projects defined in the
    configuration.

    The configuration file must be in JSON format containing an object with the
    attribute 'projects', a list of objects with defining the projects to be
    checked out.

    For example::
        {"projects": [{"name": "Gaudi",
                       "version": "v23r5"},
                      {"name": "LHCb",
                       "version": "v32r5"}]}
    '''
    __usage__ = '%prog [options] <config.json>'
    __version__ = ''

    def defineOpts(self):
        '''Options of the script.'''
        from LbNightlyTools.ScriptsCommon import addBasicOptions
        addBasicOptions(self.parser)

    def packname(self, proj):
        '''
        Return the filename of the archive (package) of the given project.
        '''
        packname = [proj.name, proj.version]
        if self.options.build_id:
            packname.append(self.options.build_id)
        packname.append('index')
        packname.append('tar.bz2')
        return '.'.join(packname)

    def main(self):
        """ User code place holder """
        from os.path import join
        from LbNightlyTools.ScriptsCommon import expandTokensInOptions

        if len(self.args) != 1:
            self.parser.error('wrong number of arguments')

        # FIXME: check if the command glimpseindex is available

        slot, projects = parseConfigFile(self.args[0])

        build_dir = join(os.getcwd(), 'build')
        indexes_dir = join(os.getcwd(), 'indexes')

        from datetime import datetime

        starttime = datetime.now()

        expandTokensInOptions(self.options, ['build_id', 'artifacts_dir'],
                              slot=slot)

        artifacts_dir = join(os.getcwd(), self.options.artifacts_dir)

        self.log.debug('cleaning indexes directory')
        if os.path.exists(indexes_dir):
            shutil.rmtree(indexes_dir)

        ensureDirs([indexes_dir, artifacts_dir])

        log_level = self.log.getEffectiveLevel()
        if log_level <= logging.DEBUG:
            glimpse_stdout = None # this prints to the regular stdout
        else:
            glimpse_stdout = open(os.devnull, 'w') # throw away output

        for proj in projects:

            proj_root = join(build_dir, proj.dir)
            # ignore missing directories
            # (the project may not have been checked out)
            if not os.path.exists(proj_root):
                self.log.warning('%s not found, skip indexing', proj)
                continue

            self.log.info('Indexing %s', proj)

            index_dir = join(indexes_dir, proj.dir)
            ensureDirs([index_dir])

            glimpseindex = Popen(['glimpseindex', '-H', index_dir, '-F'],
                                  cwd=proj_root,
                                  stdin=PIPE,
                                  stdout=glimpse_stdout)
            for f in filesToIndex(proj_root):
                glimpseindex.stdin.write(f + '\n')
            glimpseindex.stdin.close()
            glimpseindex.wait()

            self.log.info('packing indexes for %s...', proj)
            pack([proj.dir], join(artifacts_dir, self.packname(proj)),
                 cwd=indexes_dir, checksum='md5')

        self.log.info('files indexed (time taken: %s).',
                      datetime.now() - starttime)
        return 0
