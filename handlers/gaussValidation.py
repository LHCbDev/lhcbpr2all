import re, sys, os, shutil, json, glob
from BaseHandler import BaseHandler
from xml.etree.ElementTree import ElementTree
from xml.parsers.expat import ExpatError

#################################################################################
def grepPattern(P,L):
  result = None
  resultobject = re.search( P , L )
  if ( resultobject != None ):
    result = resultobject.group(1)
  return result

#################################################################################
class GaussLogFile:
  def __init__(self,N):
    self.fileName = N
    self.GaussVersion = None
    self.PythiaVersion = None
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
    
  def computeQuantities(self):
    print "self.fileName = ", self.fileName
    f = open(self.fileName)
    #f = open('run.log')
    for line in f:
      #print line
      if ( self.EventType == None ):
        self.EventType = grepPattern('Requested to generate EventType (\d+)',line)
        if ( self.EventType != None ):
          print self.EventType

      if ( self.GaussVersion == None ):
        self.GaussVersion = grepPattern( 'Welcome to Gauss version (\S+)' , line )
        if ( self.GaussVersion != None ):
          print self.GaussVersion

      if ( self.PythiaVersion == None ):
        self.PythiaVersion = grepPattern( 'This is PYTHIA version (\S+)' , line )
        if ( self.PythiaVersion != None ):
          print self.PythiaVersion

      if ( self.GeantVersion == None ):
        self.GeantVersion = grepPattern( 'Geant4 version Name: *(\S+)  *\S+' , line )
        if ( self.GeantVersion != None ):
          print "Geant version = " , self.GeantVersion

      if ( self.DDDBVersion == None ):
        self.DDDBVersion = grepPattern( 'DDDB                       INFO Using TAG (\S+)' , line )
        if ( self.DDDBVersion != None ):
          print self.DDDBVersion

      if ( self.SIMCONDVersion == None ):
        self.SIMCONDVersion = grepPattern( 'SIMCOND                    INFO Using TAG (\S+)' , line )
        if ( self.SIMCONDVersion != None ):
          print self.SIMCONDVersion

      if ( self.TotalCrossSection == None ):
        self.TotalCrossSection = grepPattern( 'All included subprocesses *I *\d+ *\d+ I *(\S+)' , line )
        if (self.TotalCrossSection != None):
          print self.TotalCrossSection
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
        else : 
          print "TotalTime = ", self.TotalTime

      if ( self.MCHits == None ):
        self.MCHits = grepPattern( 'VeloGaussMoni              INFO \| Number of MCHits\/Event:       (\S+)' , line )
        if ( self.MCHits != None ):
          print "MCHits = " , self.MCHits

      if ( self.PileUpMCHits == None ):
        self.PileUpMCHits = grepPattern( 'VeloGaussMoni              INFO \| Number of PileUpMCHits\/Event: (\S+)' , line )
        if ( self.PileUpMCHits != None ):
          print "PileUp MCHits = " , self.PileUpMCHits

#################################################
#TTHitMonitor               INFO *** Summary ***#
#################################################

      if ( self.TTHit_Hits == None ):
        self.TTHit_Hits = grepPattern( 'TTHitMonitor               INFO #hits per event: (\S+)' , line )
        if ( self.TTHit_Hits != None ):
          print "TTHit Monitor: Hits = " , self.TTHit_Hits

      if ( self.TTHit_BetaGamma == None ):
        self.TTHit_BetaGamma = grepPattern( 'TTHitMonitor               INFO Mean beta \* gamma: (\S+)' , line )
        if ( self.TTHit_BetaGamma != None ):
          print "TTHit Monitor: beta * gamma = " , self.TTHit_BetaGamma

      if ( self.TTHit_DepCharge == None ):
        self.TTHit_DepCharge = grepPattern( 'TTHitMonitor               INFO Most Probable deposited charge: (\S+)' , line )
        if ( self.TTHit_DepCharge != None ):
          print "TTHit Monitor: Most Probable deposited charge = " , self.TTHit_DepCharge

      if ( self.TTHit_HalfSampleWidth == None ):
        self.TTHit_HalfSampleWidth = grepPattern( 'TTHitMonitor               INFO Half Sample width (\S+)' , line )
        if ( self.TTHit_HalfSampleWidth != None ):
          print "TTHit Monitor: half sample width = " , self.TTHit_HalfSampleWidth

#################################################
#ITHitMonitor               INFO *** Summary ***#
#################################################


      if ( self.ITHit_Hits == None ):
        self.ITHit_Hits = grepPattern( 'ITHitMonitor               INFO #hits per event: (\S+)' , line )
        if ( self.ITHit_Hits != None ):
          print "ITHit Monitor: Hits = " , self.ITHit_Hits

      if ( self.ITHit_BetaGamma == None ):
        self.ITHit_BetaGamma = grepPattern( 'ITHitMonitor               INFO Mean beta \* gamma: (\S+)' , line )
        if ( self.ITHit_BetaGamma != None ):
          print "ITHit Monitor: beta * gamma = " , self.ITHit_BetaGamma
          
      if ( self.ITHit_DepCharge == None ):
        self.ITHit_DepCharge = grepPattern( 'ITHitMonitor               INFO Most Probable deposited charge: (\S+)' , line )
        if ( self.ITHit_DepCharge != None ):
          print "ITHit Monitor: Most Probable deposited charge = " , self.ITHit_DepCharge

      if ( self.ITHit_HalfSampleWidth == None ):
        self.ITHit_HalfSampleWidth = grepPattern( 'ITHitMonitor               INFO Half Sample width (\S+)' , line )
        if ( self.ITHit_HalfSampleWidth != None ):
          print "ITHit Monitor: half sample width = " , self.ITHit_HalfSampleWidth


#################################################
#OTHitMonitor               INFO *** Summary ***#
#################################################

      if ( self.OTHit_Hits == None ):
        self.OTHit_Hits = grepPattern( 'OTHitMonitor               INFO #hits per event: (\S+)' , line )
        if ( self.OTHit_Hits != None ):
          print "OTHit Monitor: Hits = " , self.OTHit_Hits

      if ( self.OTHit_BetaGamma == None ):
        self.OTHit_BetaGamma = grepPattern( 'OTHitMonitor               INFO Mean beta \* gamma: (\S+)' , line )
        if ( self.OTHit_BetaGamma != None ):
          print "OTHit Monitor: beta * gamma = " , self.OTHit_BetaGamma

      if ( self.OTHit_DepCharge == None ):
        self.OTHit_DepCharge = grepPattern( 'OTHitMonitor               INFO Most Probable deposited charge: (\S+)' , line )
        if ( self.OTHit_DepCharge != None ):
          print "OTHit Monitor: Most Probable deposited charge = " , self.OTHit_DepCharge

      if ( self.OTHit_HalfSampleWidth == None ):
        self.OTHit_HalfSampleWidth = grepPattern( 'OTHitMonitor               INFO Half Sample width (\S+)' , line )
        if ( self.OTHit_HalfSampleWidth != None ):
          print "OTHit Monitor: half sample width = " , self.OTHit_HalfSampleWidth


