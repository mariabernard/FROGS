#!/usr/bin/env python3
#
# Copyright (C) 2022 INRA
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

__author__ = 'Vincent Darbot - GENPHYSE'
__copyright__ = 'Copyright (C) 2022 INRA'
__license__ = 'GNU General Public License'
__version__ = '1.0'
__email__ = 'frogs-support@inrae.fr'
__status__ = 'prod'

import re
import os
import sys
import gzip
import shutil
import argparse
import ete3 as ete
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
LIB_DIR = os.path.abspath(os.path.join(os.path.dirname(CURRENT_DIR), "lib"))
sys.path.append(LIB_DIR)
if os.getenv('PYTHONPATH') is None: os.environ['PYTHONPATH'] = LIB_DIR
else: os.environ['PYTHONPATH'] = os.environ['PYTHONPATH'] + os.pathsep + LIB_DIR

from frogsBiom import Biom, BiomIO
from frogsUtils import *
from frogsSequenceIO import *

####################################################################################################################
#
# Functions
#
####################################################################################################################

def task_convert_fasta( args ):
	'''
	@summary: Removes the potential fasta headers descriptions to only 
	keep the id. (Issue with PICRSUt2 place_seqs.py tool)
	'''
	FH_input = FastaIO(args.input_fasta)
	FH_output = FastaIO(args.output_fasta, "wt")
	for record in FH_input:
		record.id = record.id
		record.description = None
		FH_output.write(record)
	FH_output.close()

def task_excluded_sequences_tree( args ):
	"""
	@summary: Returns the excluded sequences, not insert into reference tree.
	@param fasta_file: [str] Path to the fasta file to process.
	@param tree_file: [str] Path to the tree file to process.
	@output: The file of no aligned sequence names.
	"""
	tree=ete.Tree(args.input_tree)
	all_leaves = list()
	for leaf in tree:
		all_leaves.append(leaf.name)

	FH_input = FastaIO(args.input_fasta)
	excluded = open(args.output_excluded, "wt")
	list_excluded = list()
	no_excluded = True 
	for record in FH_input:
		if record.id not in all_leaves:
			excluded.write(record.id+"\n")
			list_excluded.append(record.id)
			no_excluded = False
	FH_input.close()
	if no_excluded:
		excluded.write('#No excluded ASV.\n')
	excluded.close()

def task_formate_abundances_file( args, hierarchy_tag = "classification"):
	"""
	@summary: Formates an abundances file (functions or pathways) in order to create a biom file of pathway abundances, and display sunbursts graphs.
	@param strat_file: frogsfunc_pathways or frogsfunc_functions outputs of abundances predictions (frogsfunc_pathways_unstrat.tsv)
	@param pathways_hierarchy_file: reference file that links every pathways or function ID to its hierarchy levels.
	"""
	id_to_hierarchy = {}
	path_fi = open(args.hierarchy_file)
	for li in path_fi:
		if li.startswith('#'):
			continue
		li = li.strip().split('\t')
		hierarchy = "#|#".join(li[:-1])
		hierarchy = hierarchy.replace(";",",")
		hierarchy = hierarchy.replace("#|#",";")
		id_to_hierarchy[li[-1]] = hierarchy

	data = open(args.input_abundances).readlines()
	new_data = open(args.input_tmp_unstrat, 'wt')
	sums = list()
	for row in data:
		row = row.strip().split('\t')
		if not row[0] == "db_link":
			for i in range(len(row[2:])):
				row[2+i] = float(row[2+i])
			sums = sum(row[2:])
			new_data.write("\t".join(row[:2]) + "\t" + str(sums) + "\t" + "\t".join([str(i) for i in row[2:]]) + "\n")

		else:
			row[1] = "observation_name"
			new_data.write("\t".join(row[:2]) + "\tobservation_sum\t" + "\t".join(row[2:]) + "\n")
	new_data.close()

	with open(args.input_tmp_unstrat, 'rt') as f_in:
		with open(args.input_abundances, 'wt') as f_out:
			shutil.copyfileobj(f_in, f_out)

	tmp_unstrat = open(args.input_tmp_unstrat, 'wt')
	FH_in = open(args.input_abundances).readlines()

	header = FH_in[0].strip().split('\t')
	header.insert(0, hierarchy_tag)

	tmp_unstrat.write("\t".join(header)+"\n")
	for li in FH_in[1:]:
		li = li.strip().split('\t')
		if li[1] in id_to_hierarchy:
			li.insert(0, id_to_hierarchy[li[1]])
		else:
			li.insert(0, "NA")
		tmp_unstrat.write("\t".join(li)+"\n") 

	tmp_unstrat.close()
	with open(args.input_tmp_unstrat, 'rt') as f_in:
		with open(args.input_abundances, 'wt') as f_out:
			shutil.copyfileobj(f_in, f_out)

