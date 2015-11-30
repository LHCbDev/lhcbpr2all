import os, sys, re
from BaseHandler import BaseHandler
from xml.etree.ElementTree import ElementTree
from xml.parsers.expat import ExpatError
from hlt import HLTRateParser

class HLTRateHandler(BaseHandler):
        
    def __init__(self):
        super(self.__class__, self).__init__()
        self.finished = False
        self.results = []


    RE_NBWERROR = "([0-9\.]+)\+\-([0-9\.]+)"
    def _parseValError(self, valstr):
        """ Parse a number in the format: 150.00+-35.71 """
        m = re.match(self.RE_NBWERROR, valstr)
        if m != None:
            return (m.group(1), m.group(2))
        else:
            return (None, None)


    def _parseHLTRateLog(self, filename):
        """ Parse the log of the HLT rate file to send to the DB """

        # extracted rate table from the log
        rateTable = []

        with open(filename) as f:
            # Now iterating on the file...
            for l in f.readlines():
                # Skipping till the start of the rates summary
                if "HLT rates summary starts here" in l:
                    rateTable.append(l)
                    continue
                if len(rateTable) > 0:
                    # Using the rate table length to know whether we've
                    # found the start line already
                    rateTable.append(l)
                if "HLT rates summary ends here" in l:
                    break
	        

        # Parsing the rate table to extract the figures
        from hlt import HLTRateParser
        data = HLTRateParser.parseHLTRateList("".join(rateTable))

        globalGroup = "HTLRate_Global"
        globalStatsKeys = ['TurcalRate', 'TurboRate', 'Hlt1Lines', 'Hlt2Lines', 'nbevents', 'FullRate']
        for k in globalStatsKeys:
            self.saveFloat(k, float(data[k]), group=globalGroup)
        
        globalStatsWithErrKeys = ['Hlt2GlobalRate', 'Hlt1GlobalRate' ]
        for k in globalStatsWithErrKeys:
            self.saveFloat(k, float(data[k][0]), group=globalGroup)
            self.saveFloat(k + "_error", float(data[k][1]), group=globalGroup)

        # for each line we have:
        #  <line number>, <line name>, <incl. rate>, <incl. rate error>, <excl. rate>, <excl rate error> ]
        # ['1', 'Hlt1TrackMVA', '150.00', '35.71', '80.00', '27.13']

        def saveStatsLine(prefix, statsGroup, data):
            """ Format the stats for LHCbPR """
            (num, name, irate, irateerr, erate, erateerr) = data
            
            getname = lambda par: "_".join([ prefix, name, par])

            self.saveFloat(getname("nb") , int(num), group=statsGroup)
            self.saveFloat(getname("Incl_rate") , float(irate), group=statsGroup)
            self.saveFloat(getname("Incl_rate_err") , float(irateerr), group=statsGroup)
            self.saveFloat(getname("Excl_rate") , float(erate), group=statsGroup)
            self.saveFloat(getname("Excl_rate_err") , float(erateerr), group=statsGroup)
        
        for d in data["Hlt1Stats"]:
            saveStatsLine("HLT1", "HLTRate_HLT1LineStats", d)

        for d in data["Hlt2Stats"]:
            saveStatsLine("HLT2", "HLTRate_HLT2LineStats", d)

        self.saveFile("tuples.root", "tuples.root",  group="HTLRate_Global")
        
        
    def collectResults(self, directory):
        self._parseHLTRateLog(os.path.join(directory,'run.log'))

