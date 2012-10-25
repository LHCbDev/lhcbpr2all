import os, sys, re
from BaseHandler import BaseHandler
from xml.etree.ElementTree import ElementTree
from xml.parsers.expat import ExpatError



class TimingHandler(BaseHandler):
    
    
    def __init__(self):
        super(self.__class__, self).__init__()
        self.finished = False
        self.results = []

    def collectResults(self,directory):
        #save current directory before chdir
        saved_previous_directory = os.getcwd()

        from timing.TimingParser import TimingParser
        tp = TimingParser('run.log')

        # Now saving all the nodes
        for node in tp.getAllSorted():
            name = node.name.replace(" ", "_")
            self.saveFloat(name, node.value, group="Timing")
            self.saveInt(name + "_count", node.entries, group="TimingCount")
            self.saveInt(name + "_rank", node.rank, group="TimingRank")
            if node.parent != None:
                self.saveString(name + "_parent", node.parent.name, group="TimingTree")
            else:
                self.saveString(name + "_parent", "None", group="TimingTree")
            self.saveInt(name + "_id", node.id, group="TimingID")
            

        #go back to previous directory
        os.chdir(saved_previous_directory)


