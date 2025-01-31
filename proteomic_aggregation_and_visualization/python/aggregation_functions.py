#!venv/bin python

#packages used in these functions
import requests
import pandas as pd
from io import StringIO
import re
import numpy as np
from scipy.optimize import minimize
import seaborn as sns
import matplotlib.pyplot as plt


def get_first_page_results(collection: str, filter: str, max_page_size: int, fields: str):

    """
    Define a general API call function to nmdc-runtime
     This function provides a general-purpose way to make an API request to NMDC's runtime API. Note that this 
     function will only return the first page of results. The function's input includes the name of the collection to access (e.g. `biosample_set`), 
     the filter to be performed, the maximum page size, and a list of the fields to be retrieved. It returns the metadata as a json object.
    """

    og_url = f'https://api.microbiomedata.org/nmdcschema/{collection}?&filter={filter}&max_page_size={max_page_size}&projection={fields}'
    resp = requests.get(og_url)
    data = resp.json()
    
    return data


def get_next_results(collection: str, filter: str, max_page_size: int, fields: str):

    """
    Define an nmdc-runtime API call function to include pagination
     The `get_next_results` function uses the `get_first_page_results` function, defined above, 
     to retrieve the rest of the results from a call with multiple pages. It takes the same inputs as 
     the `get_first_page_results` function above: the name of the collection to be retrieved, the filter string, 
     the maximum page size, and a list of the fields to be returned. This function returns the list of the results.
     It uses the `next_page_token` key in each page of results to retrieve the following page.
    """

    # Get initial results (before next_page_token is given in the results)
    result_list = []
    initial_data = get_first_page_results(collection, filter, max_page_size, fields)
    results = initial_data["resources"]
    
    # append first page of results to an empty list
    for result in results:
        result_list.append(result)
    
    # if there are multiple pages of results returned
    if initial_data.get("next_page_token"):
        next_page_token = initial_data["next_page_token"]

        while True:
            url = f'https://api.microbiomedata.org/nmdcschema/{collection}?&filter={filter}&max_page_size={max_page_size}&page_token={next_page_token}&projection={fields}'
            response = requests.get(url)
            data_next = response.json()
            
            results = data_next.get("resources", [])
            result_list.extend(results)
            next_page_token = data_next.get("next_page_token")
        
            if not next_page_token:
                break

    return result_list


def split_list(input_list, chunk_size=100):

    """
    Define a function to split a list into chunks 
     Since we will need to use a list of ids to query a new collection in the API, we need to limit the number of ids we put in a query. 
     This function splits a list into chunks of 100. Note that the `chunk_size` has a default of 100, but can be adjusted.
    """
    
    result = []
    
    for i in range(0, len(input_list), chunk_size):
        result.append(input_list[i:i + chunk_size])
        
    return result



def string_mongo_list(a_list: list):

    """
    Define a function to use double quotation marks
     Since the mongo-like filtering criteria for the API requests require double quotation marks (") instead of 
     single quotation marks ('), a function is defined to replace single quotes with double quotes to properly 
     structure a mongo filter paramter. The function takes a list (usually of ids) and returns a string with the 
     ids listed with double quotation marks. E.g the input is `['A','B','C']` and the output would be `'"A","B",C"'`.
    """
    
    string_with_double_quotes = str(a_list).replace("'", '"')

    return string_with_double_quotes



def get_id_list(result_list: list, id_name: str):
    """
    Define a function to get a list of ids from initial results
     In order to use the identifiers retrieved from an initial API request in another API request, this function is defined to 
     take the initial request results and use the `id_name` key from the results to create a list of all the ids. The input 
     is the initial result list and the name of the id field.
    """
    id_list = []
    for item in result_list:
        if type(item[id_name]) == str:
            id_list.append(item[id_name])
        elif type(item[id_name]) == list:
            for another_item in item[id_name]:
                id_list.append(another_item)

    return id_list


def get_id_results(newest_results: list, id_field: str, query_collection: str, match_id_field: str, query_fields: str):

    """
    Define an API request function that uses a list of ids to filter a new collection
     This function takes the `newest_results` request (e.g. `biosamples`) and 
     constructs a list of ids using `get_id_results`.
     It then uses the `split_list` function to chunk the list of ids into sets of 100 to query the API. 
     `id_field` is a field in `newest_results` containing the list of ids to search for in the query_collection (e.g. `biosample_id`).
     `match_id_field` is the field in query_collection that will be searched. query_fields is a list of the fields to be returned.
    """

    # split old results into list
    result_ids = get_id_list(newest_results, id_field)

    # chunk up the results into sets of 100 using the split_list function and call the get_first_page_results function and append
    # results to list
    chunked_list = split_list(result_ids)
    next_results = []
    for chunk in chunked_list:
        filter_string = string_mongo_list(chunk)
        # quotes around match_id_field need to look a lot different for the final data object query
        if "data_object_type" in match_id_field:
            data = get_first_page_results(query_collection, f'{{{match_id_field}: {{"$in": {filter_string}}}}}', 100, query_fields)
        else: 
            data = get_first_page_results(query_collection, f'{{"{match_id_field}": {{"$in": {filter_string}}}}}', 100, query_fields)
        next_results.extend(data["resources"])

    return next_results



