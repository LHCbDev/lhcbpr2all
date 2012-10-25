import ROOT
import os
import re
from BaseHandler import BaseHandler

class BrunelMemHandler(BaseHandler):

    def __init__(self):
        super(self.__class__, self).__init__()
        self.finished = False
        self.results = []

    def collectResults(self,directory):
        l = self.findHistoFile(directory)
        if len(l) != 1:
            raise Exception("Could not locate just 1 histo file, found:" + str(l))

        f = ROOT.TFile(os.path.join(directory, l[0]))
        b = f.Get("Brunel/MemoryTool/Total Memory [MB]")

        self.saveFloat("TotalMemory", b.GetMean(),
                       group = "Memory");

    def findHistoFile(self, dir):
        return [f for f in os.listdir(dir) if re.match("Brunel.*histos.root", f)]


