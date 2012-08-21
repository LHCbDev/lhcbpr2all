import os, sys, re
from BaseHandler import BaseHandler
from xml.etree.ElementTree import ElementTree
from xml.parsers.expat import ExpatError



class TimingHandler(BaseHandler):
    
    
    def __init__(self):
        super(self.__class__, self).__init__()
        self.finished = False
        self.column_names = ['EVENT_LOOP']
        self.results = []

    def add_column(self,name):
        if not name in self.column_names:
            self.column_names.append(name)
    
    def collectResults(self,directory):
        try:
            os.chdir(directory)
            f = open('timing.log')
            lines = f.readlines()
            f.close()
        except Exception:
            return False

        for line in lines:
            exp = re.compile('TimingAuditor\.T\.\.\.\s+INFO\s+EVENT LOOP\s*\|\s*[\d\.]+\s+\|\s*([\d\.]+)\s+\|.*$')
            m = exp.search(line)
            if not m is None:
                ev = {}
                tmp = m.groups()[0]
                ev['EVENT_LOOP'] = tmp
                colname = ""
                value = ""
        
                for sl in lines:
                    exp = re.compile('TimingAuditor\.T\.\.\.\s+INFO\s+(\w+)\s*\|\s*([\d\.]+)\s+\|\s*[\d\.]+\s+\|.*$')
                    m = exp.search(sl)
                    if not m is None:
                        colname = m.groups()[0]
                        value = m.groups()[1]
                        self.add_column(colname)
                        ev[colname] = value
                        if colname == 'Output':
                            self.results.append(ev)
                            self.finished = True
            
            if self.finished:
                break
        
        for e in self.results:
            for col in self.column_names:
                self.saveFloat(str(col), str(e[col]))

