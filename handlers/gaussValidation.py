import re, sys, os, shutil, json, glob
from BaseHandler import BaseHandler
from xml.etree.ElementTree import ElementTree
#from xml.parsers import expat
#from xml.parsers.expat import ExpatError
#from xml.etree.ElementTree  import ParseError
#
#SA
#
#from lxml.etree.ElementTree import ElementTree
#from lxml.parsers import expat
#from lxml.parsers.expat import ExpatError
#from lxml.etree.ElementTree  import ParseError
#from xml.etree.ElementTree import ElementTree
import lxml.etree as etree
#from lxml.parsers.expat import ExpatError
#
##AS

# True or False
global DEBUG 
DEBUG = True

#################################################################################
# search "pattern" on "line", if not found return "default"
# if DEBUG and "name" are define print: "name: value"  
def grepPattern(pattern, line, default =  None, name = ""):
  result = default
  resultobject = re.search( pattern, line )
  if ( resultobject != None ):
    tmp = resultobject.groups()
    if ( len(tmp) == 1 ):
      result = tmp[0]
    else:
      result = tmp
    if (DEBUG and name):
      print "[grepPattern] %s: %s" % (name, result)
  else:
    print "WARNING: attribute %s was not found!" % name
  return result

#################################################################################

class GaussLogFile:
  def __init__(self,N):
    self.fileName = N
    self.GaussVersion = None
    self.PythiaVersion = None
    self.GeneratorVersion = None
    self.GeantVersion = None
    self.DDDBVersion = None
    self.SIMCONDVersion = None
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
    
    self.MCHits = None
    self.PileUpMCHits = None
    
    self.TTHit_Hits = None
    self.TTHit_BetaGamma = None
    self.TTHit_DepCharge = None
    self.TTHit_HalfSampleWidth = None
    
    self.ITHit_Hits = None
    self.ITHit_BetaGamma = None
    self.ITHit_DepCharge = None
    self.ITHit_HalfSampleWidth = None
    
    self.OTHit_Hits = None
    self.OTHit_BetaGamma = None
    self.OTHit_DepCharge = None
    self.OTHit_HalfSampleWidth = None
    
    self.VeloPUMCHits = None
    self.MCRichTracks = None
    self.MCRichSegment = None
    self.Muon_MCHits = None
    self.IT_MCHits = None
    self.TT_MCHits = None
    self.Hcal_MCHits = None
    self.OT_MCHits = None
    self.Velo_MCHits = None
    self.Rich2_MCHits = None
    self.Spd_MCHits = None
    self.Rich1_MCHits = None
    self.MCParticles = None
    self.MCVertices = None
    self.Prs_MCHits = None
    self.MCRichOpPhoto = None
    self.Rich_MCHits = None
    self.Ecal_MCHits = None

    self.R1_M1 = None
    self.R1_M2 = None
    self.R1_M3 = None
    self.R1_M4 = None
    self.R1_M5 = None

    self.R2_M1 = None
    self.R2_M2 = None
    self.R2_M3 = None
    self.R2_M4 = None
    self.R2_M5 = None

    self.R3_M1 = None
    self.R3_M2 = None
    self.R3_M3 = None
    self.R3_M4 = None
    self.R3_M5 = None

    self.R4_M1 = None
    self.R4_M2 = None
    self.R4_M3 = None
    self.R4_M4 = None
    self.R4_M5 = None

    self.InvRichFlags = None
    self.InvRichFlagsErr = None

    self.MCRichHitsR1 = None
    self.MCRichHitsR1Err = None

    self.MCRichHitsR2 = None
    self.MCRichHitsR2Err = None

    self.InvRadHitsR1 = None
    self.InvRadHitsR1Err = None

    self.InvRadHitsR2 = None
    self.InvRadHitsR2Err = None

    self.SignalHitsR1 = None
    self.SignalHitsR1Err = None

    self.SignalHitsR2 = None
    self.SignalHitsR2Err = None

    self.GasQuartzCKHitsR1 = None
    self.GasQuartzCKHitsR1Err = None

    self.GasQuartzCKHitsR2 = None
    self.GasQuartzCKHitsR2Err = None

    self.HPDQuartzCKHitsR1 = None
    self.HPDQuartzCKHitsR1Err = None

    self.HPDQuartzCKHitsR2 = None
    self.HPDQuartzCKHitsR2Err = None

    self.NitrogenCKHitsR1 = None
    self.NitrogenCKHitsR1Err = None

    self.NitrogenCKHitsR2 = None
    self.NitrogenCKHitsR2Err = None

    self.SignalCKAero = None
    self.SignalCKAeroErr = None

    self.SignalCKC4F10 = None
    self.SignalCKC4F10Err = None

    self.SignalCKCF4 = None
    self.SignalCKCF4Err = None

    self.ScatteredHitsAero = None
    self.ScatteredHitsAeroErr = None

    self.ScatteredHitsC4F10 = None
    self.ScatteredHitsC4F10Err = None

    self.ScatteredHitsCF4 = None
    self.ScatteredHitsCF4Err = None

    self.MCParticleLessHitsAero = None
    self.MCParticleLessHitsAeroErr = None

    self.MCParticleLessHitsC4F10 = None
    self.MCParticleLessHitsC4F10Err = None

    self.MCParticleLessHitsCF4 = None
    self.MCParticleLessHitsCF4Err = None
    
	# parse the xml log file and returns a dictionary with INT and FLOAT variables
  def parseXmlLog(self, filename):
    # the result dictionary initialization
    result = {}
    result["Int"] = {} # int variables
    result["Float"] = {} # float variables
    result["String_fraction"] = {} # variables in format number (value +/- err)
    result["String_efficiency"] = {} # variables in format number (value +/- err)
    result["String_gen"] = {} # details on generator

    # fill dictionary with decay descriptions. the Key is the ID as in the GeneratorLog.xml file
    #Pythia 6
