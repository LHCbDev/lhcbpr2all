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
        nodelist = []
        eventLoop = tp.getRoot()
        nodelist.append(eventLoop)

        sequences = [ "DaVinciEventSeq", 
                      "FilteredEventSeq",
                      "DaVinciAnalysisSeq",
                      "DaVinciUserSequence",
                      "StrippingGlobal",
                      "StrippingSequenceStreamALL"]
        
        for s in sequences:
            seq = eventLoop.findByName(s)
            print s, " ", seq
            nodelist.append(seq)

        StrippingProtectedSequenceALL = eventLoop.findByName("StrippingProtectedSequenceALL")
        nodelist.append(StrippingProtectedSequenceALL)
        for c in StrippingProtectedSequenceALL.children:
            nodelist.append(c)

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


