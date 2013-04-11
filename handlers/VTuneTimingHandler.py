import os, sys, re
from BaseHandler import BaseHandler
from xml.etree.ElementTree import ElementTree
from xml.parsers.expat import ExpatError

class VTuneTimingHandler(BaseHandler):
        
    def __init__(self):
        super(self.__class__, self).__init__()
        self.finished = False
        self.results = []

    def collectResults(self,directory):

        from timing.VTuneTimingParser import VTuneTimingParser
        tp = VTuneTimingParser(os.path.join(directory,'run.log'), os.path.join(directory,'task.log'))

        # Now saving all the nodes
        for node in tp.getAllSorted():
            self.saveFloat(node.name, node.value, "Produced by VTune", "Timing")
            self.saveInt(node.name + "_count", node.entries, "Produced by VTune", "TimingCount")
            self.saveInt(node.name + "_rank", node.rank, "Produced by VTune", "TimingRank")
            if node.parent != None:
                self.saveString(node.name + "_parent", node.parent.name, "Produced by VTune", "TimingTree")
            else:
                self.saveString(node.name + "_parent", "None", "Produced by VTune", "TimingTree")
            self.saveInt(node.name + "_id", node.id, "Produced by VTune", "TimingID")


