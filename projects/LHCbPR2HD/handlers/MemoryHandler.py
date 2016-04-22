import os, sys, re
from BaseHandler import BaseHandler
from xml.etree.ElementTree import ElementTree
from xml.parsers.expat import ExpatError

class MemoryHandler(BaseHandler):

   def __init__(self):
      super(self.__class__, self).__init__()
      self.finished = False
      self.results = []

   def collectResults(self,directory):
      from timing.MemoryParser import MemoryParser, MemNode
      mp = MemoryParser(os.path.join(directory,'run.log'));

      # Now saving all the nodes
      peak_rs, peak_vm = MemNode.getPeakMemory()
      self.saveFloat("Total Virt. Memory", peak_vm, "Memory [MB]", "Memory")
      self.saveFloat("Total Res. Memory", peak_rs, "Memory [MB]", "Memory")
      init_rs, init_vm = MemNode.getInitializationMemory()
      self.saveFloat("Init. Virt. Memory", init_vm, "Memory [MB]", "Memory")
      self.saveFloat("Init. Res. Memory", init_rs, "Memory [MB]", "Memory")
      exec_rs, exec_vm = MemNode.getExecutionMemory()
      self.saveFloat("Exec. Virt. Memory", exec_vm, "Memory [MB]", "Memory")
      self.saveFloat("Exec. Res. Memory", exec_rs, "Memory [MB]", "Memory")
      fini_rs, fini_vm = MemNode.getFinalizationMemory()
      self.saveFloat("Fini. Virt. Memory", fini_vm, "Memory [MB]", "Memory")
      self.saveFloat("Fini. Res. Memory", fini_rs, "Memory [MB]", "Memory")
      evts_rs, evts_vm = MemNode.getMemPerEvent()
      self.saveFloat("Virt. Memory / Ev.", evts_vm, "Memory [MB]", "Memory")
      self.saveFloat("Res. Memory / Ev.", evts_rs, "Memory [MB]", "Memory")

