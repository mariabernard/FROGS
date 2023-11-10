#!/usr/bin/env python3
#
# Copyright (C) 2018 INRA
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

__author__ = 'Olivier Rué & Vincent Darbot - FROGS team'
__copyright__ = 'Copyright (C) 2023 INRAE'
__license__ = 'GNU General Public License'
__version__ = '5.0'
__email__ = 'frogs-support@inrae.fr'
__status__ = 'dev'

import re
import os
import sys
import gzip
import json
import shutil
import tarfile
import argparse
import threading
import multiprocessing

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# PATH
BIN_DIR = os.path.abspath(os.path.join(os.path.dirname(CURRENT_DIR), "libexec"))
os.environ['PATH'] = BIN_DIR + os.pathsep + os.environ['PATH']
# PYTHONPATH
LIB_DIR = os.path.abspath(os.path.join(os.path.dirname(CURRENT_DIR), "lib"))
sys.path.append(LIB_DIR)
if os.getenv('PYTHONPATH') is None: os.environ['PYTHONPATH'] = LIB_DIR
else: os.environ['PYTHONPATH'] = LIB_DIR + os.pathsep + os.environ['PYTHONPATH']

from frogsUtils import *
from frogsSequenceIO import *
from frogsBiom import Biom, BiomIO

##################################################################################################################################################
#
# COMMAND LINES
#
##################################################################################################################################################
class HClassification(Cmd):
    """
    @summary: Hierarchical classification on observation proportions.
    """
    def __init__(self, in_biom, out_newick, out_log, dist_method, linkage_method):
        """
        @param in_biom: [str] The processed BIOM path.
        @param out_newick: [str] The path to the output.
        @param out_log: [str] The path to the execution log.
        @param dist_method: [str] The distance method used.
        @param linkage_method: [str] The linkage method used.
        """
        self.exec_log = out_log
        Cmd.__init__( self,
                      'biomTools.py',
                      'Hierarchical classification on observation proportions.',
                      'hclassification --distance-method ' + dist_method + ' --linkage-method ' + linkage_method + ' --input-file ' + in_biom + ' --output-file ' + out_newick + ' > ' + out_log,
                      '--version' )

    def parser(self, log_file):
        """
        @summary : Parse the command results to add information in log_file.
        @log_file : [str] Path to the sample process log file.
        """
        excluded_exists = False

        # Parse execution log
        warning_lines = list()
        FH_exec_log = open( self.exec_log )
        for line in FH_exec_log:
            if line.strip() != "" and not line.startswith("#"):
                warning_lines.append(line.strip())
                if "xcluded samples" in line:
                    excluded_exists = True
        FH_exec_log.close()

        # Write warning (if at least one sample has been excluded)
        if excluded_exists:
            FH_log = Logger( log_file )
            FH_log.write( 'Warning:\n' )
            for line in warning_lines:
                FH_log.write( '\t' + line + '\n' )
            FH_log.close()
            
    def get_version(self):   
        return Cmd.get_version(self, 'stdout').strip()            


class Depths(Cmd):
    """
    @summary: Writes by abundance the number of clusters.
    """
    def __init__(self, in_biom, out_tsv):
        """
        @param in_biom: [str] The processed BIOM path.
        @param out_tsv: [str] The path of the output.
        """
        Cmd.__init__( self,
                      'biomTools.py',
                      'Writes by abundance the number of clusters.',
                      'obsdepth --input-file ' + in_biom + ' --output-file ' + out_tsv,
                      '--version' )

    def get_version(self):   
        return Cmd.get_version(self, 'stdout').strip()          
        
class ExtractSwarmsFasta(Cmd):
    """
    @summary: Extracts seeds sequences to produce the seeds fasta.
    """
    def __init__(self, in_fasta, in_swarms, out_seeds_file):
        """
        @param in_fasta: [str] Path to the input fasta file.
        @param in_swarms: [str] Path to swarm output file. It describes which reads compose each swarm.
        @param out_seeds_file: [str] Path to the output fasta file.
        """
        Cmd.__init__( self,
                      'extractSwarmsFasta.py',
                      'Extracts seeds sequences to produce the seeds fasta.',
                      '--input-fasta ' + in_fasta + ' --input-swarms ' + in_swarms + ' --output-fasta ' + out_seeds_file,
                      '--version' )

    def get_version(self):
        """
        @summary: Returns the program version number.
        @return: [str] Version number if this is possible, otherwise this method return 'unknown'.
        """
        return Cmd.get_version(self, 'stdout').strip()
        
class Swarm2Biom(Cmd):
    """
    @summary: Converts swarm results in BIOM file.
    """
    def __init__(self, in_swarms, in_count, out_biom):
        """
        @param in_swarms: [str] Path to swarm output file. It describes which reads compose each swarm.
        @param in_count: [str] Path to the count file. It contains the count by sample for each representative sequence.
        @param out_biom: [str] Path to the output BIOM.
        """
        Cmd.__init__( self,
                      'swarm2biom.py',
                      'Converts swarm output to abundance file (format BIOM).',
                      "--clusters-file " + in_swarms + " --count-file " + in_count + " --output-file " + out_biom,
                      '--version' )
    
    def get_version(self):
        """
        @summary: Returns the program version number.
        @return: [str] Version number if this is possible, otherwise this method return 'unknown'.
        """
        return Cmd.get_version(self, 'stdout').strip()
        
class Swarm(Cmd):
    """
    @summary: Sequences clustering.
    @see: https://github.com/torognes/swarm
    """
    def __init__(self, in_fasta, out_swarms, out_log, distance, fastidious_opt, nb_cpus):
        """
        @param in_fasta: [str] Path to fasta file to process.
        @param out_swarms: [str] Path to swarm output file. It describes which reads compose each swarm.
        @param out_log: [str] Path to swarm log file.
        @param distance: [int] The 'param.distance'
        @param nb_cpus : [int] 'param.nb_cpus'.
        """
        opt = ' --fastidious ' if fastidious_opt else ''
        Cmd.__init__( self,
                      'swarm',
                      'Clustering sequences.',
                      "--differences " + str(distance) + opt + " --threads " + str(nb_cpus) + " --log " + out_log + " --output-file " + out_swarms + " " + in_fasta,
                      '--version' )

    def get_version(self):
        """
        @summary: Returns the program version number.
        @return: [str] Version number if this is possible, otherwise this method return 'unknown'.
        """
        return Cmd.get_version(self, 'stderr').split()[1]

class SortFasta(Cmd):
    """
    @summary: Sort dereplicated sequences by decreasing abundance.
    """
    def __init__(self, in_fasta, out_fasta, debug, size_separator=';size='):
        """
        @param in_fasta: [str] Path to unsorted file.
        @param out_fasta: [str] Path to file after sort.
        @param size_separator: [str] Each sequence in in_fasta is see as a pre-cluster. The number of sequences represented by the pre-cluster is stored in sequence ID.
               Sequence ID format : '<REAL_ID><size_separator><NB_SEQ>'. If this size separator is missing in ID, the number of sequences represented is 1.
        """
        opt = ' --debug ' if debug else ''
        Cmd.__init__( self,
                      'sortAbundancies.py',
                      'Sort pre-clusters by abundancies.',
                      "--size-separator '" + size_separator + "' --input-file " + in_fasta + ' --output-file ' + out_fasta + opt,
                      '--version' )

    def get_version(self):
        """
        @summary: Returns the program version number.
        @return: [str] Version number if this is possible, otherwise this method return 'unknown'.
        """
        return Cmd.get_version(self, 'stdout').strip()


class Dada2Core(Cmd):
    """
    @summary: Launch Rscript to calcul data frame of DESEq2 from a phyloseq object in RData file, the result of FROGS Phyloseq Import Data.
    @see: http://rmarkdown.rstudio.com/
          https://joey711.github.io/phyloseq/
    """
    def __init__(self, r1_files, r2_files, output_dir, cpus, output_filenames, stderr, pseudo_pooling ):
        """
        @param data : [str] The path of one phyloseq-class object in Rdata file.
        @param model: [str] Experimental variable suspected to have an impact on OTUs abundances.
        @param out  : [str] Path to Rdata file storing DESeq2 prepreocessing step.
        @param stderr  : [str] Path to stderr output file
        """ 
        opts = ""
        if pseudo_pooling:
            opts = " --pseudopooling "
        if args.debug:
            opts += " --debug"
        Cmd.__init__( self,
                      'dada2_process.R',
                      'Write denoised FASTQ files from cutadapted and cleaned FASTQ files',
                      ' --R1Files ' + ",".join(r1_files) + ' --R2Files ' + ",".join(r2_files) + opts + ' --outputDir ' + output_dir + ' --fileNames ' + output_filenames + ' --threads ' + str(cpus) + ' 2> ' + stderr,
                      '--version')       
                       
    def get_version(self):
        """
        @summary: Returns the program version number.
        @return : [str] Version number if this is possible, otherwise this method return 'unknown'.
        """
        return Cmd.get_version(self, 'stdout')

        
class Pear(Cmd):
    """
    @summary: Overlapping and merging mate pairs from fragments shorter than twice the length of reads.
    """
    def __init__(self, in_R1, in_R2, out_prefix, pear_log, param):
        """
        @param in_R1: [str] Path to the R1 fastq file.
        @param in_R2: [str] Path to the R2 fastq file.
        @param out_prefix: [str] Prefix of path to the output fastq files.
        @param pear_log: [str] Path to log file
        @param param: [Namespace] The 'param.min_amplicon_size', 'param.max_amplicon_size', 'param.R1_size', 'param.R2_size'
        """
        min_overlap=max(param.R1_size+param.R2_size-param.max_amplicon_size, 10)
        max_assembly_length=min(param.max_amplicon_size, param.R1_size + param.R2_size -10)
        min_assembly_length=param.min_amplicon_size

        Cmd.__init__(self,
            'pear',
            'join overlapping paired reads',
             ' --forward-fastq ' + in_R1 + ' --reverse-fastq ' + in_R2 +' --output ' + out_prefix \
             + ' --min-overlap ' + str(min_overlap) + ' --max-assembly-length ' + str(max_assembly_length) + ' --min-assembly-length ' + str(min_assembly_length) \
             + ' --keep-original > ' + pear_log,
             ' --version')

        self.output = out_prefix + '.assembled.fastq'

    def get_version(self):
        """
        @summary: Returns the program version number.
        @return: version number if this is possible, otherwise this method return 'unknown'.
        """
        return Cmd.get_version(self, 'stdout').split()[1].strip()

    def parser(self, log_file):
        """
        @summary: Parse the command results to add information in log_file.
        @log_file: [str] Path to the sample process log file.
        """
        # Parse output
        nb_seq_merged = get_nb_seq(self.output)
        # Write result
        FH_log = Logger( log_file )
        FH_log.write( 'Results:\n' )
        FH_log.write( '\tnb seq paired-end assembled: ' + str(nb_seq_merged) + '\n' )
        FH_log.close()

class Flash(Cmd):
    """
    @summary: Overlapping and merging mate pairs from fragments shorter than twice the length of reads. The others fragments are discarded.
    """
    def __init__(self, in_R1, in_R2, out_join_prefix , flash_err, param):
        """
        @param in_R1: [str] Path to the R1 fastq file.
        @param in_R2: [str] Path to the R2 fastq file.
        @param out_join_prefix: [str] Path to the output fastq file.
        @param flash_err: [str] Path to the temporary stderr output file
        @param param: [Namespace] The 'param.min_amplicon_size', 'param.max_amplicon_size', 'param.expected_amplicon_size', 'param.fungi' and param.mismatch_rate'
        """
        #min_overlap = max(1,(param.R1_size + param.R2_size) - param.max_amplicon_size )
        min_overlap=max(param.R1_size+param.R2_size-param.max_amplicon_size, 10)
        max_expected_overlap = (param.R1_size + param.R2_size) - param.expected_amplicon_size + min(20, int((param.expected_amplicon_size - param.min_amplicon_size)/2))
        out_dir=os.path.dirname(out_join_prefix) if os.path.dirname(out_join_prefix)!= "" else "."
        Cmd.__init__( self,
                      'flash',
                      'Join overlapping paired reads.',
                      '--threads 1 --allow-outies --min-overlap ' + str(min_overlap) + ' --max-overlap ' + str(max_expected_overlap) + ' --max-mismatch-density ' + str(param.mismatch_rate) +'  --compress ' + in_R1 + ' ' + in_R2 + ' --output-directory '+ out_dir + ' --output-prefix ' + os.path.basename(out_join_prefix) +' 2> ' + flash_err,
                      ' --version' )
        self.output = out_join_prefix + ".extendedFrags.fastq.gz"

    def get_version(self):
        """
        @summary: Returns the program version number.
        @return: version number if this is possible, otherwise this method return 'unknown'.
        """
        return Cmd.get_version(self, 'stdout').split()[1].strip()

    def parser(self, log_file):
        """
        @summary: Parse the command results to add information in log_file.
        @log_file: [str] Path to the sample process log file.
        """
        # Parse output
        nb_seq_merged = get_nb_seq(self.output)
        # Write result
        FH_log = Logger( log_file )
        FH_log.write( 'Results:\n' )
        FH_log.write( '\tnb seq paired-end assembled: ' + str(nb_seq_merged) + '\n' )
        FH_log.close()

