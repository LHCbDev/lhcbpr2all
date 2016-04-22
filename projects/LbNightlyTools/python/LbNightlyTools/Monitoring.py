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
Class and functions used to collect monitoring data.
'''
__author__ = 'Marco Clemencic <marco.clemencic@cern.ch>'

import os

def getDirInfos(path):
    '''
    Return occupancy informations about a directory (on a local disk or on AFS)
    in form of a dictionary.
    '''
    from LbUtils.afs.directory import Directory, NotInAFS
    from LbUtils.afs.volume import Volume
    try:
        directory = Directory(path)
        volume = Volume(dirname=directory.getParentMountPoint())

        infos = dict(path=path,
                     AFS=True,
                     name=volume.name(),
                     mountpoints=[m.name() for m in volume.mountPoints()],
                     bsize=1024,
                     blocks=volume.quota(),
                     bavail=volume.remainingSpace())
    except NotInAFS:
        # find the root of the filesystem
        name = path
        while not os.path.ismount(name):
            name = os.path.dirname(name)

        stats = os.statvfs(name)
        infos = dict(path=path,
                     AFS=False,
                     name=name,
                     bsize=stats.f_bsize,
                     blocks=stats.f_blocks,
                     bavail=stats.f_bavail)

    return infos

