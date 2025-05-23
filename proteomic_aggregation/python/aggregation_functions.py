#!venv/bin python

#packages used in these functions
import importlib.util
import requests
import pandas as pd
from io import StringIO
import re
import numpy as np
from scipy.optimize import minimize
import seaborn as sns
import matplotlib.pyplot as plt


def import_relative_module(module_name:str,path:str):

    """
    Import a module given a relative path and module name (specifically for when a .py is located in another folder)
    """

    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    return module


def findproteinname(s):

    """
    Define a function that detects the protein type (forward, reverse, contaminant) based on a protein name (s)
    """

    p1 = re.compile(r"^Contaminant_")
    p2 = re.compile(r"^XXX_Contaminant_")
    p3 = re.compile(r"^XXX_")
    if p1.search(s) is not None:
        return "None"
    elif p2.search(s) is not None:
        return "None"
    elif p3.search(s) is not None:
        return "Reversed"
    else:  # the rest
        return "Forward"

def sequence_noprefsuff(s):

    """
    Function that takes a peptide sequence (s) and returns the same sequence but without any prefix and suffix
    """
    p = re.compile(r"\.(?P<cleanseq>[A-Z\*@#]+)\.")
    m = p.search(s)
    return m.group("cleanseq")

def tsv_extract(url:str):

    """
    Define a function to extract a tsv from a url
    """

    try:
    
        # get TSV data using URL
        response = requests.get(url)
        tsv_data = StringIO(response.text)
        tsv_df = pd.read_csv(tsv_data,sep='\t',header='infer')
        tsv_data.close()

    #if error print info
    except Exception as e:
        print(f"An error occurred fetching data from {url}: {e}")

    return pd.DataFrame(tsv_df)



def split_to_dict(row):

    """
    split string into a dictionary using title=value as format. specifically for gff_extract()
    """

    return dict(item.split('=') for item in row.split(';'))



def gff_extract_features(url:str):

    """
    Define a function to extract the feature annotations column from gff3 (9th column, equivalent to [8] in python)
    """

    try:
    
        # get TSV data using URL
        response = requests.get(url)
        tsv_data = StringIO(response.text)
        tsv_df = pd.read_csv(tsv_data,sep='\t',header=None,dtype={0:'string',1:'string',2:'string',3:'int64',4:'int64',5:'string',6:'string',7:'string',8:'string'})
        tsv_data.close()

        #create new columns for the listed values in last/feature column
        tsv_df = tsv_df.iloc[:,8].apply(split_to_dict).apply(pd.Series)


    #if error print info
    except Exception as e:
        print(f"An error occurred fetching data from {url}: {e}")

    return pd.DataFrame(tsv_df)



def iterate_file_extract(identifier_col:str,url_col:str,extract_cols:list, pd_df:pd.DataFrame, file_type:str, filter_col=None, filter_values=None):

    """
    Define a function to take a pandas dataframe (pd_df) with a column of tsv file urls (url_col) and a dataset identifier (identifier_col) and generate an aggregated pandas dataframe of the desired tsv columns (extract_cols).
    Important to specify header=None for gff files and header = 'infer' for proteomic output files
    """

    output=[]

    for index, row in pd_df.iterrows():
        
        #identifier information
        identifier = row[identifier_col]
        url = row[url_col]

        try:
        
            # get TSV data using URL
            if file_type == 'tsv':
                tsv_df = tsv_extract(url)
            if file_type == 'gff':
                tsv_df = gff_extract_features(url)

            #get the relevant data
            tsv_subset = tsv_df.loc[:,extract_cols]

            #double check that subset will have unique rows
            if len(tsv_subset)!=len(tsv_subset.drop_duplicates()):
                break

            #filter if there's a column and values to filter with
            if (filter_col != None) & (filter_values != None):
                tsv_subset = tsv_subset[tsv_subset[filter_col].isin(filter_values)]
            
            #add data set level info to dataframe
            tsv_subset['id_col']=identifier

            #append dataframe to list
            output.append(tsv_subset)

        #if error print info
        except Exception as e:
            print(f"An error occurred fetching data from {identifier}: {e}")
            continue

    #concatenate list
    output=pd.concat(output,ignore_index=True)


    return pd.DataFrame(output)



