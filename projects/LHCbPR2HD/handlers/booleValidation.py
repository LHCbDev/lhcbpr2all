import re, sys, os, shutil, json, glob
from BaseHandler import BaseHandler
from xml.etree.ElementTree import ElementTree
#from xml.parsers import expat
#from xml.parsers.expat import ExpatError
#from xml.etree.ElementTree  import ParseError
#
#SA
#
#from lxml.etree.ElementTree import ElementTree
#from lxml.parsers import expat
#from lxml.parsers.expat import ExpatError
#from lxml.etree.ElementTree  import ParseError
#from xml.etree.ElementTree import ElementTree
import lxml.etree as etree
#from lxml.parsers.expat import ExpatError
#
##AS

# True or False
global DEBUG 
DEBUG = True

  
class booleValidation(BaseHandler):
    
    def __init__(self):
        super(self.__class__, self).__init__()
    
    def findHistoFile(self, dir):
        return [f for f in os.listdir(dir) if re.match("Boole.*histos.root", f)]
    
    def collectResults(self,directory):

      
        rootfiles = glob.glob("*.root")
        
        l = self.findHistoFile(directory)
        if len(l) == 0:
            raise Exception("Could not locate histo file in the given directory")
        elif len(l) != 1:
            raise Exception("Could not locate just 1 histo file, found:" + str(l))
        
        fileName, fileExtension = os.path.splitext(l[0])
        self.saveFile(fileName, os.path.join(directory,l[0]))
            
      