#################################################################          
#******Stat******           INFO  The Final stat Table (ordered)#
#################################################################

      if ( self.VeloPUMCHits == None ):
        self.VeloPUMCHits = grepPattern( '\*\*\*\*\*\*Stat\*\*\*\*\*\*           INFO  "#VeloPU MCHits \|      *\d+ \|     *(\d+)' , line )
        if ( self.VeloPUMCHits != None ):
          print "#VeloPU MCHits = " , self.VeloPUMCHits

      if ( self.MCRichTracks == None ):
        self.MCRichTracks = grepPattern( '\*\*\*\*\*\*Stat\*\*\*\*\*\*           INFO  "#MCRichTracks" \|      *\d+ \|     *(\d+)' , line )
        if ( self.MCRichTracks != None ):
          print "#MCRichTracks = " , self.MCRichTracks

      if ( self.MCRichSegment == None ):
        self.MCRichSegment = grepPattern( '\*\*\*\*\*\*Stat\*\*\*\*\*\*           INFO  "#MCRichSegment \|      *\d+ \|      *(\d+)' , line )
        if ( self.MCRichSegment != None ):
          print "#MCRichSegment = " , self.MCRichSegment

      if ( self.Muon_MCHits == None ):
        self.Muon_MCHits = grepPattern( '\*\*\*\*\*\*Stat\*\*\*\*\*\*           INFO  "#Muon MCHits"  \|      \d+ \|      *(\d+)' , line )
        if ( self.Muon_MCHits != None ):
          print "#Muon_MCHits = " , self.Muon_MCHits

      if ( self.IT_MCHits == None ):
#there are two values in the run.log file. In this way the second is collected
        self.IT_MCHits = grepPattern( '\*\*\*\*\*\*Stat\*\*\*\*\*\*           INFO  "#TT MCHits"    \|      \d+ \|      *(\d+)' , line )
        if ( self.IT_MCHits != None ):
          print "#IT_MCHits = " , self.IT_MCHits
          
      if ( self.Hcal_MCHits == None ):
        self.Hcal_MCHits = grepPattern( '\*\*\*\*\*\*Stat\*\*\*\*\*\*           INFO  "#Hcal MCHits"  \|      \d* \|   *(\d+)' , line )
        if ( self.Hcal_MCHits != None ):
          print "#Hcal_MCHits = " , self.Hcal_MCHits

      if ( self.OT_MCHits == None ):
        self.OT_MCHits = grepPattern( '\*\*\*\*\*\*Stat\*\*\*\*\*\*           INFO  "#OT MCHits"    \|      \d+ \|    *(\d+)' , line )
        if ( self.OT_MCHits != None ):
          print "#OT_MCHits = " , self.OT_MCHits

      if ( self.Velo_MCHits == None ):
        self.Velo_MCHits = grepPattern( '\*\*\*\*\*\*Stat\*\*\*\*\*\*           INFO  "#Velo MCHits"  \|      \d+ \|   *(\d+)' , line )
        if ( self.Velo_MCHits != None ):
          print "#Velo_MCHits = " , self.Velo_MCHits

      if ( self.Rich2_MCHits == None ):
        self.Rich2_MCHits = grepPattern( '\*\*\*\*\*\*Stat\*\*\*\*\*\*           INFO  "#Rich2 MCHits" \|      \d+ \|   *(\d+)' , line )
        if ( self.Rich2_MCHits != None ):
          print "#Rich2_MCHits = " , self.Rich2_MCHits

      if ( self.Spd_MCHits == None ):
        self.Spd_MCHits = grepPattern( '\*\*\*\*\*\*Stat\*\*\*\*\*\*           INFO  "#Spd MCHits"   \|      \d+ \|    *(\d+)' , line )
        if ( self.Spd_MCHits != None ):
          print "#Spd_MCHits = " , self.Spd_MCHits

      if ( self.Rich1_MCHits == None ):
        self.Rich1_MCHits = grepPattern( '\*\*\*\*\*\*Stat\*\*\*\*\*\*           INFO  "#Rich1 MCHits" \|      \d+ \|   *(\d+)' , line )
        if ( self.Rich1_MCHits != None ):
          print "#Rich1_MCHits = " , self.Rich1_MCHits

      if ( self.MCParticles == None ):
        self.MCParticles = grepPattern( '\*\*\*\*\*\*Stat\*\*\*\*\*\*           INFO  "#MCParticles"  \|      \d+ \|   *(\d+)' , line )
        if ( self.MCParticles != None ):
          print "#MCParticles = " , self.MCParticles

      if ( self.MCVertices == None ):
        self.MCVertices = grepPattern( '\*\*\*\*\*\*Stat\*\*\*\*\*\*           INFO  "#MCVertices"   \|      \d+ \|     *(\d+)' , line )
        if ( self.MCVertices != None ):
          print "#MCVertices = " , self.MCVertices

      if ( self.Prs_MCHits == None ):
        self.Prs_MCHits = grepPattern( '\*\*\*\*\*\*Stat\*\*\*\*\*\*           INFO  "#Prs MCHits"   \|      \d+ \|    *(\d+)' , line )
        if ( self.Prs_MCHits != None ):
          print "#Prs_MCHits = " , self.Prs_MCHits

      if ( self.MCRichOpPhoto == None ):
        self.MCRichOpPhoto = grepPattern( '\*\*\*\*\*\*Stat\*\*\*\*\*\*           INFO  "#MCRichOpPhoto \|      \d+ \|    *(\d+)' , line )
        if ( self.MCRichOpPhoto != None ):
          print "#MCRichOpPhoto = " , self.MCRichOpPhoto

      if ( self.Rich_MCHits == None ):
        self.Rich_MCHits = grepPattern( '\*\*\*\*\*\*Stat\*\*\*\*\*\*           INFO  "#Rich MCHits"  \|      \d+ \|   *(\d+)' , line )
        if ( self.Rich_MCHits != None ):
          print "#RichMCHits = " , self.Rich_MCHits

      if ( self.Ecal_MCHits == None ):
        self.Ecal_MCHits = grepPattern( '\*\*\*\*\*\*Stat\*\*\*\*\*\*           INFO  "#Ecal MCHits"  \|      \d+ \|    *(\d+)' , line )
        if ( self.Ecal_MCHits != None ):
          print "#EcalMCHits = " , self.Ecal_MCHits

