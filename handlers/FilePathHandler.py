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
        filename = 'report.txt'
        report_path = directory + '/' + filename 
        if os.path.exists(report_path) :
           saveString('intel_report', report_path, 'Path to Vtune generated reports', 'file')
           print '... reported!' 
        else:
           print 'Report file does not exist (file: ' + report_path + ')'

if __name__ == "__main__":
    fh = FilePathHandler()
    fh.collectResults('/afs/cern.ch/user/s/slohn')