class Vsearch(Cmd):
    """
    @summary: Overlapping and merging mate pairs from fragments shorter than twice the length of reads.
    """
    def __init__(self, in_R1, in_R2, out_prefix, log, param):
        """
        @param in_R1: [str] Path to the R1 fastq file.
        @param in_R2: [str] Path to the R2 fastq file.
        @param out_prefix: [str] Prefix of path to the output fastq files.
        @param pear_log: [str] Path to log file
        @param param: [Namespace] The 'param.min_amplicon_size', 'param.max_amplicon_size', 'param.R1_size', 'param.R2_size'
        """
        min_overlap=max(param.R1_size+param.R2_size-param.max_amplicon_size, 10)

        Cmd.__init__(self,
            'vsearch',
            'join overlapping paired reads',
             ' --threads 1 --fastq_mergepairs ' + in_R1 + ' --reverse ' + in_R2 \
             + ' --fastqout ' + out_prefix + '.assembled.fastq ' + ' --fastqout_notmerged_fwd ' + out_prefix + '.unassembled_R1.fastq ' + ' --fastqout_notmerged_rev ' + out_prefix + '.unassembled_R2.fastq '\
             + ' --fastq_allowmergestagger --fastq_ascii ' + param.quality_scale + ' --fastq_maxdiffpct ' + str(param.mismatch_rate*100) + ' --fastq_minovlen ' + str(min_overlap) \
             + ' 2> ' + log,
             '--version')

        self.output = out_prefix + '.assembled.fastq'

    def get_version(self):
        """
        @summary: Returns the program version number.
        @return: version number if this is possible, otherwise this method return 'unknown'.
        """
        return Cmd.get_version(self, 'stderr').split(",")[0].split()[1] # vsearch v1.1.3_linux_x86_64, 126.0GB RAM, 32 cores           

    def parser(self, log_file):
        """
        @summary: Parse the command results to add information in log_file.
        @log_file: [str] Path to the sample process log file.
        """
        nb_seq_merged = get_nb_seq(self.output)
        # Write result
        FH_log = Logger( log_file )
        FH_log.write( 'Results:\n' )
        FH_log.write( '\tnb seq paired-end assembled: ' + str(nb_seq_merged) + '\n' )
        FH_log.close()

class Remove454prim(Cmd):
    """
    @summary: Removes reads without the 3' and 5' primer and removes primers sequences.
    """
    def __init__(self, in_fastq, out_fastq, cutadapt_log, cutadapt_err, param):
        """
        @param in_fastq: [str] Path to the processed fastq.
        @param out_fastq: [str] Path to the fastq with valid sequences.
        @param cutadapt_log: [str] Path to the log file.
        @param param: [Namespace] 'param.five_prim_primer', 'param.three_prim_primer' and 'param.min_amplicon_size'.
        """
        Cmd.__init__( self,
                      'remove454Adapt.py',
                      "Removes reads without the 3' and 5' primer and removes primers sequences.",
                      '--five-prim-primer ' + param.five_prim_primer + ' --three-prim-primer ' + param.three_prim_primer + ' --error-rate 0.1  --non-overlap 1 --min-length ' + str(args.min_amplicon_size) + ' -i ' + in_fastq + ' -o ' + out_fastq + ' > ' + cutadapt_log + ' 2> ' + cutadapt_err,
                      '--version' )
        self.output_seq = out_fastq

    def parser(self, log_file):
        """
        @summary: Parse the command results to add information in log_file.
        @log_file: [str] Path to the sample process log file.
        """
        # Parse output
        FH_output_seq = SequenceFileReader.factory( self.output_seq )
        nb_cleaned = 0
        for record in FH_output_seq:
            nb_cleaned += 1
        FH_output_seq.close()
        # Write result
        FH_log = Logger( log_file )
        FH_log.write( 'Results:\n' )
        FH_log.write( "\tnb seq with the two primers : " + str(nb_cleaned) + '\n' )
        FH_log.close()
        
    def get_version(self):   
        return Cmd.get_version(self, 'stdout').strip()        

class Cutadapt5prim(Cmd):
    """
    @summary: Removes reads without the 5' primer and removes primer sequence.
    """
    def __init__(self, in_fastq, out_fastq, cutadapt_log, cutadapt_err, param):
        """
        @param in_fastq: [str] Path to the processed fastq.
        @param out_fastq: [str] Path to the fastq with valid sequences.
        @param cutadapt_log: [str] Path to the log file.
        @param cutadapt_err: [str] Path to the error file.
        @param param: [Namespace] The primer sequence 'param.five_prim_primer'.
        """
        opt = ''
        if param.sequencer == "longreads":
            opt = ' --revcomp '
        Cmd.__init__( self,
                      'cutadapt',
                      "Removes reads without the 5' primer and removes primer sequence.",
                      '-g ' + param.five_prim_primer + ' --error-rate 0.1 --discard-untrimmed --match-read-wildcards --overlap ' + str(len(param.five_prim_primer) -1) + opt + ' -o ' + out_fastq + ' ' + in_fastq + ' > ' + cutadapt_log + ' 2> ' + cutadapt_err,
                      '--version' )
        self.output_seq = out_fastq

    def parser(self, log_file):
        """
        @summary: Parse the command results to add information in log_file.
        @log_file: [str] Path to the sample process log file.
        """
        # Parse output
        FH_output_seq = SequenceFileReader.factory( self.output_seq )
        nb_cleaned = 0
        for record in FH_output_seq:
            nb_cleaned += 1
        FH_output_seq.close()
        # Write result
        FH_log = Logger( log_file )
        FH_log.write( 'Results:\n' )
        FH_log.write( "\tnb seq with 5' primer : " + str(nb_cleaned) + '\n' )
        FH_log.close()

    def get_version(self):
        """
        @summary: Returns the program version number.
        @return: version number if this is possible, otherwise this method return 'unknown'.
        """
        return Cmd.get_version(self, 'stdout')


class Cutadapt3prim(Cmd):
    """
    @summary: Removes reads without the 3' primer and removes primer sequence.
    """
    def __init__(self, in_fastq, out_fastq, cutadapt_log, cutadapt_err, param):
        """
        @param in_fastq: [str] Path to the processed fastq.
        @param out_fastq: [str] Path to the fastq with valid sequences.
        @param cutadapt_log: [str] Path to the log file.
        @param cutadapt_err: [str] Path to the error file.
        @param param: [Namespace] The primer sequence 'param.three_prim_primer'.
        """
        opt = ''
        if param.sequencer == "longreads":
            opt = ' --revcomp '
        Cmd.__init__( self,
                      'cutadapt',
                      "Removes reads without the 3' primer and removes primer sequence.",
                      '-a ' + param.three_prim_primer + ' --error-rate 0.1 --discard-untrimmed --match-read-wildcards --overlap ' + str(len(param.three_prim_primer) -1) + opt + ' -o ' + out_fastq + ' ' + in_fastq + ' > ' + cutadapt_log + ' 2> ' + cutadapt_err,
                      '--version' )
        self.output_seq = out_fastq

    def parser(self, log_file):
        """
        @summary: Parse the command results to add information in log_file.
        @log_file: [str] Path to the sample process log file.
        """
        # Parse output
        FH_output_seq = SequenceFileReader.factory( self.output_seq )
        nb_cleaned = 0
        for record in FH_output_seq:
            nb_cleaned += 1
        FH_output_seq.close()
        # Write result
        FH_log = Logger( log_file )
        FH_log.write( 'Results:\n' )
        FH_log.write( "\tnb seq with 3' primer : " + str(nb_cleaned) + '\n' )
        FH_log.close()

    def get_version(self):
        """
        @summary: Returns the program version number.
        @return: version number if this is possible, otherwise this method return 'unknown'.
        """
        return Cmd.get_version(self, 'stdout')

class CutadaptPaired(Cmd):
    """
    @summary: Removes read pairs without 5' primer in R1 and 3' primer in R2 and removes primer sequences.
    """
    def __init__(self, in_R1_fastq, in_R2_fastq, out_R1_fastq, out_R2_fastq, cutadapt_log, cutadapt_err, param):
        """
        @param in_R1_fastq: [str] Path to the R1 fastq file to process.
        @param in_R2_fastq: [str] Path to the R2 fastq file to process.
        @param out_R1_fastq: [str] Path to the R1 fastq with valid sequences.
        @param out_R2_fastq: [str] Path to the R2 fastq with valid sequences.
        @param cutadapt_log: [str] Path to the log file.
        @param cutadapt_err: [str] Path to the error file.
        @param param: [Namespace] The primer sequence 'param.three_prim_primer'.
        """
        message = "Removes read pairs without the 5' and 3' primer and removes primer sequence."
        if param.swarm is False:
            message = "Before all, removes read pairs without the 5' and 3' primer and removes primer sequence."
        Cmd.__init__( self,
                      'cutadapt',
                      message,
                      '-g \"' + param.five_prim_primer + ';min_overlap=' + str(len(param.five_prim_primer)-1) + '\" -G \"' + revcomp(param.three_prim_primer) + ';min_overlap=' + str(len(param.three_prim_primer)-1) + '\" --minimum-length 1 --error-rate 0.1 --discard-untrimmed --match-read-wildcards --pair-filter=any ' + ' -o ' + out_R1_fastq + ' -p ' + out_R2_fastq + ' ' + in_R1_fastq + ' ' + in_R2_fastq + ' > ' + cutadapt_log + ' 2> ' + cutadapt_err,
                      '--version' )
        self.cutadapt_log = cutadapt_log

    def parser(self, log_file):
        """
        @summary: Parse the command results to add information in log_file.
        @log_file: [str] Path to the sample process log file.
        """
        # Parse output
        FH_cutadapt_log = open(self.cutadapt_log, 'rt')
        five_count = 0
        both = 0
        for line in FH_cutadapt_log:
            if line.strip().startswith('Read 1 with adapter:'):
                five_count = str(line.split()[4].replace(',',''))
            if line.strip().startswith('Pairs written (passing filters):'):
                both = str(line.split()[4].replace(',',''))
        FH_cutadapt_log.close()

        # Write result
        FH_log = Logger( log_file )
        FH_log.write( 'Results:\n' )
        FH_log.write( "\tnb seq with 5' primer : " + str(five_count) + '\n' )
        FH_log.write( "\tnb seq with 3' primer : " + str(both) + '\n' )
        FH_log.close()

    def get_version(self):
        """
        @summary: Returns the program version number.
        @return: version number if this is possible, otherwise this method return 'unknown'.
        """
        return Cmd.get_version(self, 'stdout')
        
class MultiFilter(Cmd):
    """
    @summary : Filters sequences.
    """
    def __init__(self, in_r1, in_r2, min_len, max_len, max_n, tag, out_r1, out_r2, log_file, param):
        """
        @param in_fastq: [str] Path to the processed fastq.
        @param min_len, max_len [int] : minimum and maximum length filter criteria
        @param tag [str] : check the presence of tag in sequence.
        @param out_fasta: [str] Path to the fasta/fastq with valid sequences.
        @param log_file: [str] Path to the log file.
        @param param: [Namespace] The 'param.sequencer'
        """
        cmd_description = 'Filters amplicons without primers by length and N count.',
        add_options = ""
        if param.sequencer == "454":
            cmd_description = 'Filters amplicons without primers by length, N count, homopolymer length and distance between quality low quality.',
            add_options = ' --max-homopolymer 7 --qual-window threshold:10 win_size:10'
        if min_len is not None:
            add_options += ' --min-length ' + str(min_len)
        if max_len is not None:
            add_options += ' --max-length ' + str(max_len)
        if not tag is None:
            add_options += ' --tag ' + tag
        if not max_n is None:
            add_options += ' --max-N ' + str(max_n)
            
        if in_r2 is None:
            Cmd.__init__( self,
              'filterSeq.py',
              'Filters amplicons without primers by length and N count.',
              '--force-fasta' + add_options + ' --input-file1 ' + in_r1 + ' --output-file1 ' + out_r1 + ' --log-file ' + log_file,
              '--version' )
        else:

            Cmd.__init__( self,
                          'filterSeq.py',
                          'Filters amplicons without primers by length and N count.',
                          add_options + ' --input-file1 ' + in_r1 + ' --input-file2 ' + in_r2 + ' --output-file1 ' + out_r1 + ' --output-file2 ' + out_r2 + ' --log-file ' + log_file,
                          '--version' )
        self.program_log = log_file

    def parser(self, log_file):
        """
        @summary: Parse the command results to add information in log_file.
        @log_file: [str] Path to the sample process log file.
        """
        # Parse output
        FH_log_filter = open( self.program_log )
        nb_processed = 0
        filtered_on_length = None
        filtered_on_tag = None
        filtered_on_N = None
        filtered_on_homopolymer = None
        filtered_on_quality = None
        for line in FH_log_filter:
            if line.startswith('Nb seq filtered on length'):
                filtered_on_length = int(line.split(':')[1].strip())
            if line.startswith('Nb seq filtered on absence of tag'):
                filtered_on_tag = int(line.split(':')[1].strip())
            elif line.startswith('Nb seq filtered on N'):
                filtered_on_N = int(line.split(':')[1].strip())
            elif line.startswith('Nb seq filtered on homopolymer'):
                filtered_on_homopolymer = int(line.split(':')[1].strip())
            elif line.startswith('Nb seq filtered on quality'):
                filtered_on_quality = int(line.split(':')[1].strip())
            elif line.startswith('Nb seq processed'):
                nb_processed = int(line.split(':')[1].strip())
        FH_log_filter.close()
        # Write result
        previous_nb_seq = nb_processed
        FH_log = Logger( log_file )
        FH_log.write( 'Results:\n' )
        if filtered_on_tag is not None:
            FH_log.write( '\t(nb seq with expected tag : ' + str(previous_nb_seq - filtered_on_tag) + ')\n' )
            previous_nb_seq -= filtered_on_tag
        if filtered_on_length is not None:
            FH_log.write( '\tnb seq with expected length : ' + str(previous_nb_seq - filtered_on_length) + '\n' )
            previous_nb_seq -= filtered_on_length
        if filtered_on_N is not None:
            FH_log.write( '\tnb seq without N : ' + str(previous_nb_seq - filtered_on_N) + '\n' )
            previous_nb_seq -= filtered_on_N
        if filtered_on_homopolymer is not None:
            FH_log.write( '\tnb seq without large homopolymer : ' + str(previous_nb_seq - filtered_on_homopolymer) + '\n' )
            previous_nb_seq -= filtered_on_homopolymer
        if filtered_on_quality is not None:
            FH_log.write( '\tnb seq without nearest poor quality : ' + str(previous_nb_seq - filtered_on_quality) + '\n' )
            previous_nb_seq -= filtered_on_quality
        FH_log.close()
        
    def get_version(self):   
        return Cmd.get_version(self, 'stdout').strip()        

class Combined(Cmd):
    """
    @summary : Artificially combined reads by adding a combined tag
    """
    def __init__(self, in_R1, in_R2, join_tag , out_join_file ):
        """
        @param input1  : [str] Path to sequence 5' (fasta/q format)
        @param input2  : [str] Path to sequence 3' (fasta/q format)
        @param join_tag     : [str] the sequence tag to add between sequences
        @param out_join_file     : [str] Path to fasta/q combined sequence output file
        """
        Cmd.__init__( self,
                      'combine_and_split.py',
                      'Concatenate paired reads.',
                      ' --reads1 ' + in_R1+ ' --reads2 ' + in_R2 + ' -c ' + join_tag + ' --combined-output ' + out_join_file,
                      '--version' )
        self.output = out_join_file

    def get_version(self):   
        return Cmd.get_version(self, 'stdout').strip()