#################################################################          
# Muon Monitoring Table                                         #
#################################################################


      if ( self.R1_M1 == None ):
        self.R1_M1 = grepPattern( 'MuonHitChecker             INFO (\S+) * \S+ * \S+ * \S+ * \S+ * R1' , line )
        if ( self.R1_M1 != None ):
          print "R1 - M1 = " , self.R1_M1

      if ( self.R1_M2 == None ):
        self.R1_M2 = grepPattern( 'MuonHitChecker             INFO \S+ * (\S+) * \S+ * \S+ * \S+ * R1' , line )
        if ( self.R1_M2 != None ):
          print "R1 - M2 = " , self.R1_M2

      if ( self.R1_M3 == None ):
        self.R1_M3 = grepPattern( 'MuonHitChecker             INFO \S+ * \S+ * (\S+) * \S+ * \S+ * R1' , line )
        if ( self.R1_M3 != None ):
          print "R1 - M3 = " , self.R1_M3

      if ( self.R1_M4 == None ):
        self.R1_M4 = grepPattern( 'MuonHitChecker             INFO \S+ * \S+ * \S+ * (\S+) * \S+ * R1' , line )
        if ( self.R1_M4 != None ):
          print "R1 - M4 = " , self.R1_M4

      if ( self.R1_M5 == None ):
        self.R1_M5 = grepPattern( 'MuonHitChecker             INFO \S+ * \S+ * \S+ * \S+ * (\S+) * R1' , line )
        if ( self.R1_M5 != None ):
          print "R1 - M5 = " , self.R1_M5



      if ( self.R2_M1 == None ):
        self.R2_M1 = grepPattern( 'MuonHitChecker             INFO (\S+) * \S+ * \S+ * \S+ * \S+ * R2' , line )
        if ( self.R2_M1 != None ):
          print "R2 - M1 = " , self.R2_M1

      if ( self.R2_M2 == None ):
        self.R2_M2 = grepPattern( 'MuonHitChecker             INFO \S+ * (\S+) * \S+ * \S+ * \S+ * R2' , line )
        if ( self.R2_M2 != None ):
          print "R2 - M2 = " , self.R2_M2

      if ( self.R2_M3 == None ):
        self.R2_M3 = grepPattern( 'MuonHitChecker             INFO \S+ * \S+ * (\S+) * \S+ * \S+ * R2' , line )
        if ( self.R2_M3 != None ):
          print "R2 - M3 = " , self.R2_M3

      if ( self.R2_M4 == None ):
        self.R2_M4 = grepPattern( 'MuonHitChecker             INFO \S+ * \S+ * \S+ * (\S+) * \S+ * R2' , line )
        if ( self.R2_M4 != None ):
          print "R2 - M4 = " , self.R2_M4

      if ( self.R2_M5 == None ):
        self.R2_M5 = grepPattern( 'MuonHitChecker             INFO \S+ * \S+ * \S+ * \S+ * (\S+) * R2' , line )
        if ( self.R2_M5 != None ):
          print "R2 - M5 = " , self.R2_M5


      if ( self.R3_M1 == None ):
        self.R3_M1 = grepPattern( 'MuonHitChecker             INFO (\S+) * \S+ * \S+ * \S+ * \S+ * R3' , line )
        if ( self.R3_M1 != None ):
          print "R3 - M1 = " , self.R3_M1

      if ( self.R3_M2 == None ):
        self.R3_M2 = grepPattern( 'MuonHitChecker             INFO \S+ * (\S+) * \S+ * \S+ * \S+ * R3' , line )
        if ( self.R3_M2 != None ):
          print "R3 - M2 = " , self.R3_M2

      if ( self.R3_M3 == None ):
        self.R3_M3 = grepPattern( 'MuonHitChecker             INFO \S+ * \S+ * (\S+) * \S+ * \S+ * R3' , line )
        if ( self.R3_M3 != None ):
          print "R3 - M3 = " , self.R3_M3

      if ( self.R3_M4 == None ):
        self.R3_M4 = grepPattern( 'MuonHitChecker             INFO \S+ * \S+ * \S+ * (\S+) * \S+ * R3' , line )
        if ( self.R3_M4 != None ):
          print "R3 - M4 = " , self.R3_M4

      if ( self.R3_M5 == None ):
        self.R3_M5 = grepPattern( 'MuonHitChecker             INFO \S+ * \S+ * \S+ * \S+ * (\S+) * R3' , line )
        if ( self.R3_M5 != None ):
          print "R3 - M5 = " , self.R3_M5


      if ( self.R4_M1 == None ):
        self.R4_M1 = grepPattern( 'MuonHitChecker             INFO (\S+) * \S+ * \S+ * \S+ * \S+ * R4' , line )
        if ( self.R4_M1 != None ):
          print "R4 - M1 = " , self.R4_M1

      if ( self.R4_M2 == None ):
        self.R4_M2 = grepPattern( 'MuonHitChecker             INFO \S+ * (\S+) * \S+ * \S+ * \S+ * R4' , line )
        if ( self.R4_M2 != None ):
          print "R4 - M2 = " , self.R4_M2

      if ( self.R4_M3 == None ):
        self.R4_M3 = grepPattern( 'MuonHitChecker             INFO \S+ * \S+ * (\S+) * \S+ * \S+ * R4' , line )
        if ( self.R4_M3 != None ):
          print "R4 - M3 = " , self.R4_M3

      if ( self.R4_M4 == None ):
        self.R4_M4 = grepPattern( 'MuonHitChecker             INFO \S+ * \S+ * \S+ * (\S+) * \S+ * R4' , line )
        if ( self.R4_M4 != None ):
          print "R4 - M4 = " , self.R4_M4

      if ( self.R4_M5 == None ):
        self.R4_M5 = grepPattern( 'MuonHitChecker             INFO \S+ * \S+ * \S+ * \S+ * (\S+) * R4' , line )
        if ( self.R4_M5 != None ):
          print "R4 - M5 = " , self.R4_M5

