import os, sys, re
from BaseHandler import BaseHandler



class ValgrindMemcheckHandler(BaseHandler):
   """ LHCbPR Handler to parse MemcheckLog files.

   It extracts the follwoing section from the valgrindmemcheck.output.log:
   
   ==13877== LEAK SUMMARY:
   ==13877==    definitely lost: 22,318 bytes in 201 blocks
   ==13877==    indirectly lost: 5,346,776 bytes in 124,690 blocks
   ==13877==      possibly lost: 44,734,124 bytes in 150,487 blocks
   ==13877==    still reachable: 129,650,622 bytes in 558,813 blocks
   ==13877==         suppressed: 11,872,312 bytes in 130,811 blocks
   ==13877== 
   
   And saves the whole log file as well.
   """
   
   def __init__(self):
      super(self.__class__, self).__init__()
      self.finished = False
      self.results = []
      self.basefilename = 'valgrindmemcheck.output.log'
      
   def collectResults(self,directory):
      """ Collect un results """
      
      # First check that we have the log file...
      filename = os.path.join(directory, self.basefilename)
      if not os.path.exists(filename):
         raise Exception("File %s does not exist" % filename)

      # Then collect the info
      self.collectLeakSummaryResults(directory)
      self.collectLogFile(directory)

      
   def collectLeakSummaryResults(self,directory):
      """ Collects the leak summary result from the log file"""
      
      filename = os.path.join(directory, self.basefilename)
      if not os.path.exists(filename):
         raise Exception("File %s does not exist" % filename)


      file     = open(filename)
      foundResults = False
      while True:
         # Skip until the LEAK SUMMARY section is found
         line = file.readline()
         if "LEAK SUMMARY" not in line: continue

         # At this point we MUST have found the LEAD SUMMARY section
         keywords = ["definitely lost",
                     "indirectly lost",
                     "possibly lost",
                     "still reachable",
                     "suppressed"]

         for k in keywords:
            tmp = file.readline()
            m = re.search("%s: ([\d,]+) bytes" % k, tmp)
            tmpval = (m.groups(1)[0]).replace(",", "")
            self.saveInt(k, int(tmpval), "ValgrindMemcheck", "Valgrind")


         foundResults = True
         break
      
      if not foundResults:
         raise Exception("Could not find LEAK SUMMARY in %s" % filename)


   def collectLogFile(self,directory):
      """ Collects the leak summary result from the log file"""
      
      filename = os.path.join(directory, self.basefilename)
      if not os.path.exists(filename):
         raise Exception("File %s does not exist" % filename)

      self.saveFile(self.basefilename, filename, "ValgrindMemcheckOutput", "Valgrind")
      