class ReplaceJoinTag(Cmd):
    """
    @summary : Replace join tag
    """
    def __init__(self, combined_input , split_tag , join_tag , out_join_file ):
        """
        @param combined_input  : [str] Path to combined sequence 
        @param split_tag     : [str] the sequence tag on which to split sequences
        @param join_tag     : [str] the sequence tag to add between sequences
        @param out_join_file     : [str] Path to fasta/q combined sequence output file
        """
        Cmd.__init__( self,
                      'combine_and_split.py',
                      'Replace join tag.',
                      ' --reads1 ' + combined_input + ' -s ' + split_tag + ' -c ' + join_tag + ' --combined-output ' + out_join_file,
                      '--version' )

    def get_version(self):   
        return Cmd.get_version(self, 'stdout').strip()

class DerepBySample(Cmd):
    """
    @summary: Dereplicates sample sequences.
    """
    def __init__(self, in_fasta, out_fasta, out_count, size_separator=None):
        """
        @param in_fasta: [str] Path to the processed fasta.
        @param out_fasta: [str] Path to the dereplicated fasta.
        @param out_count: [str] Path to the count file.
        """
        if size_separator is not None:
            Cmd.__init__( self,
                      'derepSamples.py',
                      'Dereplicates sample sequences.',
                      '--sequences-files ' + in_fasta + ' --dereplicated-file ' + out_fasta + ' --count-file ' + out_count + ' --size-separator ' + size_separator + ' ',
                      '--version' )
        else:
            Cmd.__init__( self,
                      'derepSamples.py',
                      'Dereplicates sample sequences.',
                      '--sequences-files ' + in_fasta + ' --dereplicated-file ' + out_fasta + ' --count-file ' + out_count,
                      '--version' )
                      
    def get_version(self):  
        return Cmd.get_version(self, 'stdout').strip()                      


class DerepGlobalMultiFasta(Cmd):
    """
    @summary: Dereplicates together sequences from several files.
    """
    def __init__(self, all_fasta, samples_names, out_samples_ref, out_fasta, out_count, param):
        """
        @param all_fasta: [list] Path to the processed fasta.
        @param samples_names: [list] The sample name for each fasta.
        @param out_samples_ref: [str] Path to the file containing the link between samples names and path.
        @param out_fasta: [str] Path to the dereplicated fasta.
        @param out_count: [str] Path to the count file. It contains the count by sample for each representative sequence.
        @param param: [str] The 'param.nb_cpus'.
        """
        # Write sample description
        FH_ref = open(out_samples_ref, "wt")
        FH_ref.write( "#Sequence_file\tSample_name\n" )
        for idx, current_name in enumerate(samples_names):
            FH_ref.write( all_fasta[idx] + "\t" + current_name + "\n" )
        FH_ref.close()
        # Init
        Cmd.__init__( self,
                      'derepSamples.py',
                      'Dereplicates together sequences from several samples.',
                      "--nb-cpus " + str(param.nb_cpus) + " --size-separator ';size=' --samples-ref " + out_samples_ref + " --dereplicated-file " + out_fasta + " --count-file " + out_count,
                      '--version' )
                      
    def get_version(self):   
        return Cmd.get_version(self, 'stdout').strip()                      

class DerepGlobalFastaCount(Cmd):
    """
    @summary: Dereplicates together sequences from several files.
    """
    def __init__(self, fasta, count, out_fasta, out_count, param):
        """
        @param fasta: [str] Path to the processed fasta.
        @param count: [str] Path to the processed count.
        @param out_fasta: [str] Path to the dereplicated fasta.
        @param out_count: [str] Path to the count file. It contains the count by sample for each representative sequence.
        @param param: [str] The 'param.nb_cpus'.
        """
        # Init
        Cmd.__init__( self,
                      'derepSamples.py',
                      'Dereplicates together sequences from several samples based on one fasta file and one count file.',
                      "--nb-cpus " + str(param.nb_cpus) + " --size-separator ';size=' --sequences-file " + fasta + " --samples-count " + count + " --dereplicated-file " + out_fasta + " --count-file " + out_count,
                      '--version' )
                      
    def get_version(self):   
        return Cmd.get_version(self, 'stdout').strip()                      

##################################################################################################################################################
#
# FUNCTIONS
#
##################################################################################################################################################

def replaceNtags(in_fasta, out_fasta):
    """
    @summary : for FROGS_combined sequence, replace N tags by A and record start and stop positions in description
    @param : [str] Path to input fasta file
    @param : [str] Path to output fasta file
    """

    FH_in = FastaIO(in_fasta)
    FH_out = FastaIO(out_fasta, "wt")
    for record in FH_in:
        if "FROGS_combined" in record.id :
            if not 100*"N" in record.string:
                raise_exception(Exception("\n\n#ERROR : record " + record.id + " is a FROGS_combined sequence but it does not contain de 100N tags\n"))

            N_idx1 = record.string.find("N")
            N_idx2 = record.string.rfind("N")
            replace_tag = 50*"A" + 50 * "C"
            record.string = record.string.replace(100*"N",replace_tag)

            if record.description :
                record.description += "50A50C:" + str(N_idx1) + ":" + str(N_idx2)
            else:
                record.description = "50A50C:" + str(N_idx1) + ":" + str(N_idx2)
        FH_out.write(record)

    FH_in.close()
    FH_out.close()

def addNtags(in_fasta, output_fasta):
    """
    @summary : replace sequence indicated in seed description by N : ex A:10:110 replace 100A from 10 to 110 by N
    @param : [str] Path to input fasta file
    @param : [str] Path to output fasta file
    """

    FH_in = FastaIO(in_fasta)
    FH_out = FastaIO(output_fasta, "wt")
    regexp = re.compile('50A50C:\d+:\d+$')

    for record in FH_in:
        if "FROGS_combined" in record.id :
            search = regexp.search(record.description)
            if search is None:
                raise_exception( Exception("\n\n#ERROR : " + record.id + " is a FROGS_combined cluster but has not combining tag positions in its description.\n\n"))
            
            desc = search.group()
            [N_idx1,N_idx2] = desc.split(":")[1:]
            if record.string[int(N_idx1):int(N_idx2)+1] != 50*"A" + 50*"C":
                raise_exception( Exception("\n\n#ERROR : " + record.id + " is a FROGS_combined cluster but has not combining tag 50 As followed by 50 Cs to replace with 100 Ns\n\n"))    
            record.string = record.string[:int(N_idx1)]+"N"*(int(N_idx2)-int(N_idx1)+1)+record.string[int(N_idx2)+1:]
            record.description = record.description.replace(desc,"")
        FH_out.write(record)

    FH_out.close()
    FH_in.close()

def link_inputFiles(file_list, tmpFiles, log):
    """
    @summary : link Galaxy input file into working dir to add comprehensive extension for cutadapt
    @param file_list [list] : list of input path files
    @param tmpFile [object] : tmpFiles to store link to remove at the end
    @param logfile [str] : path to logFile
    @return input file or link to process
    """
    out_list = list()

    track = True
    for file in file_list:
        if not file.endswith(".dat"):
            out_list.append(file)
        # working through Galaxy
        else:
            if track:
                Logger.static_write(log, '##Create symlink for Galaxy inputs\n')
                track = False
            if FastqIO.is_valid(file):
                if is_gzip(file):
                    link = tmpFiles.add(os.path.basename(file) + '.fastq.gz')
                    os.symlink(file, link)
                    Logger.static_write(log, '\tln -s '+ file + ' ' + link + '\n')
                    out_list.append(link)
                else:
                    link = tmpFiles.add(os.path.basename(file) + '.fastq')
                    os.symlink(file, link)
                    Logger.static_write(log, '\tln -s '+ file + ' ' + link + '\n')
                    out_list.append(link)
            elif FastaIO.is_valid(file):
                if is_gzip(file):
                    link = tmpFiles.add(os.path.basename(file) + '.fasta.gz')
                    os.symlink(file, link)
                    Logger.static_write(log, '\tln -s '+ file + ' ' + link + '\n')
                    out_list.append(link)
                else:
                    link = tmpFiles.add(os.path.basename(file) + '.fasta')
                    os.symlink(file, link)
                    Logger.static_write(log, '\tln -s '+ file + ' ' + link + '\n')
                    out_list.append(link)
            else:
                raise_exception(Exception('\n\n#ERROR :' + file + ' is neither a fasta or a fastq file\n\n'))
    return out_list


def revcomp(seq):
    """
    @summary : return reverse complement iupac sequence
    """
    return seq.translate(str.maketrans('ACGTacgtRYMKrymkVBHDvbhdSWsw', 'TGCAtgcaYRKMyrkmBVDHbvdhSWsw'))[::-1]

def get_seq_length( input_file, size_separator=None ):
    """
    @summary: Returns the number of sequences by sequences lengths.
    @param input_file: [str] The sequence file path.
    @param size_separator: [str] If it exists the size separator in sequence ID.
    @return: [dict] By sequences lengths the number of sequence.
    """
    nb_by_length = dict()
    FH_seq = SequenceFileReader.factory( input_file )
    for record in FH_seq:
        nb_seq = 1
        if size_separator is not None:
            nb_seq = int(record.id.rsplit(size_separator, 1)[-1])
        seq_length = len(record.string)
        if str(seq_length) not in nb_by_length:
            nb_by_length[str(seq_length)] = 0
        nb_by_length[str(seq_length)] += nb_seq
    FH_seq.close()
    return nb_by_length

def get_seq_length_by_sample( input_file, count_file):
    """
    @summary: Returns the number of sequences by sequences lengths.
    @param input_file: [str] The sequence file path.
    @param count_file: [str] The sequence abondance count file by sample.
    @param size_separator: [str] If it exists the size separator in sequence ID.
    @return: [dict] By sample and by sequences lengths the number of sequence.
    """
    nb_by_length = dict()
    samples_names = list()
    sample_by_seq = dict()

    FH_count = open(count_file)
    for line in FH_count :
        if line.startswith("#id") : 
            samples_names = line.strip().split("\t")[1:]
            nb_by_length = {s:{} for s in samples_names}
        else:
            seq_id = line.split()[0]
            if not "FROGS_combined" in seq_id :
                sample_by_seq[seq_id]= { samples_names[idx-1]:int(count) for idx,count in enumerate(line.strip().split()[1:]) if int(count) > 0 }
    FH_count.close()

    FH_seq = SequenceFileReader.factory( input_file )
    for record in FH_seq:
        if "FROGS_combined" in record.id:
            continue
        nb_seq = sample_by_seq[record.id.split(";size=")[0]]
        seq_length = len(record.string)
        for sample_name in nb_seq :
            if str(seq_length) not in nb_by_length[sample_name]:
                nb_by_length[sample_name][str(seq_length)] = 0
            nb_by_length[sample_name][str(seq_length)] += nb_seq[sample_name]
    FH_seq.close()
    return nb_by_length

def summarise_results( samples_names, lengths_files, biom_file, depth_file, classif_file, log_files, param ):
    """
    @summary: Writes one summary of results from several logs.
    @param samples_names: [list] The samples names.
    @param lengths_files: [list] The list of path to files containing the contiged sequences lengths (in samples_names order).
    @param log_files: [list] The list of path to log files (in samples_names order).
    @param param: [str] The 'param.summary' .
    """
    # Get data
    categories = get_filter_steps(log_files[0])
    filters_by_sample = {"before process":{}, "merged":{}}
    before_lengths_by_sample = dict()
    after_lengths_by_sample = dict()
    
    # recover all filter by sample
    for spl_idx, spl_name in enumerate(samples_names):

        filters = get_sample_results(log_files[spl_idx])
        filters_by_sample["before process"][spl_name] = filters["before process"]
        filters_by_sample["merged"][spl_name] = filters["merged"]

        if "artificial combined" in filters:
            if not "artificial combined" in filters_by_sample:
                filters_by_sample["artificial combined"] = {}
            filters_by_sample["artificial combined"][spl_name] = filters["artificial combined"]
            # add total uncombined pair
            filters_by_sample["artificial combined"][spl_name]["paired-end assembled"] = filters_by_sample["before process"][spl_name] - filters_by_sample["merged"][spl_name]["paired-end assembled"]

        
        # length distribution
        with open(lengths_files[spl_idx]) as FH_lengths:
            lenghts = json.load(FH_lengths)
            before_lengths_by_sample[spl_name] = lenghts["before"]
            after_lengths_by_sample[spl_name] = lenghts["after"]

    # check length
    b_count= 0
    a_count = 0
    
    for sample in samples_names:
        for l in before_lengths_by_sample[sample]:
            b_count += before_lengths_by_sample[sample][l]
        for l in after_lengths_by_sample[sample]:
            a_count += after_lengths_by_sample[sample][l]
    
    # Get size distribution data
    clusters_size = list()
    counts = list()
    FH_depth = open( depth_file )
    for line in FH_depth:
        if not line.startswith('#'):
            fields = line.strip().split()
            if fields[1] != "0":
                clusters_size.append( int(fields[0]) )
                counts.append( int(fields[1]) )
    FH_depth.close()

    # Get sample data
    biom = BiomIO.from_json( biom_file )
    samples_distrib = dict()
    for sample_name in biom.get_samples_names():
        shared_seq = 0
        shared_observations = 0
        own_seq = 0
        own_observations = 0
        for observation in biom.get_observations_by_sample(sample_name):
            obs_count_in_spl = biom.get_count( observation['id'], sample_name )
            if obs_count_in_spl != 0 and obs_count_in_spl == biom.get_observation_count(observation['id']):
                own_observations += 1
                own_seq += obs_count_in_spl
            else:
                shared_observations += 1
                shared_seq += obs_count_in_spl
        samples_distrib[sample_name] = {
            'shared_seq': shared_seq,
            'shared_observations': shared_observations,
            'own_seq': own_seq,
            'own_observations': own_observations
        }
    del biom

    # Get newick data
    FH_classif = open( classif_file )
    newick = FH_classif.readlines()[0].replace("\n", "")
    FH_classif.close()
    
    # Write
    FH_summary_tpl = open( os.path.join(CURRENT_DIR, "preprocess_tpl.html") )
    FH_summary_out = open( param.summary, "wt" )
    for line in FH_summary_tpl:
        if "###CLUSTERS_SIZES###" in line:
            line = line.replace( "###CLUSTERS_SIZES###", json.dumps(clusters_size) )
        elif "###DATA_COUNTS###" in line:
            line = line.replace( "###DATA_COUNTS###", json.dumps(counts) )
        elif "###DATA_SAMPLE###" in line:
            line = line.replace( "###DATA_SAMPLE###", json.dumps(samples_distrib) )
        elif "###NEWICK###" in line:
            line = line.replace( "###NEWICK###", json.dumps(newick) )
        elif "###FILTERS_CATEGORIES###" in line:
            line = line.replace( "###FILTERS_CATEGORIES###", json.dumps(categories) )
        elif "###FILTERS_DATA###" in line:
            line = line.replace( "###FILTERS_DATA###", json.dumps(filters_by_sample) )
        elif "###BEFORE_LENGTHS_DATA###" in line:
            line = line.replace( "###BEFORE_LENGTHS_DATA###", json.dumps(before_lengths_by_sample) )
        elif "###AFTER_LENGTHS_DATA###" in line:
            line = line.replace( "###AFTER_LENGTHS_DATA###", json.dumps(after_lengths_by_sample) )
        FH_summary_out.write( line )
    FH_summary_out.close()
    FH_summary_tpl.close()

