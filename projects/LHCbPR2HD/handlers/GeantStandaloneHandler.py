import os
import fnmatch
import glob
import csv

from BaseHandler import BaseHandler


class GeantStandaloneHandler(BaseHandler):

    """ LHCbPR Handler for Geant standalone tests.
          SetupProject --nightly lhcb-gauss-def Geant4 Head (--build-env)
          getpack Geant/G4examples
          make
          hadronis_tests
    """

    def __init__(self):
        super(self.__class__, self).__init__()

    def collectResults(self, directory):
        """ Collect  results """

        # Files
        exts = ['*.root']
        base = os.path.join(directory,'root')
        for file in os.listdir(base):
            for ext in exts:
                if fnmatch.fnmatch(file, ext):
                    
                    self.saveFile(
                        os.path.basename(file),
                        os.path.join(base, file)
                    )
