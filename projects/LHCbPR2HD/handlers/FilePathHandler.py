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
        run_path = os.path.join(directory, logfile)

        regxp = ".*/afs/cern.ch/lhcb/software/profiling/releases(/[A-Z0-9]+/[A-Z0-9]+_[\w-]+.*)"
        path_line = ""
        try:
           loglines = open(run_path, 'r')
           for l in loglines.readlines():
              m = re.match(regxp, l)
              if m != None:
                 path_line = m.group(1)
                 continue
           loglines.close()
        except IOError:
           raise Exception(str(self.__class__)+": File not found, this handler expects 'run.log' file in the result directory")
         
        if os.path.exists(run_path) :
           path = "$AFS_PROF" + path_line
           self.saveString("Path", path, "Results Location", "JobInfo")
           print path
        else:
           print 'File or path does not exist (file: ' + run_path + ')'

if __name__ == "__main__":
    fh = FilePathHandler()
    fh.collectResults('/afs/cern.ch/lhcb/software/profiling/releases/MOORE/MOORE_v14r11/x86_64-slc6-gcc46-opt/20131112_1712_time')
    fh.collectResults('/afs/cern.ch/lhcb/software/profiling/releases/MOORE/MOORE_lhcb-head-131111/x86_64-slc6-gcc46-opt/20131111_1931_time')
