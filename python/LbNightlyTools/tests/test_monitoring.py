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

# Uncomment to disable the tests.
#__test__ = False

import os
from pprint import pprint
from LbNightlyTools import Monitoring

def test_getDirInfos():
    if os.path.exists('/afs/cern.ch/lhcb/software'):
        infos = Monitoring.getDirInfos('/afs/cern.ch/lhcb/software')
        pprint(infos)
        assert 'path' in infos
        assert infos['path'] == '/afs/cern.ch/lhcb/software'
        assert 'AFS' in infos and infos['AFS'] is True
        assert infos.get('name') == 'p.lhcb.software'
        assert 'bsize' in infos
        assert 'blocks' in infos
        assert 'bavail' in infos
        assert 'mountpoints' in infos and len(infos['mountpoints']) > 0

    infos = Monitoring.getDirInfos('/usr/lib')
    pprint(infos)
    assert 'path' in infos
    assert infos['path'] == '/usr/lib'
    assert 'AFS' in infos and infos['AFS'] is False
    assert 'name' in infos
    assert 'bsize' in infos
    assert 'blocks' in infos
    assert 'bavail' in infos
    assert 'mountpoints' not in infos
