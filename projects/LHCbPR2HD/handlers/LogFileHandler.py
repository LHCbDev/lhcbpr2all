import os, sys, re
from BaseHandler import BaseHandler
from xml.etree.ElementTree import ElementTree
from xml.parsers.expat import ExpatError

class LogFileHandler(BaseHandler):
    """ Stores a log file called run.log. """
    def __init__(self):
        super(self.__class__, self).__init__()
        self.finished = False
        self.results = []

    def collectResults(self,directory):
        logfile  = 'run.log'
        filename = os.path.join(directory, logfile)
        if not os.path.exists(filename):
            raise Exception("File %s does not exist" % filename)

        self.saveFile(logfile, filename, "Logfile", "")

if __name__ == "__main__":
    lfh = LogFileHandler()
    lfh.collectResults('/afs/cern.ch/lhcb/software/profiling/releases/MOORE/MOORE_v14r11/x86_64-slc6-gcc46-opt/20131112_1712_time')