def specFiltValue(Params, reversed_peptides:pd.DataFrame, forward_peptides:pd.DataFrame):

    """
    Function that implements a spectral probability filter (Params:specprob) and returns a value that weighs the number of forward peptides retained with the proximity of the data set to a 0.05 FDR (filter_value)
    
    :param Params: List or tuple containing the specprob (the log10 value for ease of computation)
    :param reversed_peptides: DataFrame of reversed peptides (not optimized)
    :param forward_peptides: DataFrame of forward peptides (not optimized)
    :return: filter_value based on FDR calculation

    """

    # function to minimize
    (
        specprob,
    ) = Params  # use log10 value so that it is managable for the computer


    ### The FDR function ###

    #filter forward and reverse data sets to rows where the MSGFDB_SpecEValue is less than the specprob
    df_r = reversed_peptides[
        (reversed_peptides["MSGFDB_SpecEValue"] < 10 ** specprob)
    ].copy()
    df_f = forward_peptides[
        (forward_peptides["MSGFDB_SpecEValue"] < 10 ** specprob)
    ].copy()

    ### fdr_spec ###
    f_spec = (df_f["SpecID"].unique().size)  # Modified on Apr23 to only count for unique dataset-scan
    r_spec = df_r["SpecID"].unique().size
    if (f_spec == 0) & (r_spec == 0):
        fdr_spec = 1
    else:
        fdr_spec = (2*r_spec)/ (f_spec + r_spec)

    filter_value=1 / (0.050001 - fdr_spec) * (-f_spec)
    
    return filter_value


def optimize_specFilt(initial_specprob_filter:float,forward_peptides:pd.DataFrame,reversed_peptides:pd.DataFrame):

    """
    Function returns a spectral probability filter that optimizes the number of forward peptides retained given a false discovery rate of 0.05 (via the specFiltValue function)

    :param initial_specprob_filter: float of a spectral probability filter value to start with
    :param reversed_peptides: DataFrame of reversed peptides (not optimized)
    :param forward_peptides: DataFrame of forward peptides (not optimized)
    :return: a minimize() output containing the optimize spectral probability value
    """

    # Miminize PepFDR
    initial_guess = [
        initial_specprob_filter,
    ]

    result = minimize(
        specFiltValue, 
        initial_guess, 
        args=(reversed_peptides, forward_peptides),  # Pass in the peptides as additional arguments
        method="COBYLA"
    )

    try:
        #if minimize is succesful, save result
        if result.success:
            return result

    #if minimize() is unsuccesful
    except ValueError as e:
        print("Failed optimization:", e)