def summarise_results_dada2( samples_names, lengths_files, log_files, param ):
    """
    @summary: Writes one summary of results from several logs.
    @param samples_names: [list] The samples names.
    @param lengths_files: [list] The list of path to files containing the contiged sequences lengths (in samples_names order).
    @param log_files: [list] The list of path to log files (in samples_names order).
    @param param: [str] The 'param.summary' .
    """
    # Get data
    categories = get_filter_steps(log_files[0])
    filters_by_sample = {"before process":{}, "merged":{}}
    before_lengths_by_sample = dict()
    after_lengths_by_sample = dict()
    
    # recover all filter by sample
    for spl_idx, spl_name in enumerate(samples_names):

        filters = get_sample_results_dada2(log_files[spl_idx])
        filters_by_sample["before process"][spl_name] = filters["before process"]
        filters_by_sample["merged"][spl_name] = filters["merged"]

        if "artificial combined" in filters:
            if not "artificial combined" in filters_by_sample:
                filters_by_sample["artificial combined"] = {}
            filters_by_sample["artificial combined"][spl_name] = filters["artificial combined"]
            # add total uncombined pair
            filters_by_sample["artificial combined"][spl_name]["paired-end assembled"] = filters_by_sample["before process"][spl_name] - filters_by_sample["merged"][spl_name]["paired-end assembled"]

        
        # length distribution
        with open(lengths_files[spl_idx]) as FH_lengths:
            lenghts = json.load(FH_lengths)
            before_lengths_by_sample[spl_name] = lenghts["before"]
            after_lengths_by_sample[spl_name] = lenghts["after"]

    # check length
    b_count= 0
    a_count = 0
    
    for sample in samples_names:
        for l in before_lengths_by_sample[sample]:
            b_count += before_lengths_by_sample[sample][l]
        for l in after_lengths_by_sample[sample]:
            a_count += after_lengths_by_sample[sample][l]
    
    # Write
    FH_summary_tpl = open( os.path.join(CURRENT_DIR, "preprocess_tpl.html") )
    FH_summary_out = open( param.summary, "wt" )
    for line in FH_summary_tpl:
        if "###FILTERS_CATEGORIES###" in line:
            line = line.replace( "###FILTERS_CATEGORIES###", json.dumps(categories) )
        elif "###FILTERS_DATA###" in line:
            line = line.replace( "###FILTERS_DATA###", json.dumps(filters_by_sample) )
        elif "###BEFORE_LENGTHS_DATA###" in line:
            line = line.replace( "###BEFORE_LENGTHS_DATA###", json.dumps(before_lengths_by_sample) )
        elif "###AFTER_LENGTHS_DATA###" in line:
            line = line.replace( "###AFTER_LENGTHS_DATA###", json.dumps(after_lengths_by_sample) )
        FH_summary_out.write( line )
    FH_summary_out.close()
    FH_summary_tpl.close()

def get_filter_steps( log_file ):
    """
    @summary: Returns the ordered list of steps.
    @param log_file: [str] Path to a log file.
    @return: [list] The ordered list of steps.
    """
    steps = ["before process"]
    FH_input = open(log_file)
    for line in FH_input:
        if line.strip().startswith('nb seq') and not line.strip().startswith('nb seq before process'):
            step = line.split('nb seq')[1].split(':')[0].strip()
            if not step in steps:
                steps.append( step )
    FH_input.close()
    return steps

def get_sample_results( log_file ):
    """
    @summary: Returns the sample results (number of sequences after each filters).
    @param log_file: [str] Path to a log file.
    @return: [list] The number of sequences after each filter.
    """
    nb_seq = {"before process":0, "merged":{}}
    FH_input = open(log_file)
    key="merged"
    for line in FH_input:
        if "combine_and_split" in line or "Removes read pairs without the 5' and 3' primer and removes primer sequence." in line :
            key="artificial combined"
            if key not in nb_seq:
                nb_seq[key]={}
        if line.strip().startswith('nb seq before process'):
            nb_seq["before process"] = int(line.split(':')[1].strip())
        elif line.strip().startswith('nb seq'):
            step = line.split('nb seq')[1].split(':')[0].strip() 
            nb_seq[key][step] = int(line.split(':')[1].strip()) 
    FH_input.close()
    return nb_seq

def get_sample_results_dada2( log_file ):
    """
    @summary: Returns the sample results (number of sequences after each filters).
    @param log_file: [str] Path to a log file.
    @return: [list] The number of sequences after each filter.
    """
    nb_seq = {"before process":0, "merged":{}}
    FH_input = open(log_file)
    key="merged"
    for line in FH_input:
        if "combine_and_split" in line:            
            key="artificial combined"
            if key not in nb_seq:
                nb_seq[key]={}
        if line.strip().startswith('nb seq before process'):
            nb_seq["before process"] = int(line.split(':')[1].strip())
        elif line.strip().startswith('nb seq'):
            step = line.split('nb seq')[1].split(':')[0].strip() 
            nb_seq[key][step] = int(line.split(':')[1].strip()) 
    FH_input.close()
    return nb_seq

def log_append_files( log_file, appended_files ):
    """
    @summary: Append content of several log files in one log file.
    @param log_file: [str] The log file where contents of others are appended.
    @param appended_files: [list] List of log files to append.
    """
    FH_log = Logger( log_file )
    FH_log.write( "\n" )
    for current_file in appended_files:
        FH_input = open(current_file)
        for line in FH_input:
            FH_log.write( line )
        FH_input.close()
        FH_log.write( "\n" )
    FH_log.write( "\n" )
    FH_log.close()

def samples_from_tar( archive, contiged, global_tmp_files, R1_files, R2_files, samples_names ):
    """
    @summary: Extracts samples files from the archive and set R1_files, R2_files and samples_names.
    @param archive: [str] Path to the tar file.
    @param contiged: [bool] True if the R1 and R2 files are already contiged for each sample.
    @param global_tmp_files: [TmpFiles] The tmp file manager for the global script (extracted files will be added into this manager).
    @param R1_files: [list] The list of path to extracted R1 files.
    @param R2_files: [list] The list of path to extracted R2 files.
    @param samples_names: [list] The samples names.
    """
    R1_tmp = list()
    R2_tmp = list()
    R1_samples_names = list()
    R2_samples_names = list()
    tmp_folder = os.path.join( global_tmp_files.tmp_dir, global_tmp_files.prefix + "_tmp" )
    if not tarfile.is_tarfile(archive):
        raise_exception( Exception("\n\n#ERROR : The archive '" + archive + "' is not a tar file.\n\n"))
    FH_tar = tarfile.open(archive)
    # List R1_files, R2_files and samples_names
    archive_members = sorted(FH_tar.getmembers(), key=lambda member: member.name)
    for file_info in archive_members:
        if file_info.isfile():
            if contiged:
                samples_names.append( file_info.name.split('.')[0] )
                R1_tmp.append( os.path.join(tmp_folder, file_info.name) )
                R1_files.append( global_tmp_files.add(file_info.name) )
            else:
                if "_R1" in file_info.name or "_r1" in file_info.name:
                    samples_names.append( re.split('_[Rr]1', file_info.name)[0] )
                    R1_samples_names.append( re.split('_[Rr]1', file_info.name)[0] )
                    R1_files.append( global_tmp_files.add(file_info.name) )
                    R1_tmp.append( os.path.join(tmp_folder, file_info.name) )
                elif "_R2" in file_info.name or "_r2" in file_info.name:
                    R2_files.append( global_tmp_files.add(file_info.name) )
                    R2_tmp.append( os.path.join(tmp_folder, file_info.name) )
                    R2_samples_names.append( re.split('_[Rr]2', file_info.name)[0] )
                else:
                    raise_exception( Exception("\n\n#ERROR : The file '" + file_info.name + "' in archive '" + archive + "' is invalid. The files names must contain '_R1' or '_R2'.\n\n"))
        else:
            raise_exception( Exception("\n\n#ERROR : The archive '" + archive + "' must not contain folders."))
    R1_files = sorted(R1_files)
    R2_files = sorted(R2_files)
    R1_samples_names = sorted(R1_samples_names)
    R2_samples_names = sorted(R2_samples_names)
    samples_names = sorted(samples_names)
    if R1_samples_names != R2_samples_names:
        raise_exception( Exception( "\n\n#ERORR : Samples names are not identical in the archive '" + archive + "'. R1 samples names : [" + ", ".join(R1_samples_names) + "] ; R2 samples names : [" + ", ".join(R2_samples_names) + "]\n\n" ))
    if len(R1_files) != len(R2_files) and not contiged:
        if len(R1_files) > len(R2_files):
            raise_exception( Exception( "\n\n#ERORR : " + str(len(R1_files) - len(R2_files)) + " R2 file(s) are missing in arhive '" + archive + "'. R1 file : [" + ", ".join(R1_files) + "] ; R2 files : [" + ", ".join(R2_files) + "]\n\n" ))
        else:
            raise_exception( Exception( "\n\n#ERROR : " + str(len(R2_files) - len(R1_files)) + " R1 file(s) are missing in arhive '" + archive + "'. R1 file : [" + ", ".join(R1_files) + "] ; R2 files : [" + ", ".join(R2_files) + "]\n\n" ))
    try:
        # Extract
        FH_tar.extractall(tmp_folder)
        FH_tar.close()
        # Move files
        for idx in range(len(samples_names)):
            shutil.move( R1_tmp[idx], R1_files[idx] )
            if not contiged:
                shutil.move( R2_tmp[idx], R2_files[idx] )
    except:
        for current_file in R1_files + R2_files:
            if os.path.exists(current_file) : os.remove( current_file )
    finally:
        for current_file in R1_tmp + R2_tmp:
            if os.path.exists(current_file) : os.remove( current_file )
        os.rmdir(tmp_folder)

def is_gzip( file ):
    """
    @return: [bool] True if the file is gziped.
    @param file: [str] Path to processed file.
    """
    is_gzip = None
    FH_input = gzip.open( file )
    try:
        FH_input.readline()
        is_gzip = True
    except:
        is_gzip = False
    finally:
        FH_input.close()
    return is_gzip

def get_nb_seq( reads_file ):
    """
    @summary: Returns the number of sequences
    @param reads_file: [str] Path to the fasta/q file processed.
    @return: [int] The number of sequences.
    """
    FH_input = None
    if not is_gzip(reads_file):
        FH_input = open( reads_file )
    else:
        FH_input = gzip.open( reads_file )

    format = "fastq" if FastqIO.is_valid(reads_file) else "fasta"
    nb_seq= 0

    first_line = FH_input.readline().strip()
    if ";size=" in str(first_line):
        nb_seq += int(first_line.split()[0].split(';size=')[1])
        for li in FH_input:
            if ";size=" in li:
                li = li.strip()
                nb_seq += int(li.split()[0].split(';size=')[1])
    else:
        nb_seq += 1
        for li in FH_input:
            nb_seq += 1
        if format == "fastq":
            nb_seq = nb_seq / 4
        elif format == "fasta":
            nb_seq = nb_seq /2

    FH_input.close()
    return int(nb_seq)


def filter_process_multiples_files(R1_files, R2_files, samples_names, out_files, out_art_files, lengths_files, log_files, args):
    """
    @summary: filters sequences of samples.
    @param R1_files: [list] List of path to reads 1 fastq files or contiged files (one by sample).
    @param R2_files: [list] List of path to reads 2 fastq files (one by sample).
    @param samples_names: [list] The list of sample name for each R1/R2-files.
    @param out_files: [list] List of path to the filtered files (one by sample).
    @param out_art_files: [list] List of path to the artificial combined filtered files (one by sample).
    @param lengths_files: [list] List of path to the outputted files containing the contiged sequences lengths.
    @param log_files: [list] List of path to the outputted log (one by sample). It contains a trace of all the operations and results.
    @param args: [Namespace] Global parameters.
    """
    for idx in range(len(out_files)):
        if args.already_contiged:
            process_sample(R1_files[idx], None, samples_names[idx], out_files[idx], None, lengths_files[idx], log_files[idx], args )
        else:
            process_sample(R1_files[idx], R2_files[idx], samples_names[idx], out_files[idx], out_art_files[idx], lengths_files[idx], log_files[idx], args )


