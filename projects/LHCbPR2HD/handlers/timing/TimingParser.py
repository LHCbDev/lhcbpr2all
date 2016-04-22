#!/usr/bin/env python

import sys
import re

#
# Parser for the TimingAuditor logfile or ROOT dump
#
################################################################################
class TimingParser:
    """ Class responsible for parsing the TimingAuditor log from the
    Gaudi run  log files """
    def __init__(self, filename):
        self.root = None
        self.parse(filename)
    
    def parse(self, logfilename):
        """ Parse the log file"""

        # Now iterating on the input and looking for the TimingAuditor lines
        # The hiererarchy of Algos and sequences is rebuilt based on the order
        # in the text file.
        parent = None
        lastparent = [None]
        id = 0
        regxp = "(TIMER|TimingAuditor).(TIMER|T...)\s+INFO ([\s\w]+?)\s*\|([\d\s\.]+?)\|([\d\s\.]+?)\|([\d\s\.]+?)\|([\d\s\.]+?)\|.*"
        try:
            logf = open(logfilename, "r")
            for l in logf.readlines():
                m = re.match(regxp, l)
                if m != None:
                    level = len(m.group(3)) - len(m.group(3).lstrip())
                    parent = None
                    if level > 0:
                        try:
                            parent = lastparent[level -1]
                        except IndexError:
                            # BUG: IN some cases we jump one, to be investigated !
                            parent =  lastparent[level -2]
                        
                    name = m.group(3).strip()
                    id = id + 1
                    #print "Id: ", id, "Name: ", name, "Value: ", float(m.group(4)), "Level: ", level, "Entries: ", m.group(7).strip()
                    node = Node(id, level, name, float(m.group(4).strip()), int(m.group(7).strip()), parent)
                    try:
                        lastparent[level] = node
                    except IndexError, e:
                        lastparent.append(node)
            logf.close()
        except OSError:
            raise Exception(str(self.__class__)+": No result directory, check the given result directory")
        except IOError:
            raise Exception(str(self.__class__)+": Data file not found, this handler excepts a 'run.log' in the results directory' ")
            
        # Getting the actual root "EVENT LOOP"
        root = lastparent[0]
        # Sorting all the nodes by CPU usage and setting the "rank" attribute
        root.rankChildren()
        self.root = root

    def getRoot(self):
        """ returns the root of the tree """
        return self.root

    def getHierarchicalJSON(self):
        return "[" + self.root.getJSON() + "]"

    def getFlatJSON(self):
        ct = 1
        json="["
        for c in self.root.getAllChildren():
            if ct > 1:
                json += ",\n"
            json += c.getJSON(False)
            ct += 1
        json += "]"
        return json 

    def findByName(self, name):
        return self.root.findByName(name)

    def getTopN(self, n):
        """ Get the top N ranked algorithms"""
        return sorted(self.root.getAllChildren(), key=Node.getRank)[:n]

    def getAllSorted(self):
        """ Get the top N ranked algorithms"""
        return sorted(self.root.getAllChildren(), key=Node.getRank)


