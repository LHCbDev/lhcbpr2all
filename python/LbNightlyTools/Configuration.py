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
import logging
from LbNightlyTools.Utils import (applyenv, tee_call, ensureDirs,
                                  shallow_copytree, IgnorePackageVersions,
                                  find_path)
from collections import OrderedDict

__log__ = logging.getLogger(__name__)


# constants
GP_EXP = re.compile(r'gaudi_project\(([^)]+)\)')
HT_EXP = re.compile(r'set\(\s*heptools_version\s+([^)]+)\)')

# all configured slots (Slot instances)
slots = {}


def sortedByDeps(deps):
    '''
    Take a dictionary of dependencies as {'depender': ['dependee', ...]} and
    return the list of keys sorted according to their dependencies so that
    that a key comes after its dependencies.

    >>> sortedByDeps({'4':['2','3'],'3':['1'],'2':['1'],'1':['0'],'0':[]})
    ['0', '1', '3', '2', '4']

    If the argument is an OrderedDict, the returned list preserves the order of
    the keys (if possible).

    >>> sortedByDeps(dict([('1', []), ('2', ['1']), ('3', ['1'])]))
    ['1', '3', '2']
    >>> sortedByDeps(OrderedDict([('1', []), ('2', ['1']), ('3', ['1'])]))
    ['1', '2', '3']
    '''
    def unique(iterable):
        '''Return only the unique elements in the list l.

        >>> unique([0, 0, 1, 2, 1])
        [0, 1, 2]
        '''
        uniquelist = []
        for item in iterable:
            if item not in uniquelist:
                uniquelist.append(item)
        return uniquelist
    def recurse(keys):
        '''
        Recursive helper function to sort by dependency: for each key we
        first add (recursively) its dependencies then the key itself.'''
        result = []
        for k in keys:
            result.extend(recurse(deps[k]))
            result.append(k)
        return unique(result)
    return recurse(deps)


class _BuildToolProperty(object):
    '''
    Descriptor for the build_tool property of a slot
    '''
    def __get__(self, instance, owner):
        'getter'
        try:
            return instance.slot.build_tool
        except AttributeError:
            return instance._build_tool
    def __set__(self, instance, value):
        'setter'
        if hasattr(instance, 'slot') and instance.slot:
            raise AttributeError("can't set attribute")
        from BuildMethods import getMethod as getBuildMethod
        instance._build_tool = getBuildMethod(value)()


class _ProjectMeta(type):
    '''
    Metaclass for Project.
    '''
    def __new__(cls, name, bases, dct):
        '''
        Instrument Project classes.
        '''
        dct['__build_tool__'] = dct.get('build_tool')
        dct['build_tool'] = _BuildToolProperty()
        if 'name' in dct:
            dct['__project_name__'] = dct.pop('name')
        if 'checkout' in dct and isinstance(dct['checkout'], basestring):
            dct['__checkout__'] = dct.pop('checkout')
        return type.__new__(cls, name, bases, dct)

    def __call__(self, *args, **kwargs):
        '''
        Use the class name as project name in classes derived from Project.
        '''
        name = None
        if hasattr(self, '__project_name__'):
            name = self.__project_name__
        elif self.__name__ != 'Project':
            name = self.__name__
        if name:
            # we prepend the class name to the arguments.
            args = (name,) + args
        return type.__call__(self, *args, **kwargs)

