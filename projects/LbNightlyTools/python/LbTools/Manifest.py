###############################################################################
# (c) Copyright 2014 CERN                                                     #
#                                                                             #
# This software is distributed under the terms of the GNU General Public      #
# Licence version 3 (GPL Version 3), copied verbatim in the file "COPYING".   #
#                                                                             #
# In applying this licence, CERN does not waive the privileges and immunities #
# granted to it by virtue of its status as an Intergovernmental Organization  #
# or submit itself to any jurisdiction.                                       #
###############################################################################
'''
Nightlies for manifest.xml parser

Created on Feb 27, 2014

@author: Ben Couturier
'''

import logging
from xml.etree.ElementTree import ElementTree

__log__ = logging.getLogger(__name__)

class Parser(object):
    '''
    Parser for the manifest.xml file generated at build time
    '''
    def __init__(self, filename):
        '''
        Constructor taking the actual file name
        '''
        __log__.debug("Loading %s" % filename)
        self._filename = filename
        tree = ElementTree()
        tree.parse(self._filename)
        self._tree = tree


    def getProject(self):
        ''' Returns the pair (project, version) '''
        projectNode = self._tree.find("./project")
        if projectNode == None:
            raise Exception("project tag not found")
        return (projectNode.attrib["name"], projectNode.attrib["version"])

    def getHEPTools(self):
        ''' Returns the triplet (lcgversion, CMTCONFIG, packages) or None
        if there is no heptools tag.
        The 'packages' is a dictionary of names to versions.
        '''
        # check if there is a dependency on heptools
        node = self._tree.find('./heptools')
        if node is None:
            return None

        tags = ["./heptools/version",
                "./heptools/binary_tag"]

        tagValues = []
        for t in tags:
            node = self._tree.find(t)
            if node == None:
                raise Exception("%s not found" % t)
            tagValues.append(node.text)

        pkgs= dict((pkg.attrib['name'], pkg.attrib['version'])
                   for pkg in self._tree.findall('./heptools/packages/package'))
        tagValues.append(pkgs)
        return tuple(tagValues)

    def getLCGConfig(self):
        ''' Returns the LCG_platform and LCG_system if specified in the XML, None otherwise
        '''
        # check if there is a dependency on heptools
        node = self._tree.find('./heptools')
        if node is None:
            return None

        tags = ["./heptools/lcg_platform",
                "./heptools/lcg_system"]

        tagValues = []
        for t in tags:
            node = self._tree.find(t)
            if node == None:
                tagValues.append(None)
            else:
                tagValues.append(node.text)

        return tuple(tagValues)

    def getExtTools(self):
        ''' Returns a dictionary (name->version) of external packages.
        '''
        try:
            bin_tag = self._tree.find('./exttools/binary_tag').text.strip()
        except AttributeError:
            # exttools/binary_tag not found
            bin_tag = ''

        pkgs= dict((pkg.attrib['name'], pkg.attrib['version'])
                   for pkg in self._tree.findall('./exttools/packages/package'))
        return bin_tag, pkgs

    def getUsedProjects(self):
        ''' Returns the list of tuples (project, version) for used projects '''

        tag = "./used_projects/project"
        usedProjects = []
        nodes = self._tree.findall(tag)
        for node in nodes:
            usedProjects.append((node.attrib["name"], node.attrib["version"]))
        return usedProjects

    def getUsedDataPackages(self):
        ''' Returns the list of tuples (project, version) for used data packages '''

        tag = "./used_data_pkgs/package"
        used = []
        nodes = self._tree.findall(tag)
        for node in nodes:
            used.append((node.attrib["name"], node.attrib["version"]))
        return used

