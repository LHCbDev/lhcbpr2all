import re, sys, os, shutil, json, glob
from BaseHandler import BaseHandler
#################################################################################
def grepPattern(P,L):
  result = None
  resultobject = re.search( P , L )
  if ( resultobject != None ):
    result = resultobject.group(1)
  return result

#################################################################################
class GeneratorLogFile:
  def __init__(self,N):
    self.fileName = N
    self.GaussVersion = None
    self.PythiaVersion = None
    self.EventType = None
    self.TotalCrossSection = None
    self.TotalInteractions = None
    self.TotalIntWithB = None 
    self.TotalIntWithD = None
    self.TotalIntWithPromptCharm = None
    self.TotalAcceptedEvents = None
    self.TotalSignalProcessEvents = None
    self.TotalSignalProcessFromBEvents = None
    self.TotalZInvertedEvents = None
    self.TotalEventsAfterCut = None
    self.TotalTime = None
    
  def computeQuantities(self):
    f = open(self.fileName)
    for line in f:
      if ( self.EventType == None ):
        self.EventType = grepPattern('Requested to generate EventType (\d+)',line)
      if ( self.GaussVersion == None ):
        self.GaussVersion = grepPattern( 'Welcome to Gauss version (\S+)' , line )
      if ( self.PythiaVersion == None ):
        self.PythiaVersion = grepPattern( 'This is PYTHIA version (\S+)' , line )
      if ( self.TotalCrossSection == None ):
        self.TotalCrossSection = grepPattern( 'All included subprocesses *I *\d+ *\d+ I *(\S+)' , line )
        if (self.TotalCrossSection != None):
          if ('D' in self.TotalCrossSection):
            self.TotalCrossSection = self.TotalCrossSection.replace('D', 'E')
      if ( self.TotalInteractions == None ):
        self.TotalInteractions = grepPattern( 'Number of generated interactions : (\d+)' , line )
      if ( self.TotalIntWithB == None ):
        self.TotalIntWithB = grepPattern( 'Number of generated interactions with >= 1b : (\d+)' , line ) 
      if ( self.TotalIntWithD == None ):
        self.TotalIntWithD = grepPattern( 'Number of generated interactions with >= 1c : (\d+)' , line ) 
      if ( self.TotalIntWithPromptCharm == None):
        self.TotalIntWithPromptCharm = grepPattern( 'Number of generated interactions with >= prompt C : (\d+)' , line ) 
      if ( self.TotalAcceptedEvents == None ):
        self.TotalAcceptedEvents = grepPattern( 'Number of accepted events : (\d+)' , line )
      if ( self.TotalSignalProcessEvents == None ):
        self.TotalSignalProcessEvents = grepPattern( 'Number of events for generator level cut, before : (\d+)' , line)
      if ( self.TotalSignalProcessFromBEvents == None ):
        self.TotalSignalProcessFromBEvents = grepPattern( 'Number of accepted interactions with >= 1b : (\d+)' , line )
      if ( self.TotalZInvertedEvents == None ):
        self.TotalZInvertedEvents = grepPattern( 'Number of z-inverted events : (\d+)' , line )
      if ( self.TotalEventsAfterCut == None ):
        self.TotalEventsAfterCut = grepPattern( 'Number of events for generator level cut, before : \d+, after : (\d+)' , line )
      if ( self.TotalTime == None ):
        self.TotalTime = grepPattern( 'SequencerTime... *INFO *Generation *\| *(\S+)' , line )
        if ( self.TotalTime == None ):
          self.TotalTime = 0.
    f.close()
    
  def eventType(self):
    return self.EventType
  def gaussVersion(self):
    return self.GaussVersion
  def pythiaVersion(self):
    return self.PythiaVersion
  def totalCrossSection(self):
  #### This is the total cross-section printed by Pythia
    return float(self.TotalCrossSection)
  def bCrossSection(self):
  #### b quark or B hadron without b quark from production vertex
    return float( float(self.TotalCrossSection) * int(self.TotalIntWithB) / int(self.TotalInteractions))
  def cCrossSection(self):
  #### c quark or D hadron without c quark from production vertex
    return float( float(self.TotalCrossSection) * int(self.TotalIntWithD) / int(self.TotalInteractions))
  def promptCharmCrossSection(self):
  #### D hadron (like J/psi but also chi_c) without B hadron or c quark      
    return float( float(self.TotalCrossSection) * int(self.TotalIntWithPromptCharm) / int(self.TotalInteractions))
  def totalAcceptedEvents(self):
    return int(self.TotalAcceptedEvents)
  def signalProcessCrossSection(self):
  #### valid for J/psi (in general for all generation without CP mixture) 
    if (self.TotalSignalProcessEvents==None):
      return 0
    return float( float(self.TotalCrossSection) * int(self.TotalSignalProcessEvents) / int(self.TotalInteractions))
  def signalProcessFromBCrossSection(self):
  #### valid for J/psi (in general for all generation without CP mixture)
    return float( float(self.TotalCrossSection) * int(self.TotalSignalProcessFromBEvents) / int(self.TotalInteractions))
  def generatorLevelCutEfficiency(self):
    if ( self.TotalEventsAfterCut == None or self.TotalZInvertedEvents == None or self.TotalSignalProcessEvents == None ):
      return 0
    return float( ( int(self.TotalEventsAfterCut) - int(self.TotalZInvertedEvents) ) / float( self.TotalSignalProcessEvents) )
  def timePerEvent( self ):
    return float(self.TotalTime)

          
class gaussGenerator(BaseHandler):
    
    def __init__(self):
        super(self.__class__, self).__init__()
    
    def findHistoFile(self, dir):
        return [f for f in os.listdir(dir) if re.match("Gauss.*histos.root", f)]
    
    def collectResults(self,directory):
        try:
            with open(os.path.join(directory, 'run.log')) as f: pass
        except OSError:
            raise Exception(str(self.__class__)+": No result directory, check the given result directory")
        except IOError:
            raise Exception(str(self.__class__)+": Data file not found, this handler excepts a 'run.log' in the results directory' ")
        
        rootfiles = glob.glob("*.root")
        
        l = self.findHistoFile(directory)
        if len(l) == 0:
            raise Exception("Could not locate histo file in the given directory")
        elif len(l) != 1:
            raise Exception("Could not locate just 1 histo file, found:" + str(l))
        
        fileName, fileExtension = os.path.splitext(l[0])
        self.saveFile(fileName, os.path.join(directory,l[0]))
            
        TheLog = GeneratorLogFile( os.path.join(directory, 'run.log' ))
        TheLog.computeQuantities() 
      
        self.saveFloat('totalCrossSection',TheLog.totalCrossSection())
        self.saveFloat('bCrossSection',TheLog.bCrossSection())
        self.saveFloat('cCrossSection',TheLog.cCrossSection())
        self.saveFloat('promptCharmCrossSection',TheLog.promptCharmCrossSection())
        self.saveFloat('totalAcceptedEvents',TheLog.totalAcceptedEvents())
        self.saveFloat('signalProcessCrossSection',TheLog.signalProcessCrossSection())
        self.saveFloat('signalProcessFromBCrossSection',TheLog.signalProcessFromBCrossSection())
        self.saveFloat('generatorLevelCutEfficiency',TheLog.generatorLevelCutEfficiency())
        self.saveFloat('timePerEvent',TheLog.timePerEvent())
        