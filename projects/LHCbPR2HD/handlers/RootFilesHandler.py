import os
import fnmatch
import glob
import csv

from BaseHandler import BaseHandler


class RootFilesHandler(BaseHandler):

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
        for root, _, files in os.walk("."):
            for file in files:
                for ext in exts:
                    if fnmatch.fnmatch(file, ext):
                        self.saveFile(
                            file,
                            os.path.join(root, file)
                        )