#    process = {}		
#    process['0'] = "All included subprocesses"
#    process['11'] = "f + f' -> f + f' (QCD)"
#    process['12'] = "f + fbar -> f' + fbar'"
#    process['13'] = "f + fbar -> g + g"
#    process['28'] = "f + g -> f + g"
#    process['53'] = "g + g -> f + fbar"
#    process['68'] = "g + g -> g + g"
#    process['91'] = "Elastic scattering"
#    process['92'] = "Single diffractive (XB)"
#    process['93'] = "Single diffractive (AX)"
#    process['94'] = "Double  diffractive"
#    process['95'] = "Low-pT scattering"
#    process['421'] = "g + g  -> cc~[3S1(1)] + g"
#    process['422'] = "g + g  -> cc~[3S1(8)] + g"
#    process['423'] = "g + g  -> cc~[1S0(8)] + g"
#    process['424'] = "g + g  -> cc~[3PJ(8)] + g"
#    process['425'] = "g + q  -> q + cc~[3S1(8)]"
#    process['426'] = "g + q  -> q + cc~[1S0(8)]"
#    process['427'] = "g + q  -> q + cc~[3PJ(8)]"
#    process['428'] = "q + q~ -> g + cc~[3S1(8)]"
#    process['429'] = "q + q~ -> g + cc~[1S0(8)]"
#    process['430'] = "q + q~ -> g + cc~[3PJ(8)]"
#    process['431'] = "g + g  -> cc~[3P0(1)] + g"
#    process['432'] = "g + g  -> cc~[3P1(1)] + g"
#    process['433'] = "g + g  -> cc~[3P2(1)] + g"
#    process['434'] = "q + g  -> q + cc~[3P0(1)]"
#    process['435'] = "q + g  -> q + cc~[3P1(1)]"
#    process['436'] = "q + g  -> q + cc~[3P2(1)]"
#    process['437'] = "q + q~ -> g + cc~[3P0(1)]"
#    process['438'] = "q + q~ -> g + cc~[3P1(1)]"
#    process['439'] = "q + q~ -> g + cc~[3P2(1)]"
#    process['461'] = "g + g  -> bb~[3S1(1)] + g"
#    process['462'] = "g + g  -> bb~[3S1(8)] + g"
#    process['463'] = "g + g  -> bb~[1S0(8)] + g"
#    process['464'] = "g + g  -> bb~[3PJ(8)] + g"
#    process['465'] = "g + q  -> q + bb~[3S1(8)]"
#    process['466'] = "g + q  -> q + bb~[1S0(8)]"
#    process['467'] = "g + q  -> q + bb~[3PJ(8)]"
#    process['468'] = "q + q~ -> g + bb~[3S1(8)]"
#    process['469'] = "q + q~ -> g + bb~[1S0(8)]"
#    process['470'] = "q + q~ -> g + bb~[3PJ(8)]"
#    process['471'] = "g + g  -> bb~[3P0(1)] + g"
#    process['472'] = "g + g  -> bb~[3P1(1)] + g"
#    process['473'] = "g + g  -> bb~[3P2(1)] + g"
#    process['474'] = "q + g  -> q + bb~[3P0(1)]"
#    process['475'] = "q + g  -> q + bb~[3P1(1)]"
#    process['476'] = "q + g  -> q + bb~[3P2(1)]"
#    process['477'] = "q + q~ -> g + bb~[3P0(1)]"
#    process['478'] = "q + q~ -> g + bb~[3P1(1)]"
#    process['479'] = "q + q~ -> g + bb~[3P2(1)]"
#    process['480'] = "g + g  -> Psi(2S) + g"
#    process['481'] = "g + g  -> Upsilon(2S) + g"
#    process['482'] = "g + g  -> Upsilon(3S) + g"
#    process['483'] = "g + g  -> Upsilon(4S) + g"
#    process['485'] = "g + g  -> psi(3770) + g"
#    
    

    #tree = ElementTree()
    #parser = ET.XMLParser(encoding='utf-16')
    try:
      fd = open(filename)
      parser = etree.XMLParser(recover=True)
      tree   = etree.parse(fd, parser)
    except IOError:
      print "WARNING! File GeneratorLog.xml was not set!"
      return False
    
    if DEBUG:
      print "Parsing GeneratorLog.xml..."

    root = tree.getroot() 
    
    # first save all the couples name = value
    for counter in root.findall('counter'):
      value = counter.find('value').text
      name = counter.get('name')
      if DEBUG:
        print name, value
        
      # save all values in the dictionary
      result["Int"][name] = value
    
      # save some values in local variables to compute quantities later
      if name == "generated interactions" :
        self.TotalInteractions = value
      if name == "generated interactions with >= 1b" :
        self.TotalIntWithB = value
      if name ==  "generated interactions with >= prompt C" :
        self.TotalIntWithPromptCharm = value
      if name == "generated interactions with >= 1c" :
        self.TotalIntWithD = value
      if name == "accepted events" :
        self.TotalAcceptedEvents = value
      if name == "accepted events" :
        self.TotalSignalProcessEvents = value            
      if name == "accepted interactions with >= 1b" :
        self.TotalSignalProcessFromBEvents = value
    
    # look at the crosssection part      
    for crosssection in root.findall('crosssection'):
      description = crosssection.find('description').text
      generated = crosssection.find('generated').text
      value = crosssection.find('value').text
      id = crosssection.get('id')
      #my_description = process[id]
      result["Float"][description] = value
#      result["Float"][my_description] = value
      if DEBUG:
        print "id", id,  description, value
