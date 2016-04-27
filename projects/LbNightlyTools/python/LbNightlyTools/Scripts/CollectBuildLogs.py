###############################################################################
# (c) Copyright 2015 CERN                                                     #
#                                                                             #
# This software is distributed under the terms of the GNU General Public      #
# Licence version 3 (GPL Version 3), copied verbatim in the file "COPYING".   #
#                                                                             #
# In applying this licence, CERN does not waive the privileges and immunities #
# granted to it by virtue of its status as an Intergovernmental Organization  #
# or submit itself to any jurisdiction.                                       #
###############################################################################
'''
Collect the build logs produced by lbn-wrapcmd and write the content grouped by
subdir and target.
'''
__author__ = 'Marco Clemencic <marco.clemencic@cern.ch>'

import os
import logging

def collect_cmake_logs(path):
    '''
    Looks for files ending in '-build.log' in all the subdirs.

    @param path: directory where to start the search from
    @return: dictionary with the subdir as key (relative path) and the list of
             files (full path) as values.
    '''
    logging.getLogger('collect_cmake_logs').info('searching for log files')
    logs = {}
    for subdir, _dirs, files in os.walk(path):
        files = [os.path.join(subdir, f)
                 for f in files if f.endswith('-build.log')]
        if files:
            files.sort()
            logs[os.path.relpath(subdir, path)] = files
    return logs

def collect_cmt_logs(path, platform):
    '''
    Looks for files ending in '-build.log' in all the subdirs.

    @param path: directory where to start the search from
    @return: dictionary with the subdir as key (relative path) and the list of
             files (full path) as values.
    '''
    logging.getLogger('collect_cmt_logs').info('searching for log files')
    logs = {}
    filename = 'build.{0}.log'.format(platform)
    for subdir, _dirs, files in os.walk(path):
        if filename in files:
            logs[os.path.relpath(subdir, path)] = [os.path.join(subdir,
                                                                filename)]
    return logs

class RegexExcusion(object):
    '''
    Small helper class to filter a list excluding entries matching one of the
    provided regular expressions.
    '''
    def __init__(self, exps):
        '''
        Initialize the object with a list of regular expression (strings).
        '''
        from re import compile
        self.exps = map(compile, exps)

    def __call__(self, s):
        '''
        Check if a string is good (no match) or not (match).

        @return: True is there is no match, False if there is a match.
        '''
        for x in self.exps:
            if x.match(s):
                return False
        return True

    def filter(self, iterable):
        '''
        Generator that returns only the good (not excluded) entries in an
        iterable.
        '''
        return (s for s in iterable if self(s))

import LbUtils.Script
class Script(LbUtils.Script.PlainScript):
    '''
    Collect partial build logs from a directory and group them in a single
    file.
    '''
    __usage__ = '%prog [options] directory output_file'

    def defineOpts(self):
        '''
        Options specific to this script.
        '''
        self.parser.add_option('--append', action="store_true",
                               help='append to the output file instead of '
                                    'overwrite it')
        self.parser.add_option('-x', '--exclude', action="append",
                               help='regular expression to select files that '
                                    'should not be included in the output')
        self.parser.add_option('--cmt', action='store_const',
                               dest='build_tool', const='cmt',
                               help='expect a CMT build directory')
        self.parser.add_option('--cmake', action='store_const',
                               dest='build_tool', const='cmake',
                               help='expect a CMake build directory (default)')
        self.parser.add_option('--platform', action='store',
                               help='platform id (used only with the CMT '
                                    'scanner) [default: %default]')
        platform = os.environ.get('BINARY_TAG', os.environ.get('CMTCONFIG', ''))
        self.parser.set_defaults(exclude=[],
                                 build_tool='cmake',
                                 platform=platform)

    def cmake(self):
        '''
        CMake specific logic.
        '''
        path, output = self.args
        exclude = RegexExcusion(self.options.exclude)

        logs = collect_cmake_logs(path)
        if not logs:
            self.log.error('lbn-wrapcmd did not produce files in %s', path)
            return 1

        # sort the directories by contained filename, so that even if they
        # are built at the same time, the one that completes first wins
        # (note that the list of files in each subdir is sorted)
        from os.path import basename
        subdirs = sorted(logs, key=lambda s: (basename(logs[s][-1]), s))
        # copy the content of each log file into the output file, prepending
        # the group of files in a subdir with a separator
        with open(output, 'a' if self.options.append else 'w') as outfile:
            for subdir in subdirs:
                # we want to show only files that are not excluded
                files = exclude.filter(logs[subdir])
                if files:
                    # targets in the '.' directory are "global" targets
                    if subdir == '.':
                        subdir = "'global'"
                    outfile.write('#### CMake %s ####\n' % subdir)
                    for fname in files:
                        outfile.writelines(open(fname))

    def cmt(self):
        '''
        CMT specific logic.
        '''
        path, output = self.args
        exclude = RegexExcusion(self.options.exclude)

        logs = collect_cmt_logs(path, self.options.platform)
        if not logs:
            self.log.error('CMT build did not produce log files in %s', path)
            return 1

        # sort the directories by contained filename, so that even if they
        # are built at the same time, the one that completes first wins
        # (note that the list of files in each subdir is sorted)
        import re
        hdr = re.compile(r'Building package[^[]*\[(\d+)/\d+\]')
        def key(subdir):
            filename = logs[subdir][0]
            #self.log.debug('key for %s', filename)
            with open(filename) as f:
                m = hdr.search(f.read(1024))
            k = int(m.group(1)) if m else None
            #self.log.debug('key found: %s', k)
            return k

        subdirs = sorted(logs, key=key)
        # copy the content of each log file into the output file, prepending
        # the group of files in a subdir with a separator
        with open(output, 'a' if self.options.append else 'w') as outfile:
            for subdir in subdirs:
                # we want to show only files that are not excluded
                files = exclude.filter(logs[subdir])
                for fname in files:
                    outfile.writelines(open(fname))

    def main(self):
        '''
        Script logic.
        '''

        getattr(self, self.options.build_tool)()

        return 0