#!/usr/bin/env python3
# -*-coding:Utf-8 -*
__author__ = ' Moussa Samb & Maria Bernard & Vincent Darbot & Geraldine Pascal INRAE - SIGENAE '
__copyright__ = 'Copyright (C) 2020 INRAE'
__license__ = 'GNU General Public License'
__version__ = '1.0'
__email__ = 'frogs@inrae.fr'
__status__ = 'dev'

import os
import re
import sys
import json
import glob
import gzip
import shutil
import inspect
import argparse
import pandas as pd

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# PATH: executable
BIN_DIR = os.path.abspath(os.path.join(os.path.dirname(CURRENT_DIR), "libexec"))
os.environ['PATH'] = BIN_DIR + os.pathsep + os.environ['PATH'] 
# PYTHONPATH
LIB_DIR = os.path.abspath(os.path.join(os.path.dirname(CURRENT_DIR), "lib"))
sys.path.append(LIB_DIR) 
if os.getenv('PYTHONPATH') is None: os.environ['PYTHONPATH'] = LIB_DIR 
else: os.environ['PYTHONPATH'] = os.environ['PYTHONPATH'] + os.pathsep + LIB_DIR
DESCRIPTION_FILE = os.path.abspath(os.path.join(os.path.dirname(CURRENT_DIR), "default_files/pathways_description_file.txt.gz"))
PATHWAYS_HIERARCHY_FILE = os.path.abspath(os.path.join(os.path.dirname(CURRENT_DIR), "default_files/pathways_hierarchy.tsv"))


#import frogs
from frogsUtils import *
from frogsSequenceIO import * 
from frogsBiom import BiomIO

##################################################################################################################################################
#
# COMMAND LINES 
#
##################################################################################################################################################
class PathwayPipeline(Cmd):
	"""
	@summary: pathway_pipeline.py : Infer the presence and abundances of pathways based on gene family abundances in a sample.
	"""
	def __init__(self, input_file, map_file, per_sequence_contrib, per_sequence_abun, per_sequence_function, no_regroup, pathways_abund, pathways_contrib, pathways_predictions, pathways_abund_per_seq, log):
		opt = ''
		if per_sequence_contrib:
			opt = ' --per_sequence_contrib --per_sequence_abun ' +  per_sequence_abun + ' --per_sequence_function ' + per_sequence_function 
		if map_file is not None:
			opt += " --map " + map_file
		if no_regroup:
			opt += " --no_regroup "

		Cmd.__init__(self,
				 'pathway_pipeline.py ',
				 'predict abundance pathway', 
				  " --input " + input_file + " --out_dir ./ " + opt + ' 2> ' + log,
				"--version")

		self.pathways_abund = pathways_abund
		self.per_sequence_contrib = per_sequence_contrib
		self.pathways_contrib = pathways_contrib
		self.pathways_predictions = pathways_predictions
		self.pathways_abund_per_seq = pathways_abund_per_seq
		
	def get_version(self):
		 return Cmd.get_version(self, 'stdout').split()[1].strip()

	def parser(self, log_file):
		START_PATHWAY_LINK = "https://biocyc.org/META/NEW-IMAGE?type=PATHWAY&object="
		f_in = gzip.open('path_abun_unstrat.tsv.gz', 'rt').readlines()
		f_out = open(self.pathways_abund, 'wt')
		header = f_in[0].strip().split('\t')
		header.insert(0,'db_link')
		f_out.write("\t".join(header)+"\n")
		for li in f_in[1:]:
			li = li.strip().split('\t')
			function = li[0]
			li.insert(0,START_PATHWAY_LINK + function )
			f_out.write("\t".join(li)+"\n")
		os.remove('path_abun_unstrat.tsv.gz')
		if self.per_sequence_contrib:
			with gzip.open('path_abun_contrib.tsv.gz', 'rb') as f_in:
				with open(self.pathways_contrib, 'wb') as f_out:
					shutil.copyfileobj(f_in, f_out)
				os.remove('path_abun_contrib.tsv.gz')
			with gzip.open('path_abun_predictions.tsv.gz', 'rb') as f_in:
				with open(self.pathways_predictions, 'wb') as f_out:
					shutil.copyfileobj(f_in, f_out)
				os.remove('path_abun_predictions.tsv.gz')
			with gzip.open('path_abun_unstrat_per_seq.tsv.gz', 'rb') as f_in:
				with open(self.pathways_abund_per_seq, 'wb') as f_out:
					shutil.copyfileobj(f_in, f_out)
				os.remove('path_abun_unstrat_per_seq.tsv.gz')