def razorprotein(peptide_protein_mapping:pd.DataFrame):

    """
    Function taking a dataframe of all peptide to protein mappings and returning a dataframe of peptide to razor protein mappings.
    Rules for 'razor protein' are as follows:
    - If a peptide is unique to a protein, then that is the razor
    - If a peptide belongs to more than one protein, but one of those proteins has a unique peptide, then that protein is the razor
    - If a peptide belongs to more than one protein and one of those proteins has has the maximal number of peptides, then that protein is the razor
    - If a peptide belongs to more than one protein and more than one of those proteins has the maximal number of peptides, then collapse the proteins and gene annotations into single strings
    - If a peptide belongs to more than one protein and more than one of those proteins has a unique peptide, then the peptide is removed from analysis because its mapping is inconclusive
    
    :param peptide_protein_mapping: a pandas dataframe with a row for each unique peptide to protein mapping (columns 'Peptide Sequence with Mods' and 'Protein')
    :return: pandas dataframe with a row for each unique peptide and the 'razor' protein it maps to
    
    """

    #determine if peptides are redundant (map to more than one protein) or unique (map to only one protein)
    peptide_type = peptide_protein_mapping[["Peptide Sequence with Mods","Protein"]].groupby(["Peptide Sequence with Mods"]).count()
    peptide_type.reset_index(inplace=True)
    peptide_type['peptide_type']=np.where(peptide_type['Protein']>1,"redundant","unique")
    peptide_type = pd.DataFrame(peptide_type.drop('Protein',axis=1))

    #count the number of redundant and unique peptides mapping to each protein after FDR filter
    protein_redundancy = peptide_type.merge(peptide_protein_mapping[["Peptide Sequence with Mods","Protein"]],how='right',on=['Peptide Sequence with Mods'])
    protein_redundancy=protein_redundancy.groupby(["Protein","peptide_type"]).count().pivot_table(values='Peptide Sequence with Mods',index=['Protein'],columns=['peptide_type']).fillna(0).reset_index().rename_axis(None,axis=1)

    razor_mapping=[]

    for index, row in peptide_type.iterrows():

        mapping_subset = peptide_protein_mapping[(peptide_protein_mapping['Peptide Sequence with Mods']==row['Peptide Sequence with Mods'])]

        #if the peptide only maps to one protein, that is the razor protein
        if row['peptide_type']=='unique':
            output=pd.DataFrame(mapping_subset)
            output=output.rename(columns={'Protein':"razor"})



        #if the peptide maps to more than one protein and....
        else:

            proteins = mapping_subset["Protein"].tolist()
            redundancy_subset = protein_redundancy[(protein_redundancy['Protein'].isin(proteins))]

            #number of proteins in each group with unique peptides
            proteins_w_uniquepeptides = len(redundancy_subset[redundancy_subset['unique']>0])

            #number of proteins with highest number of reudundant peptides
            proteins_w_maxredpeptides = len(redundancy_subset[redundancy_subset['redundant']==max(redundancy_subset['redundant'])])


            #if there is only one protein with unique peptides, that is the razor protein
            if proteins_w_uniquepeptides==1:
                razor = redundancy_subset[redundancy_subset['unique']>0]['Protein'].iloc[0]
                output = pd.DataFrame(mapping_subset[(mapping_subset['Protein']==razor)])
                output=output.rename(columns={'Protein':"razor"})
 


            #if there is more than one protein with unique peptides, toss because razor protein indeterminant
            if proteins_w_uniquepeptides>1:
                continue


            #if there are no proteins with unique peptides...
            if proteins_w_uniquepeptides==0:

                    #there is one protein with the highest number of redundant peptides
                    if proteins_w_maxredpeptides==1:
                        razor = redundancy_subset[redundancy_subset['redundant']==max(redundancy_subset['redundant'])]['Protein'].iloc[0]
                        output = pd.DataFrame(mapping_subset[(mapping_subset['Protein']==razor)])
                        output=output.rename(columns={'Protein':"razor"})



                    #there is more than one protein with the highest number of redundant peptides
                    if proteins_w_maxredpeptides>1:
                        razors=redundancy_subset[redundancy_subset['redundant']==max(redundancy_subset['redundant'])]['Protein'].tolist()
                        output = pd.DataFrame(mapping_subset[mapping_subset['Protein'].isin(razors)])
                        output=output.rename(columns={'Protein':"razor"})

                        output = output.sort_values(by=['razor'])

                        #return lists of all matching protein information for each column
                        for column in output.columns[output.columns!="Peptide Sequence with Mods"]:
                            output[column]=', '.join(output[column].astype(str))

                        output = output.drop_duplicates()


        razor_mapping.append(output)

    razor_mapping=pd.concat(razor_mapping,ignore_index=True)

    return(razor_mapping)




def find_first_common_element(list1, list2):

    """
    Define function to find the first element in list2 that matches list1. utilized in firsthitprotein()
    """

    for item in list2:
        if item in list1:
            return item
    return None  # if no common element is found





