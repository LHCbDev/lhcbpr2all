import os, sys, re
from BaseHandler import BaseHandler
from xml.etree.ElementTree import ElementTree
from xml.parsers.expat import ExpatError

class UnixTimeHandler(BaseHandler):

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

      cputime, realtime = 0,0

      for l in range(len(lines)-3, len(lines)):
         name,value  = lines[l].split()
         value = float( value )
         if name in ( 'User', 'System' ) :
            cputime += value
         elif name == 'Real' :
            realtime = value

      self.saveFloat('cputime', cputime, 'Unix time cmd')
      self.saveFloat('realtime', realtime, 'Unix time cmd')
      
      #go back to previous directory
      os.chdir(saved_previous_directory)