class Biom2tsv(Cmd):
	"""
	@summary: Converts BIOM file to TSV file.
	"""
	def __init__(self, in_biom, out_tsv):

		Cmd.__init__( self,
					  'biom2tsv.py',
					  'Converts a BIOM file in TSV file.',
					  "--input-file " + in_biom + " --output-file " + out_tsv,
					  '--version' )

	def get_version(self):
		 return Cmd.get_version(self, 'stdout').strip()

class Tsv2biom(Cmd):
	"""
	@summary: In order to creates a temporary biom file that links every pathway to samples abundances.
	This is necessary in order to display sunburst plots.

	"""
	def __init__(self, in_tsv, out_biom):

		Cmd.__init__( self,
					  'tsv_to_biom.py',
					  'Converts a BIOM file in TSV file.',
					  "--input-tsv " + in_tsv + " --output-biom " + out_biom,
					  '--version' )

	def get_version(self):
		 return Cmd.get_version(self, 'stdout').strip() 


class TaxonomyTree(Cmd):
	"""
	@summary: Produces a tree with pathways abundances by sample in extended newick format.
	"""
	def __init__(self, in_biom, taxonomy_tag, out_tree, out_ids):
		"""
		@param in_biom: [str] The processed BIOM path.
		@param taxonomy_tag: [str] The metadata title for the taxonomy in BIOM file.
		@param out_tree: [str] Path to the enewick output.
		@param out_ids: [str] Path to the IDs/samples output.
		"""
		# Cmd
		Cmd.__init__( self,
					  'biomTools.py',
					  'Produces a taxonomy tree with counts by sample.',
					  'treeCount --input-file ' + in_biom + ' --taxonomy-key "' + taxonomy_tag + '" --output-enewick ' + out_tree + ' --output-samples ' + out_ids,
					  '--version' )
					  
	def get_version(self):   
		return Cmd.get_version(self, 'stdout').strip()  

##################################################################################################################################################
#
# FUNCTIONS
#
##################################################################################################################################################

def formate_input_file(input_file, tmp_tsv):
	"""
	@summary: formate gene abundances file in order to use pathways_pipeline.py
	"""
	FH_in = open(input_file).readlines()
	FH_out = open(tmp_tsv, 'wt')
	header = FH_in[0].strip().split('\t')
	formatted_col = ['classification', 'db_link']
	to_keep = list()
	to_write = list()
	for col_n in range(len(header)):
		if header[col_n] == "observation_name":
			header[col_n] = "function"
		if header[col_n] not in formatted_col:
			to_write.append(header[col_n])
			to_keep.append(col_n)
	FH_out.write('\t'.join(to_write)+'\n')
	for li in FH_in[1:]:
		li = li.strip().split('\t')
		to_write = list()
		for i in range(len(li)):
			if i in to_keep:
				to_write.append(li[i])
		FH_out.write('\t'.join(to_write)+'\n')

def formate_abundances_file(strat_file, pathways_hierarchy_file, hierarchy_tag = "classification"):
	"""
	@summary: Formate FPSTep4 output in order to create a biom file of pathways abundances.
	@param start_file: FPStep4 output of pathway abundances prediction (FPStep4_path_abun_unstrat.tsv)
	@param pathways_hierarchy_file: reference file that links every pathways ID to its hierarchy levels.
	@param tmp_tsv: temporary tsv output of abundances per samples.
	"""
	id_to_hierarchy = {}
	path_fi = open(pathways_hierarchy_file).readlines()
	for li in path_fi:
		li = li.strip().split('\t')
		id_to_hierarchy[li[-1]] = ";".join(li)

	df = pd.read_csv(strat_file,sep='\t')
	df.rename(columns = {'pathway':'observation_name'}, inplace = True)
	headers = ['observation_name', 'db_link']
	for column in df:
		if column not in headers:
			df[column] = df[column].round(0).astype(int)

	df.to_csv(strat_file ,sep='\t', index=False)
	tmp = open(strat_file +'.tmp', 'wt')
	FH_in = open(strat_file).readlines()
	header = FH_in[0].strip().split('\t')
	header.insert(0, hierarchy_tag)
	tmp.write("\t".join(header)+"\n")
	for li in FH_in[1:]:
		li = li.strip().split('\t')
		if li[1] in id_to_hierarchy:
			li.insert(0,id_to_hierarchy[li[1]])
			tmp.write("\t".join(li)+"\n")
	tmp.close()
	os.rename(strat_file+'.tmp', strat_file)
	return hierarchy_tag