def task_generate_sunburst( args, hierarchy_tag = "classification"):
	'''
	@summary: Generate sunburst input files for html graphical outputs.
	@param input-abundances: function or pathway abundances files.
	@param input-tmp-sunburst: abundances formatted file (with rounded numbers)
	'''
	tmp_sunburst = open(args.input_abundances).readlines()
	new_tmp_sunburst = open(args.input_tmp_sunburst, 'wt')
	columns_not_conserved = ['observation_name', 'db_link', hierarchy_tag]
	to_not_conserve = []
	header = tmp_sunburst[0].strip().split('\t')
	for col in range(len(header)):
		if header[col] in columns_not_conserved:
			to_not_conserve.append(col)
		new_tmp_sunburst.write(header[col] + "\t")
	new_tmp_sunburst.write("\n")
			
	for row in tmp_sunburst[1:]:
		# Keep only values with classifications
		row = row.strip().split('\t')
		if row[0] != "NA":
			for col in range(len(row)):
				if col not in to_not_conserve:
					row[col] = int(round(float(row[col]),0))
					new_tmp_sunburst.write(str(row[col]) + "\t")
				else:
					new_tmp_sunburst.write(row[col] + "\t")
			new_tmp_sunburst.write('\n')
	new_tmp_sunburst.close()

def task_parse_metagenome_pipeline( args ):
	'''
	@summary: Parses and ungzippes files from frogsfunc_functions.py and\
	adds a ddb link column that leads to the involved function.
	@param input_dir: folder of metagenome_pipeline.py default outputs.
	These gzip files are then openned and parsed. If --debug mode is activated,
	gzip files are finally deleted.
	Final files are all the output related names files (output_abund, \
	output_seqtab, output_weighted, output_contrib)
	'''
	START_GENBANK_LINK = "https://www.genome.jp/dbget-bin/www_bget?"
	START_COG_LINK = "https://www.ncbi.nlm.nih.gov/research/cog/cog/"
	START_PFAM_LINK = "https://pfam.xfam.org/family/"
	START_TIGR_LINK = "https://0-www-ncbi-nlm-nih-gov.linyanti.ub.bw/genome/annotation_prok/evidence/"
	f_in = gzip.open(args.input_dir + '/pred_metagenome_unstrat.tsv.gz', 'rt')
	f_out = open(args.output_abund, 'wt')
	for li in f_in:
		if li.startswith('function'):
			header = li.strip().split('\t')
			header.insert(0,'db_link')
			f_out.write("\t".join(header)+"\n")
			continue
		li = li.split('\t')
		function = li[0]
		if "COG" in function:
			li.insert(0,START_COG_LINK + function )
		elif "PF" in function:
			li.insert(0,START_PFAM_LINK + function )
		elif "TIGR" in function:
			li.insert(0,START_TIGR_LINK + function )
		elif re.search('K[0-9]{5}',function) or "EC:" in function:
			li.insert(0,START_GENBANK_LINK + function )
		else:
			li.insert(0,"no link" )
		f_out.write("\t".join(li))
	with gzip.open(args.input_dir + '/seqtab_norm.tsv.gz', 'rb') as f_in:
		with open(args.output_seqtab, 'wb') as f_out:
			shutil.copyfileobj(f_in, f_out)
	with gzip.open(args.input_dir + '/weighted_nsti.tsv.gz', 'rb') as f_in:
		with open(args.output_weighted, 'wb') as f_out:
			shutil.copyfileobj(f_in, f_out)
	if args.output_contrib is not None:
		with gzip.open(args.input_dir + '/pred_metagenome_contrib.tsv.gz', 'rb') as f_in:
			with open(args.output_contrib, 'wb') as f_out:
				shutil.copyfileobj(f_in, f_out)

