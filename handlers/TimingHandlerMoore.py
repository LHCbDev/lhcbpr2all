import os, sys, re
from BaseHandler import BaseHandler
from xml.etree.ElementTree import ElementTree
from xml.parsers.expat import ExpatError

class TimingHandlerMoore(BaseHandler):
      
    def __init__(self):
        super(self.__class__, self).__init__()
        self.finished = False
        self.results = []

    def collectResults(self,directory):
        
        from timing.TimingParser2 import TimingParser2
        tp = TimingParser2(os.path.join(directory, 'run.log'))

        # Now saving all the nodes
        for node in tp.getAllSorted():
            self.saveFloat(node.name, node.value, group="Timing")
            self.saveInt(node.name + "_count", node.entries, group="TimingCount")
            self.saveInt(node.name + "_rank", node.rank, group="TimingRank")
            if node.parent != None:
                self.saveString(node.name + "_parent", node.parent.name, group="TimingTree")
            else:
                self.saveString(node.name + "_parent", "None", group="TimingTree")
            self.saveInt(node.name + "_id", node.id, group="TimingID")