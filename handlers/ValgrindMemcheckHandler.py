import os, sys, re
from BaseHandler import BaseHandler

class ValgrindMemcheckHandler(BaseHandler):

   def __init__(self):
      super(self.__class__, self).__init__()
      self.finished = False
      self.results = []

   def collectResults(self,directory):

      basefilename = 'valgrindmemcheck.output.log'
      filename = os.path.join(directory, basefilename)

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
            self.saveInt(k, int(tmpval), "ValgrindMemcheck")


         foundResults = True
         break
      
      if not foundResults:
         raise Exception("Could not find LEAK SUMMARY in %s" % filename)
