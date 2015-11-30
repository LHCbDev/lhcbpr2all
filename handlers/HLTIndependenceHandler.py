import os, sys, re
from BaseHandler import BaseHandler
from xml.etree.ElementTree import ElementTree
from xml.parsers.expat import ExpatError
from hlt import HLTIndependenceParser

class HLTIndependenceHandler(BaseHandler):
        
    def __init__(self):
        super(self.__class__, self).__init__()
        self.finished = False
        self.results = []

    def _parseHLTIndepLog(self, filename):
        """ Parse the log of the HLT rate file to send to the DB """

        # extracted rate table from the log
        table = []

        with open(filename) as f:
            # Now iterating on the file...
            for l in f.readlines():
                # Skipping till the start of the rates summary
                if "all jobs completed" in l:
                    table.append(l)
                    continue
                if len(table) > 0:
                    # Using the rate table length to know whether we've
                    # found the start line already
                    table.append(l)
                if "removed lines:" in l:
                    break

        data = HLTIndependenceParser.parseHLTIndependenceTable("".join(table))
        globalGroup = "HTLIndep_Global"
        globalStatsKeys = ['requested', 'completed', 'nomismatch', 'processed']
        for k in globalStatsKeys:
            self.saveFloat(k, float(data[k]), group=globalGroup)
        
        # for each line we have:
        #  <line number>, <line name>, <All>, <Single>, <AnS>, <SnA> ]
        #                             |All(A) Single(S)  A!S    S!A
        # e.g.
        # ['2', 'Hlt1B2HH_LTUNB_KK:', '0', '0', '0', '0']
        def saveStatsLine(prefix, statsGroup, data):
            """ Format the stats for LHCbPR """
            (num, name, dsingle, dall, dans, dsna) = data
            name = name.rstrip(":")
            getname = lambda par: "_".join([ prefix, name, par])

            self.saveFloat(getname("nb") , int(num), group=statsGroup)
            self.saveFloat(getname("Single") , float(dsingle), group=statsGroup)
            self.saveFloat(getname("All") , float(dall), group=statsGroup)
            self.saveFloat(getname("A!S") , float(dans), group=statsGroup)
            self.saveFloat(getname("S!A") , float(dsna), group=statsGroup)
        for d in data["HLT1LineStats"]:
            saveStatsLine("HLT1Indep", "HLTRate_HLT1IndepStats", d)

    def collectResults(self, directory):
        self._parseHLTIndepLog(os.path.join(directory,'run.log'))

