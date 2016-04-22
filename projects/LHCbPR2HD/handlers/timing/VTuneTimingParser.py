#!/usr/bin/env python

import sys
import re

#
# Parser for the IntelAuditor logfile
#
################################################################################
class VTuneTimingParser:
    """ Class responsible for parsing the TimingAuditor log from the
    Gaudi run log files """
    def __init__(self, filename_run, filename_task):
        self.root = None
        self.parse(filename_run, filename_task)
    
    def parse(self, rfname, tfname):
        """ Parse the log file"""

        regxp = "(TIMER|TimingAuditor).(TIMER|T...)\s+INFO ([\s\w]+?)\s*\|([\d\s\.]+?)\|([\d\s\.]+?)\|([\d\s\.]+?)\|([\d\s\.]+?)\|.*"
        nb_of_evts_per_alg = []
        event_loop         = .0
        try:
            log = open(rfname, "r")
            for l in log.readlines():
                m = re.match(regxp, l)
                if m != None:
                    if "EVENT LOOP" == m.group(3).strip():
                        event_loop = float(m.group(7).strip())
                    nb_of_evts_per_alg.append([m.group(3).strip(), float(m.group(7).strip())])
            log.close()
            nb_of_evts_per_alg[0][0] = re.sub("EVENT LOOP", "EVENT_LOOP", nb_of_evts_per_alg[0][0])
            #print nb_of_evts_per_alg
        except OSError:
            raise Exception(str(self.__class__)+": No result directory, check the given result directory")
        except IOError:
            raise Exception(str(self.__class__)+": Data file not found, this handler excepts a 'run.log' in the results directory' ")
        parent       = None
        lastparent   = [None]
        id = 0
        regxp = "^\s*([\[\]\w_ ]+)\s{5,}([\d\.]+)\s+([\d\.]+)"
        try:
            logf = open(tfname, "r")
            for l in logf.readlines():
                m = re.match(regxp, l)
                if m != None:
                    full_name = m.group(1).rstrip()
                    if str(full_name) == "[Outside any task]":
                        full_name = "EVENT_LOOP"
                    final_digit = re.search('\s{3,}\d+', full_name)
                    if final_digit != None:
                        full_name = full_name[:final_digit.start(0)]
                    names = full_name.split()
                    if full_name == "EVENT_LOOP":
                       level = 0
                    else:
                       level = len(names)
                    parent = None
                    if level > 0:
                       parent = lastparent[level-1]
                    nb_of_evts = -1
                    mai        =  0
                    idx        = -1
                    for i in nb_of_evts_per_alg:
                        search_str = '^' + i[0]
                        n = re.search(search_str, names[len(names)-1])
                        if n != None:
                            if mai < len(n.group(0)):
                                mai = len(n.group(0))
                                idx = i
                    nb_of_evts = int(idx[1])
                    id = id + 1
                    node = Node(id, level, names[len(names)-1], float(m.group(2).strip()), int(nb_of_evts), parent)
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
        root.finalize()
        root.finalize2()
        # root.printTime()
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
        self.id = id
        self.level = level
        self.name = name.replace(" ", "_")
        self.rank = 0
        self.value = float(value) # in [ms]
        self.entries = int(entries)
        self.total = float(self.value) # in [s]
        self.children = []
        self.parent = parent
        self.eventTotal = None
        if parent != None:
            parent.children.append(self)

    def finalize(self):
        childs_sum = 0
        for n in self.children:
            n.finalize()
            childs_sum += n.value
        self.value += childs_sum

    def finalize2(self):
        for n in self.children:
            n.finalize2()
        self.value = (self.value/self.entries)*1000

    def printTime(self):
        print self.name, ", ", self.value, ", ", self.level, ", ", self.total , ", ", self.entries
        for n in self.children:
            n.printTime()

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
    if len(sys.argv) < 3:
        print "Please specify log filenames"
        sys.exit(1)
    else:
        filename_run  = sys.argv[1]
        filename_task = sys.argv[2]
        print "Processing ... "
        t = VTuneTimingParser(filename_run, filename_task)

        #for n in t.getTopN(10):
            #print n.name, " - ", n.perTotal()