def clean_before_denoising_process_multiples_files(R1_files, R2_files, samples_names, R1_cutadapted_files, R2_cutadapted_files, lengths_files, log_files, args):
    """
    @summary: filters sequences of samples.
    @param R1_files: [list] List of path to reads 1 fastq files or contiged files (one by sample).
    @param R2_files: [list] List of path to reads 2 fastq files (one by sample).
    @param samples_names: [list] The list of sample name for each R1/R2-files.
    @param out_files: [list] List of path to the filtered files (one by sample).
    @param out_art_files: [list] List of path to the artificial combined filtered files (one by sample).
    @param lengths_files: [list] List of path to the outputted files containing the contiged sequences lengths.
    @param log_files: [list] List of path to the outputted log (one by sample). It contains a trace of all the operations and results.
    @param args: [Namespace] Global parameters.
    """
    for idx in range(len(R1_files)):
        if args.already_contiged:
            clean_before_denoising_process( R1_files[idx], None, samples_names[idx], R1_cutadapted_files[idx], None, lengths_files[idx], log_files[idx], args )
        else:
            clean_before_denoising_process( R1_files[idx], R2_files[idx], samples_names[idx], R1_cutadapted_files[idx], R2_cutadapted_files[idx], lengths_files[idx], log_files[idx], args )


def clean_before_denoising_process(R1_file, R2_file, sample_name, R1_cutadapted_and_filtered_file, R2_cutadapted_and_filtered_file, lengths_file, log_file, args):
    """
    @summary: Merges, filters and dereplicates all sequences of one sample.
    @param R1_file: [str] Path to reads 1 fastq file or contiged file of the sample.
    @param R2_file: [str] Path to reads 2 fastq file of the sample.
    @param sample_name: [str] The sample name.
    @param out_file: [str] Path to the filtered file.
    @param art_out_file: [str] Path to the artificial combined filtered file.
    @param lengths_file: [str] Path to the outputted file containing the contiged sequences lengths.
    @param log_file: [str] Path to the outputted log. It contains a trace of all the operations and results.
    @param args: [Namespace] Global parameters.
    """
    tmp_files = TmpFiles( os.path.split(R1_file)[0] )
    
    R1_tmp_cutadapt = tmp_files.add( sample_name + '_cutadapt_R1.fastq.gz' )
    R2_tmp_cutadapt = tmp_files.add( sample_name + '_cutadapt_R2.fastq.gz' )
    log_cutadapt = tmp_files.add( sample_name + '_cutadapt.log' )
    log_Nfilter = tmp_files.add( sample_name + '_Nfilter.log' )
    err_cutadapt = tmp_files.add( sample_name + '_cutadapt.err' )
    
    FH_log = open(log_file, "at")
    FH_log.write('##Sample\nContiged file : ' + R1_file + '\nSample name : ' + sample_name + '\n')
    FH_log.write('nb seq before process : ' + str(get_nb_seq(R1_file)) +'\n' )
    FH_log.write('##Commands\n')
    FH_log.close()
    
    try:
        if args.five_prim_primer and args.three_prim_primer: # Illumina standard sequencing protocol
            CutadaptPaired(R1_file, R2_file, R1_tmp_cutadapt, R2_tmp_cutadapt, log_cutadapt, err_cutadapt, args).submit(log_file)
            MultiFilter(R1_tmp_cutadapt, R2_tmp_cutadapt, 20, None, 0, None, R1_cutadapted_and_filtered_file, R2_cutadapted_and_filtered_file, log_Nfilter, args).submit(log_file)
        else: # Custom sequencing primers. The amplicons is full length (Illumina) except PCR primers (it is use as sequencing primers). [Protocol Kozich et al. 2013]
            MultiFilter(R1_file, R2_file, 20, None, 0, None, R1_cutadapted_and_filtered_file, R2_cutadapted_and_filtered_file, log_Nfilter, args).submit(log_file)
    finally:
        if not args.debug:
            tmp_files.deleteAll()

def process_sample_after_denoising_multiple_files(R1_files, R2_files, samples_names, out_files, out_art_files, lengths_files, log_files, args):
    
    for idx in range(len(out_files)):
        if args.already_contiged:
            process_sample_after_denoising( R1_files[idx], None, samples_names[idx], out_files[idx], None, lengths_files[idx], log_files[idx], args )
        else:
            process_sample_after_denoising( R1_files[idx], R2_files[idx], samples_names[idx], out_files[idx], out_art_files[idx], lengths_files[idx], log_files[idx], args )


def process_sample_after_denoising(R1_file, R2_file, sample_name, out_file, art_out_file, lengths_file, log_file, args):
    
    tmp_files = TmpFiles( os.path.split(out_file)[0] )
    
    if args.sequencer == "illumina" and not args.already_contiged:
        # FLASH
        if args.merge_software == "flash":
            out_contig = tmp_files.add( sample_name + '_flash.extendedFrags.fastq.gz' )
            out_notcombined_R1 = tmp_files.add( sample_name + '_flash.notCombined_1.fastq.gz' )
            out_notcombined_R2 = tmp_files.add( sample_name + '_flash.notCombined_2.fastq.gz' )
            out_contig_log = tmp_files.add(sample_name + '_flash.stderr')
            # other files to remove
            tmp_files.add(sample_name + '_flash.hist')
            tmp_files.add(sample_name + '_flash.histogram')
            tmp_files.add(sample_name + '_flash.hist.outie')
            tmp_files.add(sample_name + '_flash.hist.innie')
            tmp_files.add(sample_name + '_flash.histogram.outie')
            tmp_files.add(sample_name + '_flash.histogram.innie')

        # PEAR
        elif args.merge_software == "pear":
            out_contig = tmp_files.add( sample_name + '_pear.assembled.fastq' )
            out_notcombined_R1 = tmp_files.add( sample_name + '_pear.unassembled.forward.fastq' )
            out_notcombined_R2 = tmp_files.add( sample_name + '_pear.unassembled.reverse.fastq' )
            out_contig_log = tmp_files.add(sample_name + '_pear.log')
            tmp_files.add(sample_name + '_pear.discarded.fastq')   # other file to remove

        # VSEARCH
        elif args.merge_software == "vsearch":
            out_contig = tmp_files.add( sample_name + '_vsearch.assembled.fastq' )
            out_notcombined_R1 = tmp_files.add( sample_name + '_vsearch.unassembled_R1.fastq' )
            out_notcombined_R2 = tmp_files.add( sample_name + '_vsearch.unassembled_R2.fastq' )
            out_contig_log = tmp_files.add(sample_name + '_vsearch.log')

    # MULTIFILTER ON COMBINED FILTERED CUTADAPTED
    out_NAndLengthfilter = out_file
    log_NAndLengthfilter = tmp_files.add( sample_name + '_N_and_length_filter_log.txt' )
    # FINAL COUNT ON COMBINED FILTERED CUTADAPTED MULTIFILTERED
    out_count = tmp_files.add( sample_name + '_derep_count.tsv' )

    # ARTIFICIAL COMBINED
    if not args.already_contiged:
        # ARTIFICIAL CUTADAPT TRIMMED COMBINED
        art_out_cutadapt = tmp_files.add( sample_name + '_artificial_combined.fastq.gz' )
        # MULTIFILTER ON ARTIFICIAL COMBINED CUTADAPTED
        art_out_Nfilter = art_out_file
        art_log_Nfilter = tmp_files.add( sample_name + '_art_N_filter_log.txt' )
        # REPLACE COMBINED TAG X BY N
        art_out_XtoN = tmp_files.add( sample_name + '_art_XtoN.fasta' )
        art_log_XtoN = tmp_files.add( sample_name + '_art_XtoN_log.txt' )
        # FINAL COUNT ON ARTIFICIAL COMBINED CUTADAPTED
        art_out_count = tmp_files.add( sample_name + '_derep_count.tsv' )

    try:
        # Start log
        FH_log = open(log_file, "at")
        if not args.already_contiged:
            FH_log.write('##Sample\nR1 : ' + R1_file + '\nR2 : ' + R2_file + '\nSample name : ' + sample_name + '\n')
        else:
            FH_log.write('##Sample\nContiged file : ' + R1_file + '\nSample name : ' + sample_name + '\n')
        #FH_log.write('nb seq before process : ' + str(get_nb_seq(R1_file)) +'\n' )
        FH_log.write('##Commands\n')
        FH_log.close()

        # Commands execution
        #read pair assembly
        if not args.already_contiged:
            if args.merge_software == "vsearch":
                vsearch_cmd = Vsearch(R1_file, R2_file, out_contig.replace(".assembled.fastq",""), out_contig_log, args)
                vsearch_cmd.submit(log_file)
            elif args.merge_software == "flash":
                flash_cmd = Flash(R1_file, R2_file, out_contig.replace(".extendedFrags.fastq.gz",""), out_contig_log, args)
                flash_cmd.submit(log_file)
            elif args.merge_software == "pear":
                pear_cmd = Pear(R1_file, R2_file, out_contig.replace(".assembled.fastq",""), out_contig_log, args)
                pear_cmd.submit(log_file)
                
        primers_size = 0
        if args.five_prim_primer is not None: primers_size += len(args.five_prim_primer)
        if args.three_prim_primer is not None: primers_size += len(args.three_prim_primer)
        min_len = args.min_amplicon_size - primers_size
        max_len = args.max_amplicon_size - primers_size
        # filter on length, N 
        MultiFilter(out_contig, None, min_len, max_len, None, None, out_NAndLengthfilter, None, log_NAndLengthfilter, args).submit(log_file)
        
        # Get length before and after process
        length_dict = dict()
        nb_before_by_legnth = get_seq_length( out_contig , size_separator=";size=")
        length_dict["before"]=nb_before_by_legnth
        
        nb_after_by_legnth = get_seq_length( out_NAndLengthfilter , size_separator=";size=")
        length_dict["after"] = nb_after_by_legnth
        
        with open(lengths_file, "wt") as FH_lengths:
            FH_lengths.write( json.dumps(length_dict))

        # dealing with uncontiged reads.
        if args.keep_unmerged:
            Combined(out_notcombined_R1, out_notcombined_R2, "X"*100, art_out_cutadapt ).submit(log_file)
            MultiFilter(art_out_cutadapt, None, min_len, max_len, None, None, art_out_Nfilter, None, art_log_Nfilter, args).submit(log_file)
            ReplaceJoinTag(art_out_Nfilter, "X"*100, "N"*100, art_out_XtoN ).submit(log_file)
            DerepBySample(out_NAndLengthfilter + " " + art_out_XtoN, out_file, out_count, size_separator="';size='").submit(log_file)
        
    finally:
        if not args.debug:
            tmp_files.deleteAll()
    

