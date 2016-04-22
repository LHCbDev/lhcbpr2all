import os, sys, re
from BaseHandler import BaseHandler



class ValgrindMassifHandler(BaseHandler):
   """ LHCbPR Handler to Upload Massif output. """

   def __init__(self):
      super(self.__class__, self).__init__()
      self.finished = False
      self.results = []
      self.basefilename = 'valgrindmassif.output.log'
      
   def collectResults(self,directory):
      """ Collect un results """
      
      # First check that we have the log file...
      filename = os.path.join(directory, self.basefilename)
      if not os.path.exists(filename):
         raise Exception("File %s does not exist" % filename)

      # Then collect the info
      self.collectLogFile(directory)


   def collectLogFile(self,directory):
      """ Collects the leak summary result from the log file"""
      
      filename = os.path.join(directory, self.basefilename)
      if not os.path.exists(filename):
         raise Exception("File %s does not exist" % filename)

      self.saveFile(self.basefilename, filename, "ValgrindMassifOutput", "Valgrind")
      