#
# Class representing the Nodes in the Algorithm tree
#
################################################################################
class Node:
    """ Representation of an algorithm or sequence """

    @classmethod
    def getActualTimeUsed(cls, o):
        return o.actualTimeUsed()


    @classmethod
    def getRank(cls, o):
        return o.rank


    def __init__(self, id, level, name, value, entries, parent=None):
        """ Constructor """
        self.id = id
        self.level = level
        self.name = name.replace(" ", "_")
        self.rank = 0
        self.value = float(value)
        self.entries = entries
        self.total = self.value * self.entries
        self.children = []
        self.parent = parent
        self.eventTotal = None
        if parent != None:
            parent.children.append(self)

    def findByName(self, name):
        """ Find an algorithm in the subtree related to the Node  """
        if self.name == name:
            return self

        for c in self.children:
            tmp = c.findByName(name)
            if tmp != None:
                return tmp
        return None


    def actualTimeUsed(self):
        """ returns the CPU time actually used in the sequence,
        excluding time used by the children """
        return self.total - self.getSumChildrenTime() 

    def getAllChildren(self):
        """ Navigate the tree to rturn all the children"""
        cdren = []
        cdren.append(self)
        for c in self.children:
            cdren += c.getAllChildren()
        return cdren


    def getNodesMatching(self, namepattern, foundnodes = None):
        """ Find all children matching a given name """
        if foundnodes == None:
            foundnodes = set()
        
        if re.match(namepattern, self.name):
            foundnodes.add(self)

        for c in self.children:
            foundnodes |= c.getNodesMatching(namepattern, foundnodes)
        
        return foundnodes


    def getParentNodes(self):
        """ Find all children matching a given name """

        parents = set()
        if self.parent != None:
            parents.add(self.parent)
            parents |= self.parent.getParentNodes()

        return parents



    def getMinChildrenRank(self):
        """ Get the lowest rank in all the children """
        m = self.rank
        for c in self.children:
            if c.getMinChildrenRank() < m:
                 m = c.getMinChildrenRank()
        return m
    

    def getSumChildrenTime(self):
        """ Get the sum of CPU time spent by the children """
        tmptotal = 0.0
        for c in self.children:
            tmptotal += c.total
        return tmptotal
            
    def perLevel(self):
        """ Percentage of time spent in this algo/seq over the
        time used by the parent """
        if self.parent != None:
            return round((self.total * 100.0)/self.parent.total,2)        
        else:
            return 100.0

    def getEventTotal(self):
        """ Get the total time spent in the EVENT LOOP """
        if self.eventTotal != None:
            return self.eventTotal

        if self.parent is None:
            self.eventTotal = self.total
            return self.eventTotal
        else:
            self.eventTotal = self.parent.getEventTotal()
            return self.eventTotal

    def perTotal(self):
        """ percentage time spent in this algorithm vs the TOTAL time"""
        return round(self.total * 100.0 / self.getEventTotal(),2)

    def getfullname(self):
        """ Returns the complete path flatened joined by '-' """
        if self.parent != None:
            return self.parent.getfullname() + "-" + self.name
        else:
            return self.name

    def getJSON(self, hierarchical=True):
        """ Returns teh JSON representation of thios node """
        cjson = ""

        if hierarchical and len(self.children) > 0:
            cjson = ', "children":[%s]' % self._childrenjson()

        tmpl = '{"code":%d, "name":"%s", "rank":%d, "mrank":%d, "childrenTotal":%.2f, "perTotal":%.2f, "perLevel":%.2f, "avgtime":%.2f, "total":%.2f, "entries":%d '
        vals =  [ self.id, self.name, self.rank, self.getMinChildrenRank(), self.getSumChildrenTime(), self.perTotal(), 
                  self.perLevel(), self.value, self.total, self.entries ]
        if self.parent != None:
            tmpl += ', "_parentCode":%d %s}'
            vals.append(self.parent.id)
            vals.append(cjson)
        else:
            tmpl += ' %s}'
            vals.append( cjson)

        return tmpl % tuple(vals)

    def printChildrenList(self, maxLevel=-1, thisLevel=0):
        """ Prints the list of children down to a level """

        #print ">>>> %d\t%s" % (thisLevel, self.name)
        if thisLevel < maxLevel:
            for c in self.children:
                c.printChildrenList(maxLevel, thisLevel +1)


    def _childrenjson(self):
        """ Util function to return the JSON reprentation of the children of the node """
        ct = 1
        json=""
        for c in self.children:
            if ct > 1:
                json += ",\n"
            json += c.getJSON()
            ct += 1
        return json

    def rankChildren(self):
        """ Actually sort of the children of this node and set their rank.
        This MUST be called on the tree before using teh rank value"""
        l = sorted(self.getAllChildren(), key=Node.getActualTimeUsed, reverse=True)
        for i, n in enumerate(l):
            n.rank = i + 1

#
# Main
#
################################################################################
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print "Please specify log filename"
        sys.exit(1)
    else:
        filename = sys.argv[1]
        print "Processing %s" % filename
        t = TimingParser(filename)

        #nodelist.append(eventLoop)
        
        #dvUserSeq = eventLoop.findByName("DaVinciUserSequence")
        #nodelist.append(dvUserSeq)
        #for c in dvUserSeq.children:
            #nodelist.append(c)
            
        #stripGlobal = dvUserSeq.findByName("StrippingGlobal")
        #nodelist.append(stripGlobal)
        #for c in stripGlobal.children:
            #nodelist.append(c)

        #StrippingProtectedSequenceALL = stripGlobal.findByName("StrippingProtectedSequenceALL")
        #nodelist.append(StrippingProtectedSequenceALL)
        #for c in StrippingProtectedSequenceALL.children:
            #nodelist.append(c)

        for node in t.getAllSorted():
            if node.name == 'Hlt2CharmHadD2HHHKsDD':
                print "{0} - {1} - {2} - {3}".format(node.id, node.name, node.value, node.entries)
