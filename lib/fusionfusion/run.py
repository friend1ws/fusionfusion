#! /usr/bin/env python

import sys, os, argparse, subprocess
import parseJunctionInfo
import filterJunctionInfo
import annotationFunction
import utils

# import config
from config import *

def cluster_filter_junction(inputFilePath, outputFilePrefix, args):

    # debug_mode = config.param_conf.getboolean("debug", "debug_mode")
    debug_mode = param_conf.debug

    parseJunctionInfo.clusterJuncInfo(inputFilePath,
                                      outputFilePrefix + ".chimeric.clustered.txt")

    filterJunctionInfo.filterCoverRegion(outputFilePrefix + ".chimeric.clustered.txt",
                                         outputFilePrefix + ".chimeric.clustered.filt1.txt")
    
    filterJunctionInfo.extractSplicingPattern(outputFilePrefix + ".chimeric.clustered.filt1.txt", 
                                              outputFilePrefix + ".chimeric.clustered.splicing.txt")

    ############
    filterJunctionInfo.makeJucSeqPairFa(outputFilePrefix + ".chimeric.clustered.splicing.txt",
                                        outputFilePrefix + ".chimeric.clustered.splicing.contig.fa")

    # alignment of contigs generated by manual assembly
    # blat_path = config.param_conf.get("alignment", "blat_path")
    # blat_options = config.param_conf.get("alignment", "blat_option").split(" ")
    # reference_genome = config.param_conf.get("alignment", "reference_genome")
    blat_path = "blat"
    blat_options = ["-stepSize=5", "-repMatch=2253"]
    reference_genome = param_conf.reference_genome

    FNULL = open(os.devnull, 'w')
    fRet = subprocess.call([blat_path] + blat_options + [reference_genome, 
                            outputFilePrefix + ".chimeric.clustered.splicing.contig.fa",
                            outputFilePrefix + ".chimeric.clustered.splicing.contig.psl"], stdout = FNULL, stderr = subprocess.STDOUT)

    FNULL.close()
    if fRet != 0:
        print >> sys.stderr, "blat error, error code: " + str(fRet)
        sys.exit()

    filterJunctionInfo.checkMatching(outputFilePrefix + ".chimeric.clustered.splicing.contig.psl",
                                     outputFilePrefix + ".chimeric.clustered.splicing.contig.check.txt")

    filterJunctionInfo.filterContigCheck(outputFilePrefix + ".chimeric.clustered.splicing.txt",
                                         outputFilePrefix + ".chimeric.clustered.filt2.txt",
                                         outputFilePrefix + ".chimeric.clustered.splicing.contig.check.txt")

    annotationFunction.filterAndAnnotation(outputFilePrefix + ".chimeric.clustered.filt2.txt",
                                           outputFilePrefix + ".fusion.result.txt")

    # delete intermediate files
    if debug_mode == False:
        subprocess.call(["rm", outputFilePrefix + ".chimeric.clustered.txt"])
        subprocess.call(["rm", outputFilePrefix + ".chimeric.clustered.filt1.txt"])
        subprocess.call(["rm", outputFilePrefix + ".chimeric.clustered.filt2.txt"])
        subprocess.call(["rm", outputFilePrefix + ".chimeric.clustered.splicing.txt"])
        subprocess.call(["rm", outputFilePrefix + ".chimeric.clustered.splicing.contig.fa"])
        subprocess.call(["rm", outputFilePrefix + ".chimeric.clustered.splicing.contig.psl"])
        subprocess.call(["rm", outputFilePrefix + ".chimeric.clustered.splicing.contig.check.txt"])


