#!/usr/bin/env python3
__email__ = "chienchi@lanl.gov"
__author__ = "Chienchi Lo"
__version__ = "1.0"
__update__ = "12/16/2024"
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
    anno_versions=dict()
    by_pid=defaultdict(dict)
    by_gold=defaultdict(dict)
    project_name = os.path.basename(project_d)
    with open (metadata, 'r') as f:
        for line in f:
            gold_id,its, img_oid, anno_v, assembly_v=line.rstrip().split(",")
            anno_v_name = anno_v if anno_v else "Unknown"
            assembly_v_name = assembly_v if  assembly_v else "Unknown"
            anno_versions[anno_v_name]=1
            by_pid[img_oid]['ANNO'] = anno_v_name
            by_pid[img_oid]['ASM'] = assembly_v_name

    for gold in os.listdir(project_d):
        if os.path.isfile(gold):
            continue
        by_gold[gold]=defaultdict(dict)
        for pid in os.listdir(os.path.join(project_d,gold)):

            prefix=pid.replace(":","_")
            p_dir = os.path.join(project_d,gold,pid)
            info_file = os.path.join(p_dir,prefix+'_imgap.info')
            if os.path.exists(info_file):
                with open (info_file, 'r') as info:
                    version_info = info.readline().rstrip()
                    by_pid[prefix]['ANNO'] = version_info
                    anno_versions[version_info]=1
            ko_file = os.path.join(p_dir,prefix+'_ko.tsv') if os.path.exists(os.path.join(p_dir,prefix+'_ko.tsv')) else os.path.join(p_dir,prefix+'.a.ko.txt') if os.path.exists(os.path.join(p_dir,prefix+'.a.ko.txt')) else ""
            gff_file = os.path.join(p_dir,prefix+'.a.gff') if os.path.exists(os.path.join(p_dir,prefix+'.a.gff')) else os.path.join(p_dir,prefix+'_functional_annotation.gff') if os.path.exists(os.path.join(p_dir,prefix+'_functional_annotation.gff')) else ""

        
            if ko_file:
                df = pd.read_csv( ko_file , sep='\t' , header=None)
                version_info = by_pid[prefix]['ANNO']
                by_gold[gold][version_info]['TOTAL_KO'] = len(df[2])
                by_gold[gold][version_info]['UNIQUE_KO'] = len(pd.unique(df[2]))
                #print(gold, prefix, by_pid[prefix]['ANNO'] , len(df[2]),len(pd.unique(df[2])))
            if gff_file:
                df2 = pd.read_csv( gff_file , sep='\t' , header=None,low_memory=False)
                version_info = by_pid[prefix]['ANNO']
                by_gold[gold][version_info]['TOTAL_Features'] = len(df2[2])
                by_gold[gold][version_info]['Anno_Groups'] = df2.groupby([2]).size()

    output_file = open(os.path.join(output_dir,project_name+"_stats.tsv"),'w')
    total_ko_out = open(os.path.join(output_dir,project_name+"_total_ko.tsv"),'w')
    unique_ko_out = open(os.path.join(output_dir,project_name+"_unique_ko.tsv"),'w')
    all_version_names=sorted(anno_versions.keys())
    header = '\t'.join(["Gold_biosampple"]+all_version_names)
    header1 = '\t'.join(["Gold_biosampple"]+all_version_names*3)
    header2 = '\t'.join(['ID']+['Unique_KO_count']*len(all_version_names)+['Total_KO_count']*len(all_version_names)+['Total_features_count']*len(all_version_names) )
    total_ko_out.write(header+"\n")
    unique_ko_out.write(header+"\n")
    output_file.write(header1+"\n"+header2+"\n")
    #print(header)
    for gold in by_gold:
        total_ko = [ str(by_gold[gold][v]['TOTAL_KO']) if 'TOTAL_KO' in by_gold[gold][v] else "" for v in all_version_names]
        unique_ko = [ str(by_gold[gold][v]['UNIQUE_KO']) if  'UNIQUE_KO' in by_gold[gold][v] else "" for v in all_version_names]
        total_features = [str(by_gold[gold][v]['TOTAL_Features']) if 'TOTAL_Features' in by_gold[gold][v] else "" for v in all_version_names]
        print_str_features = '\t'.join(total_features)
        print_str_ko = '\t'.join(total_ko)
        print_str_unique = '\t'.join(unique_ko)
        total_ko_out.write(gold+"\t"+print_str_ko+"\n")
        unique_ko_out.write(gold+"\t"+print_str_unique+"\n")
        output_file.write(gold+"\t"+print_str_unique+"\t"+print_str_ko+"\t"+print_str_features+"\n")
        #print(print_str)
    
    output_file.close()
    total_ko_out.close()
    unique_ko_out.close()
        

if __name__ == '__main__':
    toolname = os.path.basename(__file__)
    argv = argparse.ArgumentParser( prog=toolname,
        description = "get KO numbers",
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