def write_summary(strat_file, tree_count_file, tree_ids_file, summary_file):
	"""
	@summary: Writes the process summary in one html file.
	@param summary_file: [str] path to the output html file.
	@param align_out: [str] path to the fasta file of unaligned OTU
	@param biomfile: [str] path to the input BIOM file.
	@param closest_ref_files: [str] Path to tmp colest ref file.
	@param category: ITS or 16S
	"""

	# Get taxonomy distribution
	FH_tree_count = open( tree_count_file )
	newick_tree = FH_tree_count.readline()
	FH_tree_count.close()
	ordered_samples_names = list()
	FH_tree_ids = open( tree_ids_file )
	for line in FH_tree_ids:
		id, sample_name = line.strip().split( "\t", 1 )
		ordered_samples_names.append( sample_name )
	FH_tree_ids.close()
	
	# to summary OTUs number && abundances number			   
	# infos_otus = list()
	# details_categorys =["Pathway", "Description" ,"Observation_sum"]
	# START_METACYC_LINK = "<a href='https://biocyc.org/META/NEW-IMAGE?type=PATHWAY&object="

	# abund = open(strat_file)
	# for li in abund:
	# 	if "pathway" in li:
	# 		li = li.strip().split('\t')
	# 		for sample in li[3:]:
	# 			details_categorys.append(sample)
	# 		break

	# for li in abund:
	# 	li = li.strip().split('\t')
	# 	pathway = li[0]
	# 	li[0] = START_METACYC_LINK + pathway + "'>" + pathway + '</a>'

	# 	for i in range(len(li[2:])):
	# 		li[i+2] = round(float(li[i+2]),1)

	# 	infos_otus.append({
	# 		'name': li[0],
	# 		'data': list(map(str,li[1:]))
	# 		})
	# record details about removed OTU

	FH_summary_tpl = open( os.path.join(CURRENT_DIR, "FPStep4_tpl.html") )
	FH_summary_out = open( summary_file, "wt" )

	for line in FH_summary_tpl:
		if "###TAXONOMIC_RANKS###" in line:
			line = line.replace( "###TAXONOMIC_RANKS###", json.dumps(args.hierarchy_ranks) )
		elif "###SAMPLES_NAMES###" in line:
			line = line.replace( "###SAMPLES_NAMES###", json.dumps(ordered_samples_names) )
		elif "###DATA_SAMPLE###" in line:
			line = line.replace( "###DATA_SAMPLE###", json.dumps(samples_distrib) )
		elif "###TREE_DISTRIBUTION###" in line:
			line = line.replace( "###TREE_DISTRIBUTION###", json.dumps(newick_tree) )
		FH_summary_out.write( line )

	FH_summary_out.close()
	FH_summary_tpl.close()
