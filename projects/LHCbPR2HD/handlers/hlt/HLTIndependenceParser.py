#!/usr/bin/env python

from pyparsing import *
import operator

# Common literals and words
NL = Suppress(LineEnd())
slit = lambda x: Suppress(Literal(x))
plus  = slit("+")
minus = slit("-")
pipe  = slit("|")
kHz   = slit("kHz")
lb    = slit("(")
rb    = slit(")")
eq    = slit("=")
sc    = slit(":")
nbwitherr = Word(nums + '.') + plus + minus + Word(nums + '.')

def getPropertyMatcher(name, valType=None):
    """ Returns pyparsing structure to match a line:
    Turbo rate = 0.01 kHz
    or
    Hlt2Global rate = (30.0+-17.0587221092)kHz
    """
    expr = literalMatcher(name)
    return expr + valType + Suppress(restOfLine)

def getNbMatcher(name):
    """ Return a a pyparsing structure matching a number,
    with the name associated
    """
    return Word(nums + ".").setResultsName(name)

def literalMatcher(sentence):
    ltokens =  [Suppress(Literal(l))
                for l in sentence.split(" ")
                if l != ""]
    return reduce(operator.add, ltokens,Empty())

def getParser():
    
    # Preparing the header
    ###############################################################
    commentL = LineStart() + Suppress(Literal("-")) + restOfLine
    gpm = lambda x: getPropertyMatcher("%s = " %x, getNbMatcher(x))
    headerL = literalMatcher("all jobs completed")
    completedL = gpm("completed")
    requestedL = gpm("requested")
    processedL = getPropertyMatcher("processed ",  \
                                    getNbMatcher("processed") \
                                    + Suppress(Literal("events")))
    nomismatchL = getPropertyMatcher("No mismatches found in ",  \
                                    getNbMatcher("nomismatch"))
    
    header = [ Suppress(headerL),
               completedL,
               requestedL,
               processedL,
               nomismatchL]

    # Parser for the table
    ###############################################################
    
    tHeadL = Group(Literal("Line:") + restOfLine).suppress()
    tRowL = OneOrMore(Group(Word(nums) + sc
                            + Word(alphanums + "_:&") 
                            + pipe + Word(nums) + Word(nums)
                            + Word(nums) + Word(nums)))

    table = [ commentL
              + tHeadL
              + commentL
              + tRowL.setResultsName("HLT1LineStats")
              + commentL]

    # Assemble grammar
    ###############################################################
    bnf = reduce(operator.add, header + table , Empty())
    return bnf


def parseHLTIndependenceTable(logtxt):
    """ Tool to parse the HLT rates table"""
    grammar = getParser()
    result = grammar.parseString(logtxt)
    return dict(result)


## This parser should match a text like the following
testText = """
all jobs completed
completed = 35
requested = 35
processed 9 events
No mismatches found in 9
----------------------------------------------------------------------------
Line:                               |All(A)      Single(S)   A!S         S!A
----------------------------------------------------------------------------
1:Hlt1DiProton:                     |1           1           0           0
2:Hlt1B2HH_LTUNB_KK:                |0           0           0           0
3:Hlt1TrackMVA:                     |4           4           0           0
4:Hlt1CalibTrackingKPi:             |0           0           0           0
5:Hlt1SingleElectronNoIP:           |0           0           0           0
6:Hlt1TrackMuon:                    |1           1           0           0
7:Hlt1CalibTrackingKPiDetached:     |0           0           0           0
8:Hlt1CalibRICHMirrorRICH1:         |0           0           0           0
9:Hlt1L0AnyNoSPD:                   |0           0           0           0
10:Hlt1CalibMuonAlignJpsi:          |0           0           0           0
11:Hlt1CalibRICHMirrorRICH2:        |0           0           0           0
12:Hlt1B2HH_LTUNB_KPi:              |0           0           0           0
13:Hlt1B2PhiPhi_LTUNB:              |0           0           0           0
14:Hlt1TrackMuonNoSPD:              |0           0           0           0
15:Hlt1LowMultVeloCut_Hadrons:      |1           1           0           0
16:Hlt1LowMultMaxVeloCut:           |0           0           0           0
17:Hlt1TwoTrackMVA:                 |2           2           0           0
18:Hlt1IncPhi:                      |0           0           0           0
19:Hlt1MultiMuonNoL0:               |0           0           0           0
20:Hlt1DiMuonNoL0:                  |0           0           0           0
21:Hlt1SingleMuonHighPT:            |0           0           0           0
22:Hlt1B2PhiGamma_LTUNB:            |0           0           0           0
23:Hlt1NoBiasNonBeamBeam:           |0           0           0           0
24:Hlt1LowMultVeloCut_Leptons:      |2           2           0           0
25:Hlt1CalibHighPTLowMultTrks:      |5           5           0           0
26:Hlt1B2HH_LTUNB_PiPi:             |0           0           0           0
27:Hlt1DiMuonLowMass:               |0           0           0           0
28:Hlt1LowMult:                     |4           4           0           0
29:Hlt1DiProtonLowMult:             |0           0           0           0
30:Hlt1B2GammaGamma:                |0           0           0           0
31:Hlt1SingleMuonNoIP:              |1           1           0           0
32:Hlt1CalibTrackingKK:             |0           0           0           0
33:Hlt1CalibTrackingPiPi:           |0           0           0           0
34:Hlt1DiMuonHighMass:              |0           0           0           0
----------------------------------------------------------------------------
removed lines: ['Hlt1BeamGasCrossingForcedReco', 'Hlt1MBNoBiasRateLimited', 'Hlt1Tell1Error', 'Hlt1BeamGasCrossingEnhancedBeam1', 'Hlt1BeamGasCrossingEnhancedBeam2', 'Hlt1BeamGasBeam2', 'Hlt1BeamGasBeam1', 'Hlt1ODINTechnical', 'Hlt1BeamGasCrossingParasitic', 'Hlt1VeloClosingMicroBias', 'Hlt1BeamGasNoBeamBeam1', 'Hlt1BeamGasNoBeamBeam2', 'Hlt1Global', 'Hlt1MBNoBias', 'Hlt2PassThrough', 'Hlt1L0Any', 'Hlt1BeamGasCrossingForcedRecoFullZ', 'Hlt2Global', 'Hlt1Lumi', 'Hlt1BeamGasHighRhoVertices', 'Hlt1ErrorEvent', 'Hlt1LowMultPassThrough']
"""