def process_sample(R1_file, R2_file, sample_name, out_file, art_out_file, lengths_file, log_file, args):
    """
    @summary: Merges, filters and dereplicates all sequences of one sample.
    @param R1_file: [str] Path to reads 1 fastq file or contiged file of the sample.
    @param R2_file: [str] Path to reads 2 fastq file of the sample.
    @param sample_name: [str] The sample name.
    @param out_file: [str] Path to the filtered file.
    @param art_out_file: [str] Path to the artificial combined filtered file.
    @param lengths_file: [str] Path to the outputted file containing the contiged sequences lengths.
    @param log_file: [str] Path to the outputted log. It contains a trace of all the operations and results.
    @param args: [Namespace] Global parameters.
    """

    tmp_files = TmpFiles( os.path.split(out_file)[0] )
    
    if args.sequencer == "illumina" and not args.already_contiged:
        # FLASH
        if args.merge_software == "flash":
            out_contig = tmp_files.add( sample_name + '_flash.extendedFrags.fastq.gz' )
            out_notcombined_R1 = tmp_files.add( sample_name + '_flash.notCombined_1.fastq.gz' )
            out_notcombined_R2 = tmp_files.add( sample_name + '_flash.notCombined_2.fastq.gz' )
            out_contig_log = tmp_files.add(sample_name + '_flash.stderr')
            # other files to remove
            tmp_files.add(sample_name + '_flash.hist')
            tmp_files.add(sample_name + '_flash.histogram')
            tmp_files.add(sample_name + '_flash.hist.outie')
            tmp_files.add(sample_name + '_flash.hist.innie')
            tmp_files.add(sample_name + '_flash.histogram.outie')
            tmp_files.add(sample_name + '_flash.histogram.innie')


        # PEAR
        elif args.merge_software == "pear":
            out_contig = tmp_files.add( sample_name + '_pear.assembled.fastq' )
            out_notcombined_R1 = tmp_files.add( sample_name + '_pear.unassembled.forward.fastq' )
            out_notcombined_R2 = tmp_files.add( sample_name + '_pear.unassembled.reverse.fastq' )
            out_contig_log = tmp_files.add(sample_name + '_pear.log')
            tmp_files.add(sample_name + '_pear.discarded.fastq')   # other file to remove

        # VSEARCH
        elif args.merge_software == "vsearch":
            out_contig = tmp_files.add( sample_name + '_vsearch.assembled.fastq' )
            out_notcombined_R1 = tmp_files.add( sample_name + '_vsearch.unassembled_R1.fastq' )
            out_notcombined_R2 = tmp_files.add( sample_name + '_vsearch.unassembled_R2.fastq' )
            out_contig_log = tmp_files.add(sample_name + '_vsearch.log')

    # CUTADAPT ON COMBINED FILTER
    tmp_cutadapt = tmp_files.add( sample_name + '_cutadapt_5prim_trim.fastq.gz' )
    log_5prim_cutadapt = tmp_files.add( sample_name + '_cutadapt_5prim_log.txt' )
    err_5prim_cutadapt = tmp_files.add( sample_name + '_cutadapt_5prim_err.txt' )
    log_3prim_cutadapt = tmp_files.add( sample_name + '_cutadapt_3prim_log.txt' )
    err_3prim_cutadapt = tmp_files.add( sample_name + '_cutadapt_3prim_err.txt' )
    out_cutadapt = tmp_files.add( sample_name + '_cutadapt.fastq.gz' )
    # MULTIFILTER ON COMBINED FILTERED CUTADAPTED
    out_NAndLengthfilter = tmp_files.add( sample_name + '_N_and_length_filter.fasta' )
    log_NAndLengthfilter = tmp_files.add( sample_name + '_N_and_length_filter_log.txt' )
    # FINAL COUNT ON COMBINED FILTERED CUTADAPTED MULTIFILTERED
    out_count = tmp_files.add( sample_name + '_derep_count.tsv' )

    # ARTIFICIAL COMBINED
    if not args.already_contiged:
        # CUTADAPT ON UNCOMBINED
        uncomb_R1_tmp_cutadapt = tmp_files.add( sample_name + '_uncomb_cutadapt_paired_trim_R1.fastq.gz' )
        uncomb_R2_tmp_cutadapt = tmp_files.add( sample_name + '_uncomb_cutadapt_paired_trim_R2.fastq.gz' )
        uncomb_log_cutadapt = tmp_files.add( sample_name + '_uncomb_cutadapt_paired_log.txt' )
        uncomb_err_cutadapt = tmp_files.add( sample_name + '_uncomb_cutadapt_paired_err.txt' )
        # ARTIFICIAL CUTADAPT TRIMMED COMBINED
        art_out_cutadapt = tmp_files.add( sample_name + '_artificial_combined.fastq.gz' )
        # MULTIFILTER ON ARTIFICIAL COMBINED CUTADAPTED
        art_out_Nfilter = tmp_files.add( sample_name + '_art_N_filter.fasta' )
        art_log_Nfilter = tmp_files.add( sample_name + '_art_N_filter_log.txt' )
        # REPLACE COMBINED TAG X BY N
        art_out_XtoN = tmp_files.add( sample_name + '_art_XtoN.fasta' )
        art_log_XtoN = tmp_files.add( sample_name + '_art_XtoN_log.txt' )
        # FINAL COUNT ON ARTIFICIAL COMBINED CUTADAPTED
        art_out_count = tmp_files.add( sample_name + '_derep_count.tsv' )

    try:
        # Start log
        FH_log = open(log_file, "wt")
        if not args.already_contiged:
            FH_log.write('##Sample\nR1 : ' + R1_file + '\nR2 : ' + R2_file + '\nSample name : ' + sample_name + '\n')
        else:
            FH_log.write('##Sample\nContiged file : ' + R1_file + '\nSample name : ' + sample_name + '\n')
        FH_log.write('nb seq before process : ' + str(get_nb_seq(R1_file)) +'\n' )
        FH_log.write('##Commands\n')
        FH_log.close()

        # Commands execution
        #read pair assembly
        if not args.already_contiged:
            if args.merge_software == "vsearch":
                vsearch_cmd = Vsearch(R1_file, R2_file, out_contig.replace(".assembled.fastq",""), out_contig_log, args)
                vsearch_cmd.submit(log_file)
            elif args.merge_software == "flash":
                flash_cmd = Flash(R1_file, R2_file, out_contig.replace(".extendedFrags.fastq.gz",""), out_contig_log, args)
                flash_cmd.submit(log_file)
            elif args.merge_software == "pear":
                pear_cmd = Pear(R1_file, R2_file, out_contig.replace(".assembled.fastq",""), out_contig_log, args)
                pear_cmd.submit(log_file)
                
        else:
            out_contig = R1_file

        # remove primer
        if args.sequencer == "454": # 454
            if is_gzip( out_contig ):
                renamed_out_contig = tmp_files.add( sample_name + '_454.fastq.gz' ) # prevent cutadapt problem (type of file is checked by extension)
            else:
                renamed_out_contig = tmp_files.add( sample_name + '_454.fastq' ) # prevent cutadapt problem (type of file is checked by extension)
            shutil.copyfile( out_contig, renamed_out_contig ) # prevent symlink problem
            Remove454prim(renamed_out_contig, out_cutadapt, log_3prim_cutadapt, err_3prim_cutadapt, args).submit(log_file)
        elif args.sequencer == "illumina" or args.sequencer == "longreads": 
            if args.five_prim_primer and args.three_prim_primer: # Illumina standard sequencing protocol
                Cutadapt5prim(out_contig, tmp_cutadapt, log_5prim_cutadapt, err_5prim_cutadapt, args).submit(log_file)
                Cutadapt3prim(tmp_cutadapt, out_cutadapt, log_3prim_cutadapt, err_3prim_cutadapt, args).submit(log_file)
            else: # Custom sequencing primers. The amplicons is full length (Illumina) except PCR primers (it is use as sequencing primers). [Protocol Kozich et al. 2013]
                out_cutadapt = out_contig

        primers_size = 0
        if args.five_prim_primer is not None: primers_size += len(args.five_prim_primer)
        if args.three_prim_primer is not None: primers_size += len(args.three_prim_primer)
        min_len = args.min_amplicon_size - primers_size
        max_len = args.max_amplicon_size - primers_size
        # filter on length, N 
        MultiFilter(out_cutadapt, None, min_len, max_len, 0, None, out_NAndLengthfilter, None, log_NAndLengthfilter, args).submit(log_file)
        
        # Get length before and after process
        length_dict = dict()
        nb_before_by_legnth = get_seq_length( out_contig )
        length_dict["before"]=nb_before_by_legnth
        
        nb_after_by_legnth = get_seq_length( out_NAndLengthfilter )
        length_dict["after"] = nb_after_by_legnth
        
        with open(lengths_file, "wt") as FH_lengths:
            FH_lengths.write( json.dumps(length_dict))

        # dealing with uncontiged reads.
        if args.keep_unmerged:
            # remove primers
            if args.five_prim_primer and args.three_prim_primer: # Illumina standard sequencing protocol
                CutadaptPaired(out_notcombined_R1, out_notcombined_R2, uncomb_R1_tmp_cutadapt, uncomb_R2_tmp_cutadapt, uncomb_log_cutadapt, uncomb_err_cutadapt, args).submit(log_file)
                Combined(uncomb_R1_tmp_cutadapt, uncomb_R2_tmp_cutadapt, "X"*100, art_out_cutadapt ).submit(log_file)
            else: # Custom sequencing primers. The amplicons is full length (Illumina) except PCR primers (it is use as sequencing primers). [Protocol Kozich et al. 2013]
                Combined(out_notcombined_R1, out_notcombined_R2, "X"*100, art_out_cutadapt ).submit(log_file)
            # filter on length, N 
            MultiFilter(art_out_cutadapt, None, min_len, max_len, 0, None, art_out_Nfilter, None, art_log_Nfilter, args).submit(log_file)
            ReplaceJoinTag(art_out_Nfilter, "X"*100, "N"*100, art_out_XtoN ).submit(log_file)
            DerepBySample(out_NAndLengthfilter + " " + art_out_XtoN, out_file, out_count).submit(log_file)
        else:
            DerepBySample(out_NAndLengthfilter, out_file, out_count).submit(log_file)
        
    finally:
        if not args.debug:
            tmp_files.deleteAll()


def parallel_submission( function, R1_files, R2_files, samples_names, filtered_files, art_filtered_files, length_files, log_files, nb_processses_used, args):
    processes = [{'process':None, 'R1_files':[], 'R2_files':[], 'samples_names':[], 'filtered_files':[], 'art_filtered_files':[], 'lengths_files':[], 'log_files':[]} for idx in range(nb_processses_used)]
    # Set processes
    for idx in range(len(R1_files)):
        process_idx = idx % nb_processses_used
        processes[process_idx]['R1_files'].append(R1_files[idx])
        if not args.already_contiged:
            processes[process_idx]['R2_files'].append(R2_files[idx])
        processes[process_idx]['samples_names'].append(samples_names[idx])
        processes[process_idx]['filtered_files'].append(filtered_files[idx])
        processes[process_idx]['art_filtered_files'].append(art_filtered_files[idx])
        processes[process_idx]['lengths_files'].append(length_files[idx])
        processes[process_idx]['log_files'].append(log_files[idx])
    # Launch processes
    for current_process in processes:
        if idx == 0: # First process is threaded with parent job
            current_process['process'] = threading.Thread( target=function, 
                                                            args=(current_process['R1_files'], current_process['R2_files'], current_process['samples_names'], current_process['filtered_files'], current_process['art_filtered_files'], current_process['lengths_files'], current_process['log_files'], args) )
        else: # Others processes are processed on different CPU
            current_process['process'] = multiprocessing.Process( target=function, 
                                                            args=(current_process['R1_files'], current_process['R2_files'], current_process['samples_names'], current_process['filtered_files'], current_process['art_filtered_files'], current_process['lengths_files'], current_process['log_files'], args) )
        current_process['process'].start()
    # Wait processes end
    for current_process in processes:
        current_process['process'].join()
    # Check processes status
    for current_process in processes:
        if issubclass(current_process['process'].__class__, multiprocessing.Process) and current_process['process'].exitcode != 0:
            raise_exception( Exception( "\n\n#ERROR : Error in sub-process execution.\n\n" ))


def process( args ):
    tmp_files = TmpFiles( os.path.split(args.output_fasta)[0] )
    output_dir = os.path.abspath(tmp_files.tmp_dir)

    # Process
    try:
        samples_names = list()
        R1_files = list()
        R2_files = list()
        filtered_files = list()
        log_files = list()

        # Inputs
        if args.input_archive is not None: # input is an archive
            samples_from_tar( args.input_archive, args.already_contiged, tmp_files, R1_files, R2_files, samples_names )
        else:  # inputs are files
            R1_files = link_inputFiles(args.input_R1, tmp_files, args.log_file)
            if args.sequencer == "illumina" or args.sequencer == "longreads":
                if args.R2_size is not None:
                    R2_files = link_inputFiles(args.input_R2, tmp_files, args.log_file)

            samples_names = [os.path.basename(current_R1).split('.')[0] for current_R1 in args.input_R1]
            if args.samples_names is not None:
                samples_names = args.samples_names

        if len(samples_names) != len(set(samples_names)):
            raise_exception( Exception( '\n\n#ERROR : Impossible to retrieve unique samples names from files. The sample name must be before the first dot.\n\n' ))
        
        
        if args.swarm == True:
            # Tmp files
            filtered_files = [tmp_files.add(current_sample + '_filtered.fasta') for current_sample in samples_names]
            art_filtered_files = [tmp_files.add(current_sample + '_artComb_filtered.fasta') for current_sample in samples_names]
            lengths_files = [tmp_files.add(current_sample + '_lengths.json') for current_sample in samples_names]
            log_files = [tmp_files.add(current_sample + '_log.txt') for current_sample in samples_names]

            # Filter
            nb_processses_used = min( len(R1_files), args.nb_cpus )
            if nb_processses_used == 1:
                filter_process_multiples_files( R1_files, R2_files, samples_names, filtered_files, art_filtered_files, lengths_files, log_files, args )
            else:
                parallel_submission( filter_process_multiples_files, R1_files, R2_files, samples_names, filtered_files, art_filtered_files, lengths_files, log_files, nb_processses_used, args)

            # Write summary
            log_append_files( args.log_file, log_files )

            # Dereplicate global on combined filtered cutadapted multifiltered derep
            Logger.static_write(args.log_file, '##Sample\nAll\n##Commands\n')
            DerepGlobalMultiFasta(filtered_files, samples_names, tmp_files.add('derep_inputs.tsv'), args.output_dereplicated, args.output_count, args).submit( args.log_file )
            

            # Check the number of sequences after filtering
            nb_seq = get_nb_seq(args.output_dereplicated)
            if  nb_seq == 0:
                raise_exception( Exception( "\n\n#ERROR : The filters have eliminated all sequences (see summary for more details).\n\n" ))

            # Temporary files
            filename_woext = os.path.split(args.output_dereplicated)[1].split('.')[0]
            
            #clustering_log = tmp_files.add( filename_woext + '_clustering_log.txt' )
            
            #Clustering(args.output_dereplicated, args.output_count, args.distance, args.fastidious, args.output_compo, args.output_fasta, args.output_biom, clustering_log, args.nb_cpus).submit( args.log_file)
            Logger.static_write(args.log_file, "## Application\nSoftware :" + sys.argv[0] + " (version : " + str(__version__) + ")\nCommand : " + " ".join(sys.argv) + "\n\n")

            if args.distance == 1 and args.denoising:
                Logger.static_write(args.log_file, "Warning: using the denoising option with a distance of 1 is useless. The denoising option is cancelled\n\n")
                args.denoising = False

            sorted_fasta = tmp_files.add( filename_woext + '_sorted.fasta' )
            replaceN_fasta = tmp_files.add( filename_woext + '_sorted_NtoA.fasta' )
            final_sorted_fasta = replaceN_fasta
            swarms_file = args.output_compo
            swarms_seeds = tmp_files.add( filename_woext + '_final_seeds.fasta' )
            swarm_log = tmp_files.add( filename_woext + '_swarm_log.txt' )

            SortFasta( args.output_dereplicated, sorted_fasta, args.debug ).submit( args.log_file )
            Logger.static_write(args.log_file, "repalce 100 N tags by 50A-50C in: " + sorted_fasta + " out : "+ replaceN_fasta +"\n")
            replaceNtags(sorted_fasta, replaceN_fasta)

            if args.denoising and args.distance > 1:
                # Denoising
                denoising_log = tmp_files.add( filename_woext + '_denoising_log.txt' )
                denoising_compo = tmp_files.add( filename_woext + '_denoising_composition.txt' )
                denoising_seeds = tmp_files.add( filename_woext + '_denoising_seeds.fasta' )
                denoising_resized_seeds = tmpFiles.add( filename_woext + '_denoising_resizedSeeds.fasta' )
                swarms_file = tmp_files.add( filename_woext + '_swarmD' + str(args.distance) + '_composition.txt' )
                final_sorted_fasta = tmp_files.add( filename_woext + '_denoising_sortedSeeds.fasta' )

                Swarm( replaceN_fasta, denoising_compo, denoising_log, 1 , args.fastidious, args.nb_cpus ).submit( args.log_file )
                ExtractSwarmsFasta( replaceN_fasta, denoising_compo, denoising_seeds ).submit( args.log_file )
                resizeSeed( denoising_seeds, denoising_compo, denoising_resized_seeds ) # add size to seeds name
                SortFasta( denoising_resized_seeds, final_sorted_fasta, args.debug, "_" ).submit( args.log_file )

            Swarm( final_sorted_fasta, swarms_file, swarm_log, args.distance, args.fastidious, args.nb_cpus ).submit( args.log_file )

            if args.denoising and args.distance > 1:
                # convert cluster composition in read composition ==> final swarm composition
                agregate_composition(denoising_compo, swarms_file, args.output_compo)

            Swarm2Biom( args.output_compo, args.output_count, args.output_biom ).submit( args.log_file )
            ExtractSwarmsFasta( final_sorted_fasta, swarms_file, swarms_seeds ).submit( args.log_file )
            Logger.static_write(args.log_file, "replace 50A-50C  tags by N. in: " + swarms_seeds + " out : "+ args.output_fasta +"\n")
            addNtags(swarms_seeds, args.output_fasta)
            

        else:
            R1_cutadapted_files = [tmp_files.add(current_sample + '_cutadapt_R1.fastq.gz') for current_sample in samples_names]
            R2_cutadapted_files = [tmp_files.add(current_sample + '_cutadapt_R2.fastq.gz') for current_sample in samples_names]
            lengths_files = [tmp_files.add(current_sample + '_lengths.json') for current_sample in samples_names]
            log_files = [tmp_files.add(current_sample + '_log.txt') for current_sample in samples_names]

            nb_processses_used = min( len(R1_files), args.nb_cpus )
            if nb_processses_used == 1:
                clean_before_denoising_process_multiples_files( R1_files, R2_files, samples_names, R1_cutadapted_files, R2_cutadapted_files, lengths_files, log_files, args )
            else:
                parallel_submission( clean_before_denoising_process_multiples_files, R1_files, R2_files, samples_names, R1_cutadapted_files, R2_cutadapted_files, lengths_files, log_files, nb_processses_used, args)
            # Write summary
            log_append_files( args.log_file, log_files )
            
            R_stderr = tmp_files.add("dada2.stderr")
            tmp_output_filenames = tmp_files.add("tmp_output_filenames")
            Logger.static_write(args.log_file, '##Sample\nAll\n##Commands\n')
            R1_files = [os.path.abspath(file) for file in R1_files]
            R2_files = [os.path.abspath(file) for file in R2_files]

            #Logger.static_write(args.log_file, '##Sample\nAll\n##Commands\n')
            
            try:
                Dada2Core(R1_cutadapted_files, R2_cutadapted_files, output_dir, args.nb_cpus, tmp_output_filenames, R_stderr, args.pseudo_pooling).submit(args.log_file)
            except subprocess.CalledProcessError as e:
                f = open(R_stderr,"r")
                print(f.read())
                raise_exception( Exception( "\n\n#ERROR : "+ "Error while running DADA2 \n\n" ))
                

                
            
            R1_files = list()
            R2_files = list()
            with open(tmp_output_filenames) as FH_input:
                for li in FH_input:
                    li = li.strip().split(',')
                    R1_files.append(li[0])
                    R2_files.append(li[1])

            filtered_files = [tmp_files.add(current_sample + '_filter.fasta') for current_sample in samples_names]
            
            art_filtered_files = [tmp_files.add(current_sample + '_artComb_filter.fasta') for current_sample in samples_names]
            
            nb_processses_used = min( len(R1_files), args.nb_cpus )
            if nb_processses_used == 1:
                process_sample_after_denoising_multiple_files( R1_files, R2_files, samples_names, filtered_files, art_filtered_files, lengths_files, log_files, args )
            else:
                parallel_submission( process_sample_after_denoising_multiple_files, R1_files, R2_files, samples_names, filtered_files, art_filtered_files, lengths_files, log_files, nb_processses_used, args)

            # Write summary
            log_append_files( args.log_file, log_files )
            
            # Global dereplication
            Logger.static_write(args.log_file, '##Sample\nAll\n##Commands\n')
            DerepGlobalMultiFasta(filtered_files, samples_names, tmp_files.add('derep_inputs.tsv'), args.output_dereplicated, args.output_count, args).submit( args.log_file )
            summarise_results_dada2( samples_names, lengths_files, log_files, args )

            # Check the number of sequences after filtering
            nb_seq = get_nb_seq(args.output_dereplicated)
            if  nb_seq == 0:
                raise_exception( Exception( "\n\n#ERROR : The filters have eliminated all sequences (see summary for more details).\n\n" ))
            to_biom_and_fasta(args.output_count, args.output_dereplicated, args.output_biom, args.output_fasta)
    
        Logger.static_write(args.log_file, "## Application\nSoftware :" + sys.argv[0] + " (version : " + str(__version__) + ")\nCommand : " + " ".join(sys.argv) + "\n\n")

        classif_file = tmp_files.add( "HClassif.newick" )
        classif_log = tmp_files.add( "HClassif_log.txt" )
        #HClassification(args.output_biom, classif_file, classif_log, args.distance_method, args.linkage_method).submit( args.log_file )
        HClassification(args.output_biom, classif_file, classif_log, "braycurtis", "average").submit( args.log_file )

        depth_file = tmp_files.add( "depths.tsv" )
        Depths(args.output_biom, depth_file).submit( args.log_file )
        #if args.swarm == True:
        summarise_results( samples_names, lengths_files, args.output_biom, depth_file, classif_file, log_files, args )
        #else:
        #    summarise_results_dada2( samples_names, lengths_files, args.output_biom, depth_file, classif_file, log_files, args )


    finally:    
        if not args.debug:
            tmp_files.deleteAll()
            if not args.swarm:
                for f in R1_files:
                    os.remove(f)
                for f in R2_files:
                    os.remove(f)