def task_parse_pathway_pipeline( args ):
	'''
	@summary: Parse and ungzipped files from frogsfunc_pathways.py.
	Add a ddb link column that leads to the involved pathway.
	'''
	START_METAYC_PATHWAY_LINK = "https://biocyc.org/META/NEW-IMAGE?type=PATHWAY&object="
	START_KEGG_PATHWAY_LINK = "https://www.genome.jp/entry/"
	f_in = gzip.open(args.input_dir + '/path_abun_unstrat.tsv.gz', 'rt')
	f_out = open(args.output_abund, 'wt')

	for li in f_in:
		if li.startswith('pathway'):
			header = li.strip().split('\t')
			header.insert(0,'db_link')
			f_out.write("\t".join(header)+"\n")
			continue
		li = li.strip().split('\t')
		function = li[0]
		if function.startswith('ko'):
			li.insert(0,START_KEGG_PATHWAY_LINK + function )
		else:
			li.insert(0,START_METAYC_PATHWAY_LINK + function )
		f_out.write("\t".join(li)+"\n")
	if args.per_sequence_contrib:
		with gzip.open(args.input_dir + '/path_abun_contrib.tsv.gz', 'rb') as f_in:
			with open(args.output_contrib, 'wb') as f_out:
				shutil.copyfileobj(f_in, f_out)
		with gzip.open(args.input_dir + '/path_abun_predictions.tsv.gz', 'rb') as f_in:
			with open(args.output_predictions, 'wb') as f_out:
				shutil.copyfileobj(f_in, f_out)
		with gzip.open(args.input_dir + '/path_abun_unstrat_per_seq.tsv.gz', 'rb') as f_in:
			with open(args.output_abund_per_seq, 'wb') as f_out:
				shutil.copyfileobj(f_in, f_out)

