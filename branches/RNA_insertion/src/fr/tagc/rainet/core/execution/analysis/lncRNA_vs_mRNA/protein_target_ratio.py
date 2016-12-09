import sys
import os
import argparse

import scipy.stats as stats
import numpy
# import pandas as pd

from fr.tagc.rainet.core.util.exception.RainetException import RainetException
from fr.tagc.rainet.core.util.log.Logger import Logger
from fr.tagc.rainet.core.util.time.Timer import Timer

from statsmodels.stats.multitest import multipletests

# from fr.tagc.rainet.core.util.subprocess.SubprocessUtil import SubprocessUtil
# from fr.tagc.rainet.core.util.sql.SQLManager import SQLManager
# from fr.tagc.rainet.core.util.data.DataManager import DataManager

# from fr.tagc.rainet.core.data.Protein import Protein

#===============================================================================
# Started 29-Nov-2016 
# Diogo Ribeiro
DESC_COMMENT = "Script to analyse for each protein, the amount and ratio between lncRNA and mRNA targets"
SCRIPT_NAME = "protein_target_ratio.py"
#===============================================================================

#===============================================================================
# General plan:
# 1)
# 2)
#===============================================================================

#===============================================================================
# Processing notes:
# 1)
# 2)
#===============================================================================

SIGN_VALUE_TEST = 0.05

# #
def read_transcript_types( transcriptTypesFile):

    # Example format
    # "ENST00000000412","protein_coding","MRNA"
    # "ENST00000000442","protein_coding","MRNA"

    transcriptType = {} # key -> transcriptID, value -> type

    with open( transcriptTypesFile, "r") as inFile:
        for line in inFile:
            spl = line.strip().split(",")
            transcriptID = spl[0].replace('"','')
            type = spl[2].replace('"','')
            
            transcriptType[ transcriptID] = type
    
    print "read_transcript_types: Collected types of %s transcripts" % len( transcriptType)

    return transcriptType

# #
def read_interaction_file( interactionFile, transcriptType, outputFile):
   
    # Example format 
    # sp|O00425|sp ENST00000217233    1

    typeStats = {} # key -> proteinID, value -> dict. Key -> target type, value -> count

    proteinSet = set()
    transcriptSet = set()
    transcriptSetType = {} # key -> type, value -> set of transcripts

    # stores targets for which we do not know the biotype
    missingTargets = set()

    countLines = 0

    with open( interactionFile, "r") as inFile:
        for line in inFile:
            spl = line.split(" ")

            countLines+= 1 

            if countLines % 10000000 == 0:
                print "Processed %s interactions" % countLines
                           
            proteinID = spl[0].split( "|")[1]
            spl2 = spl[1].split( "\t")
            transcriptID = spl2[0]
            intScore = float( spl2[1])
            
            # get transcript type
            if transcriptID in transcriptType:
                txType = transcriptType[ transcriptID]
            else:
                # if not found, skip
                missingTargets.add( transcriptID)
                continue
    
            if proteinID not in typeStats:
                typeStats[ proteinID] = {}
            
            if txType not in typeStats[ proteinID]:
                typeStats[ proteinID][ txType] = 0
                
            if txType not in transcriptSetType:
                transcriptSetType[ txType] = set()
                
            transcriptSetType[ txType].add( transcriptID)

            # increment according to target type
            typeStats[ proteinID][ txType] += 1

            proteinSet.add(proteinID)
            transcriptSet.add( transcriptID)

    print "read_interaction_file: %s unique proteins" % len(proteinSet)
    print "read_interaction_file: %s unique transcripts" % len(transcriptSet)
    print "read_interaction_file: %s target with biotype not found" % len(missingTargets)

    ### report on transcript types
    
    for type in transcriptSetType:
        print type, len( transcriptSetType[ type])
    
    ### write output file

    outFile = open( outputFile,"w")

    outFile.write("proteinID\tn_mRNA\tn_lncRNA\tratio_mRNA_lncRNA\tfisher_odds\tfisher_pval\tcorrected_pval\tsignificant\n")

    
    pvalues = [] # stored pvalues for multiple test correction
    dataStore = [] # store data for writing after pvalue correction

    for protID in typeStats:
                
        if "MRNA" in typeStats[ protID]:
            nMRNA = typeStats[ protID]["MRNA"]
        else:
            nMRNA = 0
        
        if "LncRNA" in typeStats[ protID]:
            nLNCRNA = typeStats[ protID]["LncRNA"] 
        else:
            nLNCRNA = 0
        
        if nLNCRNA > 0:
            ratio = "%.2f" % ( float(nMRNA) / nLNCRNA)
        else:
            ratio = "NA"

        ## fisher exact test
        # Our question: does the protein preferentially bind mRNA or bind lncRNA? with which significance?
        # Contigency table:
        #         interacting    non_interacting
        # lncRNA    nLNCRNA    transcriptSetType["LNCRNA"] - nLNCRNA
        # mRNA    nMRNA    transcriptSetType["MRNA"] - nMRNA

        nonInteractingLNCRNA = len( transcriptSetType["LncRNA"]) - nLNCRNA
        nonInteractingMRNA = len( transcriptSetType["MRNA"]) - nMRNA

        matrix = [[nLNCRNA, nonInteractingLNCRNA], [nMRNA, nonInteractingMRNA]]
        
        oddsRatio, pvalue = fisher_exact_test(matrix)
        
        #outFile.write( "%s\t%s\t%s\t%s\t%.2f\t%.1e\n" % ( protID, nMRNA, nLNCRNA, ratio, oddsRatio, pvalue) )
        
        dataStore.append( [protID, nMRNA, nLNCRNA, ratio, oddsRatio, pvalue])
        
        pvalues.append( pvalue)

    # pvalue correction
    processedData = correct_pvalues( len( dataStore), pvalues, dataStore)
    
    # writing to file
    for item in processedData:
        outFile.write( "%s\t%s\t%s\t%s\t%.2f\t%.1e\t%s\t%s\n" % ( item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7]) )

    outFile.close()