#        print "id", id,  process[id], value
      
      if id == '0': 
        if DEBUG:
          print  generated, value
        self.TotalCrossSection = value

  #look at the fraction part
  
    for fraction in root.findall('fraction'):
      name = fraction.get('name')
      number = fraction.find('number').text
      value = fraction.find('value').text
      error = fraction.find('error').text

      result["String_fraction"][name]= number + "(" + value + "+/-" + error + ")"

      if DEBUG:
          print  name, number, value, error, result["String_fraction"][name]
      
     #efficiencies
    for efficiency in root.findall('efficiency'):
      name = efficiency.get('name')
      before = efficiency.find('before').text
      after = efficiency.find('after').text
      value = efficiency.find('value').text
      error = efficiency.find('error').text

      result["String_efficiency"][name]= before + "/" + after + "(" + value + "+/-" + error + ")"

      if DEBUG:
          print  name, before, after, value, error, result["String_efficiency"][name]

    for gen in root.findall('generator'):
      generator = gen.text
    
      result["String_gen"] = generator

      if DEBUG:
        print  generator, result["String_gen"]

    return result
  
  def computeQuantities(self):
    if DEBUG:
      print "Log file name = ", self.fileName
      
    # read logfile in one shoot  
    f = open(self.fileName)
    logfile = f.read()
    f.close()
   
    self.EventType = grepPattern('Requested to generate EventType (\d+)', logfile, 0, 'EventType')
    
    self.GaussVersion = grepPattern( 'Welcome to Gauss version (\S+)', logfile, "", 'GaussVersion')

    self.PythiaVersion = grepPattern( 'This is PYTHIA version (\S+)', logfile, "", 'PythiaVersion')
    
    self.GeantVersion = grepPattern( 'Geant4 version Name: *(\S+)  *\S+', logfile, "", 'GeantVersion')

    self.DDDBVersion = grepPattern( 'DDDB *INFO Using TAG (\S+)', logfile, "", 'DDDBVersion')

    self.SIMCONDVersion = grepPattern( 'SIMCOND *INFO Using TAG (\S+)', logfile, "", 'SIMCONDVersion')

    if ( self.TotalCrossSection == None ): # values not found in the xml file
      self.TotalCrossSection = grepPattern( 'All included subprocesses *I *\d+ *\d+ I *(\S+)', logfile, None, 'TotalCrossSection')
      if ( self.TotalCrossSection != None and 'D' in self.TotalCrossSection):
        self.TotalCrossSection = self.TotalCrossSection.replace('D', 'E')

      self.TotalInteractions = grepPattern( 'Number of generated interactions : (\d+)', logfile, 0, 'TotalInteractions')        

      self.TotalIntWithB = grepPattern( 'Number of generated interactions with >= 1b : (\d+)', logfile, 0, 'TotalIntWithB') 

      self.TotalIntWithD = grepPattern( 'Number of generated interactions with >= 1c : (\d+)', logfile, 0, 'TotalIntWithD') 

      self.TotalIntWithPromptCharm = grepPattern( 'Number of generated interactions with >= prompt C : (\d+)', logfile, 0, 'TotalIntWithPromptCharm') 

      self.TotalAcceptedEvents = grepPattern( 'Number of accepted events : (\d+)', logfile, 0, 'TotalAcceptedEvents')

      self.TotalSignalProcessEvents = grepPattern( 'Number of events for generator level cut, before : (\d+)', logfile, 0, 'TotalSignalProcessEvents')

      self.TotalSignalProcessFromBEvents = grepPattern( 'Number of accepted interactions with >= 1b : (\d+)', logfile, 0, 'TotalSignalProcessFromBEvents')

    self.TotalZInvertedEvents = grepPattern( 'Number of z-inverted events : (\d+)', logfile, 0, 'TotalZInvertedEvents')

    self.TotalEventsAfterCut = grepPattern( 'Number of events for generator level cut, before : \d+, after : (\d+)', logfile, 0, 'TotalEventsAfterCut')

    self.TotalTime = grepPattern( 'SequencerTime.*INFO *Generation *\| *(\S+)', logfile, 0, 'TotalTime')
    
    self.MCHits = grepPattern( 'VeloGaussMoni *INFO \| Number of MCHits\/Event: *(\S+)', logfile, "", 'MCHits')

    self.PileUpMCHits = grepPattern( 'VeloGaussMoni *INFO \| Number of PileUpMCHits\/Event: *(\S+)', logfile, "", 'PileUpMCHits')

#################################################
#TTHitMonitor               INFO *** Summary ***#
#################################################

    self.TTHit_Hits = grepPattern( 'TTHitMonitor *INFO #hits per event: (\S+)', logfile, "", 'TTHit_Hits')

    self.TTHit_BetaGamma = grepPattern( 'TTHitMonitor *INFO Mean beta \* gamma: (\S+)', logfile, "", 'TTHit_BetaGamma')

    self.TTHit_DepCharge = grepPattern( 'TTHitMonitor *INFO Most Probable deposited charge: (\S+)', logfile, "", 'TTHit_DepCharge')

    self.TTHit_HalfSampleWidth = grepPattern( 'TTHitMonitor *INFO Half Sample width (\S+)', logfile, "", 'TTHit_HalfSampleWidth')

#################################################
#ITHitMonitor               INFO *** Summary ***#
#################################################

    self.ITHit_Hits = grepPattern( 'ITHitMonitor *INFO #hits per event: (\S+)', logfile, "", 'ITHit_Hits')

    self.ITHit_BetaGamma = grepPattern( 'ITHitMonitor *INFO Mean beta \* gamma: (\S+)', logfile, "", 'ITHit_BetaGamma')
    
    self.ITHit_DepCharge = grepPattern( 'ITHitMonitor  *INFO Most Probable deposited charge: (\S+)', logfile, "", 'ITHit_DepCharge')

    self.ITHit_HalfSampleWidth = grepPattern( 'ITHitMonitor *INFO Half Sample width (\S+)', logfile, "", 'ITHit_HalfSampleWidth')

#################################################
#OTHitMonitor               INFO *** Summary ***#
#################################################

    self.OTHit_Hits = grepPattern( 'OTHitMonitor *INFO #hits per event: (\S+)', logfile, "", 'OTHit_Hits')

    self.OTHit_BetaGamma = grepPattern( 'OTHitMonitor  *INFO Mean beta \* gamma: (\S+)', logfile, "", 'OTHit_BetaGamma')

    self.OTHit_DepCharge = grepPattern( 'OTHitMonitor *INFO Most Probable deposited charge: (\S+)', logfile, "", 'OTHit_DepCharge')

    self.OTHit_HalfSampleWidth = grepPattern( 'OTHitMonitor *INFO Half Sample width (\S+)', logfile, "", 'OTHit_HalfSampleWidth')

