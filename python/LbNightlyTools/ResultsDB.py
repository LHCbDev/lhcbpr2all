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
Module to encapsulated the access to the database of the results.

@author: Marco Clemencic
'''

import urllib2
import httplib

from json import loads, dumps
from datetime import datetime, timedelta
from socket import gethostname

START_OFFSET = timedelta(hours=2)

class BuildInfoError(RuntimeError):
    '''
    Generic error for operations with the BuildInfo object.
    '''
    pass

class BuildInfo(object):
    '''
    Class representing a slot result object in the database.
    '''
    __slots__ = ('_id', '_rev',
                 'day', 'slot', 'platform',
                 'started', 'completed', 'host',
                 'projects')

    def __init__(self, **kwargs):
        if 'json' in kwargs:
            json = loads(kwargs['json'])
            for k in json:
                setattr(self, k, json[k])
        else:
            now = datetime.now()

            self.day = list((now + START_OFFSET).timetuple())[:3]
            self.slot = kwargs['slot']
            self.platform = kwargs['platform']

            self._id = self.id(self.day, self.slot, self.platform)

            self.host = gethostname()

            self.started = list(now.timetuple())[:6]
            self.projects = []

    def stop(self):
        self.completed = list(datetime.now().timetuple()[:6])

    @classmethod
    def id(cls, slot, platform, day=None):
        if day is None:
            day = (datetime.now() + START_OFFSET).strftime('%Y%m%d')
        elif hasattr(day, 'strftime'):
            day = day.strftime('%Y%m%d')
        elif type(day) is list:
            day = ''.join(map(str, day))
        return '{0}.{1}.{2}'.format(day, slot, platform)

    def addProject(self, project, version):
        if hasattr(self, 'completed'):
            raise BuildInfoError('cannot add project build: build already completed')
        for p in self.projects:
            if p['name'] == project:
                raise BuildInfoError('cannot add project: project %s already present' % project)
        d = {'name': project, 'version': version}
        self.projects.append(d)

    def addProjectBuild(self, project, warnings, errors):
        if hasattr(self, 'completed'):
            raise BuildInfoError('cannot add project build: build already completed')
        for p in self.projects:
            if p['name'] == project:
                if 'build' in p:
                    raise BuildInfoError('cannot add project build: project %s already built' % project)
                else:
                    p['build'] = [warnings, errors]
                    break
        else:
            raise BuildInfoError('cannot add project tests: project %s unknown' % project)

    def addProjectTests(self, project, failures, total):
        if hasattr(self, 'completed'):
            raise BuildInfoError('cannot add project tests: build already completed')
        for p in self.projects:
            if p['name'] == project:
                if 'tests' in p:
                    raise BuildInfoError('cannot add project tests: project %s already tested' % project)
                if 'build' not in p:
                    raise BuildInfoError('cannot add project tests: project %s not built' % project)
                p['tests'] = [failures, total]
                break
        else:
            raise BuildInfoError('cannot add project tests: project %s unknown' % project)

    def __str__(self):
        data = dict([(k, getattr(self, k))
                     for k in self.__slots__
                     if hasattr(self, k)])
        return dumps(data)

class CouchDB(object):
    def __init__(self, url):
        self.url = url
        self.protocol, url = urllib2.splittype(url)
        self.host, self.base = urllib2.splithost(url)

    def get(self, slot, platform, day):
        key = BuildInfo.id(slot, platform, day)
        data = urllib2.urlopen(self.url + '/' + key).read()
        return BuildInfo(json=data)

    def store(self, info):
        conn = httplib.HTTPConnection(self.host)
        conn.request('PUT', self.base + '/' + info._id, str(info), {'Content-Type': 'application/json'})
        resp = conn.getresponse()
        result = loads(resp.read())
        if resp.status >= 400:
            raise RuntimeError('{error}: {reason}'.format(**result))
        info._rev = result['rev']
        return info

def connect(url):
    return CouchDB(url)
