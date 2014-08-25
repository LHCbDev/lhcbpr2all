import os, sys, re
from BaseHandler import BaseHandler

class CallgrindHandler(BaseHandler):
   """ LHCbPR Handler to gather Callgrind output files.
   """
   
   def __init__(self):
      super(self.__class__, self).__init__()
      self.finished = False
      self.results = []
      self.basefilename = 'callgrind.out'
      
   def collectResults(self,directory):
      """ Collect un results """
      
      # First check that we have the log file...
      filename = os.path.join(directory, self.basefilename)
      foundfiles = [ f for f in os.listdir(direct) if f.startswith(self.basefilename)]
      if len(foundfiles) == 0:
         raise Exception("Could not find callgrind ouput files")

      for f in foundfiles:
         # Then collect the info
         self.collectCallgrindFile(f)

      

   def collectCallgrindFile(self, filename):
      """ Collects the leak summary result from the log file"""
      
      if not os.path.exists(filename):
         raise Exception("File %s does not exist" % filename)

      self.saveFile(self.basefilename, filename, "CallgrindOutput", "Callgrind")
      