#################################################################          
#******Stat******           INFO  The Final stat Table (ordered)#
################################################################

    # the sum is the second value

    self.VeloPUMCHits = grepPattern( '\**Stat.*INFO *"#VeloPU MCHits \| *\d+ \| *(\d+)', logfile, 0, 'VeloPUMCHits')

    self.MCRichTracks = grepPattern( '\**Stat.*INFO *"#MCRichTracks" \| *\d+ \| *(\d+)', logfile, 0, 'MCRichTracks')

    self.MCRichSegment = grepPattern( '\**Stat.*INFO *"#MCRichSegment \| *\d+ \| *(\d+)', logfile, 0, 'MCRichSegment')

    self.Muon_MCHits = grepPattern( '\**Stat.*INFO *"#Muon MCHits" *\| *\d+ \| *(\d+)', logfile, 0, 'Muon_MCHits')

    self.IT_MCHits = grepPattern( '\**Stat.*INFO *"#IT MCHits" *\| *\d+ \| *(\d+)', logfile, 0, 'IT_MCHits')

    self.TT_MCHits = grepPattern( '\**Stat.*INFO *"#TT MCHits" *\| *\d+ \| *(\d+)', logfile, 0, 'TT_MCHits')

    self.Hcal_MCHits = grepPattern( '\**Stat.*INFO *"#Hcal MCHits" *\| *\d+ \| *(\d+)', logfile, 0, 'Hcal_MCHits')

    self.OT_MCHits = grepPattern( '\**Stat.*INFO *"#OT MCHits" *\| *\d+ \| *(\d+)', logfile, 0, 'OT_MCHits')

    self.Velo_MCHits = grepPattern( '\**Stat.*INFO *"#Velo MCHits" *\| *\d+ \| *(\d+)', logfile, 0, 'Velo_MCHits')

    self.Rich2_MCHits = grepPattern( '\**Stat.*INFO *"#Rich2 MCHits" *\| *\d+ \| *(\d+)', logfile, 0, 'Rich2_MCHits')

    self.Spd_MCHits = grepPattern( '\**Stat.*INFO *"#Spd MCHits" *\| *\d+ \| *(\d+)', logfile, 0, 'Spd_MCHits')

    self.Rich1_MCHits = grepPattern( '\**Stat.*INFO *"#Rich1 MCHits" *\| *\d+ \| *(\d+)', logfile, 0, 'Rich1_MCHits')

    self.MCParticles = grepPattern( '\**Stat.*INFO *"#MCParticles" *\| *\d+ \| *(\d+)', logfile, 0, 'MCParticles')

    self.MCVertices = grepPattern( '\**Stat.*INFO *"#MCVertices" *\| *\d+ \| *(\d+)', logfile, 0, 'MCVertices')

    self.Prs_MCHits = grepPattern( '\**Stat.*INFO *"#Prs MCHits" *\| *\d+ \| *(\d+)', logfile, 0, 'Prs_MCHits')

    self.MCRichOpPhoto = grepPattern( '\**Stat.*INFO *"#MCRichOpPhoto *\| *\d+ \| *(\d+)', logfile, 0, 'MCRichOpPhoto')

    self.Rich_MCHits = grepPattern( '\**Stat.*INFO *"#Rich MCHits" *\| *\d+ \| *(\d+)', logfile, 0, 'Rich_MCHits')

    self.Ecal_MCHits = grepPattern( '\**Stat.*INFO *"#Ecal MCHits" *\| *\d+ \| *(\d+)', logfile, 0, 'Ecal_MCHits')

#################################################################          
# Muon Monitoring Table                                         #
#################################################################

    (self.R1_M1, self.R1_M2, self.R1_M3, self.R1_M4, self.R1_M5) = grepPattern( 'MuonHitChecker             INFO (\S+) * (\S+) * (\S+) * (\S+) * (\S+) * R1', logfile, (0,0,0,0,0), 'R1')

    (self.R2_M1, self.R2_M2, self.R2_M3, self.R2_M4, self.R2_M5) = grepPattern( 'MuonHitChecker             INFO (\S+) * (\S+) * (\S+) * (\S+) * (\S+) * R2', logfile, (0,0,0,0,0), 'R2')

    (self.R3_M1, self.R3_M2, self.R3_M3, self.R3_M4, self.R3_M5) = grepPattern( 'MuonHitChecker             INFO (\S+) * (\S+) * (\S+) * (\S+) * (\S+) * R3', logfile, (0,0,0,0,0), 'R3')
    
    (self.R4_M1, self.R4_M2, self.R4_M3, self.R4_M4, self.R4_M5) = grepPattern( 'MuonHitChecker             INFO (\S+) * (\S+) * (\S+) * (\S+) * (\S+) * R4', logfile, (0,0,0,0,0), 'R4')

##

    (self.InvRichFlags, self.InvRichFlagsErr) = grepPattern( 'GetRichHits *INFO.*Invalid RICH flags *= *(\S+) *\+\- *(\S+)', logfile, (0, 0), 'InvRichFlags')
    
##

    (self.MCRichHitsR1, self.MCRichHitsR1Err, self.MCRichHitsR2, self.MCRichHitsR2Err) = \
      grepPattern( 'GetRichHits *INFO.*MCRichHits *: Rich1 *= *(\S+) \+\- *(\S+).*Rich2 = *(\S+) *\+\- *(\S+)', logfile, (0,0,0,0), 'MCRichHits')
    
##

    (self.InvRadHitsR1, self.InvRadHitsR1Err, self.InvRadHitsR2, self.InvRadHitsR2Err) = \
      grepPattern( 'GetRichHits *INFO.*Invalid radiator hits *: Rich1 *= *(\S+) \+\- *(\S+).*Rich2 *= *(\S+) *\+\- *(\S+)', logfile, (0,0,0,0), 'InvRadHits')

##

    (self.SignalHitsR1, self.SignalHitsR1Err, self.SignalHitsR2, self.SignalHitsR2Err) = \
      grepPattern( 'GetRichHits *INFO.*Signal Hits *: Rich1 *= *(\S+) \+\- *(\S+).*Rich2 *= *(\S+) *\+\- *(\S+)', logfile, (0,0,0,0), 'SignalHits')

##

    (self.GasQuartzCKHitsR1, self.GasQuartzCKHitsR1Err, self.GasQuartzCKHitsR2, self.GasQuartzCKHitsR2Err) = \
      grepPattern( 'GetRichHits *INFO.*Gas Quartz CK hits *: Rich1 *= *(\S+) \+\- *(\S+).*Rich2 *= *(\S+) *\+\- *(\S+)', logfile, (0,0,0,0), 'GasQuartzCKHits')

##

    (self.HPDQuartzCKHitsR1, self.HPDQuartzCKHitsR1Err, self.HPDQuartzCKHitsR2, self.HPDQuartzCKHitsR2Err) = \
      grepPattern( 'GetRichHits *INFO.*HPD Quartz CK hits *: Rich1 *= *(\S+) \+\- *(\S+).*Rich2 *= *(\S+) *\+\- *(\S+)', logfile, (0,0,0,0), 'HPDQuartzCKHits')

##

    (self.NitrogenCKHitsR1, self.NitrogenCKHitsR1Err, self.NitrogenCKHitsR2, self.NitrogenCKHitsR2Err) = \
      grepPattern( 'GetRichHits *INFO.*Nitrogen CK hits *: Rich1 *= *(\S+) \+\- *(\S+).*Rich2 *= *(\S+) *\+\- *(\S+)', logfile, (0,0,0,0), 'NitrogenCKHits')

##

    (self.SignalCKAero, self.SignalCKAeroErr, self.SignalCKC4F10, self.SignalCKC4F10Err, self.SignalCKCF4, self.SignalCKCF4Err) = \
      grepPattern( 'GetRichHits *INFO.*Signal CK MCRichHits *: Aero *= *(\S+) \+\- *(\S+).*Rich1Gas *= *(\S+) \+\- *(\S+).*Rich2Gas *= *(\S+) *\+\- *(\S+)', logfile, (0,0,0,0,0,0), 'SignalCK')

