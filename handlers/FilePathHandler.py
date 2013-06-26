import os, sys, re
from BaseHandler import BaseHandler
from xml.etree.ElementTree import ElementTree
from xml.parsers.expat import ExpatError

class FilePathHandler(BaseHandler):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.finished = False
        self.results = []

    def collectResults(self,directory):
        logfile = 'run.log'
        run_path = directory + '/' + logfile

        loglines = open(logfile, 'r')
        lls = loglines.readlines()
        line = lls[len(lls)-3]
        loglines.close()
         
        if os.path.exists(run_path) :
           self.saveString("Path", line, "Results", "JobInfo")
        else:
           print 'File or path does not exist (file: ' + run_path + ')'

if __name__ == "__main__":
    fh = FilePathHandler()
    fh.collectResults('/afs/cern.ch/user/s/slohn')
