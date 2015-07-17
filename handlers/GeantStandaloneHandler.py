import os
import fnmatch
import glob
import csv

from BaseHandler import BaseHandler


class GeantStandaloneHandler(BaseHandler):

    """ LHCbPR Handler for Geant standalone tests.
          SetupProject --nightly lhcb-gauss-def Geant4 Head (--build-env)
          getpack Geant/G$examples
          make
          hadronis_tests
    """

    def __init__(self):
        super(self.__class__, self).__init__()

    def collectResults(self, directory):
        """ Collect  results """

        # Files
        exts = ['*.png', '*.C']
        for file in os.listdir(directory):
            for ext in exts:
                if fnmatch.fnmatch(file, ext):
                    self.saveFile(
                        os.path.basename(file),
                        os.path.join(directory, file)
                    )

        # Tables
        energies = [('1', '1.012'), ('10', '10.12'), ('100', '101.2')]

        for table_file in glob.glob(
                os.path.join(directory, 'tables', '*.txt')):
            table_name = os.path.splitext(os.path.basename(table_file))[0]
            with open(table_file, 'rb') as fh:
                reader = csv.reader(fh, delimiter=' ')
                next(reader)  # skip header
                for raw in reader:
                    if energies:
                        e = raw[0]
                        if e == energies[0][1]:
                            for i, name in enumerate(
                                    ['Elastic', 'Inelastic', 'Total']):
                                self.saveFloat('%s_%s_%s' %
                                                (
                                                    table_name,
                                                    name,
                                                    energies[0][0]
                                                ), float(raw[i+1]))
                            del energies[0]
