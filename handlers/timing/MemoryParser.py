#!/usr/bin/env python
import sys
import os
import re

#
# Parser for the MemoryAuditor logfile 
#
################################################################################
class MemoryParser:
   """ Class responsible for parsing the MemoryAuditor log from the
   Gaudi run log files """

   def __init__(self, filename):
      self.root = None
      self.alg_table = []
      self.mem_table = [] 
      self.parse(filename)

   def parse(self, logfilename):
      """ Parse the log file"""
      # Now iterating on the input and looking for the MemoryAuditor lines
      regxp = "(after|before)\s([a-zA-Z0-9_]+)\s(Initialize|Execute|Finalize)\s([\d\.]+)\s([\d\.]+)"
      try:
         logf = open(logfilename, "r")
         vm_last_after = 0
         rss_last_after = 0
         for l in logf.readlines():
            m = re.match(regxp, l)
            if m != None:
               #print m.group(2), m.group(1), m.group(3), m.group(4), m.group(5)
               if m.group(1) == "after":
                  last_elem_idx = len(self.mem_table)-1 
                  if last_elem_idx >= 0 and self.mem_table[last_elem_idx][0] == m.group(2):
                     last_elem = self.mem_table.pop()
                     self.addResult(m.group(2), 1, float(m.group(4))-last_elem[1])
                     continue;
                  #idx = self.getIndexReverse(self.mem_table, m.group(2))
                  #if idx >= 0 and float(m.group(4))-self.mem_table[idx][1] > 0:
                     #last_elem = self.mem_table.pop(idx)
                     #self.alg_table.append([m.group(2), float(m.group(4))-last_elem[1]])
               if m.group(1) == "before":
                  #idx = self.getIndexReverse(self.mem_table_b, m.group(2))
                  #if idx >= 0 and float(m.group(4))-self.mem_table_b[idx][1] > 0:
                  #self.alg_table.append([m.group(2), float(m.group(4))-self.mem_table_b[idx][1]])
                  #else:
                  self.mem_table.append([m.group(2), float(m.group(4)), float(m.group(5))])
         logf.close()
      except OSError:
         raise Exception(str(self.__class__)+": No result directory, check the given result directory")
      except IOError:
         raise Exception(str(self.__class__)+": Data file not found, please consider the correct name of the analysed log file.' ")

   def addResult(self, name, position, value):
      if position < 1 and position > 2:
         return
      idx = self.getIndexReverse(self.alg_table, name)
      if idx >= 0:
         self.alg_table[idx][position] = float(self.alg_table[idx][position]) + value
         print "Exist. result replaced ..."
      elif position == 1:
         self.alg_table.append([name, value, 0])   
         print "New result added ..."
      elif position == 2:
         self.alg_table.append([name, 0, value])
         print "New result added ..."
      return

   def getIndexReverse(self, list, elem):
      idx = len(list)-1
      for i in range(idx,-1,-1):
         if elem == list[i][0]:
            return i
      return -1

   def getTimingList(self):
      self.alg_table.sort()
      return self.alg_table

#
# Main
#
################################################################################
if __name__ == "__main__":
   import sys
   if len(sys.argv) < 2:
      print "Please specify log filename"
      sys.exit(1)
   else:
      filename = sys.argv[1]
      print "Processing %s" % filename
      t = MemoryParser(filename)
      for node in t.getTimingList():
         if node[1] > 0:
            print node[1], ", ", node[0]
