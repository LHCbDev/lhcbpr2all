#!/usr/bin/env python

import sys
import os
import re

#
# Parser for the VTune logfile 
#
################################################################################
class SimpleTimingParser:
    """ Class responsible for parsing the TimingAuditor log from the
    Gaudi run  log files """
    def __init__(self, filename):
        self.root = None
    	self.timingTable = [] 
	self.parse(filename)
    
    def parse(self, logfilename):
        """ Parse the log file"""
        # Now iterating on the input and looking for the TimingAuditor lines
        # The hiererarchy of Algos and sequences is rebuilt based on the order
        # in the text file.
        regxp = "([\w\.\d\-\_]+)\s+([\d\.]+)"
        try:
            logf = open(logfilename, "r")
            for l in logf.readlines():
                m = re.match(regxp, l)
                if m != None:
                    self.timingTable.append([m.group(1), float(m.group(2))])
            logf.close()
        except OSError:
            raise Exception(str(self.__class__)+": No result directory, check the given result directory")
        except IOError:
            raise Exception(str(self.__class__)+": Data file not found, this handler excepts a 'run.log' in the results directory' ")

    def getTimingList(self):
	return self.timingTable

#
# Main
#
################################################################################
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print "Please specify log filename"
        sys.exit(1)
    else:
        filename = sys.argv[1]
        print "Processing %s" % filename
        t = SimpleTimingParser(filename)
        for node in t.getTimingList():
            print node[0], " - ", node[1]