##

    (self.ScatteredHitsAero, self.ScatteredHitsAeroErr, self.ScatteredHitsC4F10, self.ScatteredHitsC4F10Err, self.ScatteredHitsCF4, self.ScatteredHitsCF4Err) = \
      grepPattern( 'GetRichHits *INFO.*Rayleigh scattered hits *: Aero *= *(\S+) \+\- *(\S+).*Rich1Gas *= *(\S+) \+\- *(\S+).*Rich2Gas *= *(\S+) *\+\- *(\S+)', logfile, (0,0,0,0,0,0), 'ScatteredHits')

#

    (self.MCParticleLessHitsAero, self.MCParticleLessHitsAeroErr, self.MCParticleLessHitsC4F10, self.MCParticleLessHitsC4F10Err, self.MCParticleLessHitsCF4, self.MCParticleLessHitsCF4Err) = \
      grepPattern( 'GetRichHits *INFO.*MCParticle-less hits *: Aero *= *(\S+) \+\- *(\S+).*Rich1Gas *= *(\S+) \+\- *(\S+).*Rich2Gas *= *(\S+) *\+\- *(\S+)', logfile, (0,0,0,0,0,0), 'MCParticleLessHits')


  def eventType(self):
    return self.EventType
    
  def gaussVersion(self):
    return self.GaussVersion
    
  def pythiaVersion(self):
    return self.PythiaVersion
    
  def dddbVersion(self):
    return self.DDDBVersion
    
  def simcondVersion(self):
    return self.SIMCONDVersion
  
  #### This is the total cross-section printed by Pythia  
  def totalCrossSection(self):  
    return self.TotalCrossSection

  #### b quark or B hadron without b quark from production vertex
  def bCrossSection(self):  
    return float( float(self.TotalCrossSection) * int(self.TotalIntWithB) / int(self.TotalInteractions))
 
  #### c quark or D hadron without c quark from production vertex   
  def cCrossSection(self): 
    return float( float(self.TotalCrossSection) * int(self.TotalIntWithD) / int(self.TotalInteractions))
    
  #### D hadron (like J/psi but also chi_c) without B hadron or c quark  
  def promptCharmCrossSection(self):        
    return float( float(self.TotalCrossSection) * int(self.TotalIntWithPromptCharm) / int(self.TotalInteractions))
    
  def totalAcceptedEvents(self):
    return int(self.TotalAcceptedEvents)
    
  #### valid for J/psi (in general for all generation without CP mixture)  
  def signalProcessCrossSection(self):   
    if (self.TotalSignalProcessEvents == 0):
      return 0
    return float( float(self.TotalCrossSection) * int(self.TotalSignalProcessEvents) / int(self.TotalInteractions))
    
  #### valid for J/psi (in general for all generation without CP mixture)  
  def signalProcessFromBCrossSection(self):  
    return float( float(self.TotalCrossSection) * int(self.TotalSignalProcessFromBEvents) / int(self.TotalInteractions))
    
  def generatorLevelCutEfficiency(self):
    if ( self.TotalEventsAfterCut == 0 or self.TotalZInvertedEvents == 0 or self.TotalSignalProcessEvents == 0 ):
      return 0
    return float( ( int(self.TotalEventsAfterCut) - int(self.TotalZInvertedEvents) ) / float( self.TotalSignalProcessEvents) )
    
  def timePerEvent( self ):
    return float(self.TotalTime)

  def MCHitsPerEvent( self ):
    return self.MCHits

  def PileUpMCHitsPerEvent( self ):
    return self.PileUpMCHits

  def TTHitsPerEvent( self ):
    return float (self.TTHit_Hits)

  def TTHitBetaGamma( self ):
    return float (self.TTHit_BetaGamma)

  def TTHitDepCharge( self ):
    return float (self.TTHit_DepCharge)

  def TTHitHalfSampleWidth( self ):
    return float (self.TTHit_HalfSampleWidth)

  def ITHitsPerEvent( self ):
    return float (self.ITHit_Hits)

  def ITHitBetaGamma( self ):
    return float (self.ITHit_BetaGamma)

  def ITHitDepCharge( self ):
    return float (self.ITHit_DepCharge)

  def ITHitHalfSampleWidth( self ):
    return float (self.ITHit_HalfSampleWidth)

  def OTHitsPerEvent( self ):
    return float (self.OTHit_Hits)

  def OTHitBetaGamma( self ):
    return float (self.OTHit_BetaGamma)

  def OTHitDepCharge( self ):
    return float (self.OTHit_DepCharge)

  def OTHitHalfSampleWidth( self ):
    return float (self.OTHit_HalfSampleWidth)

  def NumVeloPUMCHits( self ):
    return self.VeloPUMCHits
  
  def NumMCRichTracks( self ):
    return self.MCRichTracks
  
  def NumMCRichSegment( self ):
    return self.MCRichSegment
  
  def NumMuon_MCHits( self ):
    return self.Muon_MCHits
  
  def NumIT_MCHits( self ):
    return self.IT_MCHits
  
  def NumTT_MCHits( self ):
    return self.TT_MCHits
  
  def NumHcal_MCHits( self ):
    return self.Hcal_MCHits
  
  def NumOT_MCHits( self ):
    return self.OT_MCHits

  def NumVelo_MCHits( self ):
    return self.Velo_MCHits
  
  def NumRich2_MCHits( self ):
    return self.Rich2_MCHits
  
  def NumSpd_MCHits( self ):
    return self.Spd_MCHits

  def NumRich1_MCHits( self ):
    return self.Rich1_MCHits

  def NumMCParticles( self ):
    return self.MCParticles

  def NumMCVertices( self ):
    return self.MCVertices

  def NumPrs_MCHits( self ):
    return self.Prs_MCHits

  def NumMCRichOpPhoto( self ):
    return self.MCRichOpPhoto

  def NumRich_MCHits( self ):
    return self.Rich_MCHits

  def NumEcal_MCHits( self ):
    return self.Ecal_MCHits

  def r1_m1( self ):
    return float (self.R1_M1)
  
  def r1_m2( self ):
    return self.R1_M2
  
  def r1_m3( self ):
    return self.R1_M3

  def r1_m4( self ):
    return self.R1_M4  

  def r1_m5( self ):
    return self.R1_M5
  
  def r2_m1( self ):
    return self.R2_M1

  def r2_m2( self ):
    return self.R2_M2
  
  def r2_m3( self ):
    return self.R1_M3

  def r2_m4( self ):
    return self.R2_M4

  def r2_m5( self ):
    return self.R2_M5
  
  def r3_m1( self ):
    return self.R3_M1
  
  def r3_m2( self ):
    return self.R3_M2
  
  def r3_m3( self ):
    return self.R3_M3
  
  def r3_m4( self ):
    return self.R3_M4

  def r3_m5( self ):
    return self.R3_M5

  def r4_m1( self ):
    return self.R4_M1

  def r4_m2( self ):
    return self.R4_M2

  def r4_m3( self ):
    return self.R4_M3
  
  def r4_m4( self ):
    return self.R4_M4
  
  def r4_m5( self ):
    return self.R4_M5
  
  def invRichFlags( self ):
    return self.InvRichFlags

  def invRichFlagsErr( self ):
    return self.InvRichFlagsErr

  def mcRichHitsR1( self ):
      return self.MCRichHitsR1    
  
  def mcRichHitsR1Err( self ):
    return self.MCRichHitsR1Err

  def mcRichHitsR2( self ):
    return self.MCRichHitsR2

  def mcRichHitsR2Err( self ):
    return self.MCRichHitsR2Err

  def invRadHitsR1( self ):
    return self.InvRadHitsR1

  def invRadHitsR1Err( self ):
      return self.InvRadHitsR1Err
  
  def invRadHitsR2( self ):
    return self.InvRadHitsR2

  def invRadHitsR2Err( self ):
    return self.InvRadHitsR2Err

  def signalHitsR1( self ):
    return self.SignalHitsR1
  
  def signalHitsR1Err( self ):
    return self.SignalHitsR1Err
  
  def signalHitsR2( self ):
    return self.SignalHitsR2  
  
  def signalHitsR2Err( self ):
    return self.SignalHitsR2Err

  def gasQuartzCKHitsR1( self ):
    return self.GasQuartzCKHitsR1
  
  def gasQuartzCKHitsR1Err( self ):
    return self.GasQuartzCKHitsR1Err
  
  def gasQuartzCKHitsR2( self ):
    return self.GasQuartzCKHitsR2
  
  def gasQuartzCKHitsR2Err( self ):
    return self.GasQuartzCKHitsR2Err
  
  def hpdQuartzCKHitsR1( self ):
    return self.HPDQuartzCKHitsR1
  
  def hpdQuartzCKHitsR1Err( self ):
    return self.HPDQuartzCKHitsR1Err
  
  def hpdQuartzCKHitsR2( self ):
    return self.HPDQuartzCKHitsR2
  
  def hpdQuartzCKHitsR2Err( self ):
    return self.HPDQuartzCKHitsR2Err
  
  def nitrogenCKHitsR1( self ):
    return self.NitrogenCKHitsR1
  
  def nitrogenCKHitsR1Err( self ):
    return self.NitrogenCKHitsR1Err
  
  def nitrogenCKHitsR2( self ):
    return self.NitrogenCKHitsR2
  
  def nitrogenCKHitsR2Err( self ):
    return self.NitrogenCKHitsR2Err
  
  def signalCKAero( self ):
    return self.SignalCKAero
  
  def signalCKAeroErr( self ):
    return self.SignalCKAeroErr
  
  def signalCKC4F10( self ):
    return self.SignalCKC4F10
  
  def signalCKC4F10Err( self ):
    return self.SignalCKC4F10Err
  
  def signalCKCF4( self ):
    return self.SignalCKCF4
  
  def signalCKCF4Err( self ):
    return self.SignalCKCF4Err
  
  def scatteredHitsAero( self ):
    return self.ScatteredHitsAero
  
  def scatteredHitsAeroErr( self ):
    return self.ScatteredHitsAeroErr
  
  def scatteredHitsC4F10( self ):
    return self.ScatteredHitsC4F10
  
  def scatteredHitsC4F10Err( self ):
    return self.ScatteredHitsC4F10Err
  
  def scatteredHitsCF4( self ):
    return self.ScatteredHitsCF4
  
  def scatteredHitsCF4Err( self ):
    return self.ScatteredHitsCF4Err
  
  def mcParticleLessHitsAero( self ):
    return self.MCParticleLessHitsAero
  
  def mcParticleLessHitsAeroErr( self ):
    return self.MCParticleLessHitsAeroErr
  
  def mcParticleLessHitsC4F10( self ):
    return self.MCParticleLessHitsC4F10
  
  def mcParticleLessHitsC4F10Err( self ):
    return self.MCParticleLessHitsC4F10Err
  
  def mcParticleLessHitsCF4( self ):
    return self.MCParticleLessHitsCF4
  
  def mcParticleLessHitsCF4Err( self ):
    return self.MCParticleLessHitsCF4Err
  
