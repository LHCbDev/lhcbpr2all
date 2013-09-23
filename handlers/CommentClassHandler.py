import os, sys, re
from BaseHandler import BaseHandler
from xml.etree.ElementTree import ElementTree
from xml.parsers.expat import ExpatError

class CommentClassHandler(BaseHandler):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.finished = False
        self.results  = []

    def collectResults(self, directory):
        logfile = 'profile_info.txt'
        run_path = os.path.join(directory, logfile)

        regxp = "^comment\s*=\s*\"(.*)\s*/\s*(.*)\""
        comment = ""
        cclass = ""
        try:
           loglines = open(run_path, 'r')
           for l in loglines.readlines():
              m = re.match(regxp, l)
              if m != None:
                 comment = m.group(1)
                 cclass = m.group(2)
                 break
           loglines.close()
        except IOError:
           raise Exception(str(self.__class__)+": File not found, this handler expects 'run.log' file in the result directory")
         
        self.saveString("Comment", comment, "Comment", "JobInfo")
        self.saveString("Class", cclass, "Class", "JobInfo")

        print comment, cclass

if __name__ == "__main__":
    cch = CommentClassHandler()
    cch.collectResults('/afs/cern.ch/lhcb/software/profiling/releases/MOORE/MOORE_v20r1p1/x86_64-slc6-gcc46-opt/20130919_1659_time')
