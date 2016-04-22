import os, sys, re, subprocess
from BaseHandler import BaseHandler

#
# Utilityu methods for the JemallocHandler
#
################################################################################

def findHeapFiles(data, rundir):
    """ Find the heap files related to the main PID """
    heapfiles = [ f for f in os.listdir(rundir) \
                  if f.endswith(".heap") \
                  and ".%d." %  data["pid"] in f ]
    return sorted(heapfiles, key=lambda x: int(x.split(".")[2]))

def execute(command):    
    with open(os.devnull, 'w') as DEVNULL:
        popen = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=DEVNULL, shell=True)
        lines_iterator = iter(popen.stdout.readline, b"")
        for line in lines_iterator:
            yield line # yield line

def processPprofText(data, basefile, comparefile):
    import re
    total = None
    totalUnit = None
    allocs = []
    for l in execute("pprof -text --base=%s %s %s" % (basefile, data["exe"], comparefile)):

        # Looking for:
        #Total: 16.7 MB
        m = re.match("^\s*Total:\s+([\-\d\.]+)\s+(\w+).*", l)
        if m != None:
            total = m.group(1)
            totalUnit = m.group(2)

        # Looking for:
        # 4.0  24.0%  24.0%      4.0  24.0% TrackMasterFitter::makeNodes
        m2 = re.match("\s*([\-\d\.]+)\s+([\-\d\.]+)%\s+([\-\d\.]+)%\s+([\-\d\.]+)\s+([\-\d\.]+)%\s+(.*)", l)
        if m2 != None:
            allocs.append([ m2.group(i) for i in range(1, 7) ])
    return (total, totalUnit, allocs)

def processPprofPs(data, basefile, comparefile, outfile):
    import re
    total = None
    totalUnit = None
    allocs = []
    with open(outfile, "w") as f:
        for l in execute("pprof -ps --base=%s %s %s" % (basefile, data["exe"], comparefile)):
            f.write(l)



class JemallocHandler(BaseHandler):
   """ LHCbPR Handler to extract information from Jemalloc heap files
   """
   
   def __init__(self):
      super(self.__class__, self).__init__()
      self.finished = False
      self.results = []
      self.basefilename = "runinfo.json"

      
   def collectResults(self,directory):
      """ Collect un results """
      
      # First check that we have the log file...
      filename = os.path.join(directory, self.basefilename)
      if not os.path.exists(filename):
         raise Exception("File %s does not exist" % filename)

      # Parse the JSON input file
      data = {}
      import json
      with open(self.basefilename) as f:
         data = json.load(f)
             
      # Now find the files, sorted in order
      rundir = os.path.dirname(os.path.abspath(self.basefilename))
      heapfiles = findHeapFiles(data, rundir)

      # Choose the files to be compared...
      basefile = heapfiles[0]
      comparefile = [f for f in heapfiles if not f.endswith(".f.heap") ][-1]

      # Get the top algorithms
      (total, totalUnit, allocs) = processPprofText(data, basefile, comparefile)
      totalf = float(total)
      if totalUnit.upper() == "GB":
         totalf = totalf * 1024

         
      self.saveFloat("TOTAL", totalf, "Total diff (MB)", "Jemalloc")
      for f in allocs:
          print f
          methodname = f[-1]
          methodlost = float(f[0])
          self.saveFloat(methodname, methodlost, "Memory diff in method", "Jemalloc")
         
      # Get the display in postscript
      processPprofPs(data, basefile, comparefile, "jemalloc.ps")
      self.saveFile("jemalloc.ps", "jemalloc.ps", "Diff between memory snapshots", "Jemalloc")
      


      
