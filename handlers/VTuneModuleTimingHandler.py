import os, sys, re
from BaseHandler import BaseHandler
from xml.etree.ElementTree import ElementTree
from xml.parsers.expat import ExpatError

class VTuneModuleTimingHandler(BaseHandler):
        
    def __init__(self):
        super(self.__class__, self).__init__()
        self.finished = False
        self.results = []

    def collectResults(self,directory):

        from timing.VTuneModuleParser import VTuneModuleParser
        tp = VTuneModuleParser(os.path.join(directory,'module.log'));

        # Now saving all the nodes
        for node in tp.getTimingList():
            self.saveFloat(node[0], node[1], "Time per Module (library) [s]", "ModuleTiming")

