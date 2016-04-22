import os, sys, re
from BaseHandler import BaseHandler
from xml.etree.ElementTree import ElementTree
from xml.parsers.expat import ExpatError

class StrippingTimingHandler(BaseHandler):
        
    def __init__(self):
        super(self.__class__, self).__init__()
        self.finished = False
        self.results = []

    def collectResults(self,directory):

        # Parsing the log
        from timing.TimingParser import TimingParser
        tp = TimingParser(os.path.join(directory,'run.log'))

        # Collecting the interesting nodes
        nodelist = set()
        eventLoop = tp.getRoot()
        nodelist.add(eventLoop)

        
        # Looking for all the nodes which name finishes with line
        foundnodes = eventLoop.getNodesMatching(".*Line$")

        # Now adding the parents
        for n in foundnodes:
            nodelist.add(n)
            nodelist |= n.getParentNodes()
        

        #eventLoop.printChildrenList(8)

        # Now saving the results
        for node in nodelist:
            self.saveFloat(node.name, node.value, "Time per Ev. [ms]", "Timing")
            self.saveInt(node.name + "_count", node.entries, group="TimingCount")
            self.saveInt(node.name + "_rank", node.rank, group="TimingRank")
            if node.parent != None:
                self.saveString(node.name + "_parent", node.parent.name, group="TimingTree")
            else:
                self.saveString(node.name + "_parent", "None", group="TimingTree")
            self.saveInt(node.name + "_id", node.id, group="TimingID")


