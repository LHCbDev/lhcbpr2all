import os, sys, re
from BaseHandler import BaseHandler
from xml.etree.ElementTree import ElementTree
from xml.parsers.expat import ExpatError



class TimingHandler(BaseHandler):
    
    
    def __init__(self):
        super(self.__class__, self).__init__()
        self.finished = False
        self.column_names = ['EVENT_LOOP']
        self.results = []

    def add_column(self,name):
        if not name in self.column_names:
            self.column_names.append(name)
    
    def collectResults(self,directory):
        #save current directory before chdir
        saved_previous_directory = os.getcwd()

        from timing.TimingParser import TimingParser
        tp = TimingParser('run.log')

        # Saving the top 10
        for i, node in enumerate(tp.getTopN(10)):
            self.saveString("top" + str(i), node.name.replace(" ", "_"))

        # Now saving all the nodes
        for node in tp.getAllSorted():
            name = node.name.replace(" ", "_")
            self.saveFloat(name, node.value)
            self.saveFloat(name + "_count", node.entries)

        #go back to previous directory
        os.chdir(saved_previous_directory)


