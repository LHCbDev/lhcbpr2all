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
import shutil
import json
from tempfile import mkdtemp

from LbNightlyTools.Utils import Dashboard
db_info = ('http://dummyname:9999/', '_db')

def test_instantiation():
    tmpdir = mkdtemp()
    try:
        dash = Dashboard(submit=False)
        assert dash.db is None
        assert dash.dumpdir is None

        # these must not fail, but need a real DB to do something useful
        Dashboard(db_info=db_info)
        Dashboard(credentials=('user', 'password'), db_info=db_info)

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

def test_filedump():
    tmpdir = mkdtemp()
    try:
        dumpdir = os.path.join(tmpdir, 'db')
        dash = Dashboard(dumpdir=dumpdir, db_info=db_info)
        assert dash.dumpdir is dumpdir
        assert os.path.isdir(dumpdir)

        data = {'type': 'data-type',
                'slot': 'my-slot',
                'build_id': 121,
                'project': 'MyProject'}
        dash.publish(data)

        filename = os.path.join(dumpdir, 'my-slot.121.MyProject.data-type.json')
        assert os.path.isfile(filename)

        dump = json.load(open(filename))
        assert data == dump

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