####################################################################################################################
#
# Main
#
####################################################################################################################
if __name__ == "__main__":
    parser = argparse.ArgumentParser( description='frogsFUncUtils is a program package designed for working with frogsfunc tools.' )
    parser.add_argument( "--version", action='version', version=__version__ )
    subparsers = parser.add_subparsers()

    # Convert fasta files
    parser_convert = subparsers.add_parser('convert-fasta', help='Change fasta headers to be compatible with PICRUSt2.', usage='frogsFuncUtils.py convert-fasta [-h] -i INPUT_FILE -o OUTPUT_FILE')
    parser_convert.add_argument( '-i', '--input-fasta', required=True, type=str, help='Fasta file processed.' )
    parser_convert.add_argument( '-o', '--output-fasta', required=True, type=str, help='Output fasta file.' )   
    parser_convert.set_defaults(func=task_convert_fasta)

    # Excluded sequences 
    parser_excluded = subparsers.add_parser('excluded-sequences', help='Returns the excluded sequence, not insert into reference tree.', usage='frogsFuncUtils.py excluded-sequences [-h] -i INPUT_FASTA -t INPUT_TREE -e EXCLUDED_FILE')
    parser_excluded.add_argument( '-i', '--input-fasta', required=True, type=str, help='Input fasta file processed.' )
    parser_excluded.add_argument( '-t', '--input-tree', required=True, type=str, help='PICRUSt2 output tree with inserts sequences.' )
    parser_excluded.add_argument( '-e', '--output-excluded', required=True, type=str, help='Output file with sequences not inserts into reference tree.' )
    parser_excluded.set_defaults(func=task_excluded_sequences_tree)

    # Formate abundances files
    parser_formate = subparsers.add_parser('formate-abundances', help='Add classifications columns and create temporary abundance file to display sunburst graphs.', usage='frogsFuncUtils.py formate-abundances [-h] -i INPUT_FILE -o OUTPUT_FILE')
    parser_formate.add_argument( '-i', '--input-abundances', required=True, type=str, help='Input function or pathway abundances file.' )
    parser_formate.add_argument( '-u', '--input-tmp-unstrat', required=True, type=str, help='Tmp path of function abundances.' )
    parser_formate.add_argument( '-f', '--hierarchy-file', required=True, type=str, help='Reference file that links every pathways or function ID to its hierarchy levels..' )
    parser_formate.set_defaults(func=task_formate_abundances_file)

    # Generate sunburst input files
    parser_sunburst = subparsers.add_parser('generate-sunburst', help= 'Generate sunburst input files to display sunburst graphs in frogsfunc_function html')
    parser_sunburst.add_argument( '-i', '--input-abundances', required=True, type=str, help='Input function or pathway abundances file.' )
    parser_sunburst.add_argument( '-t', '--input-tmp-sunburst', required=True, type=str, help='Tmp path of abundances to display sunburst graphs.' )
    parser_sunburst.set_defaults(func=task_generate_sunburst)

    # Parse MetagenomePipeline outputs
    parser_function = subparsers.add_parser('parse-metagenome', help='Parse results of PICRUSt2 metageome_pipeline.py software to rerieve additional informations (i.g. databases functions links).')
    parser_function.add_argument( '-i', '--input-dir', required=True, type=str, help='Output directory for PICRSUt2 metagenome_pipeline.py functions predictions.' )
    parser_function.add_argument( '-a', '--output-abund', required=True, type=str, help='PICRSUt2 metagenome_pipeline.py output file for metagenome prediction abundances.' )
    parser_function.add_argument( '-s', '--output-seqtab', required=True, type=str, help='PICRSUt2 metagenome_pipeline.py output file with abundance normalized per marker copies number.' )
    parser_function.add_argument( '-w', '--output-weighted', required=True, type=str, help='PICRSUt2 metagenome_pipeline.py output file with the mean of nsti value per sample (format: TSV).' )
    parser_function.add_argument( '-c', '--output-contrib', default = None, type=str, help='PICRSUt2 metagenome_pipeline.py output file that reports contributions to community-wide abundances (ex pred_metagenome_contrib.tsv)' )
    parser_function.set_defaults(func=task_parse_metagenome_pipeline)

    # Parse PathwayPipeline outputs
    parser_pathway = subparsers.add_parser('parse-pathway', help='Parse results of PICRUSt2 metageome_pipeline.py software to rerieve additional informations (i.g. databases functions links).')
    parser_pathway.add_argument( '-i', '--input-dir', required=True, type=str, help='Output directory for PICRSUt2 pathway_pipeline.py pathway predictions.' )
    parser_pathway.add_argument( '-a', '--output-abund', required=True, type=str, help='PICRSUt2 pathway_pipeline.py output file for pathway prediction abundances.' )
    parser_pathway.add_argument( '--per-sequence-contrib', default=False, action='store_true', help='If stratified option is activated, a new table is built. It will contain the abundances of each function of each ASV in each sample. (in contrast to the default stratified output, which is the contribution to the community-wide pathway abundances.)')
    parser_pathway.add_argument( '--output-contrib', default = None, type=str, help='Stratified output corresponding to contribution of predicted gene family abundances within each predicted genome.' )
    parser_pathway.add_argument( '--output-predictions', default = None, type=str, help='Stratified output corresponding to contribution of predicted gene family abundances within each predicted genome.' )
    parser_pathway.add_argument( '--output-abund-per-seq', default = None, type=str, help='Pathway abundance file output per sequences (if --per-sequence-contrib set)' )
    parser_pathway.set_defaults(func=task_parse_pathway_pipeline)

    # Parse parameters and call process
    args = parser.parse_args()
    args.func(args)