##
          
      if ( self.InvRichFlags == None ):
        self.InvRichFlags = grepPattern( 'GetRichHits                INFO Av. # Invalid RICH flags   * = * (\S+)' , line )        
        if ( self.InvRichFlags != None ):
          print "InvRichFlags = " , self.InvRichFlags

      if ( self.InvRichFlagsErr == None ):
        self.InvRichFlagsErr = grepPattern( 'GetRichHits                INFO Av. # Invalid RICH flags   * = * \S+ * \+\- * (\S+)' , line )
        if ( self.InvRichFlagsErr != None ):
          print "InvRichFlagsErr = " ,  self.InvRichFlagsErr

##

      if ( self.MCRichHitsR1 == None ):
        self.MCRichHitsR1 = grepPattern( 'GetRichHits                INFO Av. # MCRichHits              : Rich1 = * (\S+)' , line )        
        if ( self.MCRichHitsR1 != None ):
          print "MCRichHitsR1 = " , self.MCRichHitsR1
          
          
      if ( self.MCRichHitsR1Err == None ):
        self.MCRichHitsR1Err = grepPattern( 'GetRichHits                INFO Av. # MCRichHits              : Rich1 = * \S+ \+\- * (\S+) *' , line )
        if ( self.MCRichHitsR1Err != None ):
          print "MCRichHitsR1Err = " , self.MCRichHitsR1Err

##
      if ( self.MCRichHitsR2 == None ):
        self.MCRichHitsR2 = grepPattern( 'GetRichHits                INFO Av. # MCRichHits              : Rich1 = * \S+ \+\- * \S+ * \(*\S+ * \S+ *\) * Rich2 = * (\S+)' , line )
        if ( self.MCRichHitsR2 != None ):
          print "MCRichHitsR2 = " , self.MCRichHitsR2

      if ( self.MCRichHitsR2Err == None ):
        self.MCRichHitsR2Err = grepPattern( 'GetRichHits                INFO Av. # MCRichHits              : Rich1 = * \S+ \+\- * \S+ * \(*\S+ * \S+ *\) * Rich2 = * \S+ * \+\- * (\S+)' , line )
        if ( self.MCRichHitsR2Err != None ):
          print "MCRichHitsR2Err = " ,  self.MCRichHitsR2Err

##

      if ( self.InvRadHitsR1 == None ):
        self.InvRadHitsR1 = grepPattern( 'GetRichHits                INFO Av. # Invalid radiator hits   : Rich1 = * (\S+)' , line )
        if ( self.InvRadHitsR1 != None ):
          print "InvRadHitsR1 = " , self.InvRadHitsR1

          
      if ( self.InvRadHitsR1Err == None ):
        self.InvRadHitsR1Err = grepPattern( 'GetRichHits                INFO Av. # Invalid radiator hits   : Rich1 = * \S+ \+\- * (\S+) *' , line )
        if ( self.InvRadHitsR1Err != None ):
          print "InvRadHitsR1Err = " ,  self.InvRadHitsR1Err


      if ( self.InvRadHitsR2 == None ):
        self.InvRadHitsR2 = grepPattern( 'GetRichHits                INFO Av. # Invalid radiator hits   : Rich1 = * \S+ \+\- * \S+ * \( * \S+ * \S+\) * Rich2 = * (\S+)' , line )
        if ( self.InvRadHitsR2 != None ):
          print "InvRadHitsR2 = " , self.InvRadHitsR2
          
      if ( self.InvRadHitsR2Err == None ):
        self.InvRadHitsR2Err = grepPattern( 'GetRichHits                INFO Av. # Invalid radiator hits   : Rich1 = * \S+ \+\- * \S+ * \( * \S+ * \S+\) * Rich2 = * \S+ \+\- * (\S+)' , line )
        if ( self.InvRadHitsR2Err != None ):
          print "InvRadHitsR2Err = " , self.InvRadHitsR2Err
          

##

      if ( self.SignalHitsR1 == None ):
        self.SignalHitsR1 = grepPattern( 'GetRichHits                INFO Av. # Signal Hits             : Rich1 = * (\S+)' , line )
        if ( self.SignalHitsR1 != None ):
          print "SignalHitsR1 = " , self.SignalHitsR1

          
      if ( self.SignalHitsR1Err == None ):
        self.SignalHitsR1Err = grepPattern( 'GetRichHits                INFO Av. # Signal Hits             : Rich1 = * \S+ \+\- * (\S+) *' , line )
        if ( self.SignalHitsR1Err != None ):
          print "SignalHitsR1Err = " ,  self.SignalHitsR1Err


      if ( self.SignalHitsR2 == None ):
        self.SignalHitsR2 = grepPattern( 'GetRichHits                INFO Av. # Signal Hits             : Rich1 = * \S+ \+\- * \S+ * \( * \S+ * \S+\) * Rich2 = * (\S+)' , line )
        if ( self.SignalHitsR2 != None ):
          print "SignalHitsR2 = " , self.SignalHitsR2
          
      if ( self.SignalHitsR2Err == None ):
        self.SignalHitsR2Err = grepPattern( 'GetRichHits                INFO Av. # Signal Hits             : Rich1 = * \S+ \+\- * \S+ * \( * \S+ * \S+\) * Rich2 = * \S+ \+\- * (\S+)' , line )
        if ( self.SignalHitsR2Err != None ):
          print "SignalHitsR2Err = " , self.SignalHitsR2Err