def spl_name_type( arg_value ):
    """
    @summary: Argparse type for samples-names.
    """
    if re.search("\s", arg_value): raise_exception( argparse.ArgumentTypeError( "\n\n#ERROR : A sample name must not contain white spaces.\n\n" ))
    return str(arg_value)

def to_biom_and_fasta(count_file, fasta_file, output_biom, output_fasta):
    """
    @summary : Write a biom file from swarm results.
    @param clusters_file : [str] path to the '.clstr' file.
    @param count_file : [str] path to the count file. It contains the count of
                         sequences by sample of each preclusters.
                         Line format : "Precluster_id    nb_in_sampleA    nb_in_sampleB"
    @param output_biom : [str] path to the output file.
    @param size_separator : [str] the pre-cluster abundance separator.
    """
    biom = Biom( generated_by='dada2', matrix_type="sparse" )
        
    in_fasta_fh = FastaIO( fasta_file )
    out_fasta_fh = FastaIO( output_fasta, "wt")
    cpt=1
    for record in in_fasta_fh:
        if "FROGS_combined" in record.id:
            record.id = "Cluster_"+str(cpt)+"_FROGS_combined"
        else:
            record.id = "Cluster_"+str(cpt)
        out_fasta_fh.write(record)
        cpt+=1
    in_fasta_fh.close()
    out_fasta_fh.close()
    
    # Preclusters count by sample
    preclusters_count = dict()
    count_fh = open( count_file )
    samples = count_fh.readline().strip().split()[1:]
    
    cpt=1
    for line in count_fh:
        precluster_id, count_str = line.strip().split(None, 1)
        preclusters_count[cpt] = count_str # For large dataset store count into a string consumes minus RAM than a sparse count
        cpt+=1
    count_fh.close()
    
    # Add samples
    for sample_name in samples:
        biom.add_sample( sample_name )

    # Process count
    cluster_idx = 1
    clusters_fh = open( count_file )
    for line in clusters_fh:
        if not line.startswith("#"):
            seq_id = line.strip().split()[0]
            if "FROGS_combined" in seq_id:
                cluster_name = "Cluster_" + str(cluster_idx) + "_FROGS_combined"
                comment = ["FROGS_combined"]
            else:
                cluster_name = "Cluster_" + str(cluster_idx)
                comment = list()
            cluster_count = {key:0 for key in samples}
            line_fields = line.strip().split()
            
            sample_counts = preclusters_count[cluster_idx].split("\t")
            for sample_idx, sample_name in enumerate(samples):
                cluster_count[sample_name] += int(sample_counts[sample_idx])
            preclusters_count[cluster_idx] = None
            
            # Add cluster on biom
            biom.add_observation( cluster_name, {'comment': comment, 'seed_id':""} )
            observation_idx = biom.find_idx("observation", cluster_name)
            for sample_idx, sample_name in enumerate(samples):
                if cluster_count[sample_name] > 0:
                    biom.data.change( observation_idx, sample_idx, cluster_count[sample_name] )
            # Next cluster
            cluster_idx += 1

    # Write
    BiomIO.write( output_biom, biom )

