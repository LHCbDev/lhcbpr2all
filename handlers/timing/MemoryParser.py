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
   Nb_of_events = -1

   def __init__(self, filename):
      self.root = None
      self.parse(filename)

   def parse(self, logfilename):
      """ Parse the log file"""
      # Now iterating on the input and looking for the MemoryAuditor lines
      regxp = "^MemoryAuditor.*\s(after|before)\s([a-zA-Z0-9_]+)\s(Initialize|Execute|Finalize).*\s\=\s([\d\.]+).*\s\=\s([\d\.]+)"
      regxp_event_loop = "(TIMER|TimingAuditor).(TIMER|T...)\s+INFO EVENT LOOP\s*\|([\d\s\.]+?)\|([\d\s\.]+?)\|([\d\s\.]+?)\|([\d\s\.]+?)\|.*"
      try:
         logf = open(logfilename, "r")
         for l in logf.readlines():
            m = re.match(regxp, l)
            if m != None:
               elem = MemNode(m.group(2), m.group(3), m.group(1), float(m.group(4)), float(m.group(5)))
            m = re.match(regxp_event_loop, l)
            if m != None:
               MemoryParser.Nb_of_events = int(m.group(6))

         logf.close()
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
            node_tmp = MemNode.NodeList[name]
            print "Name: {0}, Period: {1}, AB: {2}, Virt.: {3}, Res.: {4}".format(name, node_tmp.period, node_tmp.ab, memory_vm, memory_re)
         except KeyError:
            print "Nothing Found!"

   @staticmethod
   def getPeakMemory():
      max_memory_vm = 0
      max_memory_re = 0
      for name in MemNode.NodeList:
         try:
            node = MemNode.NodeList[name]
            if max_memory_re < node.rsmem:
               max_memory_re = node.rsmem
            if max_memory_vm < node.vsmem:
               max_memory_vm = node.vsmem
         except KeyError:
            print "Nothing Found!"
      return max_memory_re, max_memory_vm

   @staticmethod
   def getInitializationMemory():
      max_memory_vm = 0
      max_memory_re = 0
      for name in MemNode.NodeList:
         try:
            node = MemNode.NodeList[name]
            if node.period != "Initialize":
               continue
            if max_memory_re < node.rsmem:
               max_memory_re = node.rsmem
            if max_memory_vm < node.vsmem:
               max_memory_vm = node.vsmem
         except KeyError:
            print "Nothing Found!"
      return max_memory_re, max_memory_vm

   @staticmethod
   def getExecutionMemory():
      max_memory_vm = 0
      max_memory_re = 0
      max_init_re, max_init_vm = MemNode.getInitializationMemory()
      for name in MemNode.NodeList:
         try:
            node = MemNode.NodeList[name]
            if node.period != "Execute":
               continue
            if max_memory_re < node.rsmem:
               max_memory_re = node.rsmem
            if max_memory_vm < node.vsmem:
               max_memory_vm = node.vsmem
         except KeyError:
            print "Nothing Found!"
      return max_memory_re-max_init_re, max_memory_vm-max_init_vm

   @staticmethod
   def getFinalizationMemory():
      max_memory_vm = 0
      max_memory_re = 0
      max_init_re, max_init_vm = MemNode.getInitializationMemory()
      max_exec_re, max_exec_vm = MemNode.getExecutionMemory()
      for name in MemNode.NodeList:
         try:
            node = MemNode.NodeList[name]
            if node.period != "Finalize":
               continue
            if max_memory_re < node.rsmem:
               max_memory_re = node.rsmem
            if max_memory_vm < node.vsmem:
               max_memory_vm = node.vsmem
         except KeyError:
            print "Nothing Found!"
      return max_memory_re-(max_init_re+max_exec_re), max_memory_vm-(max_init_vm+max_exec_vm)

   @staticmethod
   def getMemPerEvent():
      return float(MemNode.getExecutionMemory()[0]/MemoryParser.Nb_of_events), float(MemNode.getExecutionMemory()[1]/MemoryParser.Nb_of_events)

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
      print MemNode.getPeakMemory()
      print MemNode.getInitializationMemory()
      print MemNode.getExecutionMemory()
      print MemNode.getFinalizationMemory()
      print MemNode.getMemPerEvent()