class Project(object):
    '''
    Describe a project to be checked out, built and tested.
    '''
    __metaclass__ = _ProjectMeta
    __checkout__ = 'default'
    def __init__(self, name, version, **kwargs):
        '''
        @param name: name of the project
        @param version: version of the project as 'vXrY' or 'HEAD', where 'HEAD'
                        means the head version of all the packages
        @param dependencies: optional list of dependencies (as list of project
                             names), can be used to extend the actual (code)
                             dependencies of the project
        @param overrides: dictionary describing the differences between the
                          versions of the packages in the requested projects
                          version and the ones required in the checkout
        @param checkout: callable that can check out the specified project
        @param checkout_opts: dictionary with extra options for the checkout
                              callable
        @param disabled: if set to True, the project is taken into account only
                         for the configuration
        @param env: override the environment for the project
        @param build_tool: build method used for the project
        '''
        self.name = name
        self.version = 'HEAD' if version.upper() == 'HEAD' else version

        # slot owning this project
        self.slot = None

        self.disabled = kwargs.get('disabled', False)
        self.overrides = kwargs.get('overrides', {})
        self._deps = kwargs.get('dependencies', [])
        self.env = kwargs.get('env', [])

        from CheckoutMethods import getMethod as getCheckoutMethod
        self._checkout = getCheckoutMethod(kwargs.get('checkout',
                                                      self.__checkout__))

        self.checkout_opts = kwargs.get('checkout_opts', {})

        self.build_tool = kwargs.get('build_tool', self.__build_tool__)

        self.build_results = None

    def checkout(self, **kwargs):
        '''
        Helper function to call the checkout method.
        '''
        __log__.info('checking out %s', self)
        opts = dict(self.checkout_opts)
        opts.update(kwargs)
        return self._checkout(self, **opts)

    def build(self, **kwargs):
        '''
        Build the project.
        @param jobs: number of parallel jobs to use [default: cpu count + 1]
        @param verbose: if True, print the output of the build while running
        '''
        if 'jobs' not in kwargs:
            from multiprocessing import cpu_count
            kwargs['jobs'] = cpu_count() + 1
        self.build_results = self.build_tool.build(self, **kwargs)
        return self.build_results

    def clean(self, **kwargs):
        '''
        Clean the project.
        '''
        return self.build_tool.clean(self, **kwargs)

    def test(self, **kwargs):
        '''
        Test the project.
        '''
        return self.build_tool.test(self, **kwargs)

    @property
    def baseDir(self):
        '''Name of the project directory (relative to the build directory).'''
        upcase = self.name.upper()
        return os.path.join(upcase, '{0}_{1}'.format(upcase, self.version))

    def dependencies(self):
        '''
        Return the dependencies of a checked out project using the information
        retrieved from the configuration files.
        @return: list of used projects (all converted to lowercase)
        '''
        proj_root = self.baseDir

        def fromCMake():
            '''
            Helper to extract dependencies from CMake configuration.
            '''
            deps = []
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
                deps = [p for p in args[use_idx:data_idx:2]]

            # artificial dependency on LCGCMT, if needed
            toolchain = os.path.join(proj_root, 'toolchain.cmake')
            if (os.path.exists(toolchain) and
                HT_EXP.search(open(toolchain).read())):
                # we set explicit the version of heptools,
                # so we depend on LCGCMT
                deps.append('LCGCMT')
            return deps

        def fromCMT():
            '''
            Helper to extract dependencies from CMT configuration.
            '''
            cmt = os.path.join(proj_root, 'cmt', 'project.cmt')
            # from all the lines in project.cmt that start with 'use',
            # we extract the second word (project name) and convert it to
            # lower case
            return [l.split()[1]
                    for l in [l.strip() for l in open(cmt)]
                    if l.startswith('use')]

        def fromProjInfo():
            '''
            Helper to get the dependencies from an info file in the project,
            called 'project.info'.
            The file must be in "config" format (see ConfigParser module) and
            the dependencies must be declared as a comma separated list in
            the section project.

            E.g.:
            [Project]
            dependencies: ProjectA, ProjectB
            '''
            import ConfigParser
            config = ConfigParser.ConfigParser()
            config.read(os.path.join(proj_root, 'project.info'))
            return [proj.strip()
                    for proj in config.get('Project', 'dependencies')
                                      .split(',')]

        # Try all the helpers until one succeeds
        deps = []
        for helper in (fromCMake, fromCMT, fromProjInfo):
            try:
                deps = helper()
                break
            except:
                pass
        else:
            __log__.warning('cannot discover dependencies for %s', self)

        deps = sorted(set(deps + self._deps))
        if self.slot:
            # helper dict to map case insensitive name to correct project names
            names = dict((p.name.lower(), p.name) for p in self.slot.projects)
            def fixNames(iterable):
                'helper to fix the cases of names in dependencies'
                return [names.get(name.lower(), name) for name in iterable]
            deps = fixNames(deps)

        return deps

    def __str__(self):
        '''String representation of the project.'''
        return "{0} {1}".format(self.name, self.version)

    def environment(self, envdict=None):
        '''
        Return a dictionary with the environment for the project.

        If envdict is provided, it will be used as a starting point, otherwise
        the environment defined by the slot or by the system will be used.
        '''
        # get the initial env from the argument or the system
        if envdict is None:
            envdict = os.environ
        # if we are in a slot, we first process the environment through it
        if self.slot:
            result = self.slot.environment(envdict)
        else:
            # we make a copy to avoid changes to the input
            result = dict(envdict)
        applyenv(result, self.env)
        return result