def sortedprotein(peptide_protein_mapping:pd.DataFrame):

    """
    Function taking a dataframe of all peptide to protein mappings and returning a dataframe of peptide to sorted_list protein mappings. Differs from razorprotein() in that it returns only one protein ID per peptide.
    Rules for 'sorted_list' protein are as follows:
    - If a peptide is unique to a protein, then that is the sorted_list protein
    - If a peptide belongs to more than one protein, but one of those proteins has a unique peptide, then that protein is the sorted_list protein
    - If a peptide belongs to more than one protein and one of those proteins has has the maximal number of peptides, then that is the sorted_list protein
    - If a peptide belongs to more than one protein and more than one of those proteins has the maximal number of peptides, then the sorted_list is the first protein in a sorted list of all proteins
    - If a peptide belongs to more than one protein and more than one of those proteins has a unique peptide, then the peptide is removed from analysis because its mapping is inconclusive
    
    :param peptide_protein_mapping: a pandas dataframe with a row for each unique peptide to protein mapping (columns 'Peptide Sequence with Mods' and 'Protein')
    :return: pandas dataframe with a row for each unique peptide and the unique 'sorted_list' protein it maps to
    """

    #determine if peptides are redundant (map to more than one protein) or unique (map to only one protein)
    peptide_type = peptide_protein_mapping[["Peptide Sequence with Mods","Protein"]].groupby(["Peptide Sequence with Mods"]).count()
    peptide_type.reset_index(inplace=True)
    peptide_type['peptide_type']=np.where(peptide_type['Protein']>1,"redundant","unique")
    peptide_type = pd.DataFrame(peptide_type.drop('Protein',axis=1))

    #count the number of redundant and unique peptides mapping to each protein after FDR filter
    protein_redundancy = peptide_type.merge(peptide_protein_mapping[["Peptide Sequence with Mods","Protein"]],how='right',on=['Peptide Sequence with Mods'])
    protein_redundancy=protein_redundancy.groupby(["Protein","peptide_type"]).count().pivot_table(values='Peptide Sequence with Mods',index=['Protein'],columns=['peptide_type']).fillna(0).reset_index().rename_axis(None,axis=1)


    #generate list of all proteins in a sorted order
    sorted_proteins = peptide_protein_mapping['Protein'].sort_values()

    sorted_mapping=[]

    for index, row in peptide_type.iterrows():

        mapping_subset = peptide_protein_mapping[(peptide_protein_mapping['Peptide Sequence with Mods']==row['Peptide Sequence with Mods'])]

        #if the peptide only maps to one protein, that is the sorted_list protein
        if row['peptide_type']=='unique':
            output=pd.DataFrame(mapping_subset)
            output=output.rename(columns={'Protein':"sorted_list_protein"})



        #if the peptide maps to more than one protein and....
        else:

            proteins = mapping_subset["Protein"].tolist()
            redundancy_subset = protein_redundancy[(protein_redundancy['Protein'].isin(proteins))]

            #number of proteins in each group with unique peptides
            proteins_w_uniquepeptides = len(redundancy_subset[redundancy_subset['unique']>0])

            #number of proteins with highest number of reudundant peptides
            proteins_w_maxredpeptides = len(redundancy_subset[redundancy_subset['redundant']==max(redundancy_subset['redundant'])])


            #if there is only one protein with unique peptides, that is the sorted_list protein
            if proteins_w_uniquepeptides==1:
                sorted_list_protein = redundancy_subset[redundancy_subset['unique']>0]['Protein'].iloc[0]
                output = pd.DataFrame(mapping_subset[(mapping_subset['Protein']==sorted_list_protein)])
                output=output.rename(columns={'Protein':"sorted_list_protein"})
 


            #if there is more than one protein with unique peptides, toss because razor protein indeterminant
            if proteins_w_uniquepeptides>1:
                continue


            #if there are no proteins with unique peptides...
            if proteins_w_uniquepeptides==0:

                    #there is one protein with the highest number of redundant peptides
                    if proteins_w_maxredpeptides==1:
                        sorted_list_protein = redundancy_subset[redundancy_subset['redundant']==max(redundancy_subset['redundant'])]['Protein'].iloc[0]
                        output = pd.DataFrame(mapping_subset[(mapping_subset['Protein']==sorted_list_protein)])
                        output=output.rename(columns={'Protein':"sorted_list_protein"})



                    #there is more than one protein with the highest number of redundant peptides
                    if proteins_w_maxredpeptides>1:
                        sorted_list=redundancy_subset[redundancy_subset['redundant']==max(redundancy_subset['redundant'])]['Protein'].tolist()
                        output = pd.DataFrame(mapping_subset[mapping_subset['Protein'].isin(sorted_list)])
                        output=output.rename(columns={'Protein':"sorted_list_protein"})

                        #return protein info from first match in sorted_proteins (so that the order of assignment for these peptides is the same for all)
                        sorted_list_hit=find_first_common_element(list1=sorted_list,list2=sorted_proteins)
                        output=output[output['sorted_list_protein']==sorted_list_hit]


        sorted_mapping.append(output)

    sorted_mapping=pd.concat(sorted_mapping,ignore_index=True)

    return(sorted_mapping)