# #
# Function to correct pvalues, and add correction and significance to provided 'tests' list
def correct_pvalues( nTests, pvalues, tests):
    
    testsCorrected = numpy.empty(nTests, object)  # stores data plus correction
     
    correctedPvalues = multiple_test_correction(pvalues)
    
    assert (len(pvalues) == len(correctedPvalues))

    # Correction of test selection, by ranking original pvalues, apply correction, 
    # select all the original p-values below the first where corrected pvalue is below our threshold

    # sort pvalues and keep index        
    sortedPvalues = sorted(pvalues, reverse=True)
    sortedPvaluesIdx = sorted(xrange(len(pvalues)), reverse=True, key=lambda k: pvalues[ k])

    # correspondece of pvalues -> corrected pvalues of the sorted pvalues array
    correctedPvaluesOfSorted = [ correctedPvalues[ idx]  for idx in sortedPvaluesIdx]

    # stores list of indexes deemed significant with our own selection of rejected values from 
    significantIndexes = []

    # find the first corrected pvalue below our threshold, and pick all the original pvalues on the sorted array as accepted            
    for i in xrange(len(sortedPvalues)):
        if correctedPvaluesOfSorted[ i] < SIGN_VALUE_TEST:
            significantIndexes = sortedPvaluesIdx[ i: ]
            break

    for i in xrange(0, len(tests)):
        l = tests[i][:]

        # add corrected pvalue to existing list
        corr = "%.1e" % correctedPvalues[i]
        l.append(corr)

        # significative result tag
        sign = "0"
        if i in significantIndexes:
            sign = "1"

        # add sign tag to existing list
        l.append(sign)

        # append current list to list of RNA vs annotation
        testsCorrected[ i] = l

    return testsCorrected


# #
# Perform fishers exact test using scipy
def fisher_exact_test( matrix):

    # equivalent of doing in R:    
    # fisher.test( matrix(c(8, 2, 1, 5), nrow = 2), alternative = "two.sided")

    oddsRatio, pvalue = stats.fisher_exact( matrix, alternative = "two-sided")
    
    return oddsRatio, pvalue


# #
# Run multipletest correction and return pvalues
def multiple_test_correction(pvalues, meth="fdr_bh"):
    return multipletests(pvalues, method=meth)[1]


if __name__ == "__main__":

    try:
    
        # Start chrono
        Timer.get_instance().start_chrono()
        print "STARTING " + SCRIPT_NAME
        
        #===============================================================================
        # Get input arguments
        #===============================================================================
        parser = argparse.ArgumentParser(description= DESC_COMMENT) 
    
        # positional args
        parser.add_argument('interactionFile', metavar='interactionFile', type=str,
                             help='Catrapid interactions file.')
        parser.add_argument('transcriptTypesFile', metavar='transcriptTypesFile', type=str,
                             help='RAINET DB RNA table dump. E.g. "ENST00000001146","protein_coding","MRNA"')
        parser.add_argument('outputFile', metavar='outputFile', type=str,
                             help='Output file path/')
           
        #gets the arguments
        args = parser.parse_args( ) 
    
        #===============================================================================
        # Run analysis / processing
        #===============================================================================

        Timer.get_instance().step( "Read transcript types file..")            
        transcriptType = read_transcript_types( args.transcriptTypesFile)

        Timer.get_instance().step( "Read interaction file..")            
        read_interaction_file( args.interactionFile, transcriptType, args.outputFile)

        # Stop the chrono      
        Timer.get_instance().stop_chrono( "FINISHED " + SCRIPT_NAME )

    # Use RainetException to catch errors
    except RainetException as rainet:
        Logger.get_instance().error( "Error during execution of %s. Aborting :\n" % SCRIPT_NAME + rainet.to_string())