class Package(object):
    '''
    Describe a package to be checked out.
    '''
    def __init__(self, name, version, **kwargs):
        '''
        @param name: name of the package
        @param version: version of the package as 'vXrY' or 'HEAD'
        @param checkout: callable that can check out the specified package
        @param checkout_opts: dictionary with extra options for the checkout
                              callable
        '''
        self.name = name
        if version.lower() == 'head':
            version = 'head'
        self.version = version
        self.container = None
        from CheckoutMethods import getMethod
        self._checkout = getMethod(kwargs.get('checkout'))
        self.checkout_opts = kwargs.get('checkout_opts', {})

    def checkout(self, **kwargs):
        '''
        Helper function to call the checkout method.
        '''
        __log__.info('checking out %s', self)
        opts = dict(self.checkout_opts)
        opts.update(kwargs)
        return self._checkout(self, **opts)

    @property
    def baseDir(self):
        '''Name of the package directory (relative to the build directory).'''
        if self.container:
            return os.path.join(self.container.baseDir, self.name, self.version)
        else:
            return os.path.join(self.name, self.version)

    def build(self, **kwargs):
        '''
        Build the package and return the return code of the build process.
        '''
        base = self.baseDir
        if os.path.exists(os.path.join(base, 'Makefile')):
            __log__.info('building %s (make)', self)
            return tee_call(['make'], cwd=base, **kwargs)
        elif os.path.exists(os.path.join(base, 'cmt', 'requirements')):
            __log__.info('building %s (cmt make)', self)
            # CMT is very sensitive to these variables (better to unset them)
            env = dict((key, value) for key, value in os.environ.items()
                        if key not in ('PWD', 'CWD', 'CMTSTRUCTURINGSTYLE'))
            base = os.path.join(base, 'cmt')

            tee_call(['cmt', 'config'], cwd=base, env=env, **kwargs)
            return tee_call(['cmt', 'make'], cwd=base, env=env, **kwargs)
        __log__.info('%s does not require build', self)
        return (0, '%s does not require build' % self, '')

    def getVersionLinks(self):
        '''
        Return a list of version aliases for the current package (only if the
        requested version is head).
        '''
        if self.version != 'head':
            return []
        base = self.baseDir
        aliases = ['v999r999']
        print os.path.exists(os.path.join(base, 'cmt', 'requirements'))
        if os.path.exists(os.path.join(base, 'cmt', 'requirements')):
            for l in open(os.path.join(base, 'cmt', 'requirements')):
                l = l.strip()
                if l.startswith('version'):
                    version = l.split()[1]
                    aliases.append(version[:version.rfind('r')] + 'r999')
                    break
        return aliases

    def __str__(self):
        '''String representation of the project.'''
        return "{0} {1}".format(self.name, self.version)


