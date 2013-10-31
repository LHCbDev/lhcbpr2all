import os, sys, re
from BaseHandler import BaseHandler
from xml.etree.ElementTree import ElementTree
from xml.parsers.expat import ExpatError

class VTuneTaskTimingHandler(BaseHandler):
        
    def __init__(self):
        super(self.__class__, self).__init__()
        self.finished = False
        self.results = []

    def collectResults(self,directory):

        from timing.VTuneTimingParser import VTuneTimingParser
        tp = VTuneTimingParser(os.path.join(directory,'run.log'), os.path.join(directory,'task.log'))

        # Now saving all the nodes
        for node in tp.getAllSorted():
            # self.saveFloat(node.name, node.value, "Processing per Event", "TaskTiming")
            self.saveFloat(node.name, node.value, "Time per Ev. [ms]", "TaskTiming")
            self.saveInt(node.name + "_count", node.entries, "Events processed", "TaskTimingCount")
            self.saveInt(node.name + "_rank", node.rank, "Level of Alg. in call stack", "TaskTimingRank")
            if node.parent != None:
                self.saveString(node.name + "_parent", node.parent.name, "Parent name of Alg.", "TaskTimingTree")
            else:
                self.saveString(node.name + "_parent", "None", "Root", "TaskTimingTree")
            self.saveInt(node.name + "_id", node.id, "Id in Alg. list", "TaskTimingID")