##################################################################################################################################################
#
# MAIN
#
##################################################################################################################################################
if __name__ == "__main__":
    # Manage parameters
    parser = argparse.ArgumentParser( description='Pre-process amplicons to use reads in diversity analysis.' )
    parser.add_argument( '-v', '--version', action='version', version=__version__ )
    subparsers = parser.add_subparsers()
    parser_illumina = subparsers.add_parser( 'illumina', help='Illumina sequencers.', usage='''
  For samples files:
    preprocess.py illumina
      --swarm [--denoising] [--distance DISTANCE] [--fastidious] | --dada2
      --input-R1 R1_FILE [R1_FILE ...]
      --already-contiged | --input-R2 R2_FILE [R2_FILE ...] --R1-size R1_SIZE --R2-size R2_SIZE [--mismatch-rate RATE ] [--quality-scale SCALE ] [--merge-software {vsearch,flash,pear} [--expected-amplicon-size]] [--keep-unmerged]
      --min-amplicon-size MIN_AMPLICON_SIZE
      --max-amplicon-size MAX_AMPLICON_SIZE
      --without-primers | --five-prim-primer FIVE_PRIM_PRIMER --three-prim-primer THREE_PRIM_PRIMER
      [--keep-unmerged]
      [--samples-names SAMPLE_NAME [SAMPLE_NAME ...]]
      [-p NB_CPUS] [--debug] [-v]
      [-d DEREPLICATED_FILE] [-c COUNT_FILE]
      [-b BIOM_FILE] [--output-fasta FASTA_FILE]
      [-s SUMMARY_FILE] [-l LOG_FILE]

  For samples archive:
    preprocess.py illumina
      --swarm [--denoising] [--distance DISTANCE] [--fastidious] | --dada2
      --input-archive ARCHIVE_FILE
      --already-contiged | --R1-size R1_SIZE --R2-size R2_SIZE [--mismatch-rate RATE ] [--quality-scale SCALE ] [--merge-software {vsearch,flash,pear} [--expected-amplicon-size] ] [--keep-unmerged]
      --min-amplicon-size MIN_AMPLICON_SIZE
      --max-amplicon-size MAX_AMPLICON_SIZE
      --without-primers | --five-prim-primer FIVE_PRIM_PRIMER --three-prim-primer THREE_PRIM_PRIMER
      [-p NB_CPUS] [--debug] [-v]
      [-d DEREPLICATED_FILE] [-c COUNT_FILE] [--artComb-output-dereplicated ART_DEREPLICATED_FILE] [--artComb-output-count ART_COUNT_FILE]
      [-b BIOM_FILE] [--output-fasta FASTA_FILE]
      [-s SUMMARY_FILE] [-l LOG_FILE]
''')
    #     Illumina parameters
    parser_illumina.add_argument( '--merge-software', default="vsearch", choices=["vsearch","flash","pear"], help='Software used to merge paired reads' )
    parser_illumina.add_argument( '--keep-unmerged', default=False, action='store_true', help='In case of uncontiged paired reads, keep unmerged, and artificially combined them with 100 Ns.' )
    parser_illumina.add_argument( '--min-amplicon-size', type=int, required=True, help='The minimum size for the amplicons (with primers).' )
    parser_illumina.add_argument( '--max-amplicon-size', type=int, required=True, help='The maximum size for the amplicons (with primers).' )
    parser_illumina.add_argument( '--expected-amplicon-size', type=int, help='The expected size for the majority of the amplicons (with primers), if using Flash as read pair merge software.' )
    parser_illumina.add_argument( '--five-prim-primer', type=str, help="The 5' primer sequence (wildcards are accepted)." )
    parser_illumina.add_argument( '--three-prim-primer', type=str, help="The 3' primer sequence (wildcards are accepted)." )
    parser_illumina.add_argument( '--without-primers', action='store_true', default=False, help="Use this option when you use custom sequencing primers and these primers are the PCR primers. In this case the reads do not contain the PCR primers." )
    parser_illumina.add_argument( '--R1-size', type=int, help='The read1 size.' )
    parser_illumina.add_argument( '--R2-size', type=int, help='The read2 size.' )
    parser_illumina.add_argument( '--mismatch-rate', type=float, default=0.1, help='Maximum mismatch rate in overlap region. [Default: %(default)s; must be expressed as decimal, between 0 and 1]' )
    parser_illumina.add_argument( '--quality-scale', type=str, default="33", choices=["33", "64"], help='The phred base quality scale, either 33 or 64 if using Vsearch as read pair merge software [Default: %(default)s]' )
    parser_illumina.add_argument( '--already-contiged', action='store_true', default=False, help='The archive contains 1 file by sample : Reads 1 and Reads 2 are already contiged by pair.' )
    parser_illumina.add_argument( '--dada2', action='store_true', default=False, help='Build ASVs from reads.' )
    parser_illumina.add_argument( '--swarm', action='store_true', default=False, help='Build OTUs from reads.' )   
    group_clustering = parser_illumina.add_argument_group( 'Clustering options' )
    group_clustering.add_argument( '-n', '--denoising', default=False, action='store_true',  help="denoise data by clustering read with distance=1 before perform real clustering. It is mutually exclusive with --fastidious." )
    group_clustering.add_argument( '-d', '--distance', type=int, default=1, help="Maximum distance between sequences in each aggregation step. RECOMMENDED : d=1 in combination with --fastidious option [Default: %(default)s]" )
    group_clustering.add_argument( '--fastidious', default=False, action='store_true',  help="use the fastidious option of swarm to refine OTU. RECOMMENDED in combination with a distance equal to 1 (-d). it is only usable with d=1 and mutually exclusive with --denoising." )
    group_clustering.add_argument( '--output-compo', default='clustering_swarms_composition.tsv', help='This output file will contain the composition of each cluster (format: TSV). One Line is a cluster ; each column is a sequence ID. [Default: %(default)s]')
    group_denoising = parser_illumina.add_argument_group( 'Denoising options' )
    group_denoising.add_argument( '--pseudo-pooling', default=False, action='store_true',  help="Perform dada2 pseudo-pooling to reduce inconvenients of independent sample processing" )
    parser_illumina.add_argument( '-p', '--nb-cpus', type=int, default=1, help="The maximum number of CPUs used. [Default: %(default)s]" )
    parser_illumina.add_argument( '--debug', default=False, action='store_true', help="Keep temporary files to debug program." )
    #     Illumina inputs
    group_illumina_input = parser_illumina.add_argument_group( 'Inputs' )
    group_illumina_input.add_argument( '--samples-names', type=spl_name_type, nargs='+', default=None, help='The sample name for each R1/R2-files.' )
    group_illumina_input.add_argument( '--input-archive', default=None, help='The tar file containing R1 file and R2 file for each sample.' )
    group_illumina_input.add_argument( '--input-R1', required=None, nargs='+', help='The R1 sequence file for each sample (format: fastq).' )
    group_illumina_input.add_argument( '--input-R2', required=None, nargs='+', help='The R2 sequence file for each sample (format: fastq).' )
    group_illumina_input.set_defaults( sequencer='illumina' )
    #     Illumina outputs
    group_illumina_output = parser_illumina.add_argument_group( 'Outputs' )
    group_illumina_output.add_argument( '--output-dereplicated', default='preprocess.fasta', help='FASTA file with unique sequences. Each sequence has an ID ended with the number of initial sequences represented (example : ">a0101;size=10"). [Default: %(default)s]')
    group_illumina_output.add_argument( '-c', '--output-count', default='preprocess_counts.tsv', help='TSV file with count by sample for each unique sequence (example with 3 samples : "a0101<TAB>5<TAB>8<TAB>0"). [Default: %(default)s]')
    group_illumina_output.add_argument( '-b', '--output-biom', default='clustering_abundance.biom', help='This output file will contain the abundance by sample for each OTU or ASV (format: BIOM). [Default: %(default)s]')
    group_illumina_output.add_argument( '--output-fasta', default='sequences.fasta', help='This output file will contain the sequence for each OTU or ASV (format: FASTA). [Default: %(default)s]')
    group_illumina_output.add_argument( '-s', '--summary', default='preprocess.html', help='The HTML file containing the graphs. [Default: %(default)s]')
    group_illumina_output.add_argument( '-l', '--log-file', default=sys.stdout, help='This output file will contain several information on executed commands.')


    parser_longreads = subparsers.add_parser( 'longreads', help='longreads sequencers.', usage='''
    preprocess.py longreads
    --input-archive ARCHIVE_FILE | --input-R1 R1_FILE [R1_FILE ...]
    --min-amplicon-size MIN_AMPLICON_SIZE
    --max-amplicon-size MAX_AMPLICON_SIZE
    --without-primers | --five-prim-primer FIVE_PRIM_PRIMER --three-prim-primer THREE_PRIM_PRIMER
    [-p NB_CPUS] [--debug] [-v]
    [-d DEREPLICATED_FILE] [-c COUNT_FILE]
    [-s SUMMARY_FILE] [-l LOG_FILE]
''')
    #     Long-reads parameters
    parser_longreads.add_argument( '--min-amplicon-size', type=int, required=True, help='The minimum size for the amplicons (with primers).' )
    parser_longreads.add_argument( '--max-amplicon-size', type=int, required=True, help='The maximum size for the amplicons (with primers).' )
    parser_longreads.add_argument( '--five-prim-primer', type=str, help="The 5' primer sequence (wildcards are accepted)." )
    parser_longreads.add_argument( '--three-prim-primer', type=str, help="The 3' primer sequence (wildcards are accepted)." )
    parser_longreads.add_argument( '--without-primers', action='store_true', default=False, help="Use this option when you use custom sequencing primers and these primers are the PCR primers. In this case the reads do not contain the PCR primers." )
    parser_longreads.add_argument( '-p', '--nb-cpus', type=int, default=1, help="The maximum number of CPUs used. [Default: %(default)s]" )
    parser_longreads.add_argument( '--debug', default=False, action='store_true', help="Keep temporary files to debug program." )
    # Long-reads inputs
    group_longreads_input = parser_longreads.add_argument_group('Inputs')
    group_longreads_input.add_argument('--input-archive', default=None,
                                  help='The tar file containing R1 file and R2 file for each sample (format: tar).')
    group_longreads_input.add_argument('--samples-names', type=spl_name_type,
                                  nargs='+', default=None, help='The sample name for each R1/R2-files.')
    group_longreads_input.add_argument( '--input-R1', required=None, nargs='+', help='The R1 sequence file for each sample (format: fastq). Required for single-ends OR paired-ends data.' )
    group_clustering_longreads = parser_longreads.add_argument_group( 'Clustering options' )
    group_clustering_longreads.add_argument( '-n', '--denoising', default=False, action='store_true',  help="denoise data by clustering read with distance=1 before perform real clustering. It is mutually exclusive with --fastidious." )
    group_clustering_longreads.add_argument( '-d', '--distance', type=int, default=1, help="Maximum distance between sequences in each aggregation step. RECOMMENDED : d=1 in combination with --fastidious option [Default: %(default)s]" )
    group_clustering_longreads.add_argument( '--fastidious', default=False, action='store_true',  help="use the fastidious option of swarm to refine OTU. RECOMMENDED in combination with a distance equal to 1 (-d). it is only usable with d=1 and mutually exclusive with --denoising." )
    group_clustering_longreads.add_argument( '--output-compo', default='clustering_swarms_composition.tsv', help='This output file will contain the composition of each cluster (format: TSV). One Line is a cluster ; each column is a sequence ID. [Default: %(default)s]')
    # Long-reads outputs
    group_longreads_output = parser_longreads.add_argument_group( 'Outputs' )
    group_longreads_output.add_argument( '--output-dereplicated', default='preprocess.fasta', help='FASTA file with unique sequences. Each sequence has an ID ended with the number of initial sequences represented (example : ">a0101;size=10"). [Default: %(default)s]')
    group_longreads_output.add_argument( '-c', '--output-count', default='preprocess_counts.tsv', help='TSV file with count by sample for each unique sequence (example with 3 samples : "a0101<TAB>5<TAB>8<TAB>0"). [Default: %(default)s]')
    group_longreads_output.add_argument( '-s', '--summary', default='preprocess.html', help='The HTML file containing the graphs. [Default: %(default)s]')
    group_longreads_output.add_argument( '-l', '--log-file', default=sys.stdout, help='This output file will contain several information on executed commands.')
    group_longreads_output.add_argument( '-b', '--output-biom', default='clustering_abundance.biom', help='This output file will contain the abundance by sample for each OTU or ASV (format: BIOM). [Default: %(default)s]')
    group_longreads_output.add_argument( '--output-fasta', default='sequences.fasta', help='This output file will contain the sequence for each OTU or ASV (format: FASTA). [Default: %(default)s]')
    parser_longreads.set_defaults( sequencer='longreads', already_contiged=True, keep_unmerged=False )

    # 454
    parser_454 = subparsers.add_parser('454', help='454 sequencers.', usage='''
  preprocess.py 454
    --input-archive ARCHIVE_FILE | --input-R1 R1_FILE [R1_FILE ...]
    --min-amplicon-size MIN_AMPLICON_SIZE
    --max-amplicon-size MAX_AMPLICON_SIZE
    --five-prim-primer FIVE_PRIM_PRIMER
    --three-prim-primer THREE_PRIM_PRIMER
    [-p NB_CPUS] [--debug] [-v]
    [-d DEREPLICATED_FILE] [-c COUNT_FILE]
    [-s SUMMARY_FILE] [-l LOG_FILE]
''')
    parser_454.add_argument( '--min-amplicon-size', type=int, required=True, help='The minimum size for the amplicons (with primers).' )
    parser_454.add_argument( '--max-amplicon-size', type=int, required=True, help='The maximum size for the amplicons (with primers).' )
    parser_454.add_argument( '--five-prim-primer', type=str, required=True, help="The 5' primer sequence (wildcards are accepted)." )
    parser_454.add_argument( '--three-prim-primer', type=str, required=True, help="The 3' primer sequence (wildcards are accepted)." )
    parser_454.add_argument( '-p', '--nb-cpus', type=int, default=1, help="The maximum number of CPUs used. [Default: %(default)s]" )
    parser_454.add_argument( '--debug', default=False, action='store_true', help="Keep temporary files to debug program." )
    #     454 inputs
    group_454_input = parser_454.add_argument_group( 'Inputs' )
    group_454_input.add_argument( '--samples-names', type=spl_name_type, nargs='+', default=None, help='The sample name for each R1/R2-files.' )
    group_454_input.add_argument( '--input-archive', default=None, help='The tar file containing R1 file and R2 file for each sample (format: tar).' )
    group_454_input.add_argument( '--input-R1', required=None, nargs='+', help='The sequence file for each sample (format: fastq).' )
    group_454_input.set_defaults( sequencer='454' )
    #     454 outputs
    group_454_output = parser_454.add_argument_group( 'Outputs' )
    group_454_output.add_argument( '-d', '--output-dereplicated', default='preprocess.fasta', help='FASTA file with unique sequences. Each sequence has an ID ended with the number of initial sequences represented (example : ">a0101;size=10"). [Default: %(default)s]')
    group_454_output.add_argument( '-c', '--output-count', default='preprocess_counts.tsv', help='TSV file with count by sample for each unique sequence (example with 3 samples : "a0101<TAB>5<TAB>8<TAB>0"). [Default: %(default)s]')
    #group_illumina_output.add_argument( '-d', '--output-dereplicated', default='preprocess.fasta', help='FASTA file with unique sequences. Each sequence has an ID ended with the number of initial sequences represented (example : ">a0101;size=10"). [Default: %(default)s]')
    #group_illumina_output.add_argument( '-c', '--output-count', default='preprocess_counts.tsv', help='TSV file with count by sample for each unique sequence (example with 3 samples : "a0101<TAB>5<TAB>8<TAB>0"). [Default: %(default)s]')
    group_454_output.add_argument( '-b', '--output-biom', default='abundance.biom', help='This output file will contain the abundance by sample for each OTU or ASV (format: BIOM). [Default: %(default)s]')
    group_454_output.add_argument( '--output-fasta', default='sequences.fasta', help='This output file will contain the sequence for each OTU or ASV (format: FASTA). [Default: %(default)s]')
    group_454_output.add_argument( '-s', '--summary', default='preprocess.html', help='The HTML file containing the graphs. [Default: %(default)s]')
    group_454_output.add_argument( '-l', '--log-file', default=sys.stdout, help='This output file will contain several information on executed commands.')
    parser_454.set_defaults( sequencer='454', already_contiged=True, keep_unmerged=False )


    # Parse parameters
    args = parser.parse_args()
    prevent_shell_injections(args)
    
    Logger.static_write(args.log_file, "## Application\nSoftware: " + os.path.basename(sys.argv[0]) + " (version: " + str(__version__) + ")\nCommand: " + " ".join(sys.argv) + "\n\n")
    
    # Check parameters
    if args.input_archive is not None: # input is an archive
        if args.input_R1 is not None: raise_exception( argparse.ArgumentTypeError( "\n\n#ERROR : With '--archive-file' parameter you cannot set the parameter '--R1-files'.\n\n" ))
        if args.samples_names is not None: raise_exception( argparse.ArgumentTypeError( "\n\n#ERROR : With '--archive-file' parameter you cannot set the parameter '--samples-names'.\n\n" ))
        if args.sequencer == "illumina":
            if args.input_R2 is not None: raise_exception( argparse.ArgumentTypeError( "\n\n#ERROR : With '--archive-file' parameter you cannot set the parameter '--R2-files'.\n\n" ))
        
    else:  # inputs are files
        if args.input_R1 is None: raise_exception( argparse.ArgumentTypeError( "\n\n#ERROR : '--R1-files' is required.\n\n" ))
        if args.samples_names is not None:
            if len(args.samples_names) != len(args.input_R1): raise_exception( argparse.ArgumentTypeError( "\n\n#ERROR : With '--samples-names' all samples must have a name.\n\n" ))
            if len(args.samples_names) != len(set(args.samples_names)):
                duplicated_samples = set([name for name in args.samples_names if args.samples_names.count(name) > 1])
                raise_exception( argparse.ArgumentTypeError( '\n\n#ERROR : Samples names must be unique (duplicated: "' + '", "'.join(duplicated_samples) + '").\n\n' ))
        
        if args.sequencer == "illumina" or args.sequencer == "longreads":
            if not args.already_contiged and args.input_R2 is None: raise_exception( argparse.ArgumentTypeError( "\n\n#ERROR : '--R2-files' is required.\n\n" ))

    if args.sequencer == "illumina" or args.sequencer == "longreads":
        if args.without_primers:
            if args.five_prim_primer or args.three_prim_primer: raise_exception( argparse.ArgumentTypeError( "\n\n#ERROR : The option '--without-primers' cannot be used with '--five-prim-primer' and '--three-prim-primer'.\n\n" ))
        else:
            if args.five_prim_primer is None or args.three_prim_primer is None: raise_exception( argparse.ArgumentTypeError( "\n\n#ERROR : '--five-prim-primer/--three-prim-primer' or 'without-primers'  must be setted.\n\n" ))
            if args.min_amplicon_size <= (len(args.five_prim_primer) + len(args.three_prim_primer)): raise_exception( argparse.ArgumentTypeError( "\n\n#ERROR : The minimum length of the amplicon (--min-length) must be superior to the size of the two primers, i.e "+str(len(args.five_prim_primer) + len(args.three_prim_primer)) + "\n\n"))

    if args.sequencer == "illumina":
        if (args.R1_size is None or args.R2_size is None ) and not args.already_contiged: raise_exception( Exception( "\n\n#ERROR : '--R1-size/--R2-size' or '--already-contiged' must be setted.\n\n" ))
        if (args.already_contiged and args.keep_unmerged): raise_exception( Exception("\n\n#ERROR : --already-contiged and keep-unmerged options cannot be used together\n\n"))
        if (not args.already_contiged):
            if args.merge_software == "flash":
                if args.expected_amplicon_size is None: raise_exception( argparse.ArgumentTypeError( "\n\n#ERROR : With '--merge-software flash' you need to set the parameter '--expected-amplicon-size'.\n\n" ))

        if args.mismatch_rate and args.mismatch_rate < 0 or args.mismatch_rate > 1:
            raise_exception( argparse.ArgumentTypeError( "\n\n#ERROR : mismatch-rate option need to be included between 0 and 1.\n\n" ))

    if args.sequencer == "longreads":
        args.swarm = True
        args.keep_unmerged = False
        
    if args.denoising and args.fastidious:
        raise_exception( parser.error("\n#ERROR : --fastidious and --denoising are mutually exclusive.\n\n"))
    if args.distance > 1 and args.fastidious:
        raise_exception( parser.error("\n#ERROR : --fastidious is not allowed with d>1.\n\n"))

    # Process
    process( args )