##################################################################################################################################################
#
# MAIN
#
##################################################################################################################################################
if __name__ == "__main__":

	# Manage parameters
	parser = argparse.ArgumentParser( description='Infer the presence and abundances of pathways based on gene family abundances in a sample.' )
	parser.add_argument('--debug', default=False, action='store_true', help="Keep temporary files to debug program." )
	parser.add_argument('--per_sequence_contrib', default=False, action='store_true', help='Flag to specify that MinPath is run on the genes contributed by each sequence individualy. (in contrast to the default stratified output, which is the contribution to the community-wide pathway abundances.) Options --per_sequence_abun and --per_sequence_function need to be set when this option is used (default: False) ')
	parser.add_argument('--no_regroup', default=False, action='store_true', help='Do not regroup input gene families to reactions as specified in the regrouping mapfile. ')
	# Inputs
	group_input = parser.add_argument_group( 'Inputs' )
	group_input.add_argument('-i', '--input_file', required=True, type=str, help='Input TSV table of gene family abundances (FPStep3_pred_metagenome_unstrat.tsv from FPStep3.py).')
	group_input.add_argument('-m', '--map', type=str, help='Mapping of pathways to reactions, necessary if marker studied is not 16S (metacyc_path2rxn_struc_filt_pro.txt used by default). For ITS analysis, required file is here: $PICRUST2_PATH/default_files/pathway_mapfiles/metacyc_path2rxn_struc_filt_fungi.txt).')
	group_input.add_argument('--per_sequence_abun', default=None, help='Path to table of sequence abundances across samples normalized by marker copy number (typically the normalized sequence abundance table output at the metagenome pipeline step: FPStep3_seqtab_norm.tsv by default). This input is required when the --per_sequence_contrib option is set. (default: None).')
	group_input.add_argument('--per_sequence_function', default=None, help='Path to table of function abundances per sequence, which was outputted at the hidden-state prediction step (FPStep2_predicted_functions.tsv by default). This input is required when the --per_sequence_contrib option is set. Note that this file should be the same input table as used for the metagenome pipeline step (default: None).')
	group_input.add_argument('--hierarchy_ranks', nargs='*', default=["Level1", "Level2", "Level3", "Pathway"], help='The ordered ranks levels used in the metadata hierarchy pathways. [Default: %(default)s]' )
	#Outputs
	group_output = parser.add_argument_group( 'Outputs')
	group_output.add_argument('-o', '--pathways_abund', default='FPStep4_path_abun_unstrat.tsv', help='Pathway abundance file output.')
	group_output.add_argument('--pathways_contrib', default=None, help='Stratified output corresponding to contribution of predicted gene family abundances within each predicted genome.')
	group_output.add_argument('--pathways_predictions', default=None, help='Stratified output corresponding to contribution of predicted gene family abundances within each predicted genome.')
	group_output.add_argument('--pathways_abund_per_seq', default=None, help='')
	group_output.add_argument('-v', '--version', default=False, action='version', version="%(prog)s " + __version__)
	group_output.add_argument('-l', '--log-file', default=sys.stdout, help='This output file will contain several information on executed commands.')
	group_output.add_argument('-t', '--html', default='FPStep4_summary.html', help="Path to store resulting html file. [Default: %(default)s]" )	
	args = parser.parse_args()
	prevent_shell_injections(args)

	tmp_files=TmpFiles(os.path.split(args.input_file)[0])
	try:	 
		Logger.static_write(args.log_file, "## Application\nSoftware :" + sys.argv[0] + " (version : " + str(__version__) + ")\nCommand : " + " ".join(sys.argv) + "\n\n")

		if args.per_sequence_contrib:
			if args.per_sequence_abun == None or args.per_sequence_function == None:
				parser.error("\n\n#ERROR : --per_sequence_abun and --per_sequence_function required when --per_sequence_contrib option is set!\n\n")
			if args.pathways_contrib is None:
				args.pathways_contrib = 'FPStep4_path_abun_contrib.tsv'
			if args.pathways_predictions is None:
				args.pathways_predictions = 'FPStep4_path_abun_predictions.tsv'
			if args.pathways_abund_per_seq is None:
				args.pathways_abund_per_seq = "FPStep4_path_abun_unstrat_per_seq.tsv"


		if (args.per_sequence_abun is not None or args.per_sequence_function is not None) and not args.per_sequence_contrib:
			parser.error("\n\n#ERROR : --per_sequence_contrib required when --per_sequence_contrib and --per_sequence_function option is set!\n\n")

		tmp_pathway = tmp_files.add( 'pathway_pipeline.log' )
		tmp_tsv = tmp_files.add( 'genes_abundances_formatted.tsv')
		formate_input_file(args.input_file, tmp_tsv)


		PathwayPipeline(tmp_tsv, args.map, args.per_sequence_contrib, args.per_sequence_abun, args.per_sequence_function, args.no_regroup,  args.pathways_abund, args.pathways_contrib, args.pathways_predictions, args.pathways_abund_per_seq, tmp_pathway).submit(args.log_file)

		hierarchy_tag = formate_abundances_file( args.pathways_abund, PATHWAYS_HIERARCHY_FILE )
		tmp_biom = tmp_files.add( 'pathway_abundances.biom' )
		Tsv2biom( args.pathways_abund, tmp_biom ).submit( args.log_file)
		tree_count_file = tmp_files.add( "pathwayCount.enewick" )
		tree_ids_file = tmp_files.add( "pathwayCount_ids.tsv" )
		TaxonomyTree( tmp_biom, hierarchy_tag, tree_count_file, tree_ids_file ).submit( args.log_file )

		write_summary( args.pathways_abund, tree_count_file, tree_ids_file, args.html )

	finally:
		if not args.debug:
			tmp_files.deleteAll()