##

      if ( self.GasQuartzCKHitsR1 == None ):
        self.GasQuartzCKHitsR1 = grepPattern( 'GetRichHits                INFO Av. # Gas Quartz CK hits      : Rich1 = * (\S+)' , line )
        if ( self.GasQuartzCKHitsR1 != None ):
          print "GasQuartzCKHitsR1 = " , self.GasQuartzCKHitsR1

          
      if ( self.GasQuartzCKHitsR1Err == None ):
        self.GasQuartzCKHitsR1Err = grepPattern( 'GetRichHits                INFO Av. # Gas Quartz CK hits      : Rich1 = * \S+ \+\- * (\S+) *' , line )
        if ( self.GasQuartzCKHitsR1Err != None ):
          print "GasQuartzCKHitsR1Err = " ,  self.GasQuartzCKHitsR1Err


      if ( self.GasQuartzCKHitsR2 == None ):
        self.GasQuartzCKHitsR2 = grepPattern( 'GetRichHits                INFO Av. # Gas Quartz CK hits      : Rich1 = * \S+ \+\- * \S+ * \( * \S+ * \S+\) * Rich2 = * (\S+)' , line )
        if ( self.GasQuartzCKHitsR2 != None ):
          print "GasQuartzCKHitsR2 = " , self.GasQuartzCKHitsR2
          
      if ( self.GasQuartzCKHitsR2Err == None ):
        self.GasQuartzCKHitsR2Err = grepPattern( 'GetRichHits                INFO Av. # Gas Quartz CK hits      : Rich1 = * \S+ \+\- * \S+ * \( * \S+ * \S+\) * Rich2 = * \S+ \+\- * (\S+)' , line )
        if ( self.GasQuartzCKHitsR2Err != None ):
          print "GasQuartzCKHitsR2Err = " , self.GasQuartzCKHitsR2Err

##
      if ( self.HPDQuartzCKHitsR1 == None ):
        self.HPDQuartzCKHitsR1 = grepPattern( 'GetRichHits                INFO Av. # HPD Quartz CK hits      : Rich1 = * (\S+)' , line )
        if ( self.HPDQuartzCKHitsR1 != None ):
          print "HPDQuartzCKHitsR1 = " , self.HPDQuartzCKHitsR1

          
      if ( self.HPDQuartzCKHitsR1Err == None ):
        self.HPDQuartzCKHitsR1Err = grepPattern( 'GetRichHits                INFO Av. # HPD Quartz CK hits      : Rich1 = * \S+ \+\- * (\S+) *' , line )
        if ( self.HPDQuartzCKHitsR1Err != None ):
          print "HPDQuartzCKHitsR1Err = " ,  self.HPDQuartzCKHitsR1Err


      if ( self.HPDQuartzCKHitsR2 == None ):
        self.HPDQuartzCKHitsR2 = grepPattern( 'GetRichHits                INFO Av. # HPD Quartz CK hits      : Rich1 = * \S+ \+\- * \S+ * \( * \S+ * \S+\) * Rich2 = * (\S+)' , line )
        if ( self.HPDQuartzCKHitsR2 != None ):
          print "HPDQuartzCKHitsR2 = " , self.HPDQuartzCKHitsR2
          
      if ( self.HPDQuartzCKHitsR2Err == None ):
        self.HPDQuartzCKHitsR2Err = grepPattern( 'GetRichHits                INFO Av. # HPD Quartz CK hits      : Rich1 = * \S+ \+\- * \S+ * \( * \S+ * \S+\) * Rich2 = * \S+ \+\- * (\S+)' , line )
        if ( self.HPDQuartzCKHitsR2Err != None ):
          print "HPDQuartzCKHitsR2Err = " , self.HPDQuartzCKHitsR2Err
##

      if ( self.NitrogenCKHitsR1 == None ):
        self.NitrogenCKHitsR1 = grepPattern( 'GetRichHits                INFO Av. # Nitrogen CK hits        : Rich1 = * (\S+)' , line )
        if ( self.NitrogenCKHitsR1 != None ):
          print "NitrogenCKHitsR1 = " , self.NitrogenCKHitsR1

          
      if ( self.NitrogenCKHitsR1Err == None ):
        self.NitrogenCKHitsR1Err = grepPattern( 'GetRichHits                INFO Av. # Nitrogen CK hits        : Rich1 = * \S+ \+\- * (\S+) *' , line )
        if ( self.NitrogenCKHitsR1Err != None ):
          print "NitrogenCKHitsR1Err = " ,  self.NitrogenCKHitsR1Err


      if ( self.NitrogenCKHitsR2 == None ):
        self.NitrogenCKHitsR2 = grepPattern( 'GetRichHits                INFO Av. # Nitrogen CK hits        : Rich1 = * \S+ \+\- * \S+ * \( * \S+ * \S+\) * Rich2 = * (\S+)' , line )
        if ( self.NitrogenCKHitsR2 != None ):
          print "NitrogenCKHitsR2 = " , self.NitrogenCKHitsR2
          
      if ( self.NitrogenCKHitsR2Err == None ):
        self.NitrogenCKHitsR2Err = grepPattern( 'GetRichHits                INFO Av. # Nitrogen CK hits        : Rich1 = * \S+ \+\- * \S+ * \( * \S+ * \S+\) * Rich2 = * \S+ \+\- * (\S+)' , line )
        if ( self.NitrogenCKHitsR2Err != None ):
          print "NitrogenCKHitsR2Err = " , self.NitrogenCKHitsR2Err
##

      if ( self.SignalCKAero == None ):
        self.SignalCKAero = grepPattern( 'GetRichHits                INFO Av. # Signal CK MCRichHits    : Aero  = * (\S+)' , line )
        if ( self.SignalCKAero != None ):
          print "SignalCKAero = " , self.SignalCKAero

          
      if ( self.SignalCKAeroErr == None ):
        self.SignalCKAeroErr = grepPattern( 'GetRichHits                INFO Av. # Signal CK MCRichHits    : Aero  = * \S+ \+\- * (\S+) *' , line )
        if ( self.SignalCKAeroErr != None ):
          print "SignalCKAeroErr = " ,  self.SignalCKAeroErr


      if ( self.SignalCKC4F10 == None ):
        self.SignalCKC4F10 = grepPattern( 'GetRichHits                INFO Av. # Signal CK MCRichHits    : Aero  = * \S+ \+\- * \S+ * \( * \S+ * \S+\) * Rich1Gas = * (\S+)' , line )
        if ( self.SignalCKC4F10 != None ):
          print "SignalCKC4F10 = " , self.SignalCKC4F10
          
      if ( self.SignalCKC4F10Err == None ):
        self.SignalCKC4F10Err = grepPattern( 'GetRichHits                INFO Av. # Signal CK MCRichHits    : Aero  = * \S+ \+\- * \S+ * \( * \S+ * \S+\) * Rich1Gas = * \S+ \+\- * (\S+)' , line )
        if ( self.SignalCKC4F10Err != None ):
          print "SignalCKC4F10Err = " , self.SignalCKC4F10Err

      if ( self.SignalCKCF4 == None ):
        self.SignalCKCF4 = grepPattern( 'GetRichHits                INFO Av. # Signal CK MCRichHits    : Aero  = * \S+ \+\- * \S+ * \( * \S+ * \S+\) * Rich1Gas = * \S+ * \+\- * \S+ * \( * \S+ * \S+\) * Rich2Gas = * (\S+)' , line )
        if ( self.SignalCKCF4 != None ):
          print "SignalCKCF4 = " , self.SignalCKCF4
          
      if ( self.SignalCKCF4Err == None ):
        self.SignalCKCF4Err = grepPattern( 'GetRichHits                INFO Av. # Signal CK MCRichHits    : Aero  = * \S+ \+\- * \S+ * \( * \S+ * \S+\) * Rich1Gas = * \S+ * \+\- * \S+ * \( * \S+ * \S+\) * Rich2Gas = * \S+ \+\- * (\S+)' , line )
        if ( self.SignalCKCF4Err != None ):
          print "SignalCKCF4Err = " , self.SignalCKCF4Err