def findproteinname(s):

    """
    Define a function to detect protein type (forward, reverse, contaminant) from a protein name (s)
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

def sequence_nopostpre(s):

    """
    Peptide Sequence with Mods is the sequence without prefix and postfix but with oxidation
    :param s:
    :return:
    """
    p = re.compile(r"\.(?P<cleanseq>[A-Z\*@#]+)\.")
    m = p.search(s)
    return m.group("cleanseq")


def tsv_extract(identifier_col:str,url_col:str,extract_cols:list,pd_df:pd.DataFrame,header=None):

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
            response = requests.get(url)
            tsv_data = StringIO(response.text)
            tsv_df = pd.read_csv(tsv_data,sep='\t',header=header)
            tsv_data.close()

            #get the relevant data
            tsv_subset = tsv_df.loc[:,extract_cols]


            #double check that subset will have unique rows
            if len(tsv_subset)!=len(tsv_subset.drop_duplicates()):
                break
            
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
    Function to compute the FDR and return a value for optimization.
    
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
    Function to return a spectral probablity value that optimizes FDR via the specFiltValue function.

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



    
def visualize_optimization(optimize_output,forward_peptides:pd.DataFrame,reversed_peptides:pd.DataFrame):

    """
    Function to visualize the impact of a spectral probability filter
    
    :param optimize_output: output from optimize_specFilt()
    :param reversed_peptides: DataFrame of reversed peptides (not optimized)
    :param forward_peptides: DataFrame of forward peptides (not optimized)
    """

    fitted_params=optimize_output.x

    fig, ax_main = plt.subplots()

    ax_inset = plt.axes([0.45, 0.45, 0.35, 0.35])


    #add plot content

    for ax in ax_main, ax_inset:

        #forward peptides
        sns.kdeplot(
        forward_peptides["MSGFDB_SpecEValue"], label="forward peptides\nretained", ax=ax, color="green"
        )

        #reverse peptides
        sns.kdeplot(
        reversed_peptides["MSGFDB_SpecEValue"], label="reverse peptides\nretained", ax=ax, color="red"
        )

        #filter cutoff
        ax.axvline(x=10 ** fitted_params[0], color="black", label = 'filter cutoff', linestyle="--")


    # move legend to the bottom of the main plot and add title
    ax_main.legend(bbox_to_anchor=(0.5, -0.2), loc='upper center', ncol=2,fontsize='x-small')
    ax_main.set_title('impact of imposing optimized spectral probability filter')



    # for the inset/zoom plot:

    # zoom the inset into the area around the cutoff and peptide count peak
    x_min, x_max = ax_inset.get_xlim()
    ax_inset.set_xlim([x_min/2, 2 * 10 ** -8])


    #find peak count
    x = ax_main.lines[0].get_xdata() # Get the x data of the distribution
    y = ax_main.lines[0].get_ydata() # Get the y data of the distribution
    maxid = np.argmax(y) # The id of the peak (maximum of y data)
    peak_fspece=x[maxid]

    #calculate fdr for data around peak (iterating through all options takes a LONG time)
    specelist = np.linspace(0, peak_fspece, 200)
    specedf=[]
    for spece in specelist:
        df_r = reversed_peptides[reversed_peptides["MSGFDB_SpecEValue"] < spece].copy()
        df_f = forward_peptides[forward_peptides["MSGFDB_SpecEValue"] < spece].copy()
        f_spec = (df_f["SpecID"].unique().size)  # Modified on Apr23 to only count for unique dataset-scan
        r_spec = df_r["SpecID"].unique().size
        if (f_spec == 0) & (r_spec == 0):
            fdr_spec = 1
        else:
            fdr_spec = (2*r_spec) / (f_spec + r_spec)

        specedf.append(pd.DataFrame({'MSGFDB_SpecEValue':[spece],'fdr':[fdr_spec]}))
        
    specedf=pd.DataFrame(pd.concat(specedf))


    #add fdr to the inset plot
    ax_fdr=ax_inset.twinx()
    sns.lineplot(
        #plot fdr between optimized cutoff and peak of forward peptides
        data= specedf[specedf['fdr']!=1.0], x='MSGFDB_SpecEValue', y='fdr', color='purple',ax=ax_fdr,label='fdr'
    )
    plt.legend(fontsize='x-small')




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