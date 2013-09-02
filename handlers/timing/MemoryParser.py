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
      self.parse(filename)

   def parse(self, logfilename):
      """ Parse the log file"""
      # Now iterating on the input and looking for the MemoryAuditor lines
      regxp = "^MemoryAuditor.*\s(after|before)\s([a-zA-Z0-9_]+)\s(Initialize|Execute|Finalize).*\s\=\s([\d\.]+).*\s\=\s([\d\.]+)"
      try:
         logf = open(logfilename, "r")
         last_vm = -1
         last_rs = -1
         last_alg  = ""
         for l in logf.readlines():
            m = re.match(regxp, l)
            if m != None:
               #if m.group(1) == "before" and m.group(3) == "Execute":
               if m.group(3) == "Execute":
                  if float(m.group(4))-last_vm > 0 or float(m.group(5))-last_rs > 0:
                     elem = MemNode(m.group(2), m.group(3), m.group(1), float(m.group(4))-last_vm, float(m.group(5))-last_rs)
               last_vm = float(m.group(4))
               last_rs = float(m.group(5))
               last_alg  = m.group(2)

         logf.close()
         MemNode.printMemory()
      except OSError:
         raise Exception(str(self.__class__)+": No result directory, check the given result directory")
      except IOError:
         raise Exception(str(self.__class__)+": Data file not found, please consider the correct name of the analysed log file.' ")

class MemNode:
   NodeList = {}

   def __init__(self, name, period, ab, vsmem, rsmem):
      self.name   = name
      self.period = period
      self.ab     = ab
      self.vsmem  = vsmem
      self.rsmem  = rsmem
      self.node   = None
      self.add()

   def add(self):
      try:
         node_tmp = MemNode.NodeList[self.name]
         while node_tmp.node != None:
            node_tmp = node_tmp.node
         node_tmp.node = self
      except KeyError:
         MemNode.NodeList[self.name] = self

   @staticmethod
   def last(name):
      try:
         node_tmp = MemNode.NodeList[name]
         while node_tmp.node != None:
            node_tmp = node_tmp.node
         return node_tmp
      except KeyError:
         return None

   @staticmethod
   def printMemory():
      for name in MemNode.NodeList:
         try:
            node_tmp = MemNode.NodeList[name]
            memory_re = 0
            memory_vm = 0
            while node_tmp != None:
               memory_re += node_tmp.rsmem
               memory_vm += node_tmp.vsmem
               node_tmp = node_tmp.node
            print name, ", {0}, {1}".format(memory_vm, memory_re)
         except KeyError:
            print "Nothing Found!"

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