def main(args):

    starBamFile = args.star
    ms2BamFile = args.ms2
    th2BamFile = args.th2
    output_dir = args.out

    if starBamFile == None and ms2BamFile  == None and th2BamFile == None:
        print >> sys.stderr, "At least one of --star, --ms2 or --th2 should be included"
        sys.exit(1)
 
    # config.param_conf.read(args.param)
    # debug_mode = config.param_conf.getboolean("debug", "debug_mode")

    ##########
    # set parameters
    param_conf.reference_genome = args.reference_genome
    param_conf.resource_dir = args.resource_dir
    param_conf.debug = args.debug
    param_conf.abnormal_insert_size = args.abnormal_insert_size
    param_conf.min_major_clipping_size = args.min_major_clipping_size
    param_conf.min_read_pair_num = args.min_read_pair_num
    param_conf.min_valid_read_pair_ratio = args.min_valid_read_pair_ratio
    param_conf.min_cover_size = args.min_cover_size
    param_conf.anchor_size_thres = args.anchor_size_thres
    param_conf.min_chimeric_size = args.min_chimeric_size
    param_conf.min_allowed_contig_match_diff = args.min_allowed_contig_match_diff
    param_conf.check_contig_size_other_breakpoint = args.check_contig_size_other_breakpoint
    param_conf.filter_same_gene = args.filter_same_gene
    ##########

    debug_mode = param_conf.debug

    ####################
    # make direcotry
    utils.make_directory(output_dir)
    ####################


    ####################
    # parsing chimeric reads from bam files
    if starBamFile is not None:

        parseJunctionInfo.parseJuncInfo_STAR(starBamFile, output_dir + "/star.chimeric.tmp.txt")
                                             

        hOUT = open(output_dir + "/star.chimeric.txt", "w")
        subprocess.call(["sort", "-k1,1", "-k2,2n", "-k4,4", "-k5,5n", output_dir + "/star.chimeric.tmp.txt"], stdout = hOUT)
        hOUT.close()

        cluster_filter_junction(output_dir + "/star.chimeric.txt", output_dir + "/star", args)

        if debug_mode == False:
            subprocess.call(["rm", output_dir + "/star.chimeric.tmp.txt"])
            subprocess.call(["rm", output_dir + "/star.chimeric.txt"])

    if ms2BamFile is not None:

        parseJunctionInfo.extractFusionReads_ms2(ms2BamFile, output_dir + "/ms2.chimeric.tmp.sam")

        hOUT = open(output_dir + "/ms2.chimeric.sam", "w")
        subprocess.call(["sort", "-k1", output_dir + "/ms2.chimeric.tmp.sam"], stdout = hOUT)
        hOUT.close()
    
        parseJunctionInfo.parseJuncInfo_ms2(output_dir + "/ms2.chimeric.sam", output_dir + "/ms2.chimeric.tmp.txt", args.abnormal_insert_size) 

        hOUT = open(output_dir + "/ms2.chimeric.txt", "w")
        subprocess.call(["sort", "-k1,1", "-k2,2n", "-k4,4", "-k5,5n", output_dir + "/ms2.chimeric.tmp.txt"], stdout = hOUT)
        hOUT.close()

        cluster_filter_junction(output_dir + "/ms2.chimeric.txt", output_dir + "/ms2", args)

        if debug_mode == False:
            subprocess.call(["rm", output_dir + "/ms2.chimeric.tmp.sam"])
            subprocess.call(["rm", output_dir + "/ms2.chimeric.sam"])
            subprocess.call(["rm", output_dir + "/ms2.chimeric.tmp.txt"])
            subprocess.call(["rm", output_dir + "/ms2.chimeric.txt"])


    if th2BamFile is not None:

        parseJunctionInfo.extractFusionReads_th2(th2BamFile, output_dir + "/th2.chimeric.tmp.sam")

        hOUT = open(output_dir + "/th2.chimeric.sam", "w")
        subprocess.call(["sort", "-k1", output_dir + "/th2.chimeric.tmp.sam"], stdout = hOUT)
        hOUT.close()
        parseJunctionInfo.parseJuncInfo_th2(output_dir + "/th2.chimeric.sam", output_dir + "/th2.chimeric.tmp.txt", args.abnormal_insert_size)
        
        hOUT = open(output_dir + "/th2.chimeric.txt", "w")
        subprocess.call(["sort", "-k1,1", "-k2,2n", "-k4,4", "-k5,5n", output_dir + "/th2.chimeric.tmp.txt"], stdout = hOUT)
        hOUT.close()

        cluster_filter_junction(output_dir + "/th2.chimeric.txt", output_dir + "/th2", args)

        if debug_mode == False:
            subprocess.call(["rm", output_dir + "/th2.chimeric.tmp.sam"])
            subprocess.call(["rm", output_dir + "/th2.chimeric.sam"])
            subprocess.call(["rm", output_dir + "/th2.chimeric.tmp.txt"])
            subprocess.call(["rm", output_dir + "/th2.chimeric.txt"])


    annotationFunction.merge_fusion_result(output_dir, 
                                           output_dir + "/fusion_fusion.result.txt")

    
