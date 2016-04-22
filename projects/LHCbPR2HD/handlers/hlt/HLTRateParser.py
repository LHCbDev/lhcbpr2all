#!/usr/bin/env python

from pyparsing import *

# Common literals and words 
NL = LineEnd().suppress()
plus  = Literal("+").suppress()
minus = Literal("-").suppress()
pipe  = Literal("|").suppress()
kHz = Literal("kHz").suppress()
lb = Literal("(").suppress()
rb = Literal(")").suppress()
eq = Literal("=").suppress()
nbwitherr = Word(nums + '.') + plus + minus + Word(nums + '.')

def getPropertyMatcher(name, valType=None):
    """ Returns pyparsing structure to match a line:
    Turbo rate = 0.01 kHz
    or
    Hlt2Global rate = (30.0+-17.0587221092)kHz
    """
    expr = literalMatcher(name)
    return expr + valType + Suppress(restOfLine)

def literalMatcher(sentence):
    tokens = sentence.split(" ")
    ltokens =  [Suppress(Literal(l)) for l in tokens if l != ""]
    expr = None
    for l in ltokens:
        if expr == None:
            expr = l
        else:
            expr += l
    return expr

def getHLTRateParser():
    
    # Preparing the header
    commentLine = LineStart() + Suppress(Literal("-")) + restOfLine
    headerLine = restOfLine
    header = Optional(ZeroOrMore("-")) \
             + literalMatcher("HLT rates summary starts here") \
             + Optional(ZeroOrMore("-")) 
    trailer = Optional(ZeroOrMore("-")) \
             + literalMatcher("HLT rates summary ends here") \
             + Optional(ZeroOrMore("-")) 
    removedLines = Literal("removed").suppress() \
                   + Literal("lines").suppress() + restOfLine.suppress()
    nbevents = Literal("processed:").suppress() \
               + Word(nums).setResultsName("nbevents")

    getLinesnbMatcher = lambda x: Word(nums).setResultsName(x) \
                        + Literal(x).suppress()
    hlt1Lines = getLinesnbMatcher("Hlt1Lines") 
    hlt2Lines = getLinesnbMatcher("Hlt2Lines")
    linesSep = Group(Literal("|**|*Line*") + restOfLine).suppress()
    lineslist = OneOrMore(Group(pipe + Word(nums) + pipe + Word(alphanums + "_:&") \
                                + pipe + nbwitherr + pipe + nbwitherr + pipe))
    
    
    # Assemble grammar
    bnf = Suppress(header) + removedLines + nbevents \
        + hlt1Lines + hlt2Lines \
        + getPropertyMatcher("Hlt1Global rate =", lb \
                             + nbwitherr.setResultsName("Hlt1GlobalRate") + rb) \
        + getPropertyMatcher("Hlt2Global rate =", lb \
                             + nbwitherr.setResultsName("Hlt2GlobalRate") + rb) \
        + getPropertyMatcher("Turbo rate = ", Word(nums + ".").setResultsName("TurboRate")) \
        + getPropertyMatcher("Full rate = ", Word(nums + ".").setResultsName("FullRate")) \
        + getPropertyMatcher("Turcal rate =", Word(nums + ".").setResultsName("TurcalRate")) \
        + linesSep \
        + lineslist.setResultsName("Hlt1Stats") \
        + linesSep \
        + lineslist.setResultsName("Hlt2Stats") \
        + literalMatcher("Hlt1 rates OK") \
        + literalMatcher("Hlt2 rates OK") \
        + trailer
    
    return bnf

def parseHLTRateList(logtxt):
    """ Tool to parse the HLT rates table"""
    grammar = getHLTRateParser()
    result = grammar.parseString(logtxt)
    return dict(result)

