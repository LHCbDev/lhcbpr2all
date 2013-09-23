import os, sys, re
from BaseHandler import BaseHandler
from xml.etree.ElementTree import ElementTree
from xml.parsers.expat import ExpatError

class VTuneModuleTimingHandler(BaseHandler):

   def __init__(self):
      super(self.__class__, self).__init__()
      self.finished = False
      self.results = []

      def collectResults(self,directory):
         from timing.MemoryParser import MemoryParser
         mp = MemoryParser(os.path.join(directory,'run.log'));

         # Now saving all the nodes
         peak_rs, peak_vm = MemNode.getPeakMemory()
         self.saveFloat("Total Virt. Memory", peak_vm, group="Memory")
         self.saveFloat("Total Res. Memory", peak_rs, group="Memory")
         init_rs, init_vm = MemNode.getInitializationMemory()
         self.saveFloat("Init. Virt. Memory", init_vm, group="Memory")
         self.saveFloat("Init. Res. Memory", init_rs, group="Memory")
         exec_rs, exec_vm = MemNode.getExecutionMemory()
         self.saveFloat("Exec. Virt. Memory", exec_vm, group="Memory")
         self.saveFloat("Exec. Res. Memory", exec_rs, group="Memory")
         fini_rs, fini_vm = MemNode.getFinalizationMemory()
         self.saveFloat("Fini. Virt. Memory", fini_vm, group="Memory")
         self.saveFloat("Fini. Res. Memory", fini_rs, group="Memory")
         evts_rs, evts_vm = MemNode.getMemPerEvent()
         self.saveFloat("Virt. Memory / Ev.", evts_vm, group="Memory")
         self.saveFloat("Res. Memory / Ev.", evts_rs, group="Memory")