class _ContainedList(object):
    '''
    Helper class to handle a list of projects bound to a slot.
    '''
    __type__ = None
    __container_member__ = ''
    __id_member__ = 'name'

    def _assertType(self, element):
        '''
        Ensure that the type of the parameter is the allowed one.
        '''
        types = self.__type__
        if not isinstance(element, types):
            try:
                if len(types) > 1:
                    typenames = ', '.join(t.__name__ for t in types[:-1])
                    typenames += ' and ' + types[-1].__name__
                elif types:
                    typenames = types[0].__name__
                else:
                    typenames = '()'
            except TypeError:
                typenames = types.__name__
            msg = 'only %s instances are allowed' % typenames
            raise ValueError(msg)
        return element

    def __init__(self, container, iterable=None):
        '''
        Initialize the list from an optional iterable, which must contain
        only instances of the required class.
        '''
        self.container = container
        if iterable is None:
            self._elements = []
        else:
            self._elements = list(map(self._assertType, iterable))
            for element in self._elements:
                setattr(element, self.__container_member__, self.container)

    def __getitem__(self, key):
        '''
        Get contained element either by name or by position.
        '''
        if isinstance(key, basestring):
            for element in self._elements:
                id_key = getattr(element, self.__id_member__)
                if key in (id_key, id_key.replace('/', '_')):
                    return element
            raise KeyError('%s %r not found' %
                           (self.__type__.__name__.lower(), key))
        return self._elements[key]

    def __setitem__(self, idx, element):
        '''
        Item assignment that keeps the binding between container and containee
        in sync.
        '''
        self._assertType(element)
        old = self[idx]
        self._elements(idx, element)
        setattr(element, self.__container_member__, self.container)
        setattr(old, self.__container_member__, None)

    def insert(self, idx, element):
        '''
        Item insertion that binds the added object to the container.
        '''
        self._assertType(element)
        setattr(element, self.__container_member__, self.container)
        return self._elements.insert(idx, element)

    def append(self, element):
        '''
        Item insertion that binds the added object to the container.
        '''
        self._assertType(element)
        setattr(element, self.__container_member__, self.container)
        return self._elements.append(element)

    def __delitem__(self, idx):
        '''
        Item removal that disconnect the element from the container.
        '''
        old = self[idx]
        self.remove(old)

    def remove(self, element):
        '''
        Item removal that disconnect the element from the container.
        '''
        self._assertType(element)
        self._elements.remove(element)
        setattr(element, self.__container_member__, None)

    def __len__(self):
        '''
        Return the number of elements in the list.
        '''
        return len(self._elements)


class ProjectsList(_ContainedList):
    '''
    Helper class to handle a list of projects bound to a slot.
    '''
    __type__ = Project
    __container_member__ = 'slot'


class PackagesList(_ContainedList):
    '''
    Helper class to handle a list of projects bound to a slot.
    '''
    __type__ = Package
    __container_member__ = 'container'


class DataProject(Project):
    '''
    Special Project class for projects containing only data packages.
    '''
    build_method = 'no_build'
    def __init__(self, name, packages, **kwargs):
        '''
        Initialize the instance with name and list of packages.
        '''
        # we use 'HEAD' as version just to comply with Project.__init__, but the
        # version is ignored
        Project.__init__(self, name, 'HEAD', **kwargs)
        self._packages = PackagesList(self, packages)

    @property
    def baseDir(self):
        '''Name of the package directory (relative to the build directory).'''
        return self.name.upper()

    @property
    def packages(self):
        'List of contained packages'
        return self._packages

    def __getattr__(self, name):
        '''
        Get the project with given name in the slot.
        '''
        try:
            return self._packages[name]
        except KeyError:
            raise AttributeError('%r object has no attribute %r' %
                                 (self.__class__.__name__, name))

    def checkout(self, **kwargs):
        '''
        Special checkout method to create a valid local copy of a DataProject
        using an existing one as a baseline (cloning it with symlinks).
        '''
        __log__.debug('create packages directories')
        ensureDirs([os.path.dirname(package.baseDir)
                    for package in self.packages])

        __log__.debug('create shallow clone of %s', self.name)
        ignore = IgnorePackageVersions(self.packages)
        path = find_path(self.baseDir)
        if path:
            shallow_copytree(path, self.baseDir, ignore)
        else:
            cmt_dir = os.path.join(self.baseDir, 'cmt')
            ensureDirs([cmt_dir])
            with open(os.path.join(cmt_dir, 'project.cmt'), 'w') as proj_cmt:
                proj_cmt.write('project {0}\n'.format(self.name))

        # separate checkout arguments from build arguments
        co_kwargs = dict([(key, value) for key, value in kwargs.iteritems()
                          if key in ('verbose', 'export')])
        b_kwargs = dict([(key, value) for key, value in kwargs.iteritems()
                         if key in ('verbose', 'jobs')])

        __log__.info('checkout data packages in %s', self.name)
        outputs = [package.checkout(**co_kwargs) for package in self.packages]

        __log__.info('building data packages in %s', self.name)
        outputs += [package.build(**b_kwargs) for package in self.packages]

        __log__.debug('create symlinks')
        for package in self.packages:
            for link in package.getVersionLinks():
                __log__.debug('creating symlink %s', link)
                os.symlink(package.version,
                           os.path.normpath(os.path.join(package.baseDir,
                                                         os.pardir,
                                                         link)))

        from CheckoutMethods import _merge_outputs
        return _merge_outputs(outputs)


class DBASE(DataProject):
    pass


class PARAM(DataProject):
    pass


class _SlotMeta(type):
    '''
    Metaclass for Slot.
    '''
    def __new__(cls, name, bases, dct):
        '''
        Instrument Slot classes.
        '''
        dct['__build_tool__'] = dct.get('build_tool')
        dct['build_tool'] = _BuildToolProperty()
        return type.__new__(cls, name, bases, dct)

    def __init__(cls, name, bases, dct):
        '''
        Class initialization by the metaclass.
        '''
        super(_SlotMeta, cls).__init__(name, bases, dct)

        if 'projects' in dct:
            cls.__projects__ = dct['projects']
        cls.projects = property(lambda self: self._projects)

        env = dct.get('env', [])
        if bases and hasattr(bases[0], '__env__'):
            cls.__env__ = bases[0].__env__ + env
        else:
            cls.__env__ = env


class Slot(object):
    '''
    Class representing a nightly build slot.
    '''
    __metaclass__ = _SlotMeta
    __slots__ = ('_name', '_projects', 'env', '_build_tool')
    __projects__ = []
    __env__ = []

    def __init__(self, name, **kwargs):
        '''
        Initialize the slot with name and optional list of projects.

        @param name: name of the slot
        @param projects: (optional) list of Project instances
        @param env: (optional) list of strings ('name=value') used to modify the
                    environment for the slot
        '''
        self._name = name

        projects = kwargs.get('projects', self.__projects__)
        self._projects = ProjectsList(self, projects)

        self.env = kwargs.get('env', list(self.__env__))

        self.build_tool = kwargs.get('build_tool', self.__build_tool__)

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
        try:
            return self._projects[name]
        except KeyError:
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
        results = OrderedDict()
        for project in self.projects:
            results[project.name] = project.checkout(export=export)
        return results

    def dependencies(self, projects=None):
        '''
        Dictionary of dependencies between projects (only within the slot).
        '''
        deps = self.fullDependencies()
        if projects:
            for unwanted in (set(deps) - set(projects)):
                deps.pop(unwanted)
        for key in deps:
            deps[key] = [val for val in deps[key] if val in deps]
        return deps

    def fullDependencies(self):
        '''
        Dictionary of dependencies of projects (also to projects not in the
        slot).
        '''
        return OrderedDict([(p.name, p.dependencies())
                            for p in self.projects])

    def environment(self, envdict=None):
        '''
        Return a dictionary with the environment for the slot.

        If envdict is provided, it will be used as a starting point, otherwise
        the environment defined by the system will be used.
        '''
        result = dict(os.environ) if envdict is None else dict(envdict)
        applyenv(result, self.env)
        return result

    def _projects_by_deps(self, projects=None):
        deps = self.dependencies(projects=projects)
        return [getattr(self, project) for project in sortedByDeps(deps)]

    def build(self, **kwargs):
        '''
        Build projects in the slot.

        @param projects: optional list of projects to build [default: all]
        '''
        results = OrderedDict()
        for project in self._projects_by_deps(kwargs.pop('projects', None)):
            results[project.name] = project.build(**kwargs)
        return results

    def clean(self, **kwargs):
        '''
        Clean projects in the slot.

        @param projects: optional list of projects to build [default: all]
        '''
        results = OrderedDict()
        for project in self._projects_by_deps(kwargs.pop('projects', None)):
            results[project.name] = project.clean(**kwargs)
        return results

    def test(self, **kwargs):
        '''
        Test projects in the slot.

        @param projects: optional list of projects to build [default: all]
        '''
        results = OrderedDict()
        for project in self._projects_by_deps(kwargs.pop('projects', None)):
            results[project.name] = project.test(**kwargs)
        return results


def extractVersion(tag):
    '''
    Extract the version number from as SVN tag.

    >>> extractVersion('GAUDI_v23r8')
    'v23r8'
    >>> extractVersion('LCGCMT_preview')
    'preview'
    >>> extractVersion('HEAD')
    'HEAD'
    '''
    if '_' in tag:
        return tag.split('_', 1)[1]
    return tag

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
