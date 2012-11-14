import os, sys, re
from BaseHandler import BaseHandler
from xml.etree.ElementTree import ElementTree
from xml.parsers.expat import ExpatError

class TimingHandler(BaseHandler):

   def __init__(self):
      super(self.__class__, self).__init__()
      self.finished = False
      self.results = []

   def collectResults(self,directory):
      #save current directory before chdir
      saved_previous_directory = os.getcwd()

      filename = 'run.log'
      file     = open(filename)
      lines    = file.readlines()

      cputime, real = 0,0

      for l in range(len(lines)-3, len(lines)-0):
         name,value  = lines[l].split()
         value = float( value )
         if name in ( 'User', 'System' ) :
            cputime += value
         elif name == 'System' :
            self.saveFloat('cputime', cputime, 'Unix time cmd')
         elif name == 'Real' :
            real = value
            self.saveFloat('realtime', realtime, 'Unix time cmd')
      
      #go back to previous directory
      os.chdir(saved_previous_directory)