class gaussValidation(BaseHandler):
    
    def __init__(self):
        super(self.__class__, self).__init__()
    
    def findHistoFile(self, dir):
        return [f for f in os.listdir(dir) if re.match("Gauss.*histos.root", f)]
    
    def collectResults(self,directory):

        # define groups
        grp = {}		
        grp['version'] = "Validation_Version"
        grp['time'] = "Validation_Time"
        grp['generator_count'] = "Validation_Generator_counters"
        grp['generator_cross'] = "Validation_Generator_crossSection"
        grp['generator_fraction'] = "Validation_Generator_fraction"
        grp['generator_efficiency'] = "Validation_Generator_efficiency"
        grp['it_ot_tt'] = "Validation_IT_OT_TT"
        grp['velo'] = "Validation_Velo"
        grp['muon'] = "Validation_Muon_detectors"
        grp['rich'] = "Validation_Rich"
        grp['mc_hits'] = "Validation_MC_hits"         

        # Informations are stored in two files: run.log and GeneratorLog.xml
        # will process first the xml 
        rootfiles = glob.glob("*.root")
        
        l = self.findHistoFile(directory)
        if len(l) == 0:
            raise Exception("Could not locate histo file in the given directory")
        elif len(l) != 1:
            raise Exception("Could not locate just 1 histo file, found:" + str(l))
        
        fileName, fileExtension = os.path.splitext(l[0])
        self.saveFile(fileName, os.path.join(directory,l[0]))
            
        TheLog = GaussLogFile( os.path.join(directory, 'run.log' ))
        
        # save the values found in the xml file
        xmllog = TheLog.parseXmlLog("GeneratorLog.xml")
        if xmllog:
          for name, value in xmllog["Int"].items():
            self.saveInt(name, value, "", grp['generator_count'])
          for name, value in xmllog["Float"].items():
            self.saveFloat(name, value, "", grp['generator_cross'])
          for name, value in xmllog["String_fraction"].items():
            self.saveString(name, value, "", grp['generator_fraction'])
          for name, value in xmllog["String_efficiency"].items():
            self.saveString(name, value, "", grp['generator_efficiency'])
            
          self.saveString('PythiaVersion', xmllog["String_gen"], '', grp['version'])
          
        TheLog.computeQuantities() 

        self.saveString('GaussVersion', TheLog.gaussVersion(), '', grp['version'])

        if not xmllog:
          self.saveString('PythiaVersion', TheLog.pythiaVersion(), '', grp['version'])
          
        self.saveString('DDDBVersion', TheLog.dddbVersion(), '', grp['version'])
        self.saveString('SIMCONDVersion', TheLog.simcondVersion(), '', grp['version'])
        self.saveInt('EventType', TheLog.eventType())

        self.saveFloat('signalProcessCrossSection',TheLog.signalProcessCrossSection(),'', grp['generator_cross'])
        self.saveFloat('generatorLevelCutEfficiency',TheLog.generatorLevelCutEfficiency(),'', grp['generator_cross'])
        self.saveFloat('timePerEvent',TheLog.timePerEvent(), '', grp['time'])

        self.saveString('MCHits',TheLog.MCHitsPerEvent(),'',grp["velo"])
        self.saveString('PileUpMCHits',TheLog.PileUpMCHitsPerEvent(), '', grp["velo"])
        self.saveFloat('TTHits',TheLog.TTHitsPerEvent(), '', grp["it_ot_tt"])
        self.saveFloat('TTHit_BetaGamma',TheLog.TTHitBetaGamma(), '', grp["it_ot_tt"])
        self.saveFloat('TTHit_DepCharge',TheLog.TTHitDepCharge(), '', grp["it_ot_tt"])
        self.saveFloat('TTHit_HalfSampleWidth',TheLog.TTHitHalfSampleWidth(), '', grp["it_ot_tt"])
        self.saveFloat('ITHits',TheLog.ITHitsPerEvent(), '', grp["it_ot_tt"])
        self.saveFloat('ITHit_BetaGamma',TheLog.ITHitBetaGamma(), '', grp["it_ot_tt"])
        self.saveFloat('ITHit_DepCharge',TheLog.ITHitDepCharge(), '', grp["it_ot_tt"])
        self.saveFloat('ITHit_HalfSampleWidth',TheLog.ITHitHalfSampleWidth(), '', grp["it_ot_tt"])
        self.saveFloat('OTHits',TheLog.OTHitsPerEvent(), '', grp["it_ot_tt"])
        self.saveFloat('OTHit_BetaGamma',TheLog.OTHitBetaGamma(), '', grp["it_ot_tt"])
        self.saveFloat('OTHit_DepCharge',TheLog.OTHitDepCharge(), '', grp["it_ot_tt"])
        self.saveFloat('OTHit_HalfSampleWidth',TheLog.OTHitHalfSampleWidth(), '', grp["it_ot_tt"])

        self.saveInt('VeloPUMCHits',TheLog.NumVeloPUMCHits(), '', grp["mc_hits"])
        self.saveInt('MCRichTracks',TheLog.NumMCRichTracks(), '', grp["mc_hits"])
        self.saveInt('MCRichSegment',TheLog.NumMCRichSegment(), '', grp["mc_hits"])
        self.saveInt('Muon_MCHits',TheLog.NumMuon_MCHits(), '', grp["mc_hits"])
        self.saveInt('IT_MCHits',TheLog.NumIT_MCHits(), '', grp["mc_hits"])
        self.saveInt('TT_MCHits',TheLog.NumTT_MCHits(), '', grp["mc_hits"])
        self.saveInt('Hcal_MCHits',TheLog.NumHcal_MCHits(), '', grp["mc_hits"])
        self.saveInt('OT_MCHits',TheLog.NumOT_MCHits(), '', grp["mc_hits"])
        self.saveInt('Velo_MCHits',TheLog.NumVelo_MCHits(), '', grp["mc_hits"])
        self.saveInt('Rich2_MCHits',TheLog.NumRich2_MCHits(), '', grp["mc_hits"])
        self.saveInt('Spd_MCHits',TheLog.NumSpd_MCHits(), '', grp["mc_hits"])
        self.saveInt('Rich1_MCHits',TheLog.NumRich1_MCHits(), '', grp["mc_hits"])
        self.saveInt('MCParticles',TheLog.NumMCParticles(), '', grp["mc_hits"])
        self.saveInt('MCVertices',TheLog.NumMCVertices(), '', grp["mc_hits"])
        self.saveInt('Prs_MCHits',TheLog.NumPrs_MCHits(), '', grp["mc_hits"])
        self.saveInt('MCRichOpPhoto',TheLog.NumMCRichOpPhoto(), '', grp["rich"])
        self.saveInt('Rich_MCHits',TheLog.NumRich_MCHits(), '', grp["mc_hits"])
        self.saveInt('Ecal_MCHits',TheLog.NumEcal_MCHits(), '', grp["mc_hits"])

        self.saveFloat('R1_M1', TheLog.r1_m1(), '', grp["muon"])
        self.saveFloat('R1_M2', TheLog.r1_m2(), '', grp["muon"])
        self.saveFloat('R1_M3', TheLog.r1_m3(), '', grp["muon"])
        self.saveFloat('R1_M4', TheLog.r1_m4(), '', grp["muon"])
        self.saveFloat('R1_M5', TheLog.r1_m5(), '', grp["muon"])

        self.saveFloat('R2_M1', TheLog.r2_m1(), '', grp["muon"])
        self.saveFloat('R2_M2', TheLog.r2_m2(), '', grp["muon"])
        self.saveFloat('R2_M3', TheLog.r2_m3(), '', grp["muon"])
        self.saveFloat('R2_M4', TheLog.r2_m4(), '', grp["muon"])
        self.saveFloat('R2_M5', TheLog.r2_m5(), '', grp["muon"])

        self.saveFloat('R3_M1', TheLog.r3_m1(), '', grp["muon"])
        self.saveFloat('R3_M2', TheLog.r3_m2(), '', grp["muon"])
        self.saveFloat('R3_M3', TheLog.r3_m3(), '', grp["muon"])
        self.saveFloat('R3_M4', TheLog.r3_m4(), '', grp["muon"])
        self.saveFloat('R3_M5', TheLog.r3_m5(), '', grp["muon"])

        self.saveFloat('R4_M1', TheLog.r4_m1(), '', grp["muon"])
        self.saveFloat('R4_M2', TheLog.r4_m2(), '', grp["muon"])
        self.saveFloat('R4_M3', TheLog.r4_m3(), '', grp["muon"])
        self.saveFloat('R4_M4', TheLog.r4_m4(), '', grp["muon"])
        self.saveFloat('R4_M5', TheLog.r4_m5(), '', grp["muon"])

        self.saveFloat('InvRichFlags', TheLog.invRichFlags(), '', grp["rich"])
        self.saveFloat('InvRichFlagsErr', TheLog.invRichFlagsErr(), '', grp["rich"])

        self.saveFloat('MCRichHitsR1', TheLog.mcRichHitsR1(), '', grp["rich"])
        self.saveFloat('MCRichHitsR1Err', TheLog.mcRichHitsR1Err(), '', grp["rich"])

        self.saveFloat('MCRichHitsR2', TheLog.mcRichHitsR2(), '', grp["rich"])
        self.saveFloat('MCRichHitsR2Err', TheLog.mcRichHitsR2Err(), '', grp["rich"])

        self.saveFloat('InvRadHitsR1', TheLog.invRadHitsR1(), '', grp["rich"])
        self.saveFloat('InvRadHitsR1Err', TheLog.invRadHitsR1Err(), '', grp["rich"])

        self.saveFloat('InvRadHitsR2', TheLog.invRadHitsR2(), '', grp["rich"])
        self.saveFloat('InvRadHitsR2Err', TheLog.invRadHitsR2Err(), '', grp["rich"])

        self.saveFloat('SignalHitsR1', TheLog.signalHitsR1(), '', grp["rich"])
        self.saveFloat('SignalHitsR1Err', TheLog.signalHitsR1Err(), '', grp["rich"])

        self.saveFloat('SignalHitsR2', TheLog.signalHitsR2(), '', grp["rich"])
        self.saveFloat('SignalHitsR2Err', TheLog.signalHitsR2Err(), '', grp["rich"])


        self.saveFloat('GasQuartzCKHitsR1', TheLog.gasQuartzCKHitsR1(), '', grp["rich"])
        self.saveFloat('GasQuartzCKHitsR1Err', TheLog.gasQuartzCKHitsR1Err(), '', grp["rich"])

        self.saveFloat('GasQuartzCKHitsR2', TheLog.gasQuartzCKHitsR2(), '', grp["rich"])
        self.saveFloat('GasQuartzCKHitsR2Err', TheLog.gasQuartzCKHitsR2Err(), '', grp["rich"])

        self.saveFloat('HPDQuartzCKHitsR1', TheLog.hpdQuartzCKHitsR1(), '', grp["rich"])
        self.saveFloat('HPDQuartzCKHitsR1Err', TheLog.hpdQuartzCKHitsR1Err(), '', grp["rich"])

        self.saveFloat('HPDQuartzCKHitsR2', TheLog.hpdQuartzCKHitsR1(), '', grp["rich"])
        self.saveFloat('HPDQuartzCKHitsR2Err', TheLog.hpdQuartzCKHitsR1Err(), '', grp["rich"])

        self.saveFloat('NitrogenCKHitsR1', TheLog.nitrogenCKHitsR1(), '', grp["rich"])
        self.saveFloat('NitrogenCKHitsR1Err', TheLog.nitrogenCKHitsR1Err(), '', grp["rich"])

        self.saveFloat('NitrogenCKHitsR2', TheLog.nitrogenCKHitsR2(), '', grp["rich"])
        self.saveFloat('NitrogenCKHitsR2Err', TheLog.nitrogenCKHitsR2Err(), '', grp["rich"])

        self.saveFloat('SignalCKAero', TheLog.signalCKAero(), '', grp["rich"])
        self.saveFloat('SignalCKAeroErr', TheLog.signalCKAeroErr(), '', grp["rich"])

        self.saveFloat('SignalCKC4F10', TheLog.signalCKC4F10(), '', grp["rich"])
        self.saveFloat('SignalCKC4F10Err', TheLog.signalCKC4F10Err(), '', grp["rich"])

        self.saveFloat('SignalCKCF4', TheLog.signalCKCF4(), '', grp["rich"])
        self.saveFloat('SignalCKCF4Err', TheLog.signalCKCF4Err(), '', grp["rich"])

        self.saveFloat('ScatteredHitsAero', TheLog.scatteredHitsAero(), '', grp["rich"])
        self.saveFloat('ScatteredHitsAeroErr', TheLog.scatteredHitsAeroErr(), '', grp["rich"])

        self.saveFloat('ScatteredHitsC4F10', TheLog.scatteredHitsC4F10(), '', grp["rich"])
        self.saveFloat('ScatteredHitsC4F10Err', TheLog.scatteredHitsC4F10Err(), '', grp["rich"])

        self.saveFloat('ScatteredHitsCF4', TheLog.scatteredHitsCF4(), '', grp["rich"])
        self.saveFloat('ScatteredHitsCF4Err', TheLog.scatteredHitsCF4Err(), '', grp["rich"])

        self.saveFloat('MCParticleLessHitsAero', TheLog.mcParticleLessHitsAero(), '', grp["rich"])
        self.saveFloat('MCParticleLessHitsAeroErr', TheLog.mcParticleLessHitsAeroErr(), '', grp["rich"])

        self.saveFloat('MCParticleLessHitsC4F10', TheLog.mcParticleLessHitsC4F10(), '', grp["rich"])
        self.saveFloat('MCParticleLessHitsC4F10Err', TheLog.mcParticleLessHitsC4F10Err(), '', grp["rich"])

        self.saveFloat('MCParticleLessHitsCF4', TheLog.mcParticleLessHitsCF4(), '', grp["rich"])
        self.saveFloat('MCParticleLessHitsCF4Err', TheLog.mcParticleLessHitsCF4Err(), '', grp["rich"])

        # The following info are present in run.log until XXX gauss version
        totalCrossSection = TheLog.totalCrossSection()        
        if ( totalCrossSection != None ) :
          self.saveFloat('totalCrossSection',TheLog.totalCrossSection(), '', grp["generator_cross"])       
          self.saveFloat('bCrossSection', TheLog.bCrossSection(), '', grp["generator_cross"])
          self.saveFloat('cCrossSection',TheLog.cCrossSection(), '', grp["generator_cross"])
          self.saveFloat('promptCharmCrossSection',TheLog.promptCharmCrossSection(), '', grp["generator_cross"])
          self.saveFloat('totalAcceptedEvents',TheLog.totalAcceptedEvents(), '', grp["generator_cross"])
          self.saveFloat('signalProcessFromBCrossSection',TheLog.signalProcessFromBCrossSection(), '', grp["generator_cross"])
        
        
