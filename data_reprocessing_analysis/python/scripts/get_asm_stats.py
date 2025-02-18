#!/usr/bin/env python3
__email__ = "chienchi@lanl.gov"
__author__ = "Chienchi Lo"
__version__ = "1.0"
__update__ = "02/05/2025"
__project__ = "National Microbiome Data Collaborative"
import argparse
import glob
import logging
import os
import sys
from collections import defaultdict

import pandas as pd


def main(argvs):
    #SPRUCE/Gold_ID/project_id
    project_d=argvs.input_dir
    os.chdir(project_d)
    output_dir = project_d if (not argvs.output_dir) else argvs.output_dir
    metadata = glob.glob("*gold_biosamples.csv", recursive=False)[0]
    asm_versions=dict()
    by_pid=defaultdict(dict)
    by_gold=defaultdict(dict)
    project_name = os.path.basename(project_d)
    with open (metadata, 'r') as f:
        for line in f:
            gold_id,its, img_oid, anno_v, assembly_v=line.rstrip().split(",")
            anno_v_name = anno_v if anno_v else "Unknown"
            assembly_v_name = assembly_v if  assembly_v else "Unknown"
            asm_versions[assembly_v_name]=1
            by_pid[img_oid]['ANNO'] = anno_v_name
            by_pid[img_oid]['ASM'] = assembly_v_name

    for gold in os.listdir(project_d):
        if os.path.isfile(gold):
            continue
        by_gold[gold]=defaultdict(dict)

        quast_file = os.path.join(project_d,gold,'quast/transposed_report.tsv')
        
        if os.path.exists(quast_file):
            with open (quast_file, 'r') as quast_lines:
                for line in quast_lines:
                    if 'Total length' in line:
                        continue
                    stats=line.rstrip().split("\t")
                    id = stats[0].replace(".a","").replace("_contigs","")
                    if id.startswith('nmdc'):
                        by_pid[id]['ASM'] = 'metaSPAdes v. 3.15.0'
                        asm_versions[by_pid[id]['ASM']]=1
                    version_info = by_pid[id]['ASM']
                    by_gold[gold][version_info]['contigs'] = int(stats[1])
                    by_gold[gold][version_info]['contigs_500'] = int(stats[13])
                    by_gold[gold][version_info]['contigs_1000'] = int(stats[2])
                    by_gold[gold][version_info]['contigs_len'] = int(stats[7])
                    by_gold[gold][version_info]['largest_contig'] = int(stats[14])
                    by_gold[gold][version_info]['contigs_len_500'] = int(stats[15])
                    by_gold[gold][version_info]['contigs_len_1000'] = int(stats[8])
                    by_gold[gold][version_info]['auN'] = float(stats[8])
                    # auN is the areas under the Nx curve, where x is the length of the contig
                    # to summarize assembly contiguity with a single number, auN (auNG, etc) is a better choice than N50 (NG50, etc). 
                    # It is more stable, less affected by big jumps in contig lengths and considers the entire Nx (NGx, etc) curve.
                
        

    output_file = open(os.path.join(output_dir,project_name+"_asm_stats.tsv"),'w')
    all_version_names=sorted(asm_versions.keys())
    header1 = '\t'.join(["Gold_biosample"]+all_version_names*8)
    header2 = '\t'.join(['ID']+['Total_contigs_number']*len(all_version_names)+['Total_contigs_size (bp)']*len(all_version_names)+
                        ['Contigs_number(>500bp)']*len(all_version_names)+['Contigs_size(>500bp)']*len(all_version_names)+
                        ['Contigs_number(>1000bp)']*len(all_version_names)+['Contigs_size(>1000bp)']*len(all_version_names)+
                        ['Largest_contig_size']*len(all_version_names)+['auN']*len(all_version_names))
    output_file.write(header1+"\n"+header2+"\n")
    #print(header)
    for gold in by_gold:
        total_contigs = [ str(by_gold[gold][v]['contigs']) if 'contigs' in by_gold[gold][v] else "" for v in all_version_names]
        total_contigs_500 = [ str(by_gold[gold][v]['contigs_500']) if  'contigs_500' in by_gold[gold][v] else "" for v in all_version_names]
        total_contigs_1000 = [str(by_gold[gold][v]['contigs_1000']) if 'contigs_1000' in by_gold[gold][v] else "" for v in all_version_names]
        total_contigs_len = [str(by_gold[gold][v]['contigs_len']) if 'contigs_len' in by_gold[gold][v] else "" for v in all_version_names]
        total_contigs_len_500 = [str(by_gold[gold][v]['contigs_len_500']) if 'contigs_len_500' in by_gold[gold][v] else "" for v in all_version_names]
        total_contigs_len_1000 = [str(by_gold[gold][v]['contigs_len_1000']) if 'contigs_len_1000' in by_gold[gold][v] else "" for v in all_version_names]
        total_largest_contig = [str(by_gold[gold][v]['largest_contig']) if 'largest_contig' in by_gold[gold][v] else "" for v in all_version_names]
        total_auN = [str(by_gold[gold][v]['auN']) if 'auN' in by_gold[gold][v] else "" for v in all_version_names]
        print_total_contigs = '\t'.join(total_contigs)
        print_total_contigs_500 = '\t'.join(total_contigs_500)
        print_total_contigs_1000 = '\t'.join(total_contigs_1000)
        print_total_contigs_len = '\t'.join(total_contigs_len)
        print_total_contigs_len_500 = '\t'.join(total_contigs_len_500)
        print_total_contigs_len_1000 = '\t'.join(total_contigs_len_1000)
        print_total_largest_contig = '\t'.join(total_largest_contig)
        print_total_auN = '\t'.join(total_auN)
        output_file.write(gold+"\t"+print_total_contigs+"\t"+print_total_contigs_len+"\t"+
                          print_total_contigs_500+"\t"+print_total_contigs_len_500+"\t"+
                          print_total_contigs_1000+"\t"+print_total_contigs_len_1000+"\t"+
                          print_total_largest_contig+"\t"+print_total_auN+"\n")
        #print(print_str)

    output_file.close()


if __name__ == '__main__':
    toolname = os.path.basename(__file__)
    argv = argparse.ArgumentParser( prog=toolname,
        description = "get asm stats numbers from quast results",
        formatter_class = argparse.ArgumentDefaultsHelpFormatter, epilog = """
        This program is free software: you can redistribute it and/or modify it under the terms of
        the GNU General Public License as published by the Free Software Foundation, either version
        3 of the License, or (at your option) any later version. This program is distributed in the
        hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
        more details. You should have received a copy of the GNU General Public License along with
        this program. If not, see <http://www.gnu.org/licenses/>.""")
    argv.add_argument('-d', '--input-dir', dest = 'input_dir', required = True,
        help = 'input dir')
    argv.add_argument('-o', '--output-dir', dest = 'output_dir',
        help = 'output dir')
    argv.add_argument('--version', action='version', version='%(prog)s v{version}'.format(version=__version__))

    argvs = argv.parse_args()

    log_level = logging.INFO
    logging.basicConfig(
        format='[%(asctime)s' '] %(levelname)s: %(message)s', level=log_level, datefmt='%Y-%m-%d %H:%M')

    sys.exit(not main(argvs))
