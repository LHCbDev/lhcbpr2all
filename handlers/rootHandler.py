import os, sys, re, glob
from BaseHandler import BaseHandler

class rootHandler(BaseHandler):
    
    
    def __init__(self):
        super(self.__class__, self).__init__()
    
    def collectResults(self,directory):
        try:
            os.chdir(directory)
        except OSError:
            raise Exception(str(self.__class__)+": No result directory, check the given result directory")

        current_path = os.getcwd()
        
        for file in glob.glob("*.root"):
            self.saveFile(file, current_path+os.sep+file)
            
        if not self.getResults():
            raise Exception(str(self.__class__)+": No root files were found in the given directory")

