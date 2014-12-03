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
Common functions to deal with the configuration files.
'''
__author__ = 'Marco Clemencic <marco.clemencic@cern.ch>'

import os
import re
import types
import logging

__log__ = logging.getLogger(__name__)

# constants
GP_EXP = re.compile(r'gaudi_project\(([^)]+)\)')
HT_EXP = re.compile(r'set\(\s*heptools_version\s+([^)]+)\)')

# all configured slots (Slot instances)
slots = {}

class Project(object):
    '''
    Describe a project to be checked out, built and tested.
    '''
    def __init__(self, name, version, **kwargs):
        '''
        @param name: name of the project
        @param version: version of the project as 'vXrY' or 'HEAD', where 'HEAD'
                        means the head version of all the packages
        @param overrides: dictionary describing the differences between the
                          versions of the packages in the requested projects
                          version and the ones required in the checkout
        @param checkout: callable that can check out the specified project
        @param checkout_opts: dictionary with extra options for the checkout
                              callable
        @param disabled: if set to True, the project is taken into account only
                         for the configuration
        '''
        self.name = name
        self.version = 'HEAD' if version.upper() == 'HEAD' else version

        self.disabled = kwargs.get('disabled', False)

        self.overrides = kwargs.get('overrides', {})

        import CheckoutMethods
        checkout = kwargs.get('checkout', CheckoutMethods.default)
        if type(checkout) in types.StringTypes:
            if '.' in checkout:
                m, f = checkout.rsplit('.', 1)
                checkout = getattr(__import__(m, fromlist=[f]), f)
            else:
                checkout = getattr(CheckoutMethods, checkout)
        # note that self.checkout is a method
        self.checkout = checkout

        self.checkout_opts = kwargs.get('checkout_opts', {})

        # slot owning this project
        self.slot = None

    def build(self):
        '''
        Build the project.
        '''

    @property
    def baseDir(self):
        '''Name of the project directory (relative to the build directory).'''
        upcase = self.name.upper()
        return os.path.join(upcase, '{0}_{1}'.format(upcase, self.version))

    @property
    def rootdir(self):
        '''
        Directory where the project is.
        '''
        return self.slot.rootdir if self.slot else self._rootdir

    @rootdir.setter
    def rootdir(self, value):
        '''
        Set the directory where the project is.
        '''
        if not self.slot:
            self._rootdir = value
        else:
            raise AttributeError("can't set attribute")

    def getDeps(self):
        '''
        Return the dependencies of a checked out project using the information
        retrieved from the configuration files.
        @return: list of used projects (all converted to lowercase)
        '''
        proj_root = os.path.join(self.rootdir, self.baseDir)
        deps = []

        # try with CMakeLists.txt first
        try:
            cmake = os.path.join(proj_root, 'CMakeLists.txt')
            # arguments to the gaudi_project call
            args = GP_EXP.search(open(cmake).read()).group(1).split()
            if 'USE' in args:
                # look for the indexes of the range 'USE' ... 'DATA'
                use_idx = args.index('USE') + 1
                if 'DATA' in args:
                    data_idx = args.index('DATA')
                else:
                    data_idx = len(args)
                # extract the odds elements (project names) and convert them
                # to lower case
                deps = [p.lower() for p in args[use_idx:data_idx:2]]

            # artificial dependency on LCGCMT, if needed
            toolchain = os.path.join(proj_root, 'toolchain.cmake')
            if (os.path.exists(toolchain) and
                HT_EXP.search(open(toolchain).read())):
                # we set explicit the version of heptools,
                # so we depend on LCGCMT
                deps.append('lcgcmt')
        except:
            # try with CMT
            try:
                cmt = os.path.join(proj_root, 'cmt', 'project.cmt')
                # from all the lines in project.cmt that start with 'use',
                # we extract the second word (project name) and convert it to
                # lower case
                deps = [l.split()[1].lower()
                        for l in [l.strip() for l in open(cmt)]
                        if l.startswith('use')]
            except:
                __log__.warning('cannot discover dependencies for %s', self)
        return sorted(deps)

    def __str__(self):
        '''String representation of the project.'''
        return "{0} {1}".format(self.name, self.version)


class Package(object):
    pass


class _SlotMeta(type):
    '''
    Metaclass for Slot.
    '''
    def __init__(cls, name, bases, dct):
        '''
        Class initialization by the metaclass.
        '''
        super(_SlotMeta, cls).__init__(name, bases, dct)
        if 'projects' in dct:
            cls.__projects__ = dct['projects']
        cls.projects = property(lambda self: self._projects)

class ProjectsList(list):
    '''
    Helper class to handle a list of projects bound to a slot.
    '''
    def __init__(self, slot, iterable=None):
        '''
        Initialize the ProjectList from an optional iterable, which must contain
        only Project instances.
        '''
        self.slot = slot
        def checkElements(iterable):
            '''helper to check the elements of the iterable'''
            if iterable is None:
                return
            for element in iterable:
                if isinstance(element, Project):
                    element.slot = slot
                    yield element
                else:
                    raise ValueError('only Project instances are allowed')
        super(ProjectsList, self).__init__(checkElements(iterable))

    def __getitem__(self, key):
        '''
        Extension of the default list [] operator, so that it can get the
        contained project by name or by position.
        '''
        if isinstance(key, basestring):
            for proj in self.__iter__():
                if proj.name == key:
                    return proj
            raise KeyError('project %r not found' % key)
        return super(ProjectsList, self).__getitem__(key)

    def __setitem__(self, idx, element):
        '''
        Override item assignment, so that the binding between the Project
        instances and the slot is kept in sync.
        '''
        if not isinstance(element, Project):
            raise ValueError('only Project instances are allowed')
        old = self[idx]
        super(ProjectsList, self).__setitem__(idx, element)
        element.slot = self.slot
        old.slot = None

    def insert(self, idx, element):
        '''
        Override item insertion, so that the binding between the Project
        instances and the slot is kept in sync.
        '''
        if not isinstance(element, Project):
            raise ValueError('only Project instances are allowed')
        element.slot = self.slot
        return super(ProjectsList, self).insert(idx, element)

    def append(self, element):
        '''
        Override item insertion, so that the binding between the Project
        instances and the slot is kept in sync.
        '''
        if not isinstance(element, Project):
            raise ValueError('only Project instances are allowed')
        element.slot = self.slot
        return super(ProjectsList, self).append(element)

    def __delitem__(self, idx):
        '''
        Override item removal, so that the binding between the Project
        instances and the slot is kept in sync.
        '''
        old = self[idx]
        super(ProjectsList, self).__delitem__(idx)
        old.slot = None

    def remove(self, element):
        '''
        Override item removal, so that the binding between the Project
        instances and the slot is kept in sync.
        '''
        super(ProjectsList, self).remove(element)
        element.slot = None

class Slot(object):
    '''
    Class representing a nightly build slot.
    '''
    __metaclass__ = _SlotMeta
    __slots__ = ('_name', '_projects')
    __projects__ = []
    rootdir = os.curdir

    def __init__(self, name, projects=None):
        '''
        Initialize the slot with name and optional list of projects.
        '''
        self._name = name
        if projects is None:
            projects = self.__class__.__projects__
        self._projects = ProjectsList(self, projects)

        # add this slot to the global list of slots
        global slots
        slots[name] = self

    @property
    def name(self):
        '''
        Name of the slot.
        '''
        return self._name
    @name.setter
    def name(self, value):
        '''
        Change the name of the slot, keeping the slots global list in sync.
        '''
        global slots
        del slots[self._name]
        self._name = value
        slots[self._name] = self

    def __getattr__(self, name):
        '''
        Get the project with given name in the slot.
        '''
        for proj in self._projects:
            if proj.name == name:
                return proj
        raise AttributeError('%r object has no attribute %r' %
                             (self.__class__.__name__, name))

    def __delattr__(self, name):
        '''
        Remove a project from the slot.
        '''
        self.projects.remove(self.projects[name])

    def __dir__(self):
        '''
        Return the list of names of the attributes of the instance.
        '''
        return self.__dict__.keys() + [proj.name for proj in self.projects]

    def checkout(self, export=False):
        '''
        Checkout all the projects in the slot.
        '''
        os.chdir(self.rootdir)
        for project in self.projects:
            project.checkout(export=True)


def extractVersion(tag):
    '''
    Extract the version number from as SVN tag.

    >>> extractVersion('GAUDI_v23r8')
    'v23r8'
    >>> extractVersion('LCGCMT_preview')
    'preview'
    '''
    return tag.split('_', 1)[1]

def loadFromOldXML(source, slot):
    '''
    Read an old-style XML configuration and generate the corresponding
    dictionary in the new-style configuration.

    @param source: XML path, file object, URL
    @param slot: name of the slot to extract
    '''
    from xml.etree.ElementTree import parse
    doc = parse(source)

    def fixPlaceHolders(s):
        '''
        Replace the old placeholders with the new ones.
        '''
        s = s.replace('%DAY%', '${TODAY}')
        s = s.replace('%YESTERDAY%', '${YESTERDAY}')
        s = s.replace('%PLATFORM%', '${CMTCONFIG}')
        return s

    data = {'slot': slot,
            'env': []}
    try:
        slot_el = (el for el in doc.findall('slot')
                   if el.attrib.get('name') == slot).next()

        cmt_proj_path = ':'.join([fixPlaceHolders(el.attrib['value'])
                                  for el in
                                      slot_el.findall('cmtprojectpath/path')])
        if cmt_proj_path:
            data['env'].append('CMTPROJECTPATH=' + cmt_proj_path)

        desc = slot_el.attrib.get('description', '(no description)')
        m = re.match(r'%s(:| -|\.)\s+' % slot, desc)
        if m:
            desc = desc[:m.start()] + desc[m.end():]
        data['description'] = desc

        elem = slot_el.find('cmtextratags')
        if elem is not None:
            data['env'].append('CMTEXTRATAGS=' + elem.attrib['value'])

        if slot.startswith('lhcb-compatibility'):
            data['env'].append('GAUDI_QMTEST_DEFAULT_SUITE=compatibility')

        elem = slot_el.find('waitfor')
        if elem is not None:
            path = fixPlaceHolders(elem.attrib['flag'])
            data['preconditions'] = [{"name": "waitForFile",
                                      "args": {"path": path}}]

        data['default_platforms'] = [p.attrib['name']
                                     for p in
                                         slot_el.findall('platforms/platform')
                                     if 'name' in p.attrib]

        projects = []
        project_names = set()
        for proj in slot_el.findall('projects/project'):
            name = proj.attrib['name']
            version = extractVersion(proj.attrib['tag'])
            overrides = {}
            for elem in proj.findall('addon') + proj.findall('change'):
                overrides[elem.attrib['package']] = elem.attrib['value']
            # check if we have dep overrides
            project_names.add(name) # keep track of the names found so far
            for elem in proj.findall('dependence'):
                dep_name = elem.attrib['project']
                if dep_name not in project_names:
                    project_names.add(dep_name)
                    dep_vers = extractVersion(elem.attrib['tag'])
                    projects.append({'name': dep_name,
                                     'version': dep_vers,
                                     'overrides': {},
                                     'checkout': 'ignore'})

            proj_data = {'name': name,
                         'version': version,
                         'overrides': overrides}
            if proj.attrib.get('disabled', 'false').lower() != 'false':
                proj_data['checkout'] = 'ignore'
            if 'headofeverything' in proj.attrib:
                recursive_head = proj.attrib.get('headofeverything').lower()
                recursive_head = recursive_head == 'true'
                if (version == 'HEAD') != recursive_head:
                    # HEAD implies recursive_head True, so add the special
                    # option only if needed
                    proj_data['checkout_opts'] = {'recursive_head':
                                                    recursive_head}
            if name == 'Geant4':
                # By default, created the shared tarball for Geant4
                proj_data['with_shared'] = True
            projects.append(proj_data)

        data['projects'] = projects

        if slot_el.attrib.get('use_cmake', 'false').lower() != 'true':
            data['USE_CMT'] = True

        def el2re(elem):
            '''Regex string for ignored warning or error.'''
            val = elem.attrib['value']
            if elem.attrib.get('type', 'string') == 'regex':
                return val
            else:
                return re.escape(val)
        data['error_exceptions'] = map(el2re,
                                       doc.findall('general/ignore/error'))
        data['warning_exceptions'] = map(el2re,
                                         doc.findall('general/ignore/warning'))

        return data
    except StopIteration:
        raise RuntimeError('cannot find slot {0}'.format(slot))


def load(path):
    '''
    Load the configuration from a file.

    By default, the file is assumed to be a JSON file, unless it ends with
    '#<slot-name>', in which case the XML parsing is used.
    '''
    try:
        source, slot = path.rsplit('#', 1)
        return loadFromOldXML(source, slot)
    except ValueError:
        import json
        from os.path import splitext, basename
        data = json.load(open(path, 'rb'))
        if u'slot' not in data:
            data[u'slot'] = splitext(basename(path))[0]
        return data

def save(dest, config):
    '''
    Helper function to dump the current configuration to a file.
    '''
    f = open(dest, 'wb')
    f.write(configToString(config))
    f.close()

def configToString(config):
    '''
    Convert the configuration to a string.
    '''
    import json
    return json.dumps(config, sort_keys=True, indent=2, separators=(',', ': '))