##


      if ( self.ScatteredHitsAero == None ):
        self.ScatteredHitsAero = grepPattern( 'GetRichHits                INFO Av. # Rayleigh scattered hits : Aero  = * (\S+)' , line )
        if ( self.ScatteredHitsAero != None ):
          print "ScatteredHitsAero = " , self.ScatteredHitsAero

          
      if ( self.ScatteredHitsAeroErr == None ):
        self.ScatteredHitsAeroErr = grepPattern( 'GetRichHits                INFO Av. # Rayleigh scattered hits : Aero  = * \S+ \+\- * (\S+) *' , line )
        if ( self.ScatteredHitsAeroErr != None ):
          print "ScatteredHitsAeroErr = " ,  self.ScatteredHitsAeroErr


      if ( self.ScatteredHitsC4F10 == None ):
        self.ScatteredHitsC4F10 = grepPattern( 'GetRichHits                INFO Av. # Rayleigh scattered hits : Aero  = * \S+ \+\- * \S+ * \( * \S+ * \S+\) * Rich1Gas = * (\S+)' , line )
        if ( self.ScatteredHitsC4F10 != None ):
          print "ScatteredHitsC4F10 = " , self.ScatteredHitsC4F10
          
      if ( self.ScatteredHitsC4F10Err == None ):
        self.ScatteredHitsC4F10Err = grepPattern( 'GetRichHits                INFO Av. # Rayleigh scattered hits : Aero  = * \S+ \+\- * \S+ * \( * \S+ * \S+\) * Rich1Gas = * \S+ \+\- * (\S+)' , line )
        if ( self.ScatteredHitsC4F10Err != None ):
          print "ScatteredHitsC4F10Err = " , self.ScatteredHitsC4F10Err

      if ( self.ScatteredHitsCF4 == None ):
        self.ScatteredHitsCF4 = grepPattern( 'GetRichHits                INFO Av. # Rayleigh scattered hits : Aero  = * \S+ \+\- * \S+ * \( * \S+ * \S+\) * Rich1Gas = * \S+ * \+\- * \S+ * \( * \S+ * \S+\) * Rich2Gas = * (\S+)' , line )
        if ( self.ScatteredHitsCF4 != None ):
          print "ScatteredHitsCF4 = " , self.ScatteredHitsCF4
          
      if ( self.ScatteredHitsCF4Err == None ):
        self.ScatteredHitsCF4Err = grepPattern( 'GetRichHits                INFO Av. # Rayleigh scattered hits : Aero  = * \S+ \+\- * \S+ * \( * \S+ * \S+\) * Rich1Gas = * \S+ * \+\- * \S+ * \( * \S+ * \S+\) * Rich2Gas = * \S+ \+\- * (\S+)' , line )
        if ( self.ScatteredHitsCF4Err != None ):
          print "ScatteredHitsCF4Err = " , self.ScatteredHitsCF4Err

#

      if ( self.MCParticleLessHitsAero == None ):
        self.MCParticleLessHitsAero = grepPattern( 'GetRichHits                INFO Av. # MCParticle-less hits    : Aero  = * (\S+)' , line )
        if ( self.MCParticleLessHitsAero != None ):
          print "MCParticleLessHitsAero = " , self.MCParticleLessHitsAero
 
          
      if ( self.MCParticleLessHitsAeroErr == None ):
        self.MCParticleLessHitsAeroErr = grepPattern( 'GetRichHits                INFO Av. # MCParticle-less hits    : Aero  = * \S+ \+\- * (\S+) *' , line )
        if ( self.MCParticleLessHitsAeroErr != None ):
          print "MCParticleLessHitsAeroErr = " ,  self.MCParticleLessHitsAeroErr
          
 
      if ( self.MCParticleLessHitsC4F10 == None ):
        self.MCParticleLessHitsC4F10 = grepPattern( 'GetRichHits                INFO Av. # MCParticle-less hits    : Aero  = * \S+ \+\- * \S+ * \( * \S+ * \S+\) * Rich1Gas = * (\S+)' , line )
        if ( self.MCParticleLessHitsC4F10 != None ):
          print "MCParticleLessHitsC4F10 = " , self.MCParticleLessHitsC4F10
           
      if ( self.MCParticleLessHitsC4F10Err == None ):
        self.MCParticleLessHitsC4F10Err = grepPattern( 'GetRichHits                INFO Av. # MCParticle-less hits    : Aero  = * \S+ \+\- * \S+ * \( * \S+ * \S+\) * Rich1Gas = * \S+ \+\- * (\S+)' , line )
        if ( self.MCParticleLessHitsC4F10Err != None ):
          print "MCParticleLessHitsC4F10Err = " , self.MCParticleLessHitsC4F10Err
 
      if ( self.MCParticleLessHitsCF4 == None ):
        self.MCParticleLessHitsCF4 = grepPattern( 'GetRichHits                INFO Av. # MCParticle-less hits    : Aero  = * \S+ \+\- * \S+ * \( * \S+ * \S+\) * Rich1Gas = * \S+ * \+\- * \S+ * \( * \S+ * \S+\) * Rich2Gas = * (\S+)' , line )
        if ( self.MCParticleLessHitsCF4 != None ):
          print "MCParticleLessHitsCF4 = " , self.MCParticleLessHitsCF4
           
      if ( self.MCParticleLessHitsCF4Err == None ):
        self.MCParticleLessHitsCF4Err = grepPattern( 'GetRichHits                INFO Av. # MCParticle-less hits    : Aero  = * \S+ \+\- * \S+ * \( * \S+ * \S+\) * Rich1Gas = * \S+ * \+\- * \S+ * \( * \S+ * \S+\) * Rich2Gas = * \S+ \+\- * (\S+)' , line )
        if ( self.MCParticleLessHitsCF4Err != None ):
          print "MCParticleLessHitsCF4Err = " , self.MCParticleLessHitsCF4Err
           
 

    f.close()
    
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
  def totalCrossSection(self):
  #### This is the total cross-section printed by Pythia
    return self.TotalCrossSection

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

       # Information is stored in two files: run.log and GeneratorLog.xml
       # will process first run.log 
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
            
        TheLog = GaussLogFile( os.path.join(directory, 'run.log' ))
        TheLog.computeQuantities() 


        self.saveString('GaussVersion',TheLog.gaussVersion())
        self.saveString('PythiaVersion',TheLog.pythiaVersion())
        self.saveString('DDDBVersion',TheLog.dddbVersion())
        self.saveString('SIMCONDVersion',TheLog.simcondVersion())
        self.saveInt('EventType', TheLog.eventType())

        self.saveFloat('signalProcessCrossSection',TheLog.signalProcessCrossSection())
        self.saveFloat('generatorLevelCutEfficiency',TheLog.generatorLevelCutEfficiency())
        self.saveFloat('timePerEvent',TheLog.timePerEvent())

        self.saveString('MCHits',TheLog.MCHitsPerEvent())
        self.saveString('PileUpMCHits',TheLog.PileUpMCHitsPerEvent())
        self.saveFloat('TTHits',TheLog.TTHitsPerEvent())
        self.saveFloat('TTHit_BetaGamma',TheLog.TTHitBetaGamma())
        self.saveFloat('TTHit_DepCharge',TheLog.TTHitDepCharge())
        self.saveFloat('TTHit_HalfSampleWidth',TheLog.TTHitHalfSampleWidth())
        self.saveFloat('ITHits',TheLog.ITHitsPerEvent())
        self.saveFloat('ITHit_BetaGamma',TheLog.ITHitBetaGamma())
        self.saveFloat('ITHit_DepCharge',TheLog.ITHitDepCharge())
        self.saveFloat('ITHit_HalfSampleWidth',TheLog.ITHitHalfSampleWidth())
        self.saveFloat('OTHits',TheLog.OTHitsPerEvent())
        self.saveFloat('OTHit_BetaGamma',TheLog.OTHitBetaGamma())
        self.saveFloat('OTHit_DepCharge',TheLog.OTHitDepCharge())
        self.saveFloat('OTHit_HalfSampleWidth',TheLog.OTHitHalfSampleWidth())

        self.saveInt('VeloPUMCHits',TheLog.NumVeloPUMCHits())
        self.saveInt('MCRichTracks',TheLog.NumMCRichTracks())
        self.saveInt('MCRichSegment',TheLog.NumMCRichSegment())
        self.saveInt('Muon_MCHits',TheLog.NumMuon_MCHits())
        self.saveInt('IT_MCHits',TheLog.NumIT_MCHits())
        self.saveInt('TT_MCHits',TheLog.NumTT_MCHits())
        self.saveInt('Hcal_MCHits',TheLog.NumHcal_MCHits())
        self.saveInt('OT_MCHits',TheLog.NumOT_MCHits())
        self.saveInt('Velo_MCHits',TheLog.NumVelo_MCHits())
        self.saveInt('Rich2_MCHits',TheLog.NumRich2_MCHits())
        self.saveInt('Spd_MCHits',TheLog.NumSpd_MCHits())
        self.saveInt('Rich1_MCHits',TheLog.NumRich1_MCHits())
        self.saveInt('MCParticles',TheLog.NumMCParticles())
        self.saveInt('MCVertices',TheLog.NumMCVertices())
        self.saveInt('Prs_MCHits',TheLog.NumPrs_MCHits())
        self.saveInt('MCRichOpPhoto',TheLog.NumMCRichOpPhoto())
        self.saveInt('Rich_MCHits',TheLog.NumRich_MCHits())
        self.saveInt('Ecal_MCHits',TheLog.NumEcal_MCHits())

        self.saveFloat('R1_M1', TheLog.r1_m1())
        self.saveFloat('R1_M1', TheLog.r1_m2())
        self.saveFloat('R1_M1', TheLog.r1_m3())
        self.saveFloat('R1_M1', TheLog.r1_m4())
        self.saveFloat('R1_M1', TheLog.r1_m5())

        self.saveFloat('R1_M1', TheLog.r2_m1())
        self.saveFloat('R1_M1', TheLog.r2_m2())
        self.saveFloat('R1_M1', TheLog.r2_m3())
        self.saveFloat('R1_M1', TheLog.r2_m4())
        self.saveFloat('R1_M1', TheLog.r2_m5())

        self.saveFloat('R1_M1', TheLog.r3_m1())
        self.saveFloat('R1_M1', TheLog.r3_m2())
        self.saveFloat('R1_M1', TheLog.r3_m3())
        self.saveFloat('R1_M1', TheLog.r3_m4())
        self.saveFloat('R1_M1', TheLog.r3_m5())

        self.saveFloat('R1_M1', TheLog.r4_m1())
        self.saveFloat('R1_M1', TheLog.r4_m2())
        self.saveFloat('R1_M1', TheLog.r4_m3())
        self.saveFloat('R1_M1', TheLog.r4_m4())
        self.saveFloat('R1_M1', TheLog.r4_m5())

        self.saveFloat('InvRichFlags', TheLog.invRichFlags())
        self.saveFloat('InvRichFlagsErr', TheLog.invRichFlagsErr())

        self.saveFloat('MCRichHitsR1', TheLog.mcRichHitsR1())
        self.saveFloat('MCRichHitsR1Err', TheLog.mcRichHitsR1Err())

        self.saveFloat('MCRichHitsR2', TheLog.mcRichHitsR2())
        self.saveFloat('MCRichHitsR2Err', TheLog.mcRichHitsR2Err())

        self.saveFloat('InvRadHitsR1', TheLog.invRadHitsR1())
        self.saveFloat('InvRadHitsR1Err', TheLog.invRadHitsR1Err())

        self.saveFloat('InvRadHitsR2', TheLog.invRadHitsR2())
        self.saveFloat('InvRadHitsR2Err', TheLog.invRadHitsR2Err())

        self.saveFloat('SignalHitsR1', TheLog.signalHitsR1())
        self.saveFloat('SignalHitsR1Err', TheLog.signalHitsR1Err())

        self.saveFloat('SignalHitsR2', TheLog.signalHitsR2())
        self.saveFloat('SignalHitsR2Err', TheLog.signalHitsR2Err())


        self.saveFloat('GasQuartzCKHitsR1', TheLog.gasQuartzCKHitsR1())
        self.saveFloat('GasQuartzCKHitsR1Err', TheLog.gasQuartzCKHitsR1Err())

        self.saveFloat('GasQuartzCKHitsR2', TheLog.gasQuartzCKHitsR2())
        self.saveFloat('GasQuartzCKHitsR2Err', TheLog.gasQuartzCKHitsR2Err())


        self.saveFloat('HPDQuartzCKHitsR1', TheLog.hpdQuartzCKHitsR1())
        self.saveFloat('HPDQuartzCKHitsR1Err', TheLog.hpdQuartzCKHitsR1Err())

        self.saveFloat('HPDQuartzCKHitsR2', TheLog.hpdQuartzCKHitsR1())
        self.saveFloat('HPDQuartzCKHitsR2Err', TheLog.hpdQuartzCKHitsR1Err())

        self.saveFloat('NitrogenCKHitsR1', TheLog.nitrogenCKHitsR1())
        self.saveFloat('NitrogenCKHitsR1Err', TheLog.nitrogenCKHitsR1Err())

        self.saveFloat('NitrogenCKHitsR2', TheLog.nitrogenCKHitsR2())
        self.saveFloat('NitrogenCKHitsR2Err', TheLog.nitrogenCKHitsR2Err())

        self.saveFloat('SignalCKAero', TheLog.signalCKAero())
        self.saveFloat('SignalCKAeroErr', TheLog.signalCKAeroErr())

        self.saveFloat('SignalCKC4F10', TheLog.signalCKC4F10())
        self.saveFloat('SignalCKC4F10Err', TheLog.signalCKC4F10Err())

        self.saveFloat('SignalCKCF4', TheLog.signalCKCF4())
        self.saveFloat('SignalCKCF4Err', TheLog.signalCKCF4Err())

        self.saveFloat('ScatteredHitsAero', TheLog.scatteredHitsAero())
        self.saveFloat('ScatteredHitsAeroErr', TheLog.scatteredHitsAeroErr())

        self.saveFloat('ScatteredHitC4F10', TheLog.scatteredHitsC4F10())
        self.saveFloat('ScatteredHitsC4F10Err', TheLog.scatteredHitsC4F10Err())

        self.saveFloat('ScatteredHitCF4', TheLog.scatteredHitsCF4())
        self.saveFloat('ScatteredHitsCF4Err', TheLog.scatteredHitsCF4Err())

        self.saveFloat('MCParticleLessHitsAero', TheLog.mcParticleLessHitsAero())
        self.saveFloat('MCParticleLessHitsAeroErr', TheLog.mcParticleLessHitsAeroErr())

        self.saveFloat('MCParticleLessHitsC4F10', TheLog.mcParticleLessHitsC4F10())
        self.saveFloat('MCParticleLessHitsC4F10Err', TheLog.mcParticleLessHitsC4F10Err())

        self.saveFloat('MCParticleLessHitsCF4', TheLog.mcParticleLessHitsCF4())
        self.saveFloat('MCParticleLessHitsCF4Err', TheLog.mcParticleLessHitsCF4Err())

        #The following info are present in run.log until XXX gauss version
        totalCrossSection = TheLog.totalCrossSection()        
        if( totalCrossSection != None ) :
          self.saveFloat('totalCrossSection',totalCrossSection)                    
          self.saveFloat('bCrossSection', TheLog.bCrossSection())
          self.saveFloat('cCrossSection',TheLog.cCrossSection())
          self.saveFloat('promptCharmCrossSection',TheLog.promptCharmCrossSection())
          self.saveFloat('totalAcceptedEvents',TheLog.totalAcceptedEvents())
          self.saveFloat('signalProcessFromBCrossSection',TheLog.signalProcessFromBCrossSection())
        
        
        #Now GeneratorLog.xml
        
        tree = ElementTree()
        
        try:
          tree.parse('GeneratorLog.xml')
        except ExpatError:
          return False
        except IOError:
          return False

        root = tree.getroot() 
        for counter in root.findall('counter'):
          value = counter.find('value').text
          name = counter.get('name')
          print name, value
          #save all values in the json file
          self.saveInt(name, value)
          #save some values in local variables to compute quantities of interest already at this stage
          if name == "generated interactions"  :
            TotalInteractions = value
          if name == "generated interactions with >= 1b" :
            TotalIntWithB = value
          if name ==  "generated interactions with >= prompt C" :
            TotalIntWithPromptCharm = value
          if name == "generated interactions with >= 1c" :
            TotalIntWithD = value
          if name == "accepted events" :
            TotalAcceptedEvents = value
          if name == "accepted events" :
            TotalSignalProcessEvents = value            
          if name == "accepted interactions with >= 1b" :
            TotalSignalProcessFromBEvents = value

          
        for crosssection in root.findall('crosssection'):
           description = crosssection.find('description').text
           generated = crosssection.find('generated').text
           value = crosssection.find('value').text
           id = crosssection.get('id')
           self.saveFloat(description, value)
           if id == '0' : 
             print id, description, generated, value
             TotalCrossSection = value
             self.saveFloat('totalCrossSection',value)

        #### b quark or B hadron without b quark from production vertex
        bCrossSection = float( float(TotalCrossSection) * int(TotalIntWithB) / int(TotalInteractions))   
        self.saveFloat('bCrossSection', bCrossSection)

        #### c quark or D hadron without c quark from production vertex
        cCrossSection =  float( float(TotalCrossSection) * int(TotalIntWithD) / int(TotalInteractions))
        self.saveFloat('cCrossSection',cCrossSection)

        #### D hadron (like J/psi but also chi_c) without B hadron or c quark
        promptCharmCrossSection = float( float(TotalCrossSection) * int(TotalIntWithPromptCharm) / int(TotalInteractions))
        self.saveFloat('promptCharmCrossSection', promptCharmCrossSection)

        self.saveFloat('totalAcceptedEvents',TotalAcceptedEvents)

        #### valid for J/psi (in general for all generation without CP mixture)
        signalProcessFromBCrossSection = float( float(TotalCrossSection) * int(TotalSignalProcessFromBEvents) / int(TotalInteractions))
        self.saveFloat('signalProcessFromBCrossSection',signalProcessFromBCrossSection